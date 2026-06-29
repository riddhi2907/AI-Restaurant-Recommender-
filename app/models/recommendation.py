"""Recommendation response models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recommendation:
    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
    restaurant_id: str | None = None


@dataclass(frozen=True)
class RecommendationMetadata:
    total_candidates: int
    filters_applied: dict[str, object]
    llm_used: bool
    filters_relaxed: list[str] = field(default_factory=list)
    llm_latency_ms: float | None = None
    token_usage: dict[str, int] | None = None


@dataclass(frozen=True)
class RecommendationResponse:
    summary: str | None
    recommendations: list[Recommendation]
    metadata: RecommendationMetadata
