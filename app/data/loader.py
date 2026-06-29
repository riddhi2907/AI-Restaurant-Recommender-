"""Load the Zomato dataset from Hugging Face."""

from __future__ import annotations

import gc
import logging
import time

import pandas as pd

from app.logging_config import current_memory_mb, format_memory_mb

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

LOAD_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


class DatasetLoadError(Exception):
    """Raised when the dataset cannot be loaded."""


def validate_schema(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DatasetLoadError(
            f"Dataset schema mismatch. Missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def load_raw_dataframe(*, max_retries: int = 3, retry_delay_seconds: float = 2.0) -> pd.DataFrame:
    """Load raw dataset from Hugging Face with retry on failure."""
    from datasets import load_dataset

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        dataset = None
        attempt_started = time.perf_counter()
        try:
            logger.info(
                "[dataset] huggingface — attempt %d/%d for %s (rss=%s MB)",
                attempt + 1,
                max_retries + 1,
                DATASET_ID,
                format_memory_mb(current_memory_mb()),
            )
            dataset = load_dataset(DATASET_ID, split=DATASET_SPLIT)
            keep_cols = [col for col in LOAD_COLUMNS if col in dataset.column_names]
            logger.info("[dataset] huggingface — selected columns: %s", keep_cols)
            dataset = dataset.select_columns(keep_cols)
            df = dataset.to_pandas()
            del dataset
            dataset = None
            gc.collect()
            validate_schema(df)
            logger.info(
                "[dataset] huggingface — loaded %d rows, %d columns in %.1fs (rss=%s MB)",
                len(df),
                len(df.columns),
                time.perf_counter() - attempt_started,
                format_memory_mb(current_memory_mb()),
            )
            return df
        except Exception as exc:
            last_error = exc
            logger.warning(
                "[dataset] huggingface — attempt %d failed after %.1fs: %s",
                attempt + 1,
                time.perf_counter() - attempt_started,
                exc,
                exc_info=True,
            )
            if attempt < max_retries:
                delay = retry_delay_seconds * (2**attempt)
                logger.info("[dataset] huggingface — retrying in %.1fs", delay)
                time.sleep(delay)
        finally:
            if dataset is not None:
                del dataset
                gc.collect()

    raise DatasetLoadError(
        f"Failed to load dataset {DATASET_ID} after {max_retries + 1} attempt(s)"
    ) from last_error
