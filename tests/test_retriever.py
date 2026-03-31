"""Tests for src/rag/retriever.py."""
from unittest.mock import MagicMock

from src.rag.retriever import HRRetriever
from src.rag.vector_store import Document


def _make_store(docs: list) -> MagicMock:
    store = MagicMock()
    store.search.return_value = docs
    return store


def test_retrieve_formats_results():
    docs = [
        Document(content="25 days annual leave.", metadata={"source": "leave_policy.txt"}),
        Document(content="Health covers dental.", metadata={"source": "benefits_guide.txt"}),
    ]
    retriever = HRRetriever(_make_store(docs), top_k=2)
    result = retriever.retrieve("leave entitlements")

    assert "Source 1: leave_policy.txt" in result
    assert "Source 2: benefits_guide.txt" in result
    assert "25 days annual leave." in result


def test_retrieve_empty_returns_message():
    retriever = HRRetriever(_make_store([]), top_k=5)
    result = retriever.retrieve("something obscure")
    assert "No relevant HR documents found" in result


def test_retrieve_includes_section_metadata():
    docs = [
        Document(
            content="Pension is 6%.",
            metadata={"source": "benefits_guide.txt", "section": "Pension"},
        )
    ]
    retriever = HRRetriever(_make_store(docs), top_k=1)
    result = retriever.retrieve("pension")
    assert "Pension" in result


def test_retrieve_calls_store_with_top_k():
    store = _make_store([])
    retriever = HRRetriever(store, top_k=3)
    retriever.retrieve("query")
    store.search.assert_called_once_with("query", top_k=3)
