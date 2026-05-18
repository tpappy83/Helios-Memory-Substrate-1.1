"""tests/test_chat_history.py — chat_history CRUD."""
import pytest

from core.memory import list_session, pop_last_assistant_message, write_chat


def test_write_chat_returns_int_id():
    cid = write_chat("s1", "user", "hello")
    assert isinstance(cid, int)


def test_list_session_in_order():
    write_chat("s1", "user", "first")
    write_chat("s1", "assistant", "second")
    write_chat("s1", "user", "third")
    msgs = list_session("s1")
    assert [m.content for m in msgs] == ["first", "second", "third"]


def test_invalid_role_raises():
    with pytest.raises(ValueError):
        write_chat("s1", "bogus", "x")


def test_pop_last_assistant():
    write_chat("s1", "user", "ask")
    write_chat("s1", "assistant", "reply 1")
    write_chat("s1", "user", "ask 2")
    write_chat("s1", "assistant", "reply 2")
    popped = pop_last_assistant_message("s1")
    assert popped is not None
    assert popped.content == "reply 2"
    remaining = list_session("s1")
    assert popped.content not in [m.content for m in remaining]


def test_session_isolation():
    write_chat("s1", "user", "in s1")
    write_chat("s2", "user", "in s2")
    msgs_s1 = list_session("s1")
    msgs_s2 = list_session("s2")
    assert {m.content for m in msgs_s1} == {"in s1"}
    assert {m.content for m in msgs_s2} == {"in s2"}
