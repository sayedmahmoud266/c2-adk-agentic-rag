# HR AI Assistant — Agentic RAG Chatbot

An HR chatbot powered by **Google ADK**, **ChromaDB**, **LiteLLM**, and **Chainlit**. Employees fill a short onboarding form, then interact with an AI assistant that answers HR questions grounded in company policy documents.

## Features

- **KYC landing page** — collects name, email, department, and position before the chat starts.
- **Agentic RAG** — the AI agent autonomously searches the HR knowledge base before answering.
- **Semantic chunking** — documents are split at paragraph and section boundaries, not arbitrary character windows, preserving natural meaning in every chunk.
- **Re-ranked retrieval** — results are scored by a blend of vector similarity (70 %) and keyword overlap (30 %) for higher relevance.
- **Context expansion** — the agent can fetch the full text of any document when a chunk alone is insufficient.
- **Streaming responses** — answers appear token-by-token in real time.
- **Conversation history** — prior messages are preserved within a session.
- **Any LLM** — switch between OpenAI, Anthropic, Google, Ollama, LM Studio, and more via a single env var.
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

To rebuild the index cleanly (avoids ChromaDB conflicts):

```bash
make clean-db && make build-db
```

## Architecture

```
Browser → FastAPI (KYC form) → session cookie → Chainlit (chat)
                                                      ↓
                                          Google ADK Agent (LiteLLM)
                                                      ↓
                                        ChromaDB Vector Store (ONNX embeddings)
                                        semantic chunks · re-ranked results
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
│   ├── chunker.py     # semantic chunker (paragraph + section boundaries)
│   ├── vector_store.py # ChromaDB wrapper (build/load/search/expand)
│   └── retriever.py   # re-ranked query → formatted source citations
├── tools/
│   └── hr_tools.py    # ADK FunctionTools (search, benefits, full-doc, list)
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
| `LITELLM_API_BASE` | — | Custom base URL (LM Studio, Ollama proxy, OpenRouter) |
| `OPENAI_API_KEY` | — | API key for OpenAI |
| `ANTHROPIC_API_KEY` | — | API key for Anthropic |
| `GOOGLE_API_KEY` | — | API key for Google |
| `CHROMADB_PATH` | `data/chromadb` | ChromaDB index directory |
| `TOP_K_RESULTS` | `5` | Chunks returned per query (after re-ranking) |
| `SECRET_KEY` | — | Session cookie signing key (set in production) |
| `CHAINLIT_AUTH_SECRET` | — | JWT secret for Chainlit auth (run `chainlit create-secret`) |

## Development

```bash
make test      # run tests with coverage
make lint      # ruff linter
make clean-db  # wipe ChromaDB index before a fresh rebuild
```

See [docs/setup.md](docs/setup.md) for the full setup guide including Ollama/local model configuration.
See [docs/usage.md](docs/usage.md) for end-user instructions.

## License

MIT
