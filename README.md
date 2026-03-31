# HR AI Assistant — Agentic RAG Chatbot

An HR chatbot powered by **Google ADK**, **ChromaDB**, **LiteLLM**, and **Chainlit**. Employees fill a short onboarding form, then interact with an AI assistant that answers HR questions grounded in company policy documents.

## Features

- **KYC landing page** — collects name, email, department, and position before the chat starts.
- **Agentic RAG** — the AI agent autonomously searches the HR knowledge base before answering.
- **Streaming responses** — answers appear token-by-token in real time.
- **Conversation history** — prior messages are preserved within a session.
- **Any LLM** — switch between OpenAI, Anthropic, Google, Ollama, and more via a single env var.
- **No embedding API needed** — ChromaDB handles embeddings internally via a bundled ONNX model.
- **Privacy controls** — clear conversation or delete all session data from within the chat.

## Quick Start

```bash
# 1. Install
make setup
cp .env.example .env   # edit .env and add your LLM API key

# 2. Index HR documents
make build-db          # indexes assets/ by default

# 3. Run
make serve             # opens at http://localhost:8000
```

## Architecture

```
Browser → FastAPI (KYC form) → session cookie → Chainlit (chat)
                                                      ↓
                                          Google ADK Agent (LiteLLM)
                                                      ↓
                                        ChromaDB Vector Store (ONNX embeddings)
```

See [docs/architecture.md](docs/architecture.md) for the full layered design.

## Tech Stack

| Component | Library |
|-----------|---------|
| Chat UI | [Chainlit](https://chainlit.io) |
| Landing Page | [FastAPI](https://fastapi.tiangolo.com) + Jinja2 |
| Agent framework | [Google ADK](https://github.com/google/adk-python) |
| LLM routing | [LiteLLM](https://docs.litellm.ai) |
| Vector database | [ChromaDB](https://www.trychroma.com) |

## Project Structure

```
src/
├── config.py          # centralised settings (pydantic-settings)
├── cli.py             # CLI: build-db and serve commands
├── server.py          # ASGI root: mounts landing page + Chainlit
├── landing.py         # FastAPI KYC form router
├── session_store.py   # in-memory session token store
├── models/
│   └── user.py        # UserProfile dataclass
├── templates/
│   └── index.html     # KYC form HTML
├── agents/
│   └── hr_agent.py    # ADK agent, session lifecycle, streaming
├── rag/
│   ├── loader.py      # .txt document reader
│   ├── chunker.py     # overlapping text splitter
│   ├── vector_store.py # ChromaDB wrapper (build/load/search)
│   └── retriever.py   # query → formatted source citations
├── tools/
│   └── hr_tools.py    # ADK FunctionTools (search_hr_documents, get_benefits_by_profile)
└── ui/
    └── app.py         # Chainlit entry point + header auth callback

assets/                # HR text documents (indexed by make build-db)
data/chromadb/         # generated ChromaDB index (gitignored)
docs/                  # architecture, setup, and usage guides
tests/                 # pytest unit tests
```

## Configuration

All settings are managed through environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_MODEL` | `openai/gpt-4o` | LLM to use (any LiteLLM model string) |
| `OPENAI_API_KEY` | — | API key for OpenAI |
| `ANTHROPIC_API_KEY` | — | API key for Anthropic |
| `GOOGLE_API_KEY` | — | API key for Google |
| `CHROMADB_PATH` | `data/chromadb` | ChromaDB index directory |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved per query |
| `CHUNK_SIZE` | `500` | Character chunk size for document splitting |
| `SECRET_KEY` | — | Session cookie signing key (set in production) |

## Development

```bash
make test   # run tests with coverage
make lint   # ruff linter
```

See [docs/setup.md](docs/setup.md) for the full setup guide including Ollama/local model configuration.
See [docs/usage.md](docs/usage.md) for end-user instructions.

## License

MIT
