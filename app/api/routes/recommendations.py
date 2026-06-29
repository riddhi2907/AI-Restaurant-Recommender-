"""Recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_recommendation_service
from app.api.schemas import RecommendationResponseSchema, UserPreferencesRequest, response_to_schema
from app.filters.parser import PreferenceValidationError
from app.services.recommendation import RecommendationService

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponseSchema)
def create_recommendations(
    body: UserPreferencesRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponseSchema:
    try:
        response = service.get_recommendations(
            location=body.location,
            budget=body.budget,
            cuisine=body.cuisine,
            min_rating=body.min_rating,
            additional=body.additional,
            top_k=body.top_k,
        )
    except PreferenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(exc),
                "suggestions": exc.suggestions,
            },
        ) from exc

    return response_to_schema(response)
