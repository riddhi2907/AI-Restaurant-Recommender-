"""User preference model for restaurant recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.models.restaurant import BudgetTier

LocationMatchType = Literal["city", "locality"]


@dataclass(frozen=True)
class UserPreferences:
    location: str
    budget: BudgetTier
    cuisine: str | None = None
    min_rating: float = 0.0
    additional: list[str] = field(default_factory=list)
    top_k: int = 5
    location_match: LocationMatchType = "locality"

    def __post_init__(self) -> None:
        if not self.location.strip():
            raise ValueError("location is required")
        if self.budget not in ("low", "medium", "high"):
            raise ValueError(f"invalid budget: {self.budget}")
        if not 0.0 <= self.min_rating <= 5.0:
            raise ValueError(f"min_rating must be between 0 and 5, got {self.min_rating}")
        if self.top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {self.top_k}")
