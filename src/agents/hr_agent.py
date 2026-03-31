"""Google ADK agent runner for the HR assistant."""
import logging
from typing import AsyncGenerator

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """You are a helpful and professional HR assistant for {app_name}.
You have access to the company's HR knowledge base through your tools.

Always use your search tools before answering HR-related questions to ensure accuracy.
Do not make up policies or information not found in the documents.

User Profile:
- Name: {name}
- Department: {department}
- Position: {position}

Guidelines:
- Search the knowledge base before answering any HR question.
- Be empathetic, concise, and professional in your responses.
- If a topic is not covered in the HR documents, say so clearly and suggest contacting HR directly.
- For questions about personal entitlements, call get_benefits_by_profile with the user's department and position.
- always mention the source document code when providing information with the exact section this information was found in.
- If the user asks for a specific document, use list_hr_documents to find the filename and then get_full_document to retrieve it.
- Never provide information that cannot be backed up by the documents in the knowledge base.
- If the user asks about a topic that is not in the documents, respond with "I'm sorry, but that information is not available in the HR knowledge base. Please contact HR directly for assistance."
- If the user asked about a general knowledge question that is not specific to the company. you should'nt answer it, instead respond with "I'm here to help with questions about our company's HR policies and procedures. For general information, please refer to internet search or any other reliable sources."
"""


class HRAgentRunner:
    """Manages per-session ADK agents and runners for the HR chatbot."""

    def __init__(self, model_name: str, tools: list, app_name: str, api_base: str = ""):
        self.model_name = model_name
        self.api_base = api_base
        self.tools = tools
        self.app_name = app_name
        self.session_service = InMemorySessionService()
        # Maps session_id -> Runner
        self._runners: dict[str, Runner] = {}

    def _build_runner(self, user_data: dict) -> Runner:
        """Build a personalized ADK Agent and Runner for a user session."""
        instruction = _SYSTEM_PROMPT_TEMPLATE.format(
            app_name=self.app_name,
            name=user_data.get("name", "User"),
            department=user_data.get("department", "Unknown"),
            position=user_data.get("position", "Unknown"),
        )
        litellm_kwargs = {}
        if self.api_base:
            litellm_kwargs["api_base"] = self.api_base
        agent = Agent(
            name="hr_assistant",
            model=LiteLlm(model=self.model_name, **litellm_kwargs),
            instruction=instruction,
            tools=self.tools,
        )
        return Runner(
            agent=agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

    async def create_session(
        self, user_id: str, session_id: str, user_data: dict
    ) -> None:
        """Create a new ADK session for an incoming Chainlit user."""
        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        self._runners[session_id] = self._build_runner(user_data)
        logger.info("Created ADK session: user_id=%s session_id=%s", user_id, session_id)

    async def chat_stream(
        self, message: str, user_id: str, session_id: str
    ) -> AsyncGenerator[str, None]:
        """Run the agent and yield text tokens as they arrive."""
        runner = self._runners.get(session_id)
        if runner is None:
            yield "Session not found. Please refresh the page to start over."
            return

        user_content = Content(role="user", parts=[Part(text=message)])
        run_config = RunConfig(streaming_mode=StreamingMode.SSE)
        has_streamed = False

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content,
                run_config=run_config,
            ):
                # Partial events carry incremental text deltas — stream them live
                if event.partial and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            has_streamed = True
                            yield part.text
                # If the model doesn't stream, fall back to the single final event
                elif event.is_final_response() and not has_streamed:
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                yield part.text
        except Exception:
            logger.exception("Error during agent run for session %s", session_id)
            yield "\n\n_An error occurred while processing your request. Please try again._"

    async def reset_session(
        self, user_id: str, session_id: str, user_data: dict
    ) -> None:
        """Clear conversation history by deleting and recreating the ADK session."""
        await self.delete_session(user_id, session_id)
        await self.create_session(user_id, session_id, user_data)

    async def delete_session(self, user_id: str, session_id: str) -> None:
        """Permanently remove session data from memory."""
        try:
            await self.session_service.delete_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            logger.warning("Could not delete ADK session %s (may not exist)", session_id)
        self._runners.pop(session_id, None)
        logger.info("Deleted ADK session: user_id=%s session_id=%s", user_id, session_id)
