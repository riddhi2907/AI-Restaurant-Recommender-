"""LLM response parsing, validation, and merging."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.models.preferences import UserPreferences
from app.models.recommendation import Recommendation, RecommendationMetadata, RecommendationResponse
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*\}")

_FALLBACK_EXPLANATION = (
    "Top-rated match for your preferences in {location} "
    "(budget: {budget}, min rating: {min_rating})."
)


class ResponseParser:
    """Extract structured JSON from raw LLM output."""

    def parse(self, raw_text: str) -> dict[str, Any] | None:
        if not raw_text or not raw_text.strip():
            return None

        text = raw_text.strip()

        for candidate in self._json_candidates(text):
            parsed = self._try_load(candidate)
            if parsed is not None:
                return parsed

        return None

    def _json_candidates(self, text: str) -> list[str]:
        candidates: list[str] = []

        fence_match = _JSON_FENCE_PATTERN.search(text)
        if fence_match:
            candidates.append(fence_match.group(1).strip())

        object_match = _JSON_OBJECT_PATTERN.search(text)
        if object_match:
            candidates.append(object_match.group(0).strip())

        candidates.append(text)
        return candidates

    @staticmethod
    def _try_load(text: str) -> dict[str, Any] | None:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None


class RecommendationValidator:
    """Reject hallucinated restaurant IDs and normalize recommendation entries."""

    def validate(
        self,
        parsed: dict[str, Any],
        candidates: list[Restaurant],
    ) -> dict[str, Any]:
        candidate_ids = {r.id for r in candidates}
        raw_recs = parsed.get("recommendations")
        if not isinstance(raw_recs, list):
            return {"summary": parsed.get("summary"), "recommendations": []}

        valid: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for item in raw_recs:
            if not isinstance(item, dict):
                continue
            restaurant_id = str(item.get("restaurant_id", "")).strip()
            if not restaurant_id or restaurant_id not in candidate_ids:
                if restaurant_id:
                    logger.warning("Rejected hallucinated restaurant_id: %s", restaurant_id)
                continue
            if restaurant_id in seen_ids:
                continue
            seen_ids.add(restaurant_id)
            valid.append(item)

        valid.sort(key=lambda r: self._rank_value(r))
        return {"summary": parsed.get("summary"), "recommendations": valid}

    @staticmethod
    def _rank_value(item: dict[str, Any]) -> int:
        try:
            return int(item.get("rank", 9999))
        except (TypeError, ValueError):
            return 9999


class RecommendationMerger:
    """Enrich validated LLM output with full restaurant record fields."""

    def merge(
        self,
        parsed: dict[str, Any],
        candidates: list[Restaurant],
        *,
        top_k: int,
    ) -> list[Recommendation]:
        by_id = {r.id: r for r in candidates}
        recommendations: list[Recommendation] = []
        used_ids: set[str] = set()

        for index, item in enumerate(parsed.get("recommendations", []), start=1):
            restaurant_id = str(item.get("restaurant_id", "")).strip()
            restaurant = by_id.get(restaurant_id)
            if restaurant is None:
                continue

            explanation = str(item.get("explanation", "")).strip()
            if not explanation:
                explanation = f"Recommended based on a {restaurant.rating} rating and {restaurant.cuisine} cuisine."

            recommendations.append(
                Recommendation(
                    rank=index,
                    name=restaurant.name,
                    cuisine=restaurant.cuisine,
                    rating=restaurant.rating,
                    estimated_cost=restaurant.estimated_cost,
                    explanation=explanation,
                    restaurant_id=restaurant.id,
                )
            )
            used_ids.add(restaurant.id)
            if len(recommendations) >= top_k:
                break

        if len(recommendations) < top_k:
            recommendations = self._backfill(recommendations, candidates, top_k, used_ids)

        return recommendations

    def _backfill(
        self,
        current: list[Recommendation],
        candidates: list[Restaurant],
        top_k: int,
        used_ids: set[str],
    ) -> list[Recommendation]:
        result = list(current)
        next_rank = len(result) + 1

        for restaurant in candidates:
            if restaurant.id in used_ids:
                continue
            result.append(
                Recommendation(
                    rank=next_rank,
                    name=restaurant.name,
                    cuisine=restaurant.cuisine,
                    rating=restaurant.rating,
                    estimated_cost=restaurant.estimated_cost,
                    explanation=(
                        f"Highly rated option ({restaurant.rating}) matching your search criteria."
                    ),
                    restaurant_id=restaurant.id,
                )
            )
            used_ids.add(restaurant.id)
            next_rank += 1
            if len(result) >= top_k:
                break

        return result


def build_filter_fallback(
    candidates: list[Restaurant],
    preferences: UserPreferences,
    *,
    total_candidates: int,
    filters_applied: dict[str, object],
    filters_relaxed: list[str] | None = None,
) -> RecommendationResponse:
    """Return filter-ranked recommendations when the LLM is unavailable."""
    top_k = min(preferences.top_k, len(candidates))
    explanation = _FALLBACK_EXPLANATION.format(
        location=preferences.location,
        budget=preferences.budget,
        min_rating=preferences.min_rating,
    )

    recommendations = [
        Recommendation(
            rank=index,
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            rating=restaurant.rating,
            estimated_cost=restaurant.estimated_cost,
            explanation=explanation,
            restaurant_id=restaurant.id,
        )
        for index, restaurant in enumerate(candidates[:top_k], start=1)
    ]

    return RecommendationResponse(
        summary=None,
        recommendations=recommendations,
        metadata=RecommendationMetadata(
            total_candidates=total_candidates,
            filters_applied=filters_applied,
            llm_used=False,
            filters_relaxed=list(filters_relaxed or []),
        ),
    )


def build_llm_response(
    parsed: dict[str, Any],
    candidates: list[Restaurant],
    preferences: UserPreferences,
    *,
    total_candidates: int,
    filters_applied: dict[str, object],
    filters_relaxed: list[str] | None = None,
    llm_latency_ms: float | None = None,
    token_usage: dict[str, int] | None = None,
) -> RecommendationResponse:
    """Validate, merge, and package a successful LLM parse into a response."""
    validator = RecommendationValidator()
    merger = RecommendationMerger()

    validated = validator.validate(parsed, candidates)
    recommendations = merger.merge(validated, candidates, top_k=preferences.top_k)

    summary = validated.get("summary")
    if isinstance(summary, str):
        summary = summary.strip() or None
    else:
        summary = None

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        metadata=RecommendationMetadata(
            total_candidates=total_candidates,
            filters_applied=filters_applied,
            llm_used=True,
            filters_relaxed=list(filters_relaxed or []),
            llm_latency_ms=llm_latency_ms,
            token_usage=token_usage,
        ),
    )
