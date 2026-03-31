# Setup Guide

## Prerequisites

- Python 3.11 or higher
- `pip` and `venv`
- An API key for your chosen LLM provider (or a running Ollama instance for local models)

## 1. Clone and Install

```bash
git clone <repo-url>
cd c2-adk-agentic-rag
make setup
```

`make setup` creates a virtual environment in `venv/`, installs all dependencies from `requirements.txt`, and installs the package in editable mode.

## 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and set the values relevant to your LLM provider:

```bash
# Choose one of the following model strings:
LITELLM_MODEL=openai/gpt-4o                    # OpenAI
LITELLM_MODEL=anthropic/claude-sonnet-4-6      # Anthropic
LITELLM_MODEL=google/gemini-2.0-flash          # Google
LITELLM_MODEL=ollama/llama3.2                  # Local via Ollama

# Set the matching API key
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
GOOGLE_API_KEY=AIza...
# (Ollama needs no key, just set OLLAMA_API_BASE if not default)
```

All other settings have sensible defaults. Review `.env.example` for details.

> **No embedding API key needed.** ChromaDB computes embeddings internally using
> a bundled ONNX model, so you only need an LLM key.

## 3. Add HR Documents

Place your HR documents (plain `.txt` files) in the `assets/` directory.
Several sample standards are already included for testing.

## 4. Build the Vector Database

```bash
make build-db
# Equivalent: venv/bin/python -m src.cli build-db assets
```

To index a different directory:

```bash
make build-db DOCS_PATH=/path/to/your/hr-docs
```

The ChromaDB index is saved to `data/chromadb/` by default (configurable via `CHROMADB_PATH` in `.env`).

## 5. Start the Application

```bash
make serve
# Equivalent: venv/bin/python -m src.cli serve
```

Open your browser at [http://localhost:8000](http://localhost:8000).

For development with hot reload:

```bash
venv/bin/python -m src.cli serve --reload
```

## CLI Reference

```
hr-chatbot build-db [DOCS_PATH] [OPTIONS]
  Index HR text files into ChromaDB.

  DOCS_PATH           Directory containing .txt HR documents (default: assets)

  --db-path TEXT      Override CHROMADB_PATH from .env
  --chunk-size INT    Override CHUNK_SIZE from .env
  --chunk-overlap INT Override CHUNK_OVERLAP from .env

hr-chatbot serve [OPTIONS]
  Start the web server (landing page + chat interface).

  --host TEXT   Override HOST from .env
  --port INT    Override PORT from .env
  --reload      Enable hot reload (development mode)
```

## Running Tests

```bash
make test
# Equivalent: venv/bin/pytest tests/ -v --cov=src
```

An HTML coverage report is generated in `htmlcov/`.

## Linting

```bash
make lint
# Equivalent: venv/bin/ruff check src/ tests/
```

## Switching LLM Providers

Change only the `LITELLM_MODEL` value in `.env` and restart the server. No code changes required.

| Provider | Model string example | Key variable |
|----------|---------------------|--------------|
| OpenAI | `openai/gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| Google | `google/gemini-2.0-flash` | `GOOGLE_API_KEY` |
| Ollama | `ollama/llama3.2` | `OLLAMA_API_BASE` |
| LM Studio | `openai/local-model` | `OPENAI_API_BASE=http://localhost:1234/v1` |

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_MODEL` | `openai/gpt-4o` | LLM model string (any LiteLLM-supported model) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GOOGLE_API_KEY` | — | Google API key |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama server URL |
| `CHROMADB_PATH` | `data/chromadb` | Path to the ChromaDB index directory |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved per query |
| `CHUNK_SIZE` | `500` | Max characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap characters between consecutive chunks |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `SECRET_KEY` | `change-me-in-production` | Session cookie signing key |

## Troubleshooting

**"Knowledge base is empty" warning in chat**
Run `make build-db` before starting the server.

**`ModuleNotFoundError: No module named 'src'`**
Run `make setup` to install the package in editable mode, or activate the venv: `source venv/bin/activate`.

**Ollama model not responding**
Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull llama3.2`).

**ChromaDB ONNX model download on first run**
On the first `make build-db`, ChromaDB downloads the embedding model (~90 MB). This is a one-time operation.
