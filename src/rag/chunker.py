"""Semantic chunker: splits documents at paragraph and section boundaries."""
import re
import logging

from src.rag.vector_store import Document

logger = logging.getLogger(__name__)

# Lines matching any of these patterns are treated as section headings.
_HEADING_RE = re.compile(
    r'^('
    r'\d+(\.\d+)*[\s\.\)]+\S'                        # 1.  /  1.1  /  2.3.1 Title
    r'|[A-Z][A-Z\s\-/&]{4,}'                          # ALL CAPS HEADING
    r'|(Article|Section|Chapter|Part|Appendix|Clause)'  # keyword-prefixed
    r'\s+\w+'
    r')',
    re.IGNORECASE,
)

_MIN_CHUNK_CHARS = 120   # merge paragraph into neighbour if shorter than this
_MAX_CHUNK_CHARS = 2_000  # split at sentence boundary if longer than this


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    # Headings are short single-line declarations
    if not stripped or len(stripped) > 120 or '\n' in stripped:
        return False
    return bool(_HEADING_RE.match(stripped))


def _split_at_sentences(text: str, max_chars: int) -> list[str]:
    """Break an oversized block at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        candidate = (current + " " + sent).strip() if current else sent
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks or [text]


def chunk_documents(documents: list[Document], **_kwargs) -> list[Document]:
    """Chunk each document at semantic boundaries.

    Strategy
    --------
    1. Split text into raw blocks on blank lines.
    2. Start a new chunk whenever a section heading is detected.
    3. Merge consecutive blocks that are too short into their neighbour.
    4. Split blocks that exceed *_MAX_CHUNK_CHARS* at sentence boundaries.
    5. Emit one ``Document`` per final chunk, carrying section/chunk metadata.

    All extra keyword arguments (chunk_size, chunk_overlap, …) are accepted
    but ignored — sizing is driven by paragraph/section structure instead.
    """
    all_chunks: list[Document] = []

    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        doc_id = source.rsplit(".", 1)[0]  # filename without extension

        # ── 1. Raw blocks ──────────────────────────────────────────────────
        raw_blocks = [b.strip() for b in re.split(r'\n\s*\n', doc.content) if b.strip()]

        # ── 2. Group by section headings ───────────────────────────────────
        # Each group: {"heading": str | None, "paragraphs": [str]}
        groups: list[dict] = []
        current_heading: str | None = None
        current_paragraphs: list[str] = []

        for block in raw_blocks:
            first_line = block.split('\n')[0].strip()
            if _is_heading(first_line):
                if current_paragraphs:
                    groups.append({"heading": current_heading, "paragraphs": current_paragraphs})
                rest = "\n".join(block.split('\n')[1:]).strip()
                current_heading = first_line
                current_paragraphs = [rest] if rest else []
            else:
                current_paragraphs.append(block)

        if current_paragraphs or current_heading:
            groups.append({"heading": current_heading, "paragraphs": current_paragraphs})

        # ── 3. Build raw text per group and merge short ones ───────────────
        items: list[dict] = []  # {"heading": …, "text": …}
        for group in groups:
            body = "\n\n".join(group["paragraphs"]).strip()
            heading = group["heading"]
            full_text = (f"{heading}\n\n{body}" if heading and body else heading or body).strip()
            if not full_text:
                continue

            # Merge very short, non-headed blocks into the previous item
            if items and len(full_text) < _MIN_CHUNK_CHARS and not heading:
                items[-1]["text"] += "\n\n" + full_text
            else:
                items.append({"heading": heading, "text": full_text})

        # ── 4. Split oversized items at sentence boundaries ────────────────
        final: list[tuple[str, str | None]] = []  # (text, heading)
        for item in items:
            text = item["text"].strip()
            heading = item["heading"]
            if not text:
                continue
            if len(text) <= _MAX_CHUNK_CHARS:
                final.append((text, heading))
            else:
                for sub in _split_at_sentences(text, _MAX_CHUNK_CHARS):
                    final.append((sub.strip(), heading))

        # ── 5. Emit Documents ──────────────────────────────────────────────
        total = len(final)
        for idx, (text, heading) in enumerate(final):
            all_chunks.append(Document(
                content=text,
                metadata={
                    **doc.metadata,
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "total_chunks": total,
                    "section": heading or "",
                },
            ))

        logger.info(
            "Chunked '%s': %d raw block(s) → %d semantic chunk(s)",
            source, len(raw_blocks), total,
        )

    return all_chunks
