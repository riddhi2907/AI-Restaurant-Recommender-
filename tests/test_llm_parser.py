"""Tests for LLM response parsing, validation, merging, and engine fallback."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from app.llm.client import LLMClientError, LLMCompletionResult
from app.llm.engine import RecommendationEngine
from app.llm.parser import (
    RecommendationMerger,
    RecommendationValidator,
    ResponseParser,
    build_filter_fallback,
    build_llm_response,
)
from app.llm.prompts import PromptBuilder
from app.models.preferences import UserPreferences
from app.models.restaurant import Restaurant


@pytest.fixture
def candidates() -> list[Restaurant]:
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
    ]


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="Banashankari",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional=["family-friendly"],
        top_k=2,
    )


@pytest.fixture
def filters_applied() -> dict[str, object]:
    return {
        "location": "Banashankari",
        "location_match": "locality",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
    }


def _llm_payload(recommendations: list[dict]) -> str:
    return json.dumps(
        {
            "summary": "Great Italian and Chinese options in Banashankari for your medium budget.",
            "recommendations": recommendations,
        }
    )


class TestResponseParser:
    def test_parses_valid_json(self):
        raw = _llm_payload(
            [
                {
                    "restaurant_id": "r2",
                    "name": "Beta Cafe",
                    "rank": 1,
                    "explanation": "Fits your Italian preference in Banashankari.",
                }
            ]
        )
        parsed = ResponseParser().parse(raw)
        assert parsed is not None
        assert parsed["summary"].startswith("Great Italian")
        assert len(parsed["recommendations"]) == 1

    def test_parses_markdown_wrapped_json(self):
        inner = _llm_payload(
            [
                {
                    "restaurant_id": "r1",
                    "name": "Alpha Diner",
                    "rank": 1,
                    "explanation": "Strong rating for your medium budget in Banashankari.",
                }
            ]
        )
        raw = f"Here are the results:\n```json\n{inner}\n```"
        parsed = ResponseParser().parse(raw)
        assert parsed is not None
        assert parsed["recommendations"][0]["restaurant_id"] == "r1"

    def test_malformed_json_returns_none(self):
        assert ResponseParser().parse("{not valid json") is None
        assert ResponseParser().parse("") is None


class TestRecommendationValidator:
    def test_rejects_hallucinated_restaurant_id(self, candidates):
        parsed = {
            "summary": "Test",
            "recommendations": [
                {
                    "restaurant_id": "r2",
                    "name": "Beta Cafe",
                    "rank": 1,
                    "explanation": "Valid.",
                },
                {
                    "restaurant_id": "fake-99",
                    "name": "Imaginary Place",
                    "rank": 2,
                    "explanation": "Should be dropped.",
                },
            ],
        }
        validated = RecommendationValidator().validate(parsed, candidates)
        assert len(validated["recommendations"]) == 1
        assert validated["recommendations"][0]["restaurant_id"] == "r2"

    def test_deduplicates_restaurant_ids(self, candidates):
        parsed = {
            "recommendations": [
                {"restaurant_id": "r1", "rank": 2, "explanation": "Second."},
                {"restaurant_id": "r1", "rank": 1, "explanation": "First."},
            ]
        }
        validated = RecommendationValidator().validate(parsed, candidates)
        assert len(validated["recommendations"]) == 1


class TestRecommendationMerger:
    def test_enriches_with_candidate_fields(self, candidates, preferences):
        parsed = {
            "recommendations": [
                {
                    "restaurant_id": "r2",
                    "rank": 1,
                    "explanation": "Perfect Italian spot for your medium budget in Banashankari.",
                }
            ]
        }
        merged = RecommendationMerger().merge(parsed, candidates, top_k=preferences.top_k)
        assert len(merged) == 1
        rec = merged[0]
        assert rec.name == "Beta Cafe"
        assert rec.cuisine == "Italian"
        assert rec.rating == 4.2
        assert rec.estimated_cost == "₹400 for two"
        assert "Italian" in rec.explanation

    def test_backfills_when_llm_returns_fewer_than_top_k(self, candidates):
        parsed = {
            "recommendations": [
                {
                    "restaurant_id": "r2",
                    "rank": 1,
                    "explanation": "Top pick.",
                }
            ]
        }
        merged = RecommendationMerger().merge(parsed, candidates, top_k=3)
        assert len(merged) == 3
        assert {r.restaurant_id for r in merged} == {"r2", "r1", "r3"}


class TestBuildLlmResponse:
    def test_builds_response_with_metadata(
        self, candidates, preferences, filters_applied
    ):
        parsed = {
            "summary": "Overview for Bangalore dining.",
            "recommendations": [
                {
                    "restaurant_id": "r2",
                    "rank": 1,
                    "explanation": "Italian cuisine matches your request in Banashankari with medium budget.",
                },
                {
                    "restaurant_id": "r1",
                    "rank": 2,
                    "explanation": "High rating and medium budget fit.",
                },
            ],
        }
        response = build_llm_response(
            parsed,
            candidates,
            preferences,
            total_candidates=3,
            filters_applied=filters_applied,
            llm_latency_ms=120.5,
            token_usage={"total_tokens": 500},
        )
        assert response.metadata.llm_used is True
        assert response.metadata.total_candidates == 3
        assert response.summary is not None
        assert len(response.recommendations) == 2
        assert all(r.name for r in response.recommendations)


class TestFilterFallback:
    def test_fallback_uses_filter_ranking(
        self, candidates, preferences, filters_applied
    ):
        response = build_filter_fallback(
            candidates,
            preferences,
            total_candidates=3,
            filters_applied=filters_applied,
        )
        assert response.metadata.llm_used is False
        assert len(response.recommendations) == preferences.top_k
        assert response.recommendations[0].name == "Alpha Diner"
        assert "Banashankari" in response.recommendations[0].explanation
        assert "medium" in response.recommendations[0].explanation


class TestPromptBuilder:
    def test_includes_preferences_and_candidates(self, candidates, preferences):
        messages = PromptBuilder().build_messages(preferences, candidates)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        user_prompt = messages[1]["content"]
        assert "Banashankari" in user_prompt
        assert "Italian" in user_prompt
        assert "r1" in user_prompt
        assert "family-friendly" in user_prompt
        assert "recommend ONLY from this list" in user_prompt.lower() or "ONLY from this list" in user_prompt


class TestRecommendationEngine:
    def test_successful_llm_flow(self, candidates, preferences, filters_applied):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMCompletionResult(
            content=_llm_payload(
                [
                    {
                        "restaurant_id": "r2",
                        "name": "Beta Cafe",
                        "rank": 1,
                        "explanation": "Italian cuisine in Banashankari suits your medium budget and 4.0 rating bar.",
                    },
                    {
                        "restaurant_id": "r1",
                        "name": "Alpha Diner",
                        "rank": 2,
                        "explanation": "Strong 4.5 rating in Banashankari for medium budget diners.",
                    },
                ]
            ),
            model="llama-3.3-70b-versatile",
            latency_ms=95.0,
            usage={"total_tokens": 300},
        )

        engine = RecommendationEngine(client=mock_client)
        response = engine.generate(
            preferences,
            candidates,
            total_candidates=3,
            filters_applied=filters_applied,
        )

        assert response.metadata.llm_used is True
        assert len(response.recommendations) == 2
        assert response.recommendations[0].restaurant_id == "r2"
        mock_client.complete.assert_called_once()

    def test_llm_failure_returns_filter_fallback(
        self, candidates, preferences, filters_applied
    ):
        mock_client = MagicMock()
        mock_client.complete.side_effect = LLMClientError("rate limited")

        engine = RecommendationEngine(client=mock_client)
        response = engine.generate(
            preferences,
            candidates,
            total_candidates=3,
            filters_applied=filters_applied,
        )

        assert response.metadata.llm_used is False
        assert len(response.recommendations) == preferences.top_k

    def test_malformed_llm_response_returns_filter_fallback(
        self, candidates, preferences, filters_applied
    ):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMCompletionResult(
            content="Sorry, I cannot format this as JSON today.",
            model="llama-3.3-70b-versatile",
            latency_ms=50.0,
        )

        engine = RecommendationEngine(client=mock_client)
        response = engine.generate(
            preferences,
            candidates,
            total_candidates=3,
            filters_applied=filters_applied,
        )

        assert response.metadata.llm_used is False
        assert len(response.recommendations) == preferences.top_k

    def test_all_hallucinations_trigger_fallback(
        self, candidates, preferences, filters_applied
    ):
        mock_client = MagicMock()
        mock_client.complete.return_value = LLMCompletionResult(
            content=_llm_payload(
                [
                    {
                        "restaurant_id": "ghost-1",
                        "name": "Ghost Kitchen",
                        "rank": 1,
                        "explanation": "Not real.",
                    }
                ]
            ),
            model="llama-3.3-70b-versatile",
            latency_ms=40.0,
        )

        engine = RecommendationEngine(client=mock_client)
        response = engine.generate(
            preferences,
            candidates,
            total_candidates=3,
            filters_applied=filters_applied,
        )

        assert response.metadata.llm_used is False
        assert len(response.recommendations) == preferences.top_k
        assert all(r.restaurant_id in {"r1", "r2", "r3"} for r in response.recommendations)
