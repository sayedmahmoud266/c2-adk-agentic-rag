"""Server-side session store shared between the landing page and Chainlit."""
import secrets
from typing import Optional

_sessions: dict[str, dict] = {}


def create_session(user_data: dict) -> str:
    """Store user_data and return a random opaque token."""
    token = secrets.token_hex(32)
    _sessions[token] = user_data
    return token


def get_session(token: str) -> Optional[dict]:
    """Return user_data for the token, or None if not found."""
    return _sessions.get(token)


def delete_session(token: str) -> None:
    """Remove the session from the store."""
    _sessions.pop(token, None)
