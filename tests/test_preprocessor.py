"""Tests for dataset preprocessing."""

import pandas as pd
import pytest

from app.config import Settings
from app.data.preprocessor import (
    compute_budget_tier,
    extract_city,
    extract_locality,
    make_restaurant_id,
    normalize_cuisine,
    parse_cost,
    parse_locality_from_address,
    parse_rating,
    preprocess_dataframe,
    preprocess_row,
)


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


class TestParseRating:
    def test_standard_format(self):
        assert parse_rating("4.1/5") == 4.1

    def test_plain_number(self):
        assert parse_rating("4.5") == 4.5

    def test_new_rating(self):
        assert parse_rating("NEW") == 0.0

    def test_dash_rating(self):
        assert parse_rating("-") == 0.0

    def test_none_rating(self):
        assert parse_rating(None) == 0.0

    def test_clamps_above_five(self):
        assert parse_rating("6.0") == 0.0

    def test_clamps_to_range(self):
        assert parse_rating("5.5/5") == 5.0


class TestParseCost:
    def test_integer_string(self):
        assert parse_cost("800") == 800.0

    def test_comma_separated(self):
        assert parse_cost("1,200") == 1200.0

    def test_rupee_symbol(self):
        assert parse_cost("₹500") == 500.0

    def test_missing_cost(self):
        assert parse_cost(None) is None
        assert parse_cost("-") is None

    def test_zero_cost(self):
        assert parse_cost("0") is None


class TestNormalizeCuisine:
    def test_comma_separated(self):
        assert normalize_cuisine("North Indian, Chinese") == "North Indian, Chinese"

    def test_empty_cuisine(self):
        assert normalize_cuisine(None) == "Unknown"
        assert normalize_cuisine("") == "Unknown"

    def test_extra_whitespace(self):
        assert normalize_cuisine("  Italian ,  Mexican  ") == "Italian, Mexican"


class TestExtractCity:
    def test_from_address_bangalore(self):
        assert extract_city("942, Banashankari, Bangalore", "Banashankari", "Banashankari") == "Bangalore"

    def test_from_address_bengaluru(self):
        assert extract_city("Some street, Bengaluru", None, None) == "Bangalore"

    def test_listed_in_city_is_locality_not_city(self):
        assert extract_city(None, "Koramangala", "Koramangala") == "Bangalore"

    def test_city_from_location_column(self):
        assert extract_city(None, "Bangalore", None) == "Bangalore"
        assert extract_city(None, "Bengaluru", None) == "Bangalore"


class TestExtractLocality:
    def test_from_location_column(self):
        assert extract_locality("Indiranagar", None, None) == "Indiranagar"

    def test_rejects_city_name_in_location_column(self):
        assert extract_locality("Bangalore", "Bellandur", None) == "Bellandur"

    def test_from_address_when_location_is_city(self):
        address = "12th Main, Indiranagar, Bangalore"
        assert extract_locality("Bangalore", None, address) == "Indiranagar"

    def test_from_listed_in_city_fallback(self):
        assert extract_locality(None, "Koramangala", None) == "Koramangala"

    def test_returns_none_when_only_city_known(self):
        assert extract_locality("Bangalore", "Bangalore", "Some street, Bangalore") is None


class TestParseLocalityFromAddress:
    def test_parses_locality_before_city(self):
        assert parse_locality_from_address("80 Feet Road, Banashankari, Bangalore") == "Banashankari"

    def test_parses_indiranagar(self):
        assert parse_locality_from_address("100 Feet Road, Indiranagar, Bengaluru") == "Indiranagar"


class TestBudgetTier:
    def test_low_tier(self, settings):
        assert compute_budget_tier(400, settings) == "low"

    def test_medium_tier(self, settings):
        assert compute_budget_tier(800, settings) == "medium"

    def test_high_tier(self, settings):
        assert compute_budget_tier(2000, settings) == "high"

    def test_none_cost(self, settings):
        assert compute_budget_tier(None, settings) is None


class TestMakeRestaurantId:
    def test_stable_id(self):
        id_a = make_restaurant_id("Jalsa", "Banashankari", "942, Bangalore")
        id_b = make_restaurant_id("Jalsa", "Banashankari", "942, Bangalore")
        id_c = make_restaurant_id("Jalsa", "Banashankari", "Different address")

        assert id_a == id_b
        assert id_a != id_c
        assert len(id_a) == 12


class TestPreprocessRow:
    def test_valid_row(self, settings):
        row = pd.Series(
            {
                "name": "Spice Elephant",
                "location": "Banashankari",
                "cuisines": "Chinese, North Indian",
                "rate": "4.1/5",
                "approx_cost(for two people)": "800",
                "address": "80 Feet Road, Banashankari, Bangalore",
                "listed_in(city)": "Banashankari",
                "rest_type": "Casual Dining",
                "votes": 787,
            }
        )
        restaurant = preprocess_row(row, settings)

        assert restaurant is not None
        assert restaurant.name == "Spice Elephant"
        assert restaurant.location == "Banashankari"
        assert restaurant.city == "Bangalore"
        assert restaurant.cuisine == "Chinese, North Indian"
        assert restaurant.cost == 800.0
        assert restaurant.rating == 4.1
        assert restaurant.budget_tier == "medium"
        assert restaurant.votes == 787

    def test_drops_row_without_name(self, settings):
        row = pd.Series({"name": None, "location": "Banashankari"})
        assert preprocess_row(row, settings) is None

    def test_drops_row_without_location(self, settings):
        row = pd.Series({"name": "Test Cafe", "location": None, "listed_in(city)": None})
        assert preprocess_row(row, settings) is None

    def test_location_fallback_to_listed_in_city(self, settings):
        row = pd.Series(
            {
                "name": "Test Cafe",
                "location": None,
                "listed_in(city)": "Koramangala",
                "cuisines": "Cafe",
                "rate": "3.5/5",
                "approx_cost(for two people)": "300",
            }
        )
        restaurant = preprocess_row(row, settings)
        assert restaurant is not None
        assert restaurant.location == "Koramangala"
        assert restaurant.city == "Bangalore"

    def test_location_city_name_resolved_from_address(self, settings):
        row = pd.Series(
            {
                "name": "Bellandur Bistro",
                "location": "Bangalore",
                "listed_in(city)": "Bellandur",
                "cuisines": "Cafe",
                "rate": "4.0/5",
                "approx_cost(for two people)": "600",
                "address": "Outer Ring Road, Bellandur, Bangalore",
            }
        )
        restaurant = preprocess_row(row, settings)
        assert restaurant is not None
        assert restaurant.location == "Bellandur"
        assert restaurant.city == "Bangalore"

    def test_drops_row_when_only_city_available(self, settings):
        row = pd.Series(
            {
                "name": "City Only Cafe",
                "location": "Bangalore",
                "listed_in(city)": "Bangalore",
                "cuisines": "Cafe",
                "rate": "3.5/5",
                "approx_cost(for two people)": "300",
                "address": "Bangalore",
            }
        )
        assert preprocess_row(row, settings) is None


class TestPreprocessDataframe:
    def test_preprocesses_multiple_rows(self, settings):
        df = pd.DataFrame(
            [
                {
                    "name": "A",
                    "location": "Banashankari",
                    "cuisines": "Indian",
                    "rate": "4.0/5",
                    "approx_cost(for two people)": "400",
                },
                {
                    "name": None,
                    "location": "Banashankari",
                    "cuisines": "Indian",
                    "rate": "4.0/5",
                    "approx_cost(for two people)": "400",
                },
                {
                    "name": "B",
                    "location": "Koramangala",
                    "cuisines": "Chinese",
                    "rate": "NEW",
                    "approx_cost(for two people)": "1,500",
                },
            ]
        )

        restaurants = preprocess_dataframe(df, settings)
        assert len(restaurants) == 2
        assert restaurants[0].name == "A"
        assert restaurants[1].rating == 0.0
        assert restaurants[1].cost == 1500.0
        assert restaurants[1].budget_tier == "medium"
