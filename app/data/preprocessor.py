"""Clean and normalize raw Zomato dataset records."""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

import pandas as pd

from app.models.restaurant import BudgetTier, Restaurant

if TYPE_CHECKING:
    from app.config import Settings

COST_COLUMN = "approx_cost(for two people)"
RATE_COLUMN = "rate"
CUISINES_COLUMN = "cuisines"
CITY_COLUMN = "listed_in(city)"

UNRATED_VALUES = {"new", "-", "", "nan", "none"}
DEFAULT_CITY = "Bangalore"

# Values that represent a city, not a filterable locality.
CITY_NAMES: frozenset[str] = frozenset(
    {
        "bangalore",
        "bengaluru",
        "blr",
        "delhi",
        "new delhi",
        "ncr",
    }
)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def parse_rating(value: object) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0

    text = str(value).strip().lower()
    if text in UNRATED_VALUES:
        return 0.0

    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0.0

    rating = float(match.group(1))
    if rating > 5 and "/5" not in text:
        return 0.0
    return max(0.0, min(5.0, rating))


def parse_cost(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = str(value).strip().lower()
    if text in {"", "nan", "none", "-"}:
        return None

    cleaned = text.replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "")
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        return None

    cost = float(match.group(1))
    if cost <= 0:
        return None
    return cost


def normalize_cuisine(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Unknown"

    text = normalize_whitespace(str(value))
    if not text or text.lower() in {"nan", "none", "-"}:
        return "Unknown"

    parts = [normalize_whitespace(part) for part in text.split(",") if part.strip()]
    return ", ".join(parts) if parts else "Unknown"


def is_city_name(value: str) -> bool:
    return normalize_whitespace(value).lower() in CITY_NAMES


def normalize_city_name(value: str) -> str:
    lowered = normalize_whitespace(value).lower()
    if lowered in {"bangalore", "bengaluru", "blr"}:
        return "Bangalore"
    if lowered in {"delhi", "new delhi", "ncr"}:
        return "Delhi"
    return normalize_whitespace(value)


STREET_HINTS = (" road", " street", " st ", " floor", " feet", " lane", " cross", " highway")


def _looks_like_street(value: str) -> bool:
    lowered = value.lower()
    return any(hint in lowered for hint in STREET_HINTS)


def parse_locality_from_address(address: str) -> str | None:
    """Extract locality from a comma-separated address (e.g. '..., Indiranagar, Bangalore')."""
    parts = [normalize_whitespace(part) for part in address.split(",") if part.strip()]
    if not parts:
        return None

    for index in range(len(parts) - 1, -1, -1):
        if not is_city_name(parts[index]):
            continue
        for candidate_index in range(index - 1, -1, -1):
            candidate = parts[candidate_index]
            if is_city_name(candidate) or _looks_like_street(candidate):
                continue
            return candidate
        return None

    if len(parts) >= 2 and not is_city_name(parts[-1]) and not _looks_like_street(parts[-1]):
        return parts[-1]

    return None


def extract_locality(
    location: object,
    listed_in_city: object,
    address: object,
) -> str | None:
    """Resolve the filterable locality (e.g. Indiranagar), never the city name."""
    raw_location = _safe_str(location)
    if raw_location and not is_city_name(raw_location):
        return raw_location

    zone = _safe_str(listed_in_city)
    if zone and not is_city_name(zone):
        return zone

    address_text = _safe_str(address)
    if address_text:
        parsed = parse_locality_from_address(address_text)
        if parsed:
            return parsed

    return None


def extract_city(address: object, location: object, listed_in_city: object) -> str:
    address_text = _safe_str(address)
    if address_text:
        lowered = address_text.lower()
        if "bangalore" in lowered or "bengaluru" in lowered:
            return "Bangalore"
        if "delhi" in lowered:
            return "Delhi"

    for value in (location, listed_in_city):
        text = _safe_str(value)
        if text and is_city_name(text):
            return normalize_city_name(text)

    return DEFAULT_CITY


def compute_budget_tier(cost: float | None, settings: Settings) -> BudgetTier | None:
    if cost is None:
        return None
    if cost <= settings.budget_low_max:
        return "low"
    if cost <= settings.budget_medium_max:
        return "medium"
    return "high"


def make_restaurant_id(name: str, location: str, address: str | None) -> str:
    key = f"{name}|{location}|{address or ''}".lower().strip()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def _safe_str(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = normalize_whitespace(str(value))
    return text or None


def _safe_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def preprocess_row(row: pd.Series, settings: Settings) -> Restaurant | None:
    name = _safe_str(row.get("name"))
    if not name:
        return None

    address = _safe_str(row.get("address"))
    location = extract_locality(row.get("location"), row.get(CITY_COLUMN), row.get("address"))
    if not location:
        return None

    city = extract_city(row.get("address"), row.get("location"), row.get(CITY_COLUMN))
    cuisine = normalize_cuisine(row.get(CUISINES_COLUMN))
    rating = parse_rating(row.get(RATE_COLUMN))
    cost = parse_cost(row.get(COST_COLUMN))
    budget_tier = compute_budget_tier(cost, settings)

    return Restaurant(
        id=make_restaurant_id(name, location, address),
        name=name,
        location=location,
        city=city,
        cuisine=cuisine,
        cost=cost,
        rating=rating,
        budget_tier=budget_tier,
        rest_type=_safe_str(row.get("rest_type")),
        address=address,
        votes=_safe_int(row.get("votes")),
    )


def preprocess_dataframe(df: pd.DataFrame, settings: Settings) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    dropped = 0

    for _, row in df.iterrows():
        restaurant = preprocess_row(row, settings)
        if restaurant is None:
            dropped += 1
            continue
        restaurants.append(restaurant)

    if dropped:
        logger = __import__("logging").getLogger(__name__)
        logger.info("Dropped %d invalid rows during preprocessing", dropped)

    return restaurants
