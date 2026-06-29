"""Restaurant domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BudgetTier = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Restaurant:
    id: str
    name: str
    location: str
    city: str
    cuisine: str
    cost: float | None
    rating: float
    budget_tier: BudgetTier | None = None
    rest_type: str | None = None
    address: str | None = None
    votes: int | None = None

    @property
    def estimated_cost(self) -> str:
        if self.cost is None:
            return "Not available"
        return f"₹{int(self.cost)} for two"
