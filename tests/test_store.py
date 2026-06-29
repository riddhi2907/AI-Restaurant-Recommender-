"""Tests for restaurant store and cache."""

from pathlib import Path

import pytest

from app.config import Settings
from app.data.store import RestaurantStore, _load_from_cache, _save_to_cache
from app.models.restaurant import Restaurant


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="abc123",
            name="Spice Elephant",
            location="Banashankari",
            city="Bangalore",
            cuisine="Chinese, North Indian",
            cost=800.0,
            rating=4.1,
            budget_tier="medium",
            rest_type="Casual Dining",
            address="Banashankari, Bangalore",
            votes=787,
        ),
        Restaurant(
            id="def456",
            name="Budget Bites",
            location="Koramangala",
            city="Bangalore",
            cuisine="Fast Food",
            cost=300.0,
            rating=3.8,
            budget_tier="low",
        ),
        Restaurant(
            id="ghi789",
            name="Fine Dine",
            location="Banashankari",
            city="Bangalore",
            cuisine="Italian",
            cost=2500.0,
            rating=4.5,
            budget_tier="high",
        ),
    ]


class TestRestaurantStore:
    def test_get_all(self, sample_restaurants):
        store = RestaurantStore(sample_restaurants)
        assert len(store.get_all()) == 3

    def test_get_locations(self, sample_restaurants):
        store = RestaurantStore(sample_restaurants)
        assert store.get_locations() == ["Banashankari", "Koramangala"]

    def test_get_cities(self, sample_restaurants):
        store = RestaurantStore(sample_restaurants)
        assert store.get_cities() == ["Bangalore"]

    def test_get_cuisines(self, sample_restaurants):
        store = RestaurantStore(sample_restaurants)
        cuisines = store.get_cuisines()
        assert "Chinese" in cuisines
        assert "North Indian" in cuisines
        assert "Fast Food" in cuisines
        assert "Italian" in cuisines


class TestCacheRoundtrip:
    def test_save_and_load_cache(self, sample_restaurants, tmp_path: Path):
        cache_path = tmp_path / "restaurants.parquet"
        _save_to_cache(sample_restaurants, cache_path)
        assert cache_path.exists()

        loaded = _load_from_cache(cache_path)
        assert len(loaded) == 3
        assert loaded[0].name == "Spice Elephant"
        assert loaded[0].cost == 800.0
        assert loaded[1].budget_tier == "low"

    def test_load_from_cache_via_store(self, sample_restaurants, tmp_path: Path, monkeypatch):
        cache_path = tmp_path / "restaurants.parquet"
        _save_to_cache(sample_restaurants, cache_path)

        test_settings = Settings(
            groq_api_key=None,
            llm_model="llama-3.3-70b-versatile",
            llm_temperature=0.3,
            max_candidates_for_llm=20,
            default_top_k=5,
            dataset_cache_path=cache_path,
            budget_low_max=500,
            budget_medium_max=1500,
        )

        store = RestaurantStore.load(settings=test_settings, use_cache=True)
        assert store.count == 3
        assert store.get_locations() == ["Banashankari", "Koramangala"]
