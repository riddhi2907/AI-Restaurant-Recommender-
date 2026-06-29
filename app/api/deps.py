"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.data.store import RestaurantStore
from app.services.recommendation import RecommendationService


def get_store(request: Request) -> RestaurantStore:
    store = getattr(request.app.state, "store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail="Restaurant dataset is not available. Try again later.",
        )
    return store


def get_recommendation_service(request: Request) -> RecommendationService:
    store = get_store(request)
    return RecommendationService(store)
