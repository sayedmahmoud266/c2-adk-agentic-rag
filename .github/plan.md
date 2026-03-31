# Project Initialization Plan: HR AI Assistant (Agentic RAG)

## Overview

A web-based HR AI chatbot powered by an agentic RAG pipeline. Users submit a KYC form on a landing page, then interact with an AI assistant that retrieves answers from HR documents stored in a vectordb in-memory vector database, orchestrated by a Google ADK agent and powered by LiteLLM.

---

## Tech Stack

| Layer             | Technology                              |
|-------------------|-----------------------------------------|
| Chatbot UI        | Chainlit                                |
| Landing Page      | FastAPI + Jinja2 (mounted alongside Chainlit) |
| Agent Manager     | Google ADK (`google-adk`)               |
| LLM               | LiteLLM (supports OpenAI, Anthropic, Ollama, LMStudio, etc.) |
| Vector Database   | `vectordb` — in-memory, embeddings handled internally, persisted to `/data` |
| Document Loader   | Plain `open()` reads — files are simple `.txt` |
| Config            | `pydantic-settings` + `python-dotenv`   |
| Testing           | `pytest`                                |
| Build Automation  | `Makefile`                              |

---

## Project Structure

```
c2-adk-agentic-rag/
├── .env                           # Local env vars (gitignored)
├── .env.example                   # Documented env var template
├── .gitignore
├── Makefile                       # Common automation targets
├── README.md
├── requirements.txt
│
├── assets/                        # Input: HR documents (.txt files)
│   └── .gitkeep
│
├── data/                          # Output: persisted vectordb index
│   └── .gitkeep
│
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── usage.md
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Pydantic settings model
│   │
│   ├── app.py                     # Chainlit entry point (chat interface)
│   ├── landing.py                 # FastAPI app serving KYC landing page
│   ├── server.py                  # Server entrypoint: mounts both apps
│   │
│   ├── templates/
│   │   └── index.html             # KYC form HTML (Jinja2)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── hr_agent.py            # Google ADK agent definition
│   │   └── tools.py               # Agent tools: RAG retrieval tool
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py              # Plain text file reader
│   │   ├── chunker.py             # Text splitting / chunking
│   │   ├── vector_store.py        # vectordb wrapper: build, save, load, search
│   │   └── retriever.py           # High-level RAG retrieval interface
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py                # UserProfile dataclass (name, email, dept, position)
│   │
│   └── cli/
│       ├── __init__.py
│       ├── build_db.py            # `make build-db` — ingests /assets → /data
│       └── start_server.py        # `make serve` — starts the web server
│
└── tests/
    ├── __init__.py
    ├── test_rag.py
    ├── test_agents.py
    └── test_cli.py
```

---

## Implementation Phases

### Phase 1 — Project Scaffolding

**Files to create:** `.gitignore`, `README.md`, `requirements.txt`, `.env.example`, `Makefile`, all `__init__.py` files, `assets/.gitkeep`, `data/.gitkeep`

**`requirements.txt` dependencies:**
```
# Core
chainlit
fastapi
uvicorn[standard]
jinja2
python-multipart

# Agent
google-adk

# LLM
litellm

# Vector DB (handles embeddings internally)
vectordb

# Config
pydantic-settings
python-dotenv

# Testing
pytest
pytest-asyncio
```

**`.env.example`:**
```
# LLM Configuration (LiteLLM)
LITELLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=

# Optional providers (uncomment as needed)
# ANTHROPIC_API_KEY=
# GOOGLE_API_KEY=
# OLLAMA_API_BASE=http://localhost:11434

# Vector DB
VECTOR_DB_PATH=./data/vectordb
ASSETS_PATH=./assets

# App
APP_HOST=0.0.0.0
APP_PORT=8000
```

**`Makefile` targets:**
```makefile
install        # Create venv and install requirements
build-db       # Run CLI to ingest .txt documents and build vectordb index
serve          # Start the web server (landing page + chatbot)
test           # Run pytest
lint           # Run flake8/ruff
clean          # Remove __pycache__, .pytest_cache, etc.
```

---

### Phase 2 — Configuration Layer

**`src/config.py`** — Pydantic `BaseSettings` class that reads from `.env`:
- `litellm_model: str`
- `vector_db_path: str`
- `assets_path: str`
- `app_host: str`
- `app_port: int`

Singleton `get_settings()` function with `lru_cache`.

---

### Phase 3 — Data Models

**`src/models/user.py`** — `UserProfile` dataclass:
```python
@dataclass
class UserProfile:
    name: str
    email: str
    department: str
    position: str
```

Used to carry user context through Chainlit sessions and into agent prompts.

---

### Phase 4 — RAG Pipeline (`src/rag/`)

#### 4a. Document Loader (`loader.py`)
- `load_documents(path: str) -> list[dict]`
- Scans `assets_path` for `.txt` files
- Returns list of `{"content": str, "source": filename}` dicts
- Simple `open().read()` — no third-party loaders needed

#### 4b. Text Chunker (`chunker.py`)
- `chunk_documents(docs, chunk_size=512, overlap=64) -> list[dict]`
- Splits each document's content into overlapping windows
- Preserves `source` metadata on every chunk
- Chunking is still worthwhile even for text files — large docs should not be stored as single vectors

#### 4c. Vector Store (`vector_store.py`)
- `VectorStore` class wrapping `vectordb`:
  - `build(chunks)` — adds all chunks; vectordb computes embeddings internally
  - `save(path)` — persists the index to `/data`
  - `load(path)` — loads the persisted index from `/data`
  - `search(query_text, top_k=5) -> list[dict]` — similarity search; vectordb embeds the query internally

#### 4d. Retriever (`retriever.py`)
- `retrieve(query: str, top_k=5) -> str`
- Loads the vector store (cached singleton after first load)
- Returns a formatted context string with chunk content and source filenames

---

### Phase 5 — Agent Layer (`src/agents/`)

#### 5a. RAG Tool (`tools.py`)
- Defines a Google ADK `FunctionTool` named `search_hr_documents`:
  ```python
  def search_hr_documents(query: str) -> str:
      """Search internal HR documents for relevant policy information."""
      return retriever.retrieve(query, user_profile)
  ```
- User profile is injected into the tool's closure at session start

#### 5b. HR Agent (`hr_agent.py`)
- `create_hr_agent(user_profile: UserProfile) -> Agent`
- Constructs a Google ADK `Agent` with:
  - `model`: LiteLLM-compatible model string
  - `tools`: `[search_hr_documents]`
  - `instruction`: System prompt personalized with user's name, department, and position
  - Instructs the agent to always retrieve from documents before answering

---

### Phase 6 — Landing Page (`src/landing.py` + `src/templates/index.html`)

**`landing.py`** — FastAPI app:
- `GET /` — renders `index.html` with the KYC form
- `POST /submit` — receives form data (name, email, department, position), stores in a server-side session (via `starlette.middleware.sessions`), redirects to `/chat`

**`index.html`** — Simple, clean HTML form:
- Fields: Full Name, Email Address, Department (dropdown or text), Position
- Submit button → POST to `/submit`
- Basic responsive CSS (no external frameworks required)

---

### Phase 7 — Chatbot Interface (`src/app.py`)

Chainlit event handlers:

| Event | Action |
|---|---|
| `@cl.on_chat_start` | Read user profile from session; create HR agent; store agent in `cl.user_session`; display welcome message |
| `@cl.on_message` | Get agent from session; run agent with user message; stream response token-by-token via `cl.Message` |
| `@cl.on_chat_end` | Clean up session data |
| Custom action: **Clear History** | `cl.user_session` cleared; confirmation message shown |
| Custom action: **Delete My Data** | Session data cleared + flag set; confirmation shown |

**Streaming:** Use LiteLLM's streaming + Chainlit's `cl.Message` streaming API to display tokens as they arrive.

**Error handling:**
- vectordb index not found → graceful error message with instructions to run `make build-db`
- LLM API error → user-friendly error message + log the exception
- No relevant documents found → agent responds with "I couldn't find specific information..."

---

### Phase 8 — Server Entrypoint (`src/server.py`)

- Creates a root FastAPI app
- Mounts the landing FastAPI app at `/`
- Mounts the Chainlit app at `/chat`
- Session middleware shared across both mounts
- Runs with `uvicorn`

---

### Phase 9 — CLI Commands

#### `src/cli/build_db.py`
```
Usage: make build-db
       python -m src.cli.build_db [--assets-path PATH] [--output-path PATH]
```
Steps:
1. Scan `assets_path` for `.txt` files
2. Load and chunk all documents
3. Build vectordb index (embeddings computed internally by vectordb)
4. Save index to `data_path`
5. Print summary: N files, M chunks ingested

#### `src/cli/start_server.py`
```
Usage: make serve
       python -m src.cli.start_server [--host HOST] [--port PORT]
```
Steps:
1. Validate that vectordb index exists in `/data` (warn if not)
2. Pre-load the vector store into memory
3. Start `uvicorn` with the server from `src/server.py`

---

### Phase 10 — Tests (`tests/`)

#### `test_rag.py`
- Test document loading from `.txt` files
- Test chunking produces correct sizes and overlap
- Test vectordb vector store: build, save, load, search (mocked vectordb internals)

#### `test_agents.py`
- Test HR agent creation with a mock user profile
- Test `search_hr_documents` tool with mocked retriever
- Test agent produces a response (mocked LiteLLM call)

#### `test_cli.py`
- Test `build_db` CLI with a temp directory of sample docs
- Test error handling for missing assets directory

---

### Phase 11 — Documentation (`docs/`)

#### `docs/architecture.md`
- System diagram (text-based) showing: Browser → FastAPI → Chainlit → ADK Agent → LiteLLM / vectordb
- Description of each component and its responsibilities
- Data flow walkthrough (KYC form → session → chat → agent → RAG → response)

#### `docs/setup.md`
- Prerequisites (Python 3.11+, required API keys)
- Step-by-step installation with `make install`
- How to add HR documents to `/assets`
- How to build the vector DB with `make build-db`
- Environment variable reference table

#### `docs/usage.md`
- How to start the server (`make serve`)
- Navigating the KYC form
- Using the chatbot
- Clearing conversation history
- Deleting user data

#### `README.md`
- Project description (2-3 sentences)
- Quick start (3 commands: install, build-db, serve)
- Link to `/docs` for details

---

## System Flow (End-to-End)

```
1. User visits http://localhost:8000/
   └── FastAPI serves KYC form (index.html)

2. User fills form → POST /submit
   └── FastAPI stores UserProfile in server session → redirect to /chat

3. User arrives at /chat (Chainlit)
   └── on_chat_start reads UserProfile from session
   └── Creates personalized HR Agent (Google ADK) with RAG tool injected
   └── Displays welcome message

4. User sends question
   └── Chainlit on_message calls agent.run(user_message)
   └── ADK Agent decides to call search_hr_documents(query)
       └── Retriever queries vectordb (embedding computed internally) → top-K chunks returned
   └── Agent generates response using retrieved context via LiteLLM
   └── Response streamed token-by-token to Chainlit UI

5. User clears history or deletes data
   └── cl.user_session cleared
   └── Confirmation displayed
```

---

## Implementation Order

1. Phase 1 — Scaffolding (structure, requirements, Makefile, .env)
2. Phase 2 — Config layer
3. Phase 3 — Data models
4. Phase 4 — RAG pipeline (loader → chunker → embeddings → vector store → retriever)
5. Phase 9a — `build_db` CLI (validates RAG pipeline end-to-end)
6. Phase 5 — Agent layer
7. Phase 6 — Landing page
8. Phase 7 — Chainlit chat interface
9. Phase 8 — Server entrypoint
10. Phase 9b — `start_server` CLI
11. Phase 10 — Tests
12. Phase 11 — Documentation
