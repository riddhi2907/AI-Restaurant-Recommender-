"""In-memory restaurant store with optional Parquet cache."""

from __future__ import annotations

import gc
import logging
from pathlib import Path

import pandas as pd

from app.config import Settings, settings as default_settings
from app.data.loader import DatasetLoadError, load_raw_dataframe
from app.data.preprocessor import is_city_name, preprocess_dataframe
from app.logging_config import current_memory_mb, format_memory_mb, log_phase
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

RESTAURANT_COLUMNS = (
    "id",
    "name",
    "location",
    "city",
    "cuisine",
    "cost",
    "rating",
    "budget_tier",
    "rest_type",
    "address",
    "votes",
)


class RestaurantStore:
    """ Holds preprocessed restaurant records and exposes query helpers."""

    def __init__(self, restaurants: list[Restaurant]) -> None:
        self._restaurants = restaurants

    @property
    def count(self) -> int:
        return len(self._restaurants)

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_locations(self) -> list[str]:
        """Return distinct localities (e.g. Indiranagar, Bellandur), not city names."""
        locations = sorted(
            {
                r.location
                for r in self._restaurants
                if r.location and not is_city_name(r.location)
            }
        )
        return locations

    def get_cities(self) -> list[str]:
        cities = sorted({r.city for r in self._restaurants if r.city})
        return cities

    def get_cuisines(self) -> list[str]:
        cuisine_tokens: set[str] = set()
        for restaurant in self._restaurants:
            for part in restaurant.cuisine.split(","):
                token = part.strip()
                if token and token.lower() != "unknown":
                    cuisine_tokens.add(token)
        return sorted(cuisine_tokens)

    @classmethod
    def load(cls, settings: Settings | None = None, *, use_cache: bool = True) -> RestaurantStore:
        settings = settings or default_settings
        cache_path = settings.dataset_cache_path

        logger.info(
            "[dataset] cache_path=%s exists=%s size_bytes=%s",
            cache_path,
            cache_path.exists(),
            cache_path.stat().st_size if cache_path.exists() else 0,
        )

        if use_cache and cache_path.exists():
            try:
                with log_phase(logger, "dataset.cache_load"):
                    restaurants = _load_from_cache(cache_path)
                logger.info("[dataset] cache_load — %d restaurants ready", len(restaurants))
                return cls(restaurants)
            except Exception as exc:
                logger.warning(
                    "[dataset] cache_load — invalid cache at %s (%s); falling back to Hugging Face",
                    cache_path,
                    exc,
                    exc_info=True,
                )

        with log_phase(logger, "dataset.huggingface_download"):
            df = load_raw_dataframe()

        try:
            with log_phase(logger, "dataset.preprocess"):
                restaurants = preprocess_dataframe(df, settings)
        finally:
            del df
            gc.collect()

        if not restaurants:
            raise DatasetLoadError("No valid restaurants after preprocessing")

        if use_cache:
            with log_phase(logger, "dataset.cache_save"):
                _save_to_cache(restaurants, cache_path)
            gc.collect()

        logger.info(
            "[dataset] load_complete — %d restaurants (rss=%s MB)",
            len(restaurants),
            format_memory_mb(current_memory_mb()),
        )
        return cls(restaurants)


def _restaurants_to_dataframe(restaurants: list[Restaurant]) -> pd.DataFrame:
    records = [
        {
            "id": r.id,
            "name": r.name,
            "location": r.location,
            "city": r.city,
            "cuisine": r.cuisine,
            "cost": r.cost,
            "rating": r.rating,
            "budget_tier": r.budget_tier,
            "rest_type": r.rest_type,
            "address": r.address,
            "votes": r.votes,
        }
        for r in restaurants
    ]
    return pd.DataFrame.from_records(records, columns=list(RESTAURANT_COLUMNS))


def _dataframe_to_restaurants(df: pd.DataFrame) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    for row in df.itertuples(index=False):
        cost = None if pd.isna(row.cost) else float(row.cost)
        budget_tier = None if pd.isna(row.budget_tier) else row.budget_tier
        rest_type = None if pd.isna(row.rest_type) else row.rest_type
        address = None if pd.isna(row.address) else row.address
        votes = None if pd.isna(row.votes) else int(row.votes)

        restaurants.append(
            Restaurant(
                id=row.id,
                name=row.name,
                location=row.location,
                city=row.city,
                cuisine=row.cuisine,
                cost=cost,
                rating=float(row.rating),
                budget_tier=budget_tier,
                rest_type=rest_type,
                address=address,
                votes=votes,
            )
        )
    return restaurants


def _save_to_cache(restaurants: list[Restaurant], cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df = _restaurants_to_dataframe(restaurants)
    df.to_parquet(cache_path, index=False)
    logger.info(
        "[dataset] cache_save — wrote %d rows to %s (%d bytes)",
        len(restaurants),
        cache_path,
        cache_path.stat().st_size,
    )


def _load_from_cache(cache_path: Path) -> list[Restaurant]:
    df = pd.read_parquet(cache_path)
    missing = [col for col in RESTAURANT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Cache schema mismatch. Missing columns: {missing}")
    return _dataframe_to_restaurants(df)


def get_restaurant_store(*, use_cache: bool = True, settings: Settings | None = None) -> RestaurantStore:
    """Convenience factory for loading the restaurant store."""
    return RestaurantStore.load(settings=settings, use_cache=use_cache)
