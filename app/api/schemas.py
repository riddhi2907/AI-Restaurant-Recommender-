"""Pydantic schemas for the REST API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.recommendation import (
    Recommendation,
    RecommendationMetadata,
    RecommendationResponse,
)


class UserPreferencesRequest(BaseModel):
    location: str = Field(..., min_length=1, description="City or locality from the dataset")
    budget: Literal["low", "medium", "high"]
    cuisine: str | None = None
    min_rating: float = Field(0.0, ge=0.0, le=5.0)
    additional: list[str] = Field(default_factory=list)
    top_k: int = Field(5, ge=1)


class RecommendationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
    restaurant_id: str | None = None


class RecommendationMetadataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_candidates: int
    filters_applied: dict[str, object]
    llm_used: bool
    filters_relaxed: list[str] = Field(default_factory=list)
    llm_latency_ms: float | None = None
    token_usage: dict[str, int] | None = None


class RecommendationResponseSchema(BaseModel):
    summary: str | None
    recommendations: list[RecommendationSchema]
    metadata: RecommendationMetadataSchema


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    dataset_loaded: bool
    restaurant_count: int
    groq_configured: bool
    warnings: list[str] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    detail: str
    suggestions: list[str] = Field(default_factory=list)


def recommendation_to_schema(rec: Recommendation) -> RecommendationSchema:
    return RecommendationSchema(
        rank=rec.rank,
        name=rec.name,
        cuisine=rec.cuisine,
        rating=rec.rating,
        estimated_cost=rec.estimated_cost,
        explanation=rec.explanation,
        restaurant_id=rec.restaurant_id,
    )


def metadata_to_schema(meta: RecommendationMetadata) -> RecommendationMetadataSchema:
    return RecommendationMetadataSchema(
        total_candidates=meta.total_candidates,
        filters_applied=meta.filters_applied,
        llm_used=meta.llm_used,
        filters_relaxed=list(meta.filters_relaxed),
        llm_latency_ms=meta.llm_latency_ms,
        token_usage=meta.token_usage,
    )


def response_to_schema(response: RecommendationResponse) -> RecommendationResponseSchema:
    return RecommendationResponseSchema(
        summary=response.summary,
        recommendations=[recommendation_to_schema(rec) for rec in response.recommendations],
        metadata=metadata_to_schema(response.metadata),
    )
