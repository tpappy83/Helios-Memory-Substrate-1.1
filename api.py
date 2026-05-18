"""api.py — Helios FastAPI surface (port 8000).

v0.2 additions:
- Namespace threading on memory routes (X-Namespace header > ?namespace= query)
- GET /stats — runtime introspection
- PATCH /config/retrieval — live reranker weight tuning
- POST /memory/batch — batch ingest with per-item error capture
- GET /memory/{id}, DELETE /memory/{id} — namespace-gated
- GET /audit, GET /events — audit log + frontend event stream
- latency_ms in response bodies
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Path as PathParam, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.db import init_schema, resource_path, connect
from core import memory as memory_mod
from core import llm as llm_mod
from core import tiering
from core import audit as audit_mod
from core import tenants as tenants_mod
from core.tenants import (
    TenantContext, DEFAULT_TENANT_ID,
    create_tenant, get_tenant, get_tenant_by_email,
    create_api_key, verify_api_key, list_api_keys, revoke_api_key,
)

app = FastAPI(title="Helios", version="0.3.0")


@app.on_event("startup")
def _startup():
    init_schema()


def _require_key(x_openrouter_key: Optional[str] = Header(None)) -> str:
    """Pass-through OpenRouter key header. No auth issuance in v0.2 yet."""
    return x_openrouter_key or ""


def _resolve_namespace(
    header_ns: Optional[str] = Header(None, alias="X-Namespace"),
    query_ns: Optional[str] = Query(None, alias="namespace"),
) -> str:
    """X-Namespace header takes precedence over ?namespace= query.

    NOTE: this is the v0.2 unauthenticated path. When `Authorization: Bearer <api_key>`
    is provided, _require_tenant() takes precedence and forces namespace = tenant_id,
    ignoring any X-Namespace or ?namespace= passed by the client.
    """
    return header_ns or query_ns or "default"


def _require_tenant(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_namespace:    Optional[str] = Header(None, alias="X-Namespace"),
    namespace:      Optional[str] = Query(None, alias="namespace"),
) -> TenantContext:
    """Resolve TenantContext from Authorization: Bearer <api_key>.

    - If a valid API key is presented: forces namespace = tenant_id (header/query ignored)
    - If no API key: falls back to local-first single-tenant mode with X-Namespace honored
    - If an invalid API key is presented: raises HTTPException(401)
    """
    raw_key: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization[7:].strip()
    try:
        ctx = tenants_mod.resolve_tenant_context(
            raw_key,
            fallback_namespace=x_namespace or namespace,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return ctx


# ─── Health ───────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}


# ─── Tenant lifecycle (v0.3) ─────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    name: str


class SignupResponse(BaseModel):
    tenant_id: str
    email:     str
    name:      str
    api_key:   str    # Raw key, shown ONCE
    key_id:    str
    key_prefix: str


@app.post("/signup", response_model=SignupResponse, status_code=201)
def signup(body: SignupRequest):
    """Create a new tenant + first API key. Returns the raw key ONCE — store it now."""
    try:
        tenant = create_tenant(email=body.email, name=body.name)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    key, raw = create_api_key(tenant.id, name="default")
    return SignupResponse(
        tenant_id=tenant.id, email=tenant.email, name=tenant.name,
        api_key=raw, key_id=key.id, key_prefix=key.prefix,
    )


class TokenCreate(BaseModel):
    name: str = "secondary"


class TokenOut(BaseModel):
    id:           str
    prefix:       str
    name:         str
    created_at:   float
    last_used_at: Optional[float] = None
    revoked_at:   Optional[float] = None


class TokenCreatedResponse(BaseModel):
    api_key: str
    key:     TokenOut


@app.post("/tokens", response_model=TokenCreatedResponse, status_code=201)
def create_token(body: TokenCreate, ctx: TenantContext = Depends(_require_tenant)):
    """Create a new API key for the authenticated tenant. Raw key shown ONCE."""
    if not ctx.authenticated:
        raise HTTPException(status_code=401, detail="Authentication required to create new tokens")
    key, raw = create_api_key(ctx.tenant_id, name=body.name)
    audit_mod.write_audit(
        action="apikey.create", target_kind="api_key", target_ref=key.id,
        actor_ref=ctx.actor_ref, namespace=ctx.tenant_id,
        reason=f"name={body.name}",
    )
    return TokenCreatedResponse(
        api_key=raw,
        key=TokenOut(
            id=key.id, prefix=key.prefix, name=key.name,
            created_at=key.created_at,
        ),
    )


@app.get("/tokens", response_model=list[TokenOut])
def list_tokens(
    include_revoked: bool = Query(False),
    ctx: TenantContext = Depends(_require_tenant),
):
    if not ctx.authenticated:
        raise HTTPException(status_code=401, detail="Authentication required to list tokens")
    keys = list_api_keys(ctx.tenant_id, include_revoked=include_revoked)
    return [
        TokenOut(
            id=k.id, prefix=k.prefix, name=k.name,
            created_at=k.created_at, last_used_at=k.last_used_at, revoked_at=k.revoked_at,
        )
        for k in keys
    ]


@app.delete("/tokens/{key_id}", status_code=204)
def revoke_token(key_id: str, ctx: TenantContext = Depends(_require_tenant)):
    if not ctx.authenticated:
        raise HTTPException(status_code=401, detail="Authentication required to revoke tokens")
    if not revoke_api_key(key_id, ctx.tenant_id):
        raise HTTPException(status_code=404, detail=f"Key {key_id!r} not found or already revoked")
    audit_mod.write_audit(
        action="apikey.revoke", target_kind="api_key", target_ref=key_id,
        actor_ref=ctx.actor_ref, namespace=ctx.tenant_id,
        reason="user_requested",
    )
    return None


@app.get("/me")
def whoami(ctx: TenantContext = Depends(_require_tenant)):
    """Return the authenticated tenant identity, or {authenticated: false} for local."""
    tenant = get_tenant(ctx.tenant_id) if ctx.authenticated else None
    return {
        "authenticated": ctx.authenticated,
        "tenant_id":     ctx.tenant_id,
        "email":         tenant.email if tenant else None,
        "name":          tenant.name if tenant else None,
        "api_key_id":    ctx.api_key_id,
    }


# ─── Stats (v0.2 — runtime introspection) ─────────────────────────

class StatsResponse(BaseModel):
    record_count:      int
    namespace_count:   int
    tier_distribution: dict[str, int]
    reranker_weights:  dict[str, float]
    schema_version:    int


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    with connect() as cx:
        rcount = cx.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0]
        ncount = cx.execute("SELECT COUNT(DISTINCT namespace) FROM memory_records").fetchone()[0]
        schema_ver = cx.execute("PRAGMA user_version").fetchone()[0]
    return StatsResponse(
        record_count=rcount,
        namespace_count=ncount,
        tier_distribution=tiering.tier_distribution(),
        reranker_weights=tiering.reranker_weights(),
        schema_version=schema_ver,
    )


# ─── Live config tuning (v0.2) ────────────────────────────────────

class RetrievalConfig(BaseModel):
    w_similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_value:      Optional[float] = Field(None, ge=0.0, le=1.0)
    w_recency:    Optional[float] = Field(None, ge=0.0, le=1.0)
    w_tier:       Optional[float] = Field(None, ge=0.0, le=1.0)
    w_drift:      Optional[float] = Field(None, ge=0.0, le=1.0)


@app.patch("/config/retrieval")
def update_retrieval_config(body: RetrievalConfig):
    """Live-tune reranker weights without restart. Module-level constants in core.tiering."""
    diff = {}
    if body.w_similarity is not None: tiering.W_SIMILARITY = body.w_similarity; diff["w_similarity"] = body.w_similarity
    if body.w_value      is not None: tiering.W_VALUE      = body.w_value;      diff["w_value"]      = body.w_value
    if body.w_recency    is not None: tiering.W_RECENCY    = body.w_recency;    diff["w_recency"]    = body.w_recency
    if body.w_tier       is not None: tiering.W_TIER       = body.w_tier;       diff["w_tier"]       = body.w_tier
    if body.w_drift      is not None: tiering.W_DRIFT      = body.w_drift;      diff["w_drift"]      = body.w_drift

    audit_mod.write_audit(
        action="config.update", target_kind="config",
        target_ref="retrieval", namespace="system",
        reason=str(diff),
    )
    return {"success": True, "weights": tiering.reranker_weights()}


# ─── Memory CRUD ──────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    content: str
    type: str = Field(default="observation")
    metadata: dict = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryOut(BaseModel):
    id: str
    type: str
    content: str
    metadata: dict
    timestamp: float
    importance: float
    namespace: str
    tier: str
    temperature: float


@app.post("/memory", response_model=MemoryOut, status_code=201)
def create_memory(
    body: MemoryCreate,
    namespace: str = Depends(_resolve_namespace),
    _key: str = Depends(_require_key),
):
    rid = memory_mod.write_memory(
        content=body.content, type=body.type,
        metadata=body.metadata, importance=body.importance,
        namespace=namespace,
    )
    return _memory_out(rid)


def _memory_out(rid: str) -> MemoryOut:
    with connect() as cx:
        r = cx.execute(
            "SELECT id, type, content, metadata, timestamp, importance, "
            "namespace, tier, temperature FROM memory_records WHERE id = ?",
            (rid,),
        ).fetchone()
    return MemoryOut(
        id=r["id"], type=r["type"], content=r["content"],
        metadata=json.loads(r["metadata"]), timestamp=r["timestamp"],
        importance=r["importance"], namespace=r["namespace"],
        tier=r["tier"], temperature=r["temperature"],
    )


@app.get("/memory", response_model=list[MemoryOut])
def list_memory(
    limit: int = Query(10, ge=1, le=500),
    namespace: str = Depends(_resolve_namespace),
):
    with connect() as cx:
        rows = cx.execute(
            "SELECT id FROM memory_records WHERE namespace = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (namespace, limit),
        ).fetchall()
    return [_memory_out(r["id"]) for r in rows]


class BatchIngestItem(BaseModel):
    content: str
    type: str = "observation"
    importance: float = Field(0.5, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class BatchIngestResponse(BaseModel):
    results: list[dict]
    success_count: int
    error_count: int
    latency_ms: float


@app.post("/memory/batch", response_model=BatchIngestResponse, status_code=201)
def memory_batch_ingest(
    items: list[BatchIngestItem],
    namespace: str = Depends(_resolve_namespace),
):
    t0 = time.perf_counter()
    results, succ, err = [], 0, 0
    for it in items:
        try:
            mid = memory_mod.write_memory(
                content=it.content, type=it.type,
                metadata=it.metadata, importance=it.importance,
                namespace=namespace,
            )
            results.append({"success": True, "id": mid})
            succ += 1
        except Exception as exc:
            results.append({"success": False, "error": str(exc)})
            err += 1
    return BatchIngestResponse(
        results=results, success_count=succ, error_count=err,
        latency_ms=(time.perf_counter() - t0) * 1000.0,
    )


@app.get("/memory/{record_id}", response_model=MemoryOut)
def get_memory_route(
    record_id: str = PathParam(...),
    namespace: str = Depends(_resolve_namespace),
):
    with connect() as cx:
        r = cx.execute(
            "SELECT id FROM memory_records WHERE id = ? AND namespace = ?",
            (record_id, namespace),
        ).fetchone()
    if r is None:
        raise HTTPException(
            status_code=404,
            detail=f"No record id={record_id!r} in namespace={namespace!r}",
        )
    return _memory_out(record_id)


@app.delete("/memory/{record_id}", status_code=204)
def delete_memory_route(
    record_id: str = PathParam(...),
    namespace: str = Depends(_resolve_namespace),
):
    deleted = memory_mod.delete_memory(record_id, namespace=namespace)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No record id={record_id!r} in namespace={namespace!r}",
        )
    return None


# ─── Chat (non-streaming + streaming) ─────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    memory_id: Optional[str] = None
    latency_ms: float


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, _key: str = Depends(_require_key)):
    t0 = time.perf_counter()
    reply = llm_mod.chat_response(body.message)
    return ChatResponse(
        response=reply,
        latency_ms=(time.perf_counter() - t0) * 1000.0,
    )


@app.post("/chat/stream")
def chat_stream(body: ChatRequest, _key: str = Depends(_require_key)):
    def gen():
        t0 = time.perf_counter()
        for event in llm_mod.chat_response_stream(body.message):
            if event["type"] == "done":
                event["latency_ms"] = (time.perf_counter() - t0) * 1000.0
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


# ─── Sessions ─────────────────────────────────────────────────────

@app.get("/sessions/{session_id}")
def get_session(session_id: str, limit: int = Query(100, ge=1, le=1000)):
    msgs = memory_mod.list_session(session_id, limit=limit)
    return [m.__dict__ for m in msgs]


# ─── Audit log + event stream (v0.2) ──────────────────────────────

@app.get("/audit")
def get_audit_log(
    namespace: str = Depends(_resolve_namespace),
    since: float = Query(0.0, ge=0.0),
    limit: int = Query(50, ge=1, le=500),
):
    entries = audit_mod.list_audit(namespace=namespace, since=since, limit=limit)
    return {"entries": entries, "namespace": namespace, "count": len(entries)}


@app.get("/events")
def get_events(
    namespace: str = Depends(_resolve_namespace),
    since: float = Query(0.0, ge=0.0),
    limit: int = Query(20, ge=1, le=100),
):
    """Live event stream alias for the frontend event log component."""
    entries = audit_mod.list_audit(namespace=namespace, since=since, limit=limit)
    return [{
        "timestamp":  e["timestamp"],
        "type":       e["action"].split(".")[-1],
        "message":    e["reason"] or "",
        "target_ref": e["target_ref"],
    } for e in entries]


# ─── Static frontend auto-mount ───────────────────────────────────

_frontend_path = resource_path("frontend")
if Path(_frontend_path).is_dir():
    app.mount("/ui", StaticFiles(directory=_frontend_path, html=True), name="ui")
