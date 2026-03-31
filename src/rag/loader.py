"""Plain-text document loader for the HR knowledge base."""
import logging
from pathlib import Path

from src.rag.vector_store import Document

logger = logging.getLogger(__name__)


def load_documents(assets_path: str) -> list[Document]:
    """Load all .txt files from assets_path into Document objects.

    Args:
        assets_path: Directory containing HR text documents.

    Returns:
        List of Document objects with content and source metadata.

    Raises:
        FileNotFoundError: If assets_path does not exist.
    """
    path = Path(assets_path)
    if not path.exists():
        raise FileNotFoundError(f"Assets directory not found: {assets_path}")

    documents: list[Document] = []
    for txt_file in sorted(path.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            logger.warning("Skipping empty file: %s", txt_file.name)
            continue
        documents.append(Document(content=text, metadata={"source": txt_file.name}))
        logger.debug("Loaded %s (%d chars)", txt_file.name, len(text))

    logger.info("Loaded %d documents from %s", len(documents), assets_path)
    return documents
