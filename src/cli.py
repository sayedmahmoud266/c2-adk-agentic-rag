"""CLI commands: build-db and serve."""
import sys
import subprocess
from pathlib import Path

import click


@click.group()
def cli():
    """HR Chatbot CLI — Agentic RAG powered by Google ADK and ChromaDB."""


@cli.command("build-db")
@click.argument(
    "docs_path",
    default=None,
    required=False,
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option("--db-path", default=None, help="Output path for ChromaDB (overrides .env)")
@click.option("--chunk-size", default=None, type=int, help="Chunk size in characters")
@click.option("--chunk-overlap", default=None, type=int, help="Overlap between chunks")
def build_db(docs_path, db_path, chunk_size, chunk_overlap):
    """Build the ChromaDB vector index from HR text files at DOCS_PATH.

    DOCS_PATH defaults to the ASSETS_PATH setting (assets/ by default).
    """
    from src.config import get_settings
    from src.rag.loader import load_documents
    from src.rag.chunker import chunk_documents
    from src.rag.vector_store import VectorStore

    settings = get_settings()
    _docs_path = docs_path or "assets"
    _db_path = db_path or settings.chromadb_path
    _chunk_size = chunk_size or settings.chunk_size
    _chunk_overlap = chunk_overlap or settings.chunk_overlap

    docs_dir = Path(_docs_path)
    if not docs_dir.exists():
        click.echo(f"Error: directory not found: {_docs_path}", err=True)
        sys.exit(1)

    click.echo(f"Loading documents from: {_docs_path}")
    documents = load_documents(_docs_path)

    if not documents:
        click.echo("No .txt files found in the directory.", err=True)
        sys.exit(1)

    click.echo(f"Loaded {len(documents)} file(s). Chunking...")
    chunks = chunk_documents(documents, chunk_size=_chunk_size, chunk_overlap=_chunk_overlap)
    click.echo(f"Created {len(chunks)} chunk(s). Indexing into ChromaDB...")

    store = VectorStore(_db_path)
    store.build(chunks)

    click.echo(f"\nDone. {len(chunks)} chunks from {len(documents)} file(s) saved to: {_db_path}")


@cli.command("serve")
@click.option("--host", default=None, help="Host to bind (overrides .env HOST)")
@click.option("--port", default=None, type=int, help="Port (overrides .env PORT)")
@click.option("--reload", is_flag=True, default=False, help="Enable hot reload (dev)")
def serve(host, port, reload):
    """Start the HR chatbot web server (landing page + chat interface)."""
    from src.config import get_settings

    settings = get_settings()
    _host = host or settings.host
    _port = port or settings.port

    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.server:app",
        "--host", _host,
        "--port", str(_port),
    ]
    if reload:
        cmd.append("--reload")

    click.echo(f"Starting HR Assistant at http://{_host}:{_port}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    cli()
