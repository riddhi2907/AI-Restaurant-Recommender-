"""Tests for application configuration."""

import os
from pathlib import Path

import pytest


def test_settings_loads_defaults(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    from app.config import Settings

    settings = Settings.from_env()
    assert settings.llm_model == "llama-3.3-70b-versatile"
    assert settings.groq_api_key is None
    assert settings.max_candidates_for_llm == 20
    assert settings.default_top_k == 5


def test_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    monkeypatch.setenv("LLM_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("MAX_CANDIDATES_FOR_LLM", "15")

    from app.config import Settings

    settings = Settings.from_env()
    assert settings.groq_api_key == "gsk_test_key"
    assert settings.llm_model == "llama-3.1-8b-instant"
    assert settings.max_candidates_for_llm == 15
    assert settings.groq_configured is True


def test_budget_threshold_validation(monkeypatch):
    monkeypatch.setenv("BUDGET_LOW_MAX", "1500")
    monkeypatch.setenv("BUDGET_MEDIUM_MAX", "500")

    from app.config import Settings

    with pytest.raises(ValueError, match="BUDGET_LOW_MAX"):
        Settings.from_env()


def test_dataset_cache_path_resolves_relative(monkeypatch):
    monkeypatch.setenv("DATASET_CACHE_PATH", "./data/cache/restaurants.parquet")

    from app.config import Settings

    settings = Settings.from_env()
    assert settings.dataset_cache_path.name == "restaurants.parquet"
    assert "data" in settings.dataset_cache_path.parts
