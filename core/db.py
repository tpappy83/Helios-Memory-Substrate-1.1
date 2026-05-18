"""core/db.py — Helios DB connection + schema bootstrap + migrations.

Single source of truth for:
- DB connection (WAL mode for multi-surface concurrency)
- Schema initialization (reads schema.sql)
- Migration runner (PRAGMA user_version-based)
- Resource path resolution (bundled SQL/frontend assets via PyInstaller)
- HELIOS_DB_PATH env var support for test isolation and containerization
"""
from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = os.environ.get("HELIOS_DB_PATH", "helios_memory.db")


def resource_path(*parts: str) -> str:
    """Resolve a bundled data file (works in dev and frozen EXE)."""
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / Path(*parts))   # type: ignore[attr-defined]
    candidates.append(Path.cwd() / Path(*parts))
    candidates.append(Path(__file__).parent / Path(*parts))
    candidates.append(Path(__file__).parent.parent / Path(*parts))

    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[-1])


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Context-managed connection. Auto-commits on exit, rolls back on exception."""
    cx = sqlite3.connect(DB_PATH)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA journal_mode = WAL")
    try:
        yield cx
        cx.commit()
    except Exception:
        cx.rollback()
        raise
    finally:
        cx.close()


def _resolve_schema_path() -> str:
    return resource_path("schema.sql")


# ─── Migration machinery (v0.2) ──────────────────────────────────────

def get_schema_version(cx: sqlite3.Connection) -> int:
    return cx.execute("PRAGMA user_version").fetchone()[0]


def _read_migration(name: str) -> str:
    """Resolve migration SQL from the bundled migrations/ folder."""
    path = resource_path("migrations", name)
    return Path(path).read_text(encoding="utf-8")


def migrate_v1_to_v2(cx: sqlite3.Connection) -> None:
    """Apply migrations/002_tiering_namespace_audit.sql against an existing v1 DB.

    Adds tiering columns, namespace columns, audit_log table, indexes.
    Bumps user_version to 2.
    """
    sql = _read_migration("002_tiering_namespace_audit.sql")
    cx.executescript(sql)


def migrate_v2_to_v3(cx: sqlite3.Connection) -> None:
    """Apply migrations/003_tenants_apikeys_v3.sql against an existing v2 DB.

    Adds tenants + api_keys control-plane tables, indexes, bootstrap default tenant.
    Bumps user_version to 3.
    """
    sql = _read_migration("003_tenants_apikeys_v3.sql")
    cx.executescript(sql)


def apply_pending_migrations() -> list[str]:
    """Apply all pending migrations in order. Returns list of applied names."""
    applied: list[str] = []
    with connect() as cx:
        version = get_schema_version(cx)
        if version < 2:
            migrate_v1_to_v2(cx)
            applied.append("002_tiering_namespace_audit.sql")
        if version < 3:
            migrate_v2_to_v3(cx)
            applied.append("003_tenants_apikeys_v3.sql")
    return applied


def init_schema() -> None:
    """Initialize DB from schema.sql (fresh install) or apply pending migrations."""
    with connect() as cx:
        existing = cx.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='memory_records'"
        ).fetchone()

    if existing is None:
        # Fresh install: load full schema.sql (already v2)
        with connect() as cx:
            sql = Path(_resolve_schema_path()).read_text(encoding="utf-8")
            cx.executescript(sql)
    else:
        # Existing DB: apply any pending migrations
        apply_pending_migrations()
