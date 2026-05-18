"""tests/test_schema.py — schema invariants."""
from core.db import connect


def test_memory_records_table_columns():
    with connect() as cx:
        rows = cx.execute("PRAGMA table_info(memory_records)").fetchall()
    cols = {r["name"]: r for r in rows}
    for c in ("id", "type", "content", "metadata", "timestamp", "importance"):
        assert c in cols, f"missing column: {c}"


def test_chat_history_table_columns():
    with connect() as cx:
        rows = cx.execute("PRAGMA table_info(chat_history)").fetchall()
    cols = {r["name"] for r in rows}
    for c in ("id", "session_id", "role", "content", "timestamp", "metadata"):
        assert c in cols


def test_fts5_virtual_table_exists():
    with connect() as cx:
        row = cx.execute(
            "SELECT name FROM sqlite_master "
            "WHERE name = 'memory_records_fts' AND type = 'table'"
        ).fetchone()
    assert row is not None


def test_indexes_exist():
    with connect() as cx:
        rows = cx.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    index_names = {r["name"] for r in rows}
    expected = {
        "idx_memory_records_type",
        "idx_memory_records_timestamp",
        "idx_memory_records_importance",
        "idx_chat_history_session_ts",
    }
    assert expected.issubset(index_names), \
        f"missing indexes: {expected - index_names}"
