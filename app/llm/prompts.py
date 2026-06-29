"""LLM prompt templates for restaurant recommendations."""

from __future__ import annotations

import json
import re
from typing import Any

from app.models.preferences import UserPreferences
from app.models.restaurant import Restaurant

_MAX_FIELD_LEN = 200
_MAX_ADDITIONAL_LEN = 300

_INJECTION_PATTERNS = (
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|above)\s+instructions"),
    re.compile(r"(?i)you\s+are\s+now"),
    re.compile(r"(?i)system\s*:"),
    re.compile(r"(?i)assistant\s*:"),
)

SYSTEM_PROMPT = """You are a restaurant recommendation assistant for Zomato-style dining suggestions in India.

Your task is to rank restaurants from a PROVIDED candidate list only. You must NEVER invent or suggest restaurants that are not in the candidate list.

Rules:
1. Recommend ONLY restaurants whose restaurant_id appears in the candidate list.
2. Return exactly the requested number of recommendations (top_k), ranked from best fit to least fit.
3. Each explanation must reference specific user preferences (location, budget, cuisine, minimum rating, and any additional preferences).
4. Use the restaurant's actual attributes from the candidate data when explaining (rating, cuisine, cost).
5. Respond with valid JSON only — no markdown, no prose outside the JSON object.

Output JSON schema:
{
  "summary": "Optional one-paragraph overview tying recommendations to user preferences",
  "recommendations": [
    {
      "restaurant_id": "string (must match a candidate id)",
      "name": "string (from candidate)",
      "rank": 1,
      "explanation": "Why this restaurant fits the user's preferences"
    }
  ]
}

Ranks must be sequential integers starting at 1. Do not duplicate restaurant_id values."""


def _truncate(text: str, max_len: int) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _sanitize_additional(text: str) -> str:
    cleaned = text.strip()
    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return _truncate(cleaned, _MAX_ADDITIONAL_LEN)


def _serialize_preferences(preferences: UserPreferences) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "location": preferences.location,
        "location_match": preferences.location_match,
        "budget": preferences.budget,
        "min_rating": preferences.min_rating,
        "top_k": preferences.top_k,
    }
    if preferences.cuisine:
        payload["cuisine"] = preferences.cuisine
    if preferences.additional:
        payload["additional"] = [_sanitize_additional(item) for item in preferences.additional if item.strip()]
    return payload


def _serialize_candidate(restaurant: Restaurant) -> dict[str, Any]:
    return {
        "restaurant_id": restaurant.id,
        "name": _truncate(restaurant.name, _MAX_FIELD_LEN),
        "location": _truncate(restaurant.location, _MAX_FIELD_LEN),
        "city": restaurant.city,
        "cuisine": _truncate(restaurant.cuisine, _MAX_FIELD_LEN),
        "rating": restaurant.rating,
        "cost": restaurant.cost,
        "budget_tier": restaurant.budget_tier,
    }


class PromptBuilder:
    """Build structured prompts for the Groq recommendation call."""

    def build_messages(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> list[dict[str, str]]:
        user_content = self.build_user_prompt(preferences, candidates)
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def build_user_prompt(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> str:
        prefs_json = json.dumps(_serialize_preferences(preferences), indent=2)
        candidates_json = json.dumps(
            [_serialize_candidate(r) for r in candidates],
            indent=2,
        )

        cuisine_line = (
            f"- Preferred cuisine: {preferences.cuisine}\n"
            if preferences.cuisine
            else "- Preferred cuisine: any\n"
        )
        additional_line = ""
        if preferences.additional:
            sanitized = [_sanitize_additional(a) for a in preferences.additional if a.strip()]
            if sanitized:
                additional_line = f"- Additional preferences: {', '.join(sanitized)}\n"

        return f"""Rank the best {preferences.top_k} restaurants for this user.

User preferences:
- Location: {preferences.location} ({preferences.location_match} match)
- Budget tier: {preferences.budget}
{cuisine_line}- Minimum rating: {preferences.min_rating}
{additional_line}
Full preferences JSON:
{prefs_json}

Candidate restaurants (recommend ONLY from this list):
{candidates_json}

Return JSON with "summary" and "recommendations" containing exactly {preferences.top_k} items (or fewer if fewer candidates are provided). Each explanation must mention why the restaurant suits the user's location, budget, and other stated preferences."""
