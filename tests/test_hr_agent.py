"""Tests for src/agents/hr_agent.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def agent_runner():
    with patch("src.agents.hr_agent.InMemorySessionService") as MockService, \
         patch("src.agents.hr_agent.Agent"), \
         patch("src.agents.hr_agent.LiteLlm"), \
         patch("src.agents.hr_agent.Runner"):

        mock_service = AsyncMock()
        MockService.return_value = mock_service

        from src.agents.hr_agent import HRAgentRunner

        runner = HRAgentRunner(
            model_name="openai/gpt-4o",
            tools=[],
            app_name="Test HR",
        )
        runner.session_service = mock_service
        return runner


@pytest.mark.asyncio
async def test_create_session_stores_runner(agent_runner):
    user_data = {"name": "Alice", "email": "alice@test.com", "department": "Eng", "position": "Dev"}

    with patch("src.agents.hr_agent.Runner") as MockRunner, \
         patch("src.agents.hr_agent.Agent"), \
         patch("src.agents.hr_agent.LiteLlm"):
        MockRunner.return_value = MagicMock()
        await agent_runner.create_session("alice@test.com", "sess-1", user_data)

    assert "sess-1" in agent_runner._runners


@pytest.mark.asyncio
async def test_delete_session_removes_runner(agent_runner):
    agent_runner._runners["sess-2"] = MagicMock()

    await agent_runner.delete_session("user@test.com", "sess-2")

    assert "sess-2" not in agent_runner._runners


@pytest.mark.asyncio
async def test_chat_stream_missing_session_yields_error(agent_runner):
    chunks = []
    async for chunk in agent_runner.chat_stream("hello", "user", "nonexistent-session"):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert "not found" in chunks[0].lower() or "refresh" in chunks[0].lower()
