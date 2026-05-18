"""tests/test_memory.py — memory_records CRUD."""
import pytest

from core.memory import (
    Memory, delete_memory, get_memory, keyword_candidates,
    list_recent, write_memory,
)


def test_write_returns_id():
    rid = write_memory(content="hello world", type="observation")
    assert isinstance(rid, str)
    assert len(rid) > 10


def test_get_after_write():
    rid = write_memory(content="apple banana", type="event", importance=0.7)
    m = get_memory(rid)
    assert m is not None
    assert m.content == "apple banana"
    assert m.type == "event"
    assert m.importance == 0.7


def test_list_recent_orders_by_timestamp_desc():
    write_memory(content="first")
    write_memory(content="second")
    write_memory(content="third")
    recent = list_recent(limit=3)
    assert len(recent) == 3
    assert recent[0].content == "third"
    assert recent[-1].content == "first"


def test_delete_existing_returns_true():
    rid = write_memory(content="to delete")
    assert delete_memory(rid) is True
    assert get_memory(rid) is None


def test_delete_missing_returns_false():
    assert delete_memory("nonexistent-id") is False


def test_invalid_type_raises():
    with pytest.raises(ValueError):
        write_memory(content="x", type="bogus")


def test_fts5_keyword_candidates():
    write_memory(content="the quick brown fox jumps over the lazy dog")
    write_memory(content="apple banana cherry")
    results = keyword_candidates("fox", k=5)
    assert len(results) >= 1
    assert any("fox" in r.content for r in results)
