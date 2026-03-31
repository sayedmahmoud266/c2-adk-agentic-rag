"""Shared pytest fixtures."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.rag.vector_store import Document, VectorStore


@pytest.fixture
def tmp_assets(tmp_path) -> Path:
    """Temporary directory with sample HR text files."""
    (tmp_path / "leave_policy.txt").write_text(
        "Annual leave is 25 days per calendar year. Sick leave is 10 days.", encoding="utf-8"
    )
    (tmp_path / "benefits_guide.txt").write_text(
        "Health insurance covers dental and vision for all employees.", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def sample_docs() -> list[Document]:
    return [
        Document(
            content="Annual leave is 25 days per calendar year.",
            metadata={"source": "leave_policy.txt"},
        ),
        Document(
            content="Health insurance covers dental and vision.",
            metadata={"source": "benefits_guide.txt"},
        ),
    ]


@pytest.fixture
def built_store(tmp_path, sample_docs) -> VectorStore:
    """A VectorStore built and persisted to a temp directory."""
    store = VectorStore(str(tmp_path / "chromadb"))
    store.build(sample_docs)
    return store
