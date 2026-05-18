"""core/audit.py — Helios v0.2: lightweight audit log primitive.

Closes the B2D productization gap surfaced in the Glyph audit:
even a narrow audit_log shape (action, target, reason, timestamp, namespace)
unblocks the "who touched what when" question hosted-API customers ask.

Write convention: best-effort, never block the caller's write path on failure.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from core.db import connect


def write_audit(
    action: str,
    target_kind: str,
    target_ref: Optional[str] = None,
    actor_ref: str = "default",
    namespace: str = "default",
    reason: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> int:
    """Record an audit entry. Returns the new audit_log.id, or -1 on failure."""
    md_json = json.dumps(metadata) if metadata else None
    try:
        with connect() as cx:
            cur = cx.execute(
                "INSERT INTO audit_log "
                "(timestamp, actor_ref, namespace, action, target_kind, target_ref, reason, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (time.time(), actor_ref, namespace, action, target_kind, target_ref, reason, md_json),
            )
            return cur.lastrowid
    except Exception:
        return -1   # audit must never block the write path


def list_audit(
    namespace: str = "default",
    since: float = 0.0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List audit entries newest-first."""
    with connect() as cx:
        rows = cx.execute(
            "SELECT id, timestamp, actor_ref, namespace, action, target_kind, "
            "target_ref, reason, metadata FROM audit_log "
            "WHERE namespace = ? AND timestamp > ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (namespace, since, limit),
        ).fetchall()
    return [{
        "id":          r["id"],
        "timestamp":   r["timestamp"],
        "actor_ref":   r["actor_ref"],
        "namespace":   r["namespace"],
        "action":      r["action"],
        "target_kind": r["target_kind"],
        "target_ref":  r["target_ref"],
        "reason":      r["reason"],
        "metadata":    json.loads(r["metadata"]) if r["metadata"] else None,
    } for r in rows]
