# Architecture

## System Overview

The HR Chatbot is a layered, agentic RAG (Retrieval-Augmented Generation) system. It combines a FastAPI landing page, a Chainlit chat interface, a Google ADK AI agent, a LiteLLM model adapter, and a ChromaDB vector database to answer employee questions based on curated HR documents.

```
┌─────────────────────────────────────────────┐
│              Browser (User)                 │
└────────────────────┬────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────┐
│           Presentation Layer                │
│  FastAPI Landing Page  (src/landing.py)     │
│  - KYC form (name, email, dept, position)   │
│  - Session token set in cookie              │
│  - Redirects to /chat on submit             │
└────────────────────┬────────────────────────┘
                     │ redirect → /chat (WebSocket)
┌────────────────────▼────────────────────────┐
│           Presentation Layer                │
│        Chainlit  (src/ui/app.py)            │
│  - Reads user profile from session cookie   │
│  - Streaming chat interface (SSE)           │
│  - Clear / delete session actions           │
└────────────────────┬────────────────────────┘
                     │ async call
┌────────────────────▼────────────────────────┐
│           Business Logic Layer              │
│       Google ADK Agent  (src/agents/)       │
│  - Personalized system prompt per user      │
│  - Tool orchestration (4 RAG tools)         │
│  - LiteLLM model routing (any provider)     │
│  - In-memory conversation history (ADK)     │
└──────────┬──────────────────────────────────┘
           │ tool calls
┌──────────▼──────────────────────────────────┐
│           Data Access Layer                 │
│     ChromaDB Vector Store  (src/rag/)       │
│  - Semantic chunks (paragraph/section)      │
│  - Embeddings computed internally (ONNX)    │
│  - Re-ranked results (cosine + keyword)     │
│  - Full-document context expansion          │
└─────────────────────────────────────────────┘
```

## Request Flow

1. **User opens** `http://localhost:8000/` → FastAPI serves the KYC form.
2. **Form submission** → `POST /submit` stores user profile in the in-memory session store (`src/session_store.py`), sets an `hr_session` cookie, and redirects to `/chat`.
3. **Chainlit auth** → `@cl.header_auth_callback` reads the cookie, looks up the user profile in the session store, and returns a `cl.User` that Chainlit attaches to the WebSocket session.
4. **Chat starts** → `@cl.on_chat_start` reads the `cl.User` metadata, creates a personalised ADK `Agent` (system prompt includes name, department, position) and an ADK `Runner`.
5. **User sends a message** → `@cl.on_message` appends lightweight profile context, calls `HRAgentRunner.chat_stream()`.
6. **Agent runs** → ADK `Runner.run_async(run_config=RunConfig(streaming_mode=StreamingMode.SSE))` invokes the LiteLLM model with streaming enabled. The LLM calls one or more `FunctionTool` instances.
7. **Tool execution** → one of four tools is called:
   - `search_hr_documents` — vector search + keyword re-ranking, returns top-K cited excerpts.
   - `get_benefits_by_profile` — same as above but with a role-scoped query.
   - `get_full_document` — fetches and reassembles the complete ordered content of a named source file when chunk context is insufficient.
   - `list_hr_documents` — lists all indexed filenames so the agent can identify valid targets for `get_full_document`.
8. **LLM generates response** → based on retrieved context, citing source document and section.
9. **Streaming to UI** → partial ADK events (`event.partial=True`) are forwarded to `cl.Message.stream_token()`, producing token-by-token output. If the model does not stream, the single final event is used as a fallback.
10. **Conversation history** → maintained by ADK `InMemorySessionService` across messages within a session.

## Chunking and Retrieval Strategy

### Semantic Chunking

Documents are split at natural semantic boundaries rather than arbitrary character windows:

1. **Paragraph splitting** — raw text is split on blank lines (`\n\n`) into blocks.
2. **Section heading detection** — blocks whose first line matches a heading pattern (numbered sections `1.`, `1.1`, ALL-CAPS headings, or `Article/Section/Clause N`) start a new chunk and are recorded as the section label in metadata.
3. **Short-block merging** — consecutive blocks shorter than 120 characters are merged into their neighbour to avoid overly granular chunks.
4. **Long-block splitting** — blocks exceeding 2 000 characters are split at sentence boundaries to respect context-window limits.

Each chunk carries `source`, `doc_id`, `section`, `chunk_index`, and `total_chunks` metadata.

### Re-ranked Retrieval

`HRRetriever.retrieve()` applies a two-stage retrieval strategy:

1. **Candidate fetch** — ChromaDB returns `top_k × 2` candidates ranked by cosine similarity, including the raw distance score in each document's metadata.
2. **Re-ranking** — each candidate is scored by:
   ```
   combined = 0.7 × cosine_similarity + 0.3 × keyword_overlap
   ```
   where `keyword_overlap` is the fraction of query words present in the chunk text.
3. **Top-K selection** — the `top_k` highest-scoring candidates are returned with source citations.

### Context Expansion

When a chunk alone is insufficient, the agent calls `get_full_document(source_filename)`. The retriever reassembles all chunks for that file in `chunk_index` order, returning the complete document as a single string.

## Key Components

| Component | Module | Responsibility |
|-----------|--------|----------------|
| Config | `src/config.py` `Settings` | Centralised env-var loading via pydantic-settings |
| Session Store | `src/session_store.py` | In-process dict mapping tokens → user profiles |
| Loader | `src/rag/loader.py` | Reads `.txt` files from assets directory |
| Chunker | `src/rag/chunker.py` | Semantic splitter: paragraph/section boundaries, merge/split rules |
| Vector Store | `src/rag/vector_store.py` `VectorStore` | ChromaDB wrapper: build / load / search (with distances) / get chunks / list sources |
| Retriever | `src/rag/retriever.py` `HRRetriever` | Re-ranked query → formatted citations; full-doc retrieval; source listing |
| Tools | `src/tools/hr_tools.py` `create_hr_tools()` | 4 ADK FunctionTools: search, benefits, full-doc, list |
| Agent | `src/agents/hr_agent.py` `HRAgentRunner` | Per-session ADK Agent + Runner lifecycle; SSE streaming |
| Landing Page | `src/landing.py` | FastAPI router: KYC form + session cookie |
| Chat UI | `src/ui/app.py` | Chainlit handlers + header auth callback |
| Server | `src/server.py` | Mounts landing router and Chainlit at `/chat`; loads `.env` before Chainlit init |
| CLI | `src/cli.py` | `build-db` (index assets) and `serve` (launch app) |

## Design Decisions

- **Semantic chunking over fixed windows**: Paragraph and section-boundary detection preserves the natural grouping of HR policy text. A fixed-size window would routinely bisect a bullet list or split a numbered clause from its preamble, reducing retrieval quality.
- **Re-ranking with keyword overlap**: Pure cosine similarity can rank paraphrased content higher than an exact-match clause. Adding a 30 % keyword-overlap component ensures that queries using the exact terminology from the document surface the most relevant chunk.
- **Context expansion as an agent tool**: Rather than always fetching full documents (expensive) or only chunks (sometimes insufficient), the agent decides at inference time when broader context is needed and calls `get_full_document` explicitly.
- **ChromaDB with internal embeddings**: ChromaDB embeds text internally using its bundled ONNX model (`all-MiniLM-L6-v2`). No separate embedding service or API key is required, simplifying the stack.
- **SSE streaming mode**: ADK's `RunConfig(streaming_mode=StreamingMode.SSE)` enables partial events per token. Without this, ADK defaults to `StreamingMode.NONE` and the full response arrives as a single event, blocking the UI until generation completes.
- **Shared in-process session store**: Both the FastAPI landing page and the Chainlit UI run within the same `uvicorn` process (via `mount_chainlit`), allowing them to share a Python dict as a lightweight session store without a Redis dependency.
- **Per-session ADK Agent**: The system prompt is personalized per user. A new `Agent` + `Runner` is created per Chainlit session (not per message) to keep the personalized instruction fixed.
- **LiteLLM as model adapter**: A single `LITELLM_MODEL` env var switches between any supported provider (OpenAI, Anthropic, Google, Ollama, LM Studio) without code changes. Custom base URLs are supported via `LITELLM_API_BASE`.
- **Text-only assets**: HR documents are stored as plain `.txt` files in `assets/`, keeping the pipeline simple — no PDF/DOCX parsing libraries required.
