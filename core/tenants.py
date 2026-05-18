"""core/tenants.py — Helios v0.3 multi-tenant control plane.

Implements:
- TenantContext: per-request authoritative tenant identity (forces namespace = tenant_id)
- create_tenant / get_tenant: tenant lifecycle
- create_api_key / verify_api_key / revoke_api_key: API key lifecycle
- API key format: hel_<prefix>_<random36chars>; SHA-256 hashed in DB; raw shown to user once

Per the research blueprint (Crucible §5.2):
- Multi-tenant scaffolding explicitly violates wedge #1 (local-first) when deployed
  against multiple tenants. The synthetic SQLite environment uses LOGICAL isolation
  via namespace=tenant_id enforced at the auth layer. Production deployment uses
  Postgres schema-per-tenant with `search_path` manipulation (not implemented in the
  synthetic; see deployment notes in this module's docstring).
- The "default" tenant is bootstrapped by the v3 migration for backward compat with
  the single-tenant local-first code path.

Security notes:
- Raw API key is shown to the user ONCE on /signup and /tokens POST. Never persisted.
- key_hash is SHA-256 of the full raw key. Equality check is constant-time.
- prefix (first 12 chars including 'hel_' marker) is stored for UI display. Like
  Stripe's `sk_live_AAA...` pattern — operator can identify which key without seeing
  the full secret.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from core.db import connect


API_KEY_PREFIX = "hel_"        # Helios marker
API_KEY_PREFIX_LEN = 12        # Stored prefix length (e.g., "hel_AbCd1234")
API_KEY_BODY_LEN = 36          # Random bytes after the prefix (URL-safe base64)
DEFAULT_TENANT_ID = "default"  # Backward-compat single-tenant


# ─── Data classes ────────────────────────────────────────────────────

@dataclass
class Tenant:
    id:         str
    email:      str
    name:       str
    created_at: float
    status:     str
    metadata:   dict


@dataclass
class ApiKey:
    id:           str
    tenant_id:    str
    key_hash:     str
    prefix:       str
    name:         str
    created_at:   float
    last_used_at: Optional[float] = None
    revoked_at:   Optional[float] = None


@dataclass
class TenantContext:
    """Per-request authoritative tenant identity. Use as a FastAPI dependency.

    When an authenticated request arrives:
    - tenant_id is forced to the API key's owning tenant (any X-Namespace header is ignored)
    - any subsequent memory write/read is scoped to this tenant_id

    When an unauthenticated request arrives (local-first):
    - tenant_id defaults to "default"
    - X-Namespace header is honored for compatibility
    """
    tenant_id:    str
    authenticated: bool
    api_key_id:   Optional[str] = None
    actor_ref:    str = "default"


# ─── Helpers ──────────────────────────────────────────────────────────

def _generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (raw_key, prefix, sha256_hex)."""
    body = secrets.token_urlsafe(API_KEY_BODY_LEN)
    raw = API_KEY_PREFIX + body
    prefix = raw[:API_KEY_PREFIX_LEN]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, prefix, digest


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# ─── Tenant lifecycle ─────────────────────────────────────────────────

def create_tenant(email: str, name: str, metadata: Optional[dict] = None) -> Tenant:
    """Create a new tenant. Raises ValueError if email exists."""
    tid = str(uuid.uuid4())
    md_json = json.dumps(metadata or {})
    now = time.time()
    with connect() as cx:
        try:
            cx.execute(
                "INSERT INTO tenants (id, email, name, created_at, status, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (tid, email, name, now, "active", md_json),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise ValueError(f"Tenant with email={email!r} already exists") from exc
            raise
    return Tenant(id=tid, email=email, name=name, created_at=now, status="active", metadata=metadata or {})


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    with connect() as cx:
        r = cx.execute(
            "SELECT id, email, name, created_at, status, metadata FROM tenants WHERE id = ?",
            (tenant_id,),
        ).fetchone()
    if r is None:
        return None
    return Tenant(
        id=r["id"], email=r["email"], name=r["name"],
        created_at=r["created_at"], status=r["status"],
        metadata=json.loads(r["metadata"]),
    )


def get_tenant_by_email(email: str) -> Optional[Tenant]:
    with connect() as cx:
        r = cx.execute(
            "SELECT id, email, name, created_at, status, metadata FROM tenants WHERE email = ?",
            (email,),
        ).fetchone()
    if r is None:
        return None
    return Tenant(
        id=r["id"], email=r["email"], name=r["name"],
        created_at=r["created_at"], status=r["status"],
        metadata=json.loads(r["metadata"]),
    )


# ─── API key lifecycle ────────────────────────────────────────────────

def create_api_key(tenant_id: str, name: str = "default") -> tuple[ApiKey, str]:
    """Create a new API key for a tenant.

    Returns (ApiKey record, RAW_KEY). The raw key is shown to the user ONCE
    and never persisted in plaintext. Future verification uses the hash.
    """
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id!r} not found")
    if tenant.status != "active":
        raise ValueError(f"Tenant {tenant_id!r} is not active (status={tenant.status})")

    kid = str(uuid.uuid4())
    raw, prefix, digest = _generate_api_key()
    now = time.time()
    with connect() as cx:
        cx.execute(
            "INSERT INTO api_keys (id, tenant_id, key_hash, prefix, name, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (kid, tenant_id, digest, prefix, name, now),
        )
    return ApiKey(
        id=kid, tenant_id=tenant_id, key_hash=digest, prefix=prefix,
        name=name, created_at=now, last_used_at=None, revoked_at=None,
    ), raw


def verify_api_key(raw_key: Optional[str]) -> Optional[ApiKey]:
    """Look up an API key by its raw value. Returns None if invalid/revoked.

    Updates last_used_at on successful verification (best-effort, not blocking).
    """
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        return None
    digest = _hash_key(raw_key)
    with connect() as cx:
        r = cx.execute(
            "SELECT id, tenant_id, key_hash, prefix, name, created_at, last_used_at, revoked_at "
            "FROM api_keys WHERE key_hash = ?",
            (digest,),
        ).fetchone()
    if r is None:
        return None
    # Constant-time comparison guard (digest matched the index, but check explicitly)
    if not hmac.compare_digest(r["key_hash"], digest):
        return None
    if r["revoked_at"] is not None:
        return None
    # Tenant must be active
    tenant = get_tenant(r["tenant_id"])
    if tenant is None or tenant.status != "active":
        return None
    # Touch last_used_at (best-effort)
    try:
        with connect() as cx:
            cx.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (time.time(), r["id"]),
            )
    except Exception:
        pass  # auth must not fail on touch failure
    return ApiKey(
        id=r["id"], tenant_id=r["tenant_id"], key_hash=r["key_hash"], prefix=r["prefix"],
        name=r["name"], created_at=r["created_at"],
        last_used_at=r["last_used_at"], revoked_at=r["revoked_at"],
    )


def list_api_keys(tenant_id: str, include_revoked: bool = False) -> list[ApiKey]:
    with connect() as cx:
        if include_revoked:
            rows = cx.execute(
                "SELECT id, tenant_id, key_hash, prefix, name, created_at, last_used_at, revoked_at "
                "FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
        else:
            rows = cx.execute(
                "SELECT id, tenant_id, key_hash, prefix, name, created_at, last_used_at, revoked_at "
                "FROM api_keys WHERE tenant_id = ? AND revoked_at IS NULL ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
    return [
        ApiKey(
            id=r["id"], tenant_id=r["tenant_id"], key_hash=r["key_hash"], prefix=r["prefix"],
            name=r["name"], created_at=r["created_at"],
            last_used_at=r["last_used_at"], revoked_at=r["revoked_at"],
        )
        for r in rows
    ]


def revoke_api_key(api_key_id: str, tenant_id: str) -> bool:
    """Revoke an API key. Returns True if revoked, False if not found / already revoked
    / doesn't belong to this tenant.
    """
    with connect() as cx:
        # Confirm the key belongs to this tenant
        r = cx.execute(
            "SELECT id, revoked_at FROM api_keys WHERE id = ? AND tenant_id = ?",
            (api_key_id, tenant_id),
        ).fetchone()
        if r is None or r["revoked_at"] is not None:
            return False
        cx.execute(
            "UPDATE api_keys SET revoked_at = ? WHERE id = ?",
            (time.time(), api_key_id),
        )
    return True


# ─── Context resolution ──────────────────────────────────────────────

def resolve_tenant_context(
    api_key_header: Optional[str],
    fallback_namespace: Optional[str] = None,
) -> TenantContext:
    """Convert an incoming API key header + optional X-Namespace into a TenantContext.

    - If api_key is valid: tenant_id = key's owning tenant; fallback_namespace IGNORED
    - If api_key is invalid (provided but wrong): raise (caller should 401)
    - If api_key absent: tenant_id = "default" or fallback_namespace if set (local-first compat)
    """
    if api_key_header:
        key = verify_api_key(api_key_header)
        if key is None:
            # Caller should translate to HTTPException(401)
            raise PermissionError("Invalid or revoked API key")
        return TenantContext(
            tenant_id=key.tenant_id,
            authenticated=True,
            api_key_id=key.id,
            actor_ref=key.id,
        )
    return TenantContext(
        tenant_id=fallback_namespace or DEFAULT_TENANT_ID,
        authenticated=False,
        api_key_id=None,
        actor_ref=fallback_namespace or DEFAULT_TENANT_ID,
    )


# ─── Production deployment notes (not implemented in synthetic) ──────
#
# In production (Postgres), schema-per-tenant routing requires:
#
#   1. On tenant creation: CREATE SCHEMA tenant_<id>; clone the canonical
#      tables (memory_records, chat_history, audit_log) into the new schema.
#   2. On each authenticated request: SET search_path TO tenant_<tenant_id>, public;
#      so all `SELECT ... FROM memory_records` queries hit the tenant's schema.
#   3. Migrations: a tooling layer iterates over all tenant schemas and applies
#      each migration.
#
# The synthetic SQLite implementation uses LOGICAL isolation only (namespace =
# tenant_id column on memory_records). This is sufficient for the audit/test/demo
# but does NOT provide the cryptographic isolation of schema-per-tenant.
#
# Migration path (per Crucible §5):
#   v0.3.0: TenantContext in code, single-DB logical isolation (THIS)
#   v0.3.1: tenants + api_keys tables (THIS)
#   v0.3.2: Postgres backend + schema-per-tenant (future)
#   v0.3.3: Qdrant payload partitioning (see core/qdrant_client.py)
#   v0.4+:  Per-tenant envelope encryption for regulated tier
