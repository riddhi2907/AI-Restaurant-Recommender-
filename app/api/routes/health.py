"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.schemas import HealthResponse, ReadyResponse
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request) -> ReadyResponse:
    store = getattr(request.app.state, "store", None)
    warnings: list[str] = []

    if getattr(request.app.state, "dataset_loading", False):
        return ReadyResponse(
            status="loading",
            dataset_loaded=False,
            restaurant_count=0,
            groq_configured=settings.groq_configured,
            warnings=["Restaurant dataset is still loading."],
        )

    if store is None:
        error = getattr(request.app.state, "dataset_load_error", None)
        return ReadyResponse(
            status="not_ready",
            dataset_loaded=False,
            restaurant_count=0,
            groq_configured=settings.groq_configured,
            warnings=[
                error or "Restaurant dataset failed to load during startup.",
            ],
        )

    if not settings.groq_configured:
        warnings.append("GROQ_API_KEY is not configured. Recommendations will use filter-only fallback.")

    return ReadyResponse(
        status="ready",
        dataset_loaded=True,
        restaurant_count=store.count,
        groq_configured=settings.groq_configured,
        warnings=warnings,
    )
