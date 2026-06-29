"""Validate and normalize user preference input."""

from __future__ import annotations

import difflib
import re
from typing import TYPE_CHECKING

from app.config import Settings, settings as default_settings
from app.models.preferences import LocationMatchType, UserPreferences
from app.models.restaurant import BudgetTier
from app.data.preprocessor import is_city_name

if TYPE_CHECKING:
    from app.data.store import RestaurantStore

LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "blr": "bangalore",
    "bangalore": "bangalore",
    "new delhi": "delhi",
    "ncr": "delhi",
}

VALID_BUDGETS: frozenset[BudgetTier] = frozenset({"low", "medium", "high"})


class PreferenceValidationError(ValueError):
    """Raised when user preferences fail validation."""

    def __init__(self, message: str, *, suggestions: list[str] | None = None) -> None:
        super().__init__(message)
        self.suggestions = suggestions or []


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_budget(value: str) -> BudgetTier:
    budget = normalize_whitespace(value).lower()
    if budget not in VALID_BUDGETS:
        raise PreferenceValidationError(
            f"Invalid budget '{value}'. Choose one of: low, medium, high."
        )
    return budget  # type: ignore[return-value]


def clamp_min_rating(value: float) -> float:
    return max(0.0, min(5.0, float(value)))


def _canonical_location(value: str) -> str:
    lowered = normalize_whitespace(value).lower()
    return LOCATION_ALIASES.get(lowered, lowered)


def _build_location_index(store: RestaurantStore) -> tuple[dict[str, str], dict[str, str]]:
    """Map lowercase locality/city names to canonical display values."""
    localities: dict[str, str] = {}
    cities: dict[str, str] = {}

    for restaurant in store.get_all():
        if restaurant.location and not is_city_name(restaurant.location):
            key = restaurant.location.lower()
            localities.setdefault(key, restaurant.location)
        if restaurant.city:
            key = restaurant.city.lower()
            cities.setdefault(key, restaurant.city)

    return localities, cities


def resolve_location(raw_location: str, store: RestaurantStore) -> tuple[str, LocationMatchType]:
    """Resolve user location to a known city or locality from the dataset."""
    if not raw_location or not raw_location.strip():
        raise PreferenceValidationError("Location is required.")

    canonical = _canonical_location(raw_location)
    localities, cities = _build_location_index(store)

    if canonical in localities:
        return localities[canonical], "locality"

    if canonical in cities:
        return cities[canonical], "city"

    # Try matching original input before alias normalization for locality names
    original = normalize_whitespace(raw_location).lower()
    if original in localities:
        return localities[original], "locality"
    if original in cities:
        return cities[original], "city"

    suggestions = suggest_locations(raw_location, store)
    message = f"Unknown location '{raw_location}'."
    if suggestions:
        message += f" Did you mean: {', '.join(suggestions[:3])}?"
    raise PreferenceValidationError(message, suggestions=suggestions)


def suggest_locations(raw_location: str, store: RestaurantStore, *, limit: int = 5) -> list[str]:
    """Return closest known locations/cities for an unknown input."""
    localities, cities = _build_location_index(store)
    choices = sorted(set(localities.values()) | set(cities.values()))
    if not choices:
        return []

    query = _canonical_location(raw_location)
    matches = difflib.get_close_matches(query, [c.lower() for c in choices], n=limit, cutoff=0.5)
    lookup = {choice.lower(): choice for choice in choices}
    return [lookup[match] for match in matches]


def parse_additional(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_whitespace(item) for item in value if item and str(item).strip()]
    text = normalize_whitespace(str(value))
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]


def parse_preferences(
    *,
    location: str,
    budget: str,
    cuisine: str | None = None,
    min_rating: float = 0.0,
    additional: str | list[str] | None = None,
    top_k: int | None = None,
    store: RestaurantStore,
    settings: Settings | None = None,
) -> UserPreferences:
    """Validate raw inputs and return a normalized UserPreferences object."""
    settings = settings or default_settings

    resolved_location, match_type = resolve_location(location, store)
    normalized_budget = normalize_budget(budget)
    normalized_cuisine = normalize_whitespace(cuisine) if cuisine and cuisine.strip() else None
    normalized_rating = clamp_min_rating(min_rating)
    normalized_additional = parse_additional(additional)
    normalized_top_k = top_k if top_k is not None else settings.default_top_k
    if normalized_top_k < 1:
        normalized_top_k = settings.default_top_k

    return UserPreferences(
        location=resolved_location,
        budget=normalized_budget,
        cuisine=normalized_cuisine,
        min_rating=normalized_rating,
        additional=normalized_additional,
        top_k=normalized_top_k,
        location_match=match_type,
    )
