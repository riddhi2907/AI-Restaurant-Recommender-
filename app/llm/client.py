"""Groq LLM client wrapper with retry logic."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from groq import Groq

from app.config import Settings, settings as default_settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
_RETRY_BASE_DELAY_SEC = 1.0


class LLMClientError(Exception):
    """Raised when the Groq API call fails after retries."""


@dataclass(frozen=True)
class LLMCompletionResult:
    content: str
    model: str
    latency_ms: float
    usage: dict[str, int] | None = None


class LLMClient:
    """Thin wrapper around the Groq chat completions API."""

    def __init__(self, settings: Settings | None = None, *, client: Groq | None = None) -> None:
        self.settings = settings or default_settings
        self._client = client

    def _get_client(self) -> Groq:
        if self._client is not None:
            return self._client
        if not self.settings.groq_configured:
            raise LLMClientError("GROQ_API_KEY is not configured")
        return Groq(api_key=self.settings.groq_api_key)

    def complete(self, messages: list[dict[str, str]]) -> LLMCompletionResult:
        """Send a chat completion request with exponential backoff on rate limits."""
        if not self.settings.groq_configured:
            raise LLMClientError("GROQ_API_KEY is not configured")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._call(messages)
            except Exception as exc:
                if not self._is_retryable(exc) or attempt >= MAX_RETRIES:
                    raise LLMClientError(str(exc)) from exc
                delay = _RETRY_BASE_DELAY_SEC * (2**attempt)
                logger.warning(
                    "Groq rate limit or transient error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    delay,
                    exc,
                )
                last_error = exc
                time.sleep(delay)

        raise LLMClientError(str(last_error)) from last_error

    def _call(self, messages: list[dict[str, str]]) -> LLMCompletionResult:
        client = self._get_client()
        started = time.perf_counter()

        kwargs: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
        }
        try:
            kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            if self._is_response_format_error(exc):
                kwargs.pop("response_format", None)
                response = client.chat.completions.create(**kwargs)
            else:
                raise

        latency_ms = (time.perf_counter() - started) * 1000
        content = response.choices[0].message.content or ""
        usage = self._extract_usage(response)

        return LLMCompletionResult(
            content=content,
            model=response.model,
            latency_ms=latency_ms,
            usage=usage,
        )

    @staticmethod
    def _extract_usage(response: Any) -> dict[str, int] | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "total_tokens": getattr(usage, "total_tokens", 0) or 0,
        }

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None)
        if status == 429:
            return True
        if status in (500, 502, 503, 504):
            return True
        exc_name = type(exc).__name__.lower()
        return "ratelimit" in exc_name or "rate_limit" in exc_name

    @staticmethod
    def _is_response_format_error(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None)
        if status in (400, 422):
            message = str(exc).lower()
            return "response_format" in message or "json" in message
        return False
