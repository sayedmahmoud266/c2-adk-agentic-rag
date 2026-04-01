# Usage Guide

## Starting the Application

```bash
make serve
```

The application starts at [http://localhost:8000](http://localhost:8000).

## Onboarding Form (Landing Page)

When you first visit the app, you will see a simple onboarding form. Fill in:

- **Full Name** — your name as you would like the assistant to address you.
- **Work Email** — used as your session identifier.
- **Department** — select from the dropdown (Engineering, Finance, HR, etc.).
- **Position / Job Title** — your current role.

Click **Start Chat →** to submit the form and be redirected to the chat interface.

> Your information is stored only in memory for the duration of your session and is never persisted to a database or disk.

## Chat Interface

Once redirected to `/chat`, the HR assistant greets you by name and shows:

- The number of document chunks currently indexed in the knowledge base.
- A warning if the database is empty (run `make build-db` in that case).

### Asking Questions

Type your question in the chat input and press **Enter** (or click Send).

The assistant will:
1. Search the HR knowledge base for relevant policy excerpts, re-ranking results by a blend of semantic similarity and keyword match.
2. If the initial results lack sufficient context, automatically fetch the full text of the relevant document.
3. Generate a response grounded in those excerpts, citing the source document and section.
4. Stream the response token-by-token so you see it as it is generated.

Example questions:
- "How many days of annual leave am I entitled to?"
- "What is the remote work policy?"
- "Can I carry over unused leave to the next year?"
- "What happens during the probation period?"

### Session Actions

Two action buttons appear at the start of each chat session (and after clearing history):

| Button | Effect |
|--------|--------|
| **Clear Conversation** | Deletes the current conversation history from memory. The assistant's context resets but your profile is retained. |
| **Delete My Data** | Removes your profile and session data from memory. You will need to refresh and complete the onboarding form again. |

## Indexing HR Documents

Place `.txt` files in the `assets/` directory, then run:

```bash
make clean-db && make build-db
```

`clean-db` removes the existing ChromaDB index to avoid conflicts with stale data. `build-db` re-indexes all documents using **semantic chunking** — each file is split at paragraph and section boundaries rather than arbitrary character windows, so every chunk represents a coherent piece of policy text.

To index a custom directory:

```bash
make build-db DOCS_PATH=/path/to/your/docs
```

Restart the server afterwards if it is already running so the new index is loaded.


## Accessing the Chat Directly

If you navigate directly to `/chat` without completing the onboarding form, the assistant will display a link back to the landing page (`/`).

## Stopping the Server

Press `Ctrl+C` in the terminal where `make serve` is running.
