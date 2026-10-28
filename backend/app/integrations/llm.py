
"""Groq LLM integration for the CRM."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured."""


class LLMProviderError(RuntimeError):
    """Raised when the LLM provider request fails."""


class GroqLLMClient:
    """Async client for generating text with Groq."""

    def __init__(self) -> None:
        self._client: ChatGroq | None = None

    def _get_client(self) -> ChatGroq:
        """Create the provider client only when it is first needed."""

        if not settings.GROQ_API_KEY:
            raise LLMConfigurationError(
                "The AI provider is not configured."
            )

        if self._client is None:
            self._client = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                timeout=settings.GROQ_TIMEOUT_SECONDS,
                max_retries=settings.GROQ_MAX_RETRIES,
            )

        return self._client

    def get_chat_model(self) -> ChatGroq:
      """Return the configured Groq chat model."""
      return self._get_client()

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a text response without blocking the event loop."""

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        messages = []

        if system_prompt and system_prompt.strip():
            messages.append(SystemMessage(content=system_prompt.strip()))

        messages.append(HumanMessage(content=prompt.strip()))

        client = self._get_client()

        try:
            response = await client.ainvoke(messages)
        except Exception as exc:
            # Do not log prompts, API keys, or raw provider error details.
            logger.warning(
                "Groq request failed; error_type=%s",
                type(exc).__name__,
            )
            raise LLMProviderError(
                "The AI provider request failed."
            ) from exc

        if not isinstance(response.content, str):
            raise LLMProviderError(
                "The AI provider returned an unsupported response."
            )

        result = response.content.strip()

        if not result:
            raise LLMProviderError(
                "The AI provider returned an empty response."
            )

        return result



groq_client = GroqLLMClient()
