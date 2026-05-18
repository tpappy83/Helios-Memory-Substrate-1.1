"""tests/test_db.py — connection + schema bootstrap."""
import os
import sqlite3

from core.db import connect, init_schema, resource_path, DB_PATH


def test_connect_returns_context_managed_connection():
    with connect() as cx:
        assert isinstance(cx, sqlite3.Connection)
        cur = cx.execute("SELECT 1")
        assert cur.fetchone()[0] == 1


def test_env_var_override():
    """HELIOS_DB_PATH env var must override default."""
    assert os.environ["HELIOS_DB_PATH"] == DB_PATH


def test_init_schema_creates_tables():
    init_schema()
    with connect() as cx:
        rows = cx.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
    assert "memory_records" in names
    assert "chat_history" in names


def test_resource_path_resolves():
    """resource_path('schema.sql') must resolve to an existing file."""
    p = resource_path("schema.sql")
    assert os.path.exists(p), f"resource_path returned non-existent {p}"


def test_wal_mode_enabled():
    """PRAGMA journal_mode should be WAL after connect()."""
    with connect() as cx:
        mode = cx.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
