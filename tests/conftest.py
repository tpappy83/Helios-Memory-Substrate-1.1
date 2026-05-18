"""tests/conftest.py — pytest fixtures with isolated DB per test session.

Sets HELIOS_DB_PATH before any helios import, pointing at a tempfile.
"""
import os
import tempfile

# Set DB path BEFORE any helios imports so module-level DB_PATH picks it up
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["HELIOS_DB_PATH"] = _TMP_DB.name
os.environ["HELIOS_LLM_MOCK"] = "1"

import pytest


@pytest.fixture(autouse=True)
def reset_db():
    """Before each test, drop all tables and re-init from schema.sql."""
    from core.db import connect, init_schema

    with connect() as cx:
        # Wipe any prior state (v3 includes tenants + api_keys)
        cx.execute("DROP TABLE IF EXISTS api_keys")
        cx.execute("DROP TABLE IF EXISTS tenants")
        cx.execute("DROP TABLE IF EXISTS audit_log")
        cx.execute("DROP TABLE IF EXISTS memory_records_fts")
        cx.execute("DROP TABLE IF EXISTS memory_records")
        cx.execute("DROP TABLE IF EXISTS chat_history")
        cx.execute("PRAGMA user_version = 0")

    init_schema()
    yield
