"""
NeuroTrace - LLM API Client
Wrapper around Groq / OpenAI APIs with retry logic and token tracking.
"""

import json
import asyncio
from groq import Groq, APIError, RateLimitError
from openai import OpenAI

from backend.config import get_settings

settings = get_settings()


class LLMClient:
    """Unified LLM client that supports Groq and OpenAI providers."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.total_tokens_used = 0

        if self.provider == "groq":
            self._client = Groq(api_key=settings.groq_api_key)
        else:
            self._client = OpenAI(api_key=settings.openai_api_key)

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Send a chat completion request and return the response text."""
        model = model or self.model
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        self.total_tokens_used += response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> dict:
        """Send a chat request and parse the response as JSON."""
        raw = self.chat(messages, model, temperature, max_tokens, json_mode=True)
        # sometimes the model wraps JSON in markdown code fences
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        return json.loads(cleaned)

    async def achat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Async wrapper around chat using run_in_executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.chat(messages, model, temperature, max_tokens, json_mode)
        )

    async def achat_json(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> dict:
        """Async wrapper around chat_json."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.chat_json(messages, model, temperature, max_tokens)
        )


_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create a singleton LLM client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
