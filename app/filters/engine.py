"""Deterministic restaurant filter pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.config import Settings, settings as default_settings
from app.data.preprocessor import is_city_name
from app.models.preferences import UserPreferences
from app.models.restaurant import Restaurant

if TYPE_CHECKING:
    pass

RELAXATION_ORDER = ("cuisine", "budget", "min_rating")


@dataclass(frozen=True)
class ActiveFilters:
    location: str
    location_match: str
    budget: str
    cuisine: str | None
    min_rating: float

    def as_dict(self) -> dict[str, object]:
        return {
            "location": self.location,
            "location_match": self.location_match,
            "budget": self.budget,
            "cuisine": self.cuisine,
            "min_rating": self.min_rating,
        }


@dataclass
class FilterResult:
    candidates: list[Restaurant]
    total_matched: int
    filters_applied: dict[str, object]
    filters_relaxed: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.candidates) == 0


def matches_location(restaurant: Restaurant, preferences: UserPreferences) -> bool:
    target = preferences.location.lower()
    if preferences.location_match == "city":
        return restaurant.city.lower() == target
    return restaurant.location.lower() == target


def matches_rating(restaurant: Restaurant, min_rating: float) -> bool:
    return restaurant.rating >= min_rating


def matches_cuisine(restaurant: Restaurant, cuisine: str | None) -> bool:
    if not cuisine:
        return True
    return cuisine.lower() in restaurant.cuisine.lower()


def matches_budget(restaurant: Restaurant, budget: str) -> bool:
    if restaurant.budget_tier is None:
        return True
    return restaurant.budget_tier == budget


def apply_filters(
    restaurants: list[Restaurant],
    preferences: UserPreferences,
    *,
    apply_cuisine: bool = True,
    apply_budget: bool = True,
    apply_min_rating: bool = True,
) -> list[Restaurant]:
    results = restaurants

    results = [r for r in results if matches_location(r, preferences)]

    if apply_min_rating:
        results = [r for r in results if matches_rating(r, preferences.min_rating)]

    if apply_cuisine and preferences.cuisine:
        results = [r for r in results if matches_cuisine(r, preferences.cuisine)]

    if apply_budget:
        results = [r for r in results if matches_budget(r, preferences.budget)]

    return results


def sort_candidates(restaurants: list[Restaurant]) -> list[Restaurant]:
    return sorted(restaurants, key=lambda r: (-r.rating, r.name.lower(), r.id))


def cap_candidates(restaurants: list[Restaurant], max_candidates: int) -> list[Restaurant]:
    return restaurants[:max_candidates]


class FilterEngine:
    """Filter restaurants by user preferences with progressive relaxation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings

    def apply(self, preferences: UserPreferences, restaurants: list[Restaurant]) -> FilterResult:
        active = ActiveFilters(
            location=preferences.location,
            location_match=preferences.location_match,
            budget=preferences.budget,
            cuisine=preferences.cuisine,
            min_rating=preferences.min_rating,
        )
        relaxed: list[str] = []

        matched = apply_filters(restaurants, preferences)
        if not matched:
            matched, relaxed = self._relax_filters(restaurants, preferences)

        sorted_matches = sort_candidates(matched)
        total_matched = len(sorted_matches)
        candidates = cap_candidates(sorted_matches, self.settings.max_candidates_for_llm)

        suggestions: list[str] = []
        if not candidates:
            suggestions = self._build_suggestions(preferences, restaurants)

        return FilterResult(
            candidates=candidates,
            total_matched=total_matched,
            filters_applied=active.as_dict(),
            filters_relaxed=relaxed,
            suggestions=suggestions,
        )

    def _relax_filters(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> tuple[list[Restaurant], list[str]]:
        flags = {
            "cuisine": True,
            "budget": True,
            "min_rating": True,
        }
        relaxed: list[str] = []

        for filter_name in RELAXATION_ORDER:
            if filter_name == "cuisine" and not preferences.cuisine:
                continue
            if filter_name == "min_rating" and preferences.min_rating <= 0.0:
                continue

            flags[filter_name] = False
            relaxed.append(filter_name)

            matched = apply_filters(
                restaurants,
                preferences,
                apply_cuisine=flags["cuisine"],
                apply_budget=flags["budget"],
                apply_min_rating=flags["min_rating"],
            )
            if matched:
                return matched, relaxed

        return [], relaxed

    def _build_suggestions(
        self,
        preferences: UserPreferences,
        restaurants: list[Restaurant],
    ) -> list[str]:
        location_matches = [r for r in restaurants if matches_location(r, preferences)]
        if not location_matches:
            cities = sorted({r.city for r in restaurants if r.city})
            localities = sorted(
                {
                    r.location
                    for r in restaurants
                    if r.location and not is_city_name(r.location)
                }
            )
            return (cities[:5] + localities[:5])[:8]

        cuisines = sorted(
            {
                token
                for r in location_matches
                for token in (part.strip() for part in r.cuisine.split(","))
                if token and token.lower() != "unknown"
            }
        )
        return cuisines[:8]
