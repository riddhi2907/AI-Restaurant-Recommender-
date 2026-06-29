"""LLM recommendation engine — prompt, call, parse, validate, fallback."""

from __future__ import annotations

import logging

from app.llm.client import LLMClient, LLMClientError
from app.llm.parser import (
    ResponseParser,
    build_filter_fallback,
    build_llm_response,
)
from app.llm.prompts import PromptBuilder
from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationMetadata, RecommendationResponse
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate ranked, explained recommendations from filtered candidates."""

    def __init__(
        self,
        *,
        prompt_builder: PromptBuilder | None = None,
        client: LLMClient | None = None,
        parser: ResponseParser | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.client = client or LLMClient()
        self.parser = parser or ResponseParser()

    def generate(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        *,
        total_candidates: int,
        filters_applied: dict[str, object],
        filters_relaxed: list[str] | None = None,
    ) -> RecommendationResponse:
        if not candidates:
            return RecommendationResponse(
                summary=None,
                recommendations=[],
                metadata=RecommendationMetadata(
                    total_candidates=total_candidates,
                    filters_applied=filters_applied,
                    llm_used=False,
                    filters_relaxed=list(filters_relaxed or []),
                ),
            )

        try:
            messages = self.prompt_builder.build_messages(preferences, candidates)
            completion = self.client.complete(messages)
        except LLMClientError as exc:
            logger.warning("LLM call failed, using filter fallback: %s", exc)
            return build_filter_fallback(
                candidates,
                preferences,
                total_candidates=total_candidates,
                filters_applied=filters_applied,
                filters_relaxed=filters_relaxed,
            )

        parsed = self.parser.parse(completion.content)
        if parsed is None:
            logger.warning("Failed to parse LLM response, using filter fallback")
            return build_filter_fallback(
                candidates,
                preferences,
                total_candidates=total_candidates,
                filters_applied=filters_applied,
                filters_relaxed=filters_relaxed,
            )

        response = build_llm_response(
            parsed,
            candidates,
            preferences,
            total_candidates=total_candidates,
            filters_applied=filters_applied,
            filters_relaxed=filters_relaxed,
            llm_latency_ms=completion.latency_ms,
            token_usage=completion.usage,
        )

        if not response.recommendations:
            logger.warning("No valid LLM recommendations after validation, using filter fallback")
            return build_filter_fallback(
                candidates,
                preferences,
                total_candidates=total_candidates,
                filters_applied=filters_applied,
                filters_relaxed=filters_relaxed,
            )

        return response
