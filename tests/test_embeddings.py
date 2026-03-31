"""Tests for src/rag/loader.py and src/rag/chunker.py."""
import pytest
from pathlib import Path

from src.rag.loader import load_documents
from src.rag.chunker import chunk_documents
from src.rag.vector_store import Document


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

def test_load_documents_reads_txt_files(tmp_assets):
    docs = load_documents(str(tmp_assets))
    assert len(docs) == 2
    sources = {d.metadata["source"] for d in docs}
    assert "leave_policy.txt" in sources
    assert "benefits_guide.txt" in sources


def test_load_documents_content_non_empty(tmp_assets):
    docs = load_documents(str(tmp_assets))
    for doc in docs:
        assert len(doc.content) > 0


def test_load_documents_ignores_non_txt(tmp_path):
    (tmp_path / "valid.txt").write_text("Valid content.", encoding="utf-8")
    (tmp_path / "ignored.md").write_text("# Ignored")
    (tmp_path / "ignored.pdf").write_bytes(b"%PDF")
    docs = load_documents(str(tmp_path))
    assert len(docs) == 1
    assert docs[0].metadata["source"] == "valid.txt"


def test_load_documents_skips_empty_files(tmp_path):
    (tmp_path / "empty.txt").write_text("   \n\t", encoding="utf-8")
    (tmp_path / "valid.txt").write_text("Content here.", encoding="utf-8")
    docs = load_documents(str(tmp_path))
    assert len(docs) == 1


def test_load_documents_missing_dir():
    with pytest.raises(FileNotFoundError):
        load_documents("/nonexistent/directory")


def test_load_documents_empty_dir(tmp_path):
    docs = load_documents(str(tmp_path))
    assert docs == []


# ---------------------------------------------------------------------------
# Chunker tests
# ---------------------------------------------------------------------------

def test_chunk_single_short_doc():
    docs = [Document(content="Short text.", metadata={"source": "f.txt"})]
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0].content == "Short text."


def test_chunk_long_doc_produces_multiple_chunks():
    long_text = "Word " * 300  # 1500 chars
    docs = [Document(content=long_text, metadata={"source": "big.txt"})]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1


def test_chunk_max_size_respected():
    long_text = "A" * 2000
    docs = [Document(content=long_text, metadata={"source": "f.txt"})]
    chunks = chunk_documents(docs, chunk_size=300, chunk_overlap=30)
    for chunk in chunks:
        assert len(chunk.content) <= 300


def test_chunk_preserves_source_metadata():
    docs = [Document(content="A" * 1000, metadata={"source": "policy.txt"})]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    for chunk in chunks:
        assert chunk.metadata["source"] == "policy.txt"


def test_chunk_adds_chunk_index():
    docs = [Document(content="A" * 1000, metadata={"source": "f.txt"})]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    indices = [c.metadata["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_invalid_overlap_raises():
    docs = [Document(content="text", metadata={})]
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_documents(docs, chunk_size=100, chunk_overlap=100)


def test_chunk_multiple_docs():
    docs = [
        Document(content="A" * 600, metadata={"source": "a.txt"}),
        Document(content="B" * 600, metadata={"source": "b.txt"}),
    ]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    sources = {c.metadata["source"] for c in chunks}
    assert sources == {"a.txt", "b.txt"}
