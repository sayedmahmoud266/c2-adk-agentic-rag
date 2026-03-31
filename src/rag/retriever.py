"""HR document retriever: queries the vector store and formats results."""
import re

from src.rag.vector_store import VectorStore, Document


class HRRetriever:
    def __init__(self, vector_store: VectorStore, top_k: int = 5):
        self.vector_store = vector_store
        self.top_k = top_k

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _keyword_score(query: str, text: str) -> float:
        """Fraction of query words that appear in the document text (0–1)."""
        query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())
        if not query_words:
            return 0.0
        doc_words = set(re.sub(r'[^\w\s]', '', text.lower()).split())
        return len(query_words & doc_words) / len(query_words)

    @staticmethod
    def _format_chunk(index: int, doc: Document) -> str:
        source = doc.metadata.get("source", "HR Document")
        section = doc.metadata.get("section", "")
        header = f"[Source {index}: {source}" + (f" → {section}" if section else "") + "]"
        return f"{header}\n{doc.content}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, query: str) -> str:
        """Search the HR knowledge base and return re-ranked, formatted results.

        Retrieval strategy
        ------------------
        1. Fetch ``top_k * 2`` candidates from ChromaDB (cosine similarity).
        2. Re-rank by a weighted combination of cosine similarity (70 %) and
           keyword overlap (30 %) to surface the most literally relevant chunks
           even when vector distance alone would rank them lower.
        3. Return the top ``top_k`` results with source citations.
        """
        # Fetch extra candidates so re-ranking has room to work
        candidates = self.vector_store.search(query, top_k=self.top_k * 2)
        if not candidates:
            return "No relevant HR documents found for this query."

        # Re-rank
        scored: list[tuple[float, Document]] = []
        for doc in candidates:
            distance = doc.metadata.get("_distance", 1.0)  # lower = more similar
            cosine_sim = max(0.0, 1.0 - distance)          # convert to similarity
            keyword = self._keyword_score(query, doc.content)
            combined = 0.7 * cosine_sim + 0.3 * keyword
            scored.append((combined, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_docs = [doc for _, doc in scored[: self.top_k]]

        return "\n\n---\n\n".join(
            self._format_chunk(i, doc) for i, doc in enumerate(top_docs, 1)
        )

    def retrieve_full_document(self, source: str) -> str:
        """Return the complete, ordered content of a source file.

        Use this when the initial search results provide insufficient context,
        or when the user explicitly asks for the full document.
        """
        chunks = self.vector_store.get_document_chunks(source)
        if not chunks:
            return f"Document '{source}' not found in the knowledge base."

        full_text = "\n\n".join(doc.content for doc in chunks)
        return f"[Full document: {source}]\n\n{full_text}"

    def list_documents(self) -> str:
        """Return a formatted list of all indexed HR documents."""
        sources = self.vector_store.list_sources()
        if not sources:
            return "No documents are currently indexed in the knowledge base."
        lines = "\n".join(f"- {s}" for s in sources)
        return f"Available HR documents:\n{lines}"
