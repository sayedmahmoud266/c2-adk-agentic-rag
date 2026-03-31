"""Tests for src/rag/vector_store.py (ChromaDB implementation)."""
import tempfile
from pathlib import Path

import pytest

from src.rag.vector_store import Document, VectorStore


def test_build_creates_index(tmp_path, sample_docs):
    store = VectorStore(str(tmp_path / "db"))
    store.build(sample_docs)
    assert store.doc_count == len(sample_docs)


def test_build_empty_docs_logs_warning(tmp_path, caplog):
    import logging
    store = VectorStore(str(tmp_path / "db"))
    with caplog.at_level(logging.WARNING):
        store.build([])
    assert store.doc_count == 0


def test_load_after_build(tmp_path, sample_docs):
    db_path = str(tmp_path / "db")
    store = VectorStore(db_path)
    store.build(sample_docs)

    store2 = VectorStore(db_path)
    store2.load()
    assert store2.doc_count == len(sample_docs)


def test_search_returns_documents(built_store):
    results = built_store.search("annual leave", top_k=2)
    assert len(results) > 0
    assert all(isinstance(r, Document) for r in results)


def test_search_empty_store(tmp_path):
    store = VectorStore(str(tmp_path / "db"))
    store.build([])
    results = store.search("anything")
    assert results == []


def test_search_top_k_limit(tmp_path, sample_docs):
    store = VectorStore(str(tmp_path / "db"))
    store.build(sample_docs)
    results = store.search("policy", top_k=1)
    assert len(results) == 1


def test_search_before_load_raises(tmp_path):
    store = VectorStore(str(tmp_path / "db"))
    with pytest.raises(RuntimeError, match="not loaded"):
        store.search("query")


def test_rebuild_replaces_old_index(tmp_path, sample_docs):
    db_path = str(tmp_path / "db")
    store = VectorStore(db_path)
    store.build(sample_docs)

    new_docs = [Document(content="New HR policy.", metadata={"source": "new.txt"})]
    store.build(new_docs)
    assert store.doc_count == 1


def test_search_preserves_metadata(tmp_path):
    docs = [Document(content="Remote work requires manager approval.", metadata={"source": "remote.txt", "section": "Approval"})]
    store = VectorStore(str(tmp_path / "db"))
    store.build(docs)
    results = store.search("remote work")
    assert results[0].metadata["source"] == "remote.txt"
    assert results[0].metadata["section"] == "Approval"
