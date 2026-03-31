"""ChromaDB-backed vector store (handles embeddings internally via ONNX)."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import chromadb

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "hr_documents"


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """Persistent ChromaDB vector store.

    ChromaDB computes embeddings internally using its bundled ONNX model
    (all-MiniLM-L6-v2), so no separate embedding step is required.

    Usage::

        store = VectorStore("data/chromadb")
        store.build(documents)   # index and persist
        # --- later / different process ---
        store.load()
        results = store.search("annual leave policy")
    """

    def __init__(self, path: str):
        self._path = str(Path(path).resolve())
        self._client: Optional[Any] = None
        self._collection = None

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def build(self, documents: list[Document]) -> None:
        """Index documents and persist the collection to disk.

        Existing collection is replaced on every call, enabling full rebuilds
        without leftover stale data.
        """
        Path(self._path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self._path)

        try:
            self._client.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass  # collection may not exist on first run

        self._collection = self._client.create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        if not documents:
            logger.warning("build() called with no documents — collection is empty.")
            return

        self._collection.add(
            documents=[doc.content for doc in documents],
            metadatas=[doc.metadata for doc in documents],
            ids=[f"doc_{i}" for i in range(len(documents))],
        )
        logger.info("Indexed %d documents into ChromaDB at %s", len(documents), self._path)

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load the persisted collection from disk."""
        self._client = chromadb.PersistentClient(path=self._path)
        self._collection = self._client.get_collection(_COLLECTION_NAME)
        logger.info("Loaded vector store (%d docs) from %s", self.doc_count, self._path)

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Return the top-k most similar documents to query.

        ChromaDB embeds the query with the same internal model used during
        indexing, so no manual embedding step is needed here.
        The cosine distance is stored in each document's metadata under
        ``_distance`` (0 = identical, 2 = opposite) for downstream re-ranking.
        """
        if self._collection is None:
            raise RuntimeError("Vector store not loaded. Call load() first.")

        count = self._collection.count()
        if count == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        return [
            Document(content=content, metadata={**metadata, "_distance": distance})
            for content, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def get_document_chunks(self, source: str) -> list[Document]:
        """Return all chunks for a given source file, ordered by chunk_index."""
        if self._collection is None:
            raise RuntimeError("Vector store not loaded. Call load() first.")

        results = self._collection.get(
            where={"source": source},
            include=["documents", "metadatas"],
        )
        docs = [
            Document(content=content, metadata=metadata)
            for content, metadata in zip(results["documents"], results["metadatas"])
        ]
        docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))
        return docs

    def list_sources(self) -> list[str]:
        """Return sorted list of all unique source filenames in the collection."""
        if self._collection is None:
            raise RuntimeError("Vector store not loaded. Call load() first.")

        results = self._collection.get(include=["metadatas"])
        sources = {m.get("source", "") for m in results["metadatas"]}
        return sorted(s for s in sources if s)

    @property
    def doc_count(self) -> int:
        if self._collection is None:
            return 0
        return self._collection.count()
