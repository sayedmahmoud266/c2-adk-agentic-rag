"""Chainlit application entry point for the HR AI assistant."""
import logging
from typing import Optional

import chainlit as cl

from src.agents.hr_agent import HRAgentRunner
from src.config import get_settings
from src.rag.retriever import HRRetriever
from src.rag.vector_store import VectorStore
from src.tools.hr_tools import create_hr_tools
from src import session_store

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level initialization — runs once when the server process starts.
# ---------------------------------------------------------------------------
settings = get_settings()

vector_store = VectorStore(settings.chromadb_path)
try:
    vector_store.load()
except Exception:
    logger.warning(
        "ChromaDB index not found at '%s'. Run 'make build-db' to index HR documents.",
        settings.chromadb_path,
    )

retriever = HRRetriever(vector_store, top_k=settings.top_k_results)
tools = create_hr_tools(retriever)

agent_runner = HRAgentRunner(
    model_name=settings.litellm_model,
    tools=tools,
    app_name=settings.app_name,
    api_base=settings.litellm_api_base,
)

_SESSION_ACTIONS = [
    cl.Action(name="clear_conversation", label="Clear Conversation", payload={}),
    cl.Action(name="delete_user_data", label="Delete My Data", payload={}),
]


# ---------------------------------------------------------------------------
# Auth — reads the hr_session cookie set by the landing page
# ---------------------------------------------------------------------------
def _parse_cookies(cookie_header: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for item in cookie_header.split(";"):
        if "=" in item:
            key, _, value = item.strip().partition("=")
            cookies[key.strip()] = value.strip()
    return cookies


@cl.header_auth_callback
def header_auth_callback(headers: dict) -> Optional[cl.User]:
    """Authenticate the user from the landing-page session cookie."""
    cookies = _parse_cookies(headers.get("cookie", ""))
    token = cookies.get("hr_session")
    if not token:
        return cl.User(identifier="anonymous", metadata={})

    user_data = session_store.get_session(token)
    if not user_data:
        return cl.User(identifier="anonymous", metadata={})

    return cl.User(identifier=user_data["email"], metadata=user_data)


# ---------------------------------------------------------------------------
# Chat lifecycle
# ---------------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start():
    app_user: Optional[cl.User] = cl.user_session.get("user")

    # Guard: redirect if the user skipped the landing page
    if not app_user or not app_user.metadata:
        await cl.Message(
            content=(
                "## Welcome to HR Assistant\n\n"
                "Please complete the onboarding form before starting a chat session.\n\n"
                "[**Go to the onboarding form →**](/)"
            )
        ).send()
        return

    user_data = app_user.metadata
    session_id = cl.context.session.id
    user_id = user_data["email"]

    cl.user_session.set("user_data", user_data)
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("user_id", user_id)

    await agent_runner.create_session(user_id, session_id, user_data)

    if vector_store.doc_count == 0:
        index_warning = (
            "\n\n> **Note:** The HR knowledge base is empty. "
            "Run `make build-db` to index HR documents."
        )
    else:
        index_warning = (
            f"\n\n> Knowledge base loaded with **{vector_store.doc_count}** document chunks."
        )

    await cl.Message(
        content=(
            f"Hello **{user_data['name']}** "
            f"({user_data['position']}, {user_data['department']})!\n\n"
            "I'm your HR assistant. Ask me anything about company policies, "
            "benefits, leave entitlements, or HR procedures."
            + index_warning
        ),
        actions=_SESSION_ACTIONS,
    ).send()


# ---------------------------------------------------------------------------
# Message handler with streaming
# ---------------------------------------------------------------------------
@cl.on_message
async def on_message(message: cl.Message):
    user_data = cl.user_session.get("user_data")
    session_id = cl.user_session.get("session_id")
    user_id = cl.user_session.get("user_id")

    if not user_data or not session_id:
        await cl.Message(
            content="Your session has expired. Please refresh the page."
        ).send()
        return

    # Append lightweight profile context so the agent can call the right tool
    enriched = (
        f"{message.content}\n\n"
        f"[My profile: {user_data['position']} in {user_data['department']}]"
    )

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        async for chunk in agent_runner.chat_stream(
            message=enriched,
            user_id=user_id,
            session_id=session_id,
        ):
            await response_msg.stream_token(chunk)
        await response_msg.update()
    except Exception:
        logger.exception("Unhandled error in on_message for session %s", session_id)
        await response_msg.update()
        await cl.Message(
            content="An unexpected error occurred. Please try again or refresh the page."
        ).send()


# ---------------------------------------------------------------------------
# Action callbacks
# ---------------------------------------------------------------------------
@cl.action_callback("clear_conversation")
async def clear_conversation(action: cl.Action):
    user_data = cl.user_session.get("user_data")
    session_id = cl.user_session.get("session_id")
    user_id = cl.user_session.get("user_id")

    if not user_data or not session_id:
        await cl.Message("No active session to clear.").send()
        return

    await agent_runner.reset_session(user_id, session_id, user_data)
    await cl.Message(
        content="Conversation history cleared. How can I help you?",
        actions=_SESSION_ACTIONS,
    ).send()


@cl.action_callback("delete_user_data")
async def delete_user_data(action: cl.Action):
    session_id = cl.user_session.get("session_id")
    user_id = cl.user_session.get("user_id")

    if session_id and user_id:
        await agent_runner.delete_session(user_id, session_id)

    cl.user_session.set("user_data", None)
    cl.user_session.set("session_id", None)
    cl.user_session.set("user_id", None)

    await cl.Message(
        content=(
            "All your session data has been deleted. "
            "Please refresh the page to start a new session."
        )
    ).send()
