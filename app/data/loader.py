"""Load the Zomato dataset from Hugging Face."""

from __future__ import annotations

import logging
import time

import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
DATASET_SPLIT = "train"

REQUIRED_COLUMNS = (
    "name",
    "location",
    "cuisines",
    "rate",
    "approx_cost(for two people)",
)

OPTIONAL_COLUMNS = (
    "address",
    "listed_in(city)",
    "rest_type",
    "votes",
)


class DatasetLoadError(Exception):
    """Raised when the dataset cannot be loaded."""


def validate_schema(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DatasetLoadError(
            f"Dataset schema mismatch. Missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def load_raw_dataframe(*, max_retries: int = 1, retry_delay_seconds: float = 2.0) -> pd.DataFrame:
    """Load raw dataset from Hugging Face with retry on failure."""
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            logger.info("Loading dataset %s (attempt %d)", DATASET_ID, attempt + 1)
            dataset = load_dataset(DATASET_ID, split=DATASET_SPLIT)
            df = dataset.to_pandas()
            validate_schema(df)
            logger.info("Loaded %d rows from %s", len(df), DATASET_ID)
            return df
        except Exception as exc:
            last_error = exc
            logger.warning("Dataset load attempt %d failed: %s", attempt + 1, exc)
            if attempt < max_retries:
                time.sleep(retry_delay_seconds * (2**attempt))

    raise DatasetLoadError(
        f"Failed to load dataset {DATASET_ID} after {max_retries + 1} attempt(s)"
    ) from last_error
