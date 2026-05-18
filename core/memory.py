"""core/memory.py — Memory + ChatMessage dataclasses + CRUD.

The five fixed memory types (event/state/summary/decision/observation) are
enforced via the CHECK constraint on memory_records.type. Roles on chat_history
similarly constrained.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from core.db import connect
from core import audit

VALID_TYPES = {"event", "state", "summary", "decision", "observation"}
VALID_ROLES = {"user", "assistant", "system"}


@dataclass
class Memory:
    id:         str
    type:       str
    content:    str
    metadata:   dict
    timestamp:  float
    importance: float = 0.5


@dataclass
class ChatMessage:
    id:         Optional[int]
    session_id: str
    role:       str
    content:    str
    timestamp:  float
    metadata:   dict = field(default_factory=dict)


def write_memory(
    content: str,
    type: str = "observation",
    metadata: Optional[dict] = None,
    importance: float = 0.5,
    namespace: str = "default",
) -> str:
    """Persist a new memory record. Returns the generated record id."""
    if type not in VALID_TYPES:
        raise ValueError(f"Invalid memory type: {type!r}; must be one of {sorted(VALID_TYPES)}")
    rid = str(uuid.uuid4())
    md_json = json.dumps(metadata or {})
    with connect() as cx:
        cx.execute(
            "INSERT INTO memory_records (id, type, content, metadata, timestamp, importance, namespace) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rid, type, content, md_json, time.time(), importance, namespace),
        )
    audit.write_audit(
        action="memory.write", target_kind="memory_record",
        target_ref=rid, namespace=namespace,
        reason=f"type={type}",
    )
    return rid


def list_recent(limit: int = 10, namespace: Optional[str] = None) -> list[Memory]:
    """Return the N most recent memory records."""
    with connect() as cx:
        rows = cx.execute(
            "SELECT id, type, content, metadata, timestamp, importance "
            "FROM memory_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        Memory(
            id=r["id"], type=r["type"], content=r["content"],
            metadata=json.loads(r["metadata"]),
            timestamp=r["timestamp"], importance=r["importance"],
        )
        for r in rows
    ]


def get_memory(record_id: str) -> Optional[Memory]:
    """Fetch a single memory by id."""
    with connect() as cx:
        r = cx.execute(
            "SELECT id, type, content, metadata, timestamp, importance "
            "FROM memory_records WHERE id = ?", (record_id,),
        ).fetchone()
    if r is None:
        return None
    return Memory(
        id=r["id"], type=r["type"], content=r["content"],
        metadata=json.loads(r["metadata"]),
        timestamp=r["timestamp"], importance=r["importance"],
    )


def delete_memory(record_id: str, namespace: str = "default") -> bool:
    """Delete a memory record. Returns True if it existed in the given namespace."""
    with connect() as cx:
        # Confirm record belongs to this namespace before deleting
        existing = cx.execute(
            "SELECT id FROM memory_records WHERE id = ? AND namespace = ?",
            (record_id, namespace),
        ).fetchone()
        if existing is None:
            return False
        cur = cx.execute(
            "DELETE FROM memory_records WHERE id = ? AND namespace = ?",
            (record_id, namespace),
        )
        deleted = cur.rowcount > 0
    if deleted:
        audit.write_audit(
            action="memory.delete", target_kind="memory_record",
            target_ref=record_id, namespace=namespace,
            reason="user_requested",
        )
    return deleted


def keyword_candidates(query: str, k: int = 25) -> list[Memory]:
    """FTS5 keyword candidate generation. Returns up to k Memory objects."""
    # Sanitize query: whitespace tokens → quoted phrases, OR-combined
    parts = [f'"{t.strip()}"' for t in query.split() if t.strip()]
    if not parts:
        return []
    fts_query = " OR ".join(parts)
    with connect() as cx:
        rows = cx.execute(
            "SELECT m.id, m.type, m.content, m.metadata, m.timestamp, m.importance "
            "FROM memory_records m "
            "JOIN memory_records_fts fts ON m.rowid = fts.rowid "
            "WHERE memory_records_fts MATCH ? "
            "ORDER BY rank LIMIT ?",
            (fts_query, k),
        ).fetchall()
    return [
        Memory(
            id=r["id"], type=r["type"], content=r["content"],
            metadata=json.loads(r["metadata"]),
            timestamp=r["timestamp"], importance=r["importance"],
        )
        for r in rows
    ]


def write_chat(session_id: str, role: str, content: str, metadata: Optional[dict] = None) -> int:
    """Append a chat turn to chat_history. Returns the autoincrement id."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role!r}; must be one of {sorted(VALID_ROLES)}")
    md_json = json.dumps(metadata or {})
    with connect() as cx:
        cur = cx.execute(
            "INSERT INTO chat_history (session_id, role, content, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, time.time(), md_json),
        )
        return cur.lastrowid


def list_session(session_id: str, limit: int = 100) -> list[ChatMessage]:
    """Return chat turns for a session, oldest first."""
    with connect() as cx:
        rows = cx.execute(
            "SELECT id, session_id, role, content, timestamp, metadata "
            "FROM chat_history WHERE session_id = ? "
            "ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [
        ChatMessage(
            id=r["id"], session_id=r["session_id"], role=r["role"],
            content=r["content"], timestamp=r["timestamp"],
            metadata=json.loads(r["metadata"]),
        )
        for r in rows
    ]


def pop_last_assistant_message(session_id: str) -> Optional[ChatMessage]:
    """Remove and return the most recent assistant turn (for regen)."""
    with connect() as cx:
        r = cx.execute(
            "SELECT id, session_id, role, content, timestamp, metadata "
            "FROM chat_history WHERE session_id = ? AND role = 'assistant' "
            "ORDER BY timestamp DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if r is None:
            return None
        cx.execute("DELETE FROM chat_history WHERE id = ?", (r["id"],))
    return ChatMessage(
        id=r["id"], session_id=r["session_id"], role=r["role"],
        content=r["content"], timestamp=r["timestamp"],
        metadata=json.loads(r["metadata"]),
    )
