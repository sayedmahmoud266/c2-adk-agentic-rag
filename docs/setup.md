# Setup Guide

## Prerequisites

- Python 3.10 or higher
- `pip` and `venv`
- An API key for your chosen LLM provider (or a running Ollama / LM Studio instance for local models)

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
# Cloud providers
LITELLM_MODEL=openai/gpt-4o                    # OpenAI
LITELLM_MODEL=anthropic/claude-sonnet-4-6      # Anthropic
LITELLM_MODEL=gemini/gemini-2.0-flash          # Google Gemini

# Local via Ollama
LITELLM_MODEL=ollama/llama3.2
OLLAMA_API_BASE=http://localhost:11434          # default, change if needed

# Local via LM Studio
LITELLM_MODEL=openai/local-model-name          # use openai/ prefix
LITELLM_API_BASE=http://localhost:1234/v1

# OpenRouter
LITELLM_MODEL=openrouter/google/gemma-3-12b
OPENROUTER_API_KEY=sk-or-...
```

All other settings have sensible defaults. Review `.env.example` for the full list.

> **No embedding API key needed.** ChromaDB computes embeddings internally using
> a bundled ONNX model (`all-MiniLM-L6-v2`), so you only need an LLM key.

### Chainlit Auth Secret

```bash
# Generate a secret and paste it into .env
venv/bin/chainlit create-secret
# CHAINLIT_AUTH_SECRET=<paste output here>
```

This is required because the app uses `@cl.header_auth_callback` to read the session cookie.

## 3. Add HR Documents

Place your HR documents (plain `.txt` files) in the `assets/` directory.
Several sample standards are already included for testing.

## 4. Build the Vector Database

```bash
make build-db
# Equivalent: venv/bin/python -m src.cli build-db assets
```

The chunker splits each document at **paragraph and section boundaries** (not fixed character windows). Each chunk carries its section heading as metadata, enabling more precise citations.

To index a different directory:

```bash
make build-db DOCS_PATH=/path/to/your/hr-docs
```

The ChromaDB index is saved to `data/chromadb/` by default (configurable via `CHROMADB_PATH` in `.env`).

### Rebuilding the index

If you add, remove, or update documents, wipe the old index first to avoid stale data:

```bash
make clean-db && make build-db
```

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
  Index HR text files into ChromaDB using semantic chunking.

  DOCS_PATH      Directory containing .txt HR documents (default: assets)
  --db-path TEXT Override CHROMADB_PATH from .env

hr-chatbot serve [OPTIONS]
  Start the web server (landing page + chat interface).

  --host TEXT    Override HOST from .env
  --port INT     Override PORT from .env
  --reload       Enable hot reload (development mode)
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

Change only the relevant variables in `.env` and restart the server. No code changes required.

| Provider | `LITELLM_MODEL` example | Key variable |
|----------|------------------------|--------------|
| OpenAI | `openai/gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-2.0-flash` | `GOOGLE_API_KEY` |
| OpenRouter | `openrouter/google/gemma-3-12b` | `OPENROUTER_API_KEY` |
| Ollama | `ollama/llama3.2` | `OLLAMA_API_BASE` |
| LM Studio | `openai/local-model` | `LITELLM_API_BASE=http://localhost:1234/v1` |

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_MODEL` | `openai/gpt-4o` | LLM model string (any LiteLLM-supported model) |
| `LITELLM_API_BASE` | — | Custom base URL for LM Studio, Ollama proxy, or OpenRouter |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GOOGLE_API_KEY` | — | Google API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama server URL |
| `CHROMADB_PATH` | `data/chromadb` | Path to the ChromaDB index directory |
| `TOP_K_RESULTS` | `5` | Number of chunks returned per query (after re-ranking) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `SECRET_KEY` | `change-me-in-production` | Session cookie signing key |
| `CHAINLIT_AUTH_SECRET` | — | JWT secret for Chainlit auth (`chainlit create-secret`) |

> `CHUNK_SIZE` and `CHUNK_OVERLAP` are no longer used. The semantic chunker determines split points from paragraph and section structure, not character counts.

## Troubleshooting

**"Knowledge base is empty" warning in chat**
Run `make build-db` before starting the server.

**ChromaDB conflict errors when rebuilding**
Run `make clean-db` before `make build-db` to wipe the old index.

**`ModuleNotFoundError: No module named 'src'`**
Run `make setup` to install the package in editable mode, or activate the venv: `source venv/bin/activate`.

**Ollama model not responding**
Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull llama3.2`).

**ChromaDB ONNX model download on first run**
On the first `make build-db`, ChromaDB downloads the embedding model (~90 MB). This is a one-time operation.

**`ValueError: You must provide a JWT secret`**
Set `CHAINLIT_AUTH_SECRET` in `.env`. Generate one with `venv/bin/chainlit create-secret`.
