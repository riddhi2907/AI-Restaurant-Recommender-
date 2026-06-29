"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _detect_env_encoding(env_path: Path) -> str:
    raw = env_path.read_bytes()[:4]
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return "utf-16"
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"


def _load_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path, encoding=_detect_env_encoding(env_path))
    else:
        load_dotenv()


_load_env()


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default).strip()


def _env_int(key: str, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.getenv(key)
    try:
        value = int(raw) if raw is not None else default
    except ValueError:
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _env_float(key: str, default: float, *, minimum: float | None = None, maximum: float | None = None) -> float:
    raw = os.getenv(key)
    try:
        value = float(raw) if raw is not None else default
    except ValueError:
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _env_path(key: str, default: Path) -> Path:
    raw = os.getenv(key)
    if not raw:
        return default
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _env_csv(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(key)
    if not raw:
        return default
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    return values or default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    llm_model: str
    llm_temperature: float
    max_candidates_for_llm: int
    default_top_k: int
    dataset_cache_path: Path
    budget_low_max: int
    budget_medium_max: int
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> Settings:
        api_key = os.getenv("GROQ_API_KEY")
        api_key = api_key.strip() if api_key else None
        if api_key == "":
            api_key = None

        budget_low = _env_int("BUDGET_LOW_MAX", 500, minimum=0)
        budget_medium = _env_int("BUDGET_MEDIUM_MAX", 1500, minimum=1)
        if budget_low >= budget_medium:
            raise ValueError(
                f"BUDGET_LOW_MAX ({budget_low}) must be less than BUDGET_MEDIUM_MAX ({budget_medium})"
            )

        max_candidates = _env_int("MAX_CANDIDATES_FOR_LLM", 20, minimum=1, maximum=50)
        default_top_k = _env_int("DEFAULT_TOP_K", 5, minimum=1)

        return cls(
            groq_api_key=api_key,
            llm_model=_env_str("LLM_MODEL", "llama-3.3-70b-versatile"),
            llm_temperature=_env_float("LLM_TEMPERATURE", 0.3, minimum=0.0, maximum=1.0),
            max_candidates_for_llm=max_candidates,
            default_top_k=default_top_k,
            dataset_cache_path=_env_path("DATASET_CACHE_PATH", PROJECT_ROOT / "data" / "cache" / "restaurants.parquet"),
            budget_low_max=budget_low,
            budget_medium_max=budget_medium,
            cors_origins=_env_csv(
                "CORS_ORIGINS",
                ("http://localhost:5173", "http://localhost:3000"),
            ),
        )

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)


settings = Settings.from_env()
