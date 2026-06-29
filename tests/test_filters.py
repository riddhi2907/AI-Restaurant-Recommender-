"""Tests for preference parser and filter engine."""

import pytest

from app.config import Settings
from app.data.store import RestaurantStore
from app.filters.engine import FilterEngine, apply_filters, matches_cuisine, sort_candidates
from app.filters.parser import PreferenceValidationError, parse_preferences, resolve_location
from app.models.preferences import UserPreferences
from app.models.restaurant import Restaurant


@pytest.fixture
def settings() -> Settings:
    return Settings(
        groq_api_key=None,
        llm_model="llama-3.3-70b-versatile",
        llm_temperature=0.3,
        max_candidates_for_llm=20,
        default_top_k=5,
        dataset_cache_path=Settings.from_env().dataset_cache_path,
        budget_low_max=500,
        budget_medium_max=1500,
    )


@pytest.fixture
def restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="r1",
            name="Alpha Diner",
            location="Banashankari",
            city="Bangalore",
            cuisine="North Indian, Chinese",
            cost=800.0,
            rating=4.5,
            budget_tier="medium",
        ),
        Restaurant(
            id="r2",
            name="Beta Cafe",
            location="Banashankari",
            city="Bangalore",
            cuisine="Italian",
            cost=400.0,
            rating=4.2,
            budget_tier="low",
        ),
        Restaurant(
            id="r3",
            name="Gamma Grill",
            location="Banashankari",
            city="Bangalore",
            cuisine="Chinese",
            cost=2000.0,
            rating=4.8,
            budget_tier="high",
        ),
        Restaurant(
            id="r4",
            name="Delta Dine",
            location="Koramangala",
            city="Bangalore",
            cuisine="Italian",
            cost=900.0,
            rating=3.5,
            budget_tier="medium",
        ),
        Restaurant(
            id="r5",
            name="Epsilon Eats",
            location="Banashankari",
            city="Bangalore",
            cuisine="Mexican",
            cost=600.0,
            rating=3.0,
            budget_tier="medium",
        ),
        Restaurant(
            id="r6",
            name="Zeta Place",
            location="Banashankari",
            city="Bangalore",
            cuisine="Cafe",
            cost=None,
            rating=4.0,
            budget_tier=None,
        ),
    ]


@pytest.fixture
def store(restaurants: list[Restaurant]) -> RestaurantStore:
    return RestaurantStore(restaurants)


class TestPreferenceParser:
    def test_parse_valid_locality(self, store, settings):
        prefs = parse_preferences(
            location="Banashankari",
            budget="medium",
            min_rating=4.0,
            store=store,
            settings=settings,
        )
        assert prefs.location == "Banashankari"
        assert prefs.location_match == "locality"
        assert prefs.budget == "medium"
        assert prefs.min_rating == 4.0

    def test_parse_city_bangalore(self, store, settings):
        prefs = parse_preferences(
            location="Bangalore",
            budget="medium",
            store=store,
            settings=settings,
        )
        assert prefs.location == "Bangalore"
        assert prefs.location_match == "city"

    def test_bengaluru_alias(self, store, settings):
        prefs = parse_preferences(
            location="Bengaluru",
            budget="low",
            store=store,
            settings=settings,
        )
        assert prefs.location == "Bangalore"
        assert prefs.location_match == "city"

    def test_invalid_budget(self, store):
        with pytest.raises(PreferenceValidationError, match="Invalid budget"):
            parse_preferences(location="Banashankari", budget="premium", store=store)

    def test_unknown_location_with_suggestions(self, store):
        with pytest.raises(PreferenceValidationError) as exc_info:
            parse_preferences(location="Mumbai", budget="low", store=store)
        assert exc_info.value.suggestions

    def test_clamps_min_rating(self, store, settings):
        prefs = parse_preferences(
            location="Banashankari",
            budget="low",
            min_rating=10.0,
            store=store,
            settings=settings,
        )
        assert prefs.min_rating == 5.0

    def test_parse_additional_tags(self, store, settings):
        prefs = parse_preferences(
            location="Banashankari",
            budget="low",
            additional="family-friendly, quick service",
            store=store,
            settings=settings,
        )
        assert prefs.additional == ["family-friendly", "quick service"]


class TestFilterEngine:
    def test_location_and_rating_filter(self, store, settings, restaurants):
        prefs = UserPreferences(
            location="Banashankari",
            budget="medium",
            min_rating=4.0,
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)

        ids = {r.id for r in result.candidates}
        assert ids == {"r1", "r6"}
        assert all(r.rating >= 4.0 for r in result.candidates)
        assert all(r.budget_tier in ("medium", None) for r in result.candidates)

    def test_city_level_bangalore_medium_rating(self, store, settings, restaurants):
        prefs = parse_preferences(
            location="Bangalore",
            budget="medium",
            min_rating=4.0,
            store=store,
            settings=settings,
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)

        assert len(result.candidates) <= 20
        assert all(r.city == "Bangalore" for r in result.candidates)
        assert all(r.rating >= 4.0 for r in result.candidates)
        assert all(r.budget_tier in ("medium", None) for r in result.candidates)
        assert result.candidates == sort_candidates(result.candidates)

    def test_cuisine_filter(self, restaurants):
        prefs = UserPreferences(
            location="Banashankari",
            budget="high",
            cuisine="Italian",
            location_match="locality",
        )
        matched = apply_filters(restaurants, prefs)
        assert matched == []

    def test_budget_tier_mapping(self, restaurants, settings):
        prefs = UserPreferences(
            location="Banashankari",
            budget="low",
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)
        assert {r.id for r in result.candidates} == {"r2"}

    def test_restaurant_without_budget_tier_passes_budget_filter(self, restaurants, settings):
        prefs = UserPreferences(
            location="Banashankari",
            budget="high",
            min_rating=4.0,
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)
        assert any(r.id == "r6" for r in result.candidates)

    def test_candidate_cap(self, settings):
        many = [
            Restaurant(
                id=f"r{i}",
                name=f"Restaurant {i:03d}",
                location="Banashankari",
                city="Bangalore",
                cuisine="Indian",
                cost=800.0,
                rating=4.0 + (i % 10) * 0.01,
                budget_tier="medium",
            )
            for i in range(50)
        ]
        prefs = UserPreferences(
            location="Banashankari",
            budget="medium",
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, many)

        assert len(result.candidates) == 20
        assert result.total_matched == 50
        ratings = [r.rating for r in result.candidates]
        assert ratings == sorted(ratings, reverse=True)

    def test_zero_match_relaxes_cuisine(self, store, settings, restaurants):
        prefs = UserPreferences(
            location="Banashankari",
            budget="medium",
            cuisine="Mexican",
            min_rating=4.5,
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)

        assert result.candidates
        assert "cuisine" in result.filters_relaxed

    def test_zero_match_relaxes_budget(self, restaurants, settings):
        prefs = UserPreferences(
            location="Banashankari",
            budget="low",
            cuisine="Chinese",
            min_rating=4.7,
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)

        assert result.candidates
        assert "budget" in result.filters_relaxed or "cuisine" in result.filters_relaxed

    def test_all_relaxed_still_empty_returns_suggestions(self, restaurants, settings):
        prefs = UserPreferences(
            location="Banashankari",
            budget="low",
            cuisine="Japanese",
            min_rating=4.9,
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)

        assert result.is_empty
        assert result.suggestions

    def test_grounded_candidates_only(self, store, settings, restaurants):
        prefs = parse_preferences(
            location="Bangalore",
            budget="medium",
            min_rating=3.0,
            store=store,
            settings=settings,
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, restaurants)
        restaurant_ids = {r.id for r in restaurants}
        assert all(r.id in restaurant_ids for r in result.candidates)

    def test_stable_sort_on_tied_ratings(self, settings):
        tied = [
            Restaurant(
                id="b",
                name="Bravo",
                location="Banashankari",
                city="Bangalore",
                cuisine="Indian",
                cost=800.0,
                rating=4.0,
                budget_tier="medium",
            ),
            Restaurant(
                id="a",
                name="Alpha",
                location="Banashankari",
                city="Bangalore",
                cuisine="Indian",
                cost=800.0,
                rating=4.0,
                budget_tier="medium",
            ),
        ]
        prefs = UserPreferences(
            location="Banashankari",
            budget="medium",
            location_match="locality",
        )
        engine = FilterEngine(settings)
        result = engine.apply(prefs, tied)
        assert [r.name for r in result.candidates] == ["Alpha", "Bravo"]


class TestFilterHelpers:
    def test_cuisine_case_insensitive(self):
        restaurant = Restaurant(
            id="x",
            name="Test",
            location="Banashankari",
            city="Bangalore",
            cuisine="North Indian, Chinese",
            cost=500.0,
            rating=4.0,
            budget_tier="low",
        )
        assert matches_cuisine(restaurant, "chinese")
        assert matches_cuisine(restaurant, "CHINESE")

    def test_resolve_location_locality(self, store):
        location, match_type = resolve_location("banashankari", store)
        assert location == "Banashankari"
        assert match_type == "locality"
