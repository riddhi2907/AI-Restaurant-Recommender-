"""Orchestrates parse → filter → LLM for recommendation requests."""

from __future__ import annotations

import logging

from app.config import Settings, settings as default_settings
from app.data.store import RestaurantStore
from app.filters.engine import FilterEngine
from app.filters.parser import parse_preferences
from app.llm.engine import RecommendationEngine
from app.models.recommendation import RecommendationResponse

logger = logging.getLogger(__name__)


class RecommendationService:
    """End-to-end recommendation pipeline."""

    def __init__(
        self,
        store: RestaurantStore,
        *,
        settings: Settings | None = None,
        filter_engine: FilterEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
    ) -> None:
        self.store = store
        self.settings = settings or default_settings
        self.filter_engine = filter_engine or FilterEngine(self.settings)
        self.recommendation_engine = recommendation_engine or RecommendationEngine()

    def get_recommendations(
        self,
        *,
        location: str,
        budget: str,
        cuisine: str | None = None,
        min_rating: float = 0.0,
        additional: list[str] | None = None,
        top_k: int | None = None,
    ) -> RecommendationResponse:
        preferences = parse_preferences(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            additional=additional,
            top_k=top_k,
            store=self.store,
            settings=self.settings,
        )

        filter_result = self.filter_engine.apply(preferences, self.store.get_all())
        logger.info(
            "Filter produced %d candidates (total matched: %d)",
            len(filter_result.candidates),
            filter_result.total_matched,
        )

        return self.recommendation_engine.generate(
            preferences,
            filter_result.candidates,
            total_candidates=filter_result.total_matched,
            filters_applied=filter_result.filters_applied,
            filters_relaxed=filter_result.filters_relaxed,
        )
