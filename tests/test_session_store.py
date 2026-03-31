"""Tests for src/session_store.py."""
from src import session_store


def test_create_and_get_session():
    data = {"name": "Alice", "email": "alice@example.com", "department": "Eng", "position": "Dev"}
    token = session_store.create_session(data)
    assert token is not None
    assert len(token) == 64  # 32 hex bytes → 64 chars

    result = session_store.get_session(token)
    assert result == data


def test_get_unknown_token_returns_none():
    assert session_store.get_session("nonexistent-token") is None


def test_delete_session_removes_data():
    token = session_store.create_session({"name": "Bob"})
    session_store.delete_session(token)
    assert session_store.get_session(token) is None


def test_delete_unknown_token_is_safe():
    session_store.delete_session("nonexistent")  # must not raise


def test_tokens_are_unique():
    t1 = session_store.create_session({"x": 1})
    t2 = session_store.create_session({"x": 2})
    assert t1 != t2
