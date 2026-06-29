"""One-off prediction script for CLI smoke tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.data import get_restaurant_store
from app.filters.engine import FilterEngine
from app.filters.parser import parse_preferences
from app.llm.engine import RecommendationEngine


def _budget_tier_for_amount(amount: int) -> str:
    from app.config import settings

    if amount <= settings.budget_low_max:
        return "low"
    if amount <= settings.budget_medium_max:
        return "medium"
    return "high"


def main() -> None:
    parser = argparse.ArgumentParser(description="Get AI restaurant recommendations")
    parser.add_argument("--location", required=True)
    parser.add_argument("--budget", default="medium", help="low/medium/high or INR amount e.g. 1500")
    parser.add_argument("--min-rating", type=float, default=0.0)
    parser.add_argument("--cuisine", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    budget = args.budget
    if budget.isdigit():
        budget = _budget_tier_for_amount(int(budget))

    print("Loading dataset...")
    store = get_restaurant_store()
    print(f"Loaded {store.count} restaurants")

    prefs = parse_preferences(
        location=args.location,
        budget=budget,
        min_rating=args.min_rating,
        cuisine=args.cuisine,
        top_k=args.top_k,
        store=store,
    )

    filter_result = FilterEngine().apply(prefs, store.get_all())
    print(
        f"Candidates after filter: {len(filter_result.candidates)} "
        f"(total matched: {filter_result.total_matched})"
    )
    if filter_result.filters_relaxed:
        print(f"Relaxed filters: {filter_result.filters_relaxed}")

    print("Calling Groq LLM...")
    response = RecommendationEngine().generate(
        prefs,
        filter_result.candidates,
        total_candidates=filter_result.total_matched,
        filters_applied=filter_result.filters_applied,
        filters_relaxed=filter_result.filters_relaxed,
    )

    print()
    if response.summary:
        print("SUMMARY:", response.summary)
        print()

    for rec in response.recommendations:
        print(f"#{rec.rank} {rec.name}")
        print(f"   Cuisine: {rec.cuisine}")
        print(f"   Rating: {rec.rating}")
        print(f"   Cost: {rec.estimated_cost}")
        print(f"   Explanation: {rec.explanation}")
        print()

    print(
        "Metadata:",
        json.dumps(
            {
                "llm_used": response.metadata.llm_used,
                "total_candidates": response.metadata.total_candidates,
                "llm_latency_ms": response.metadata.llm_latency_ms,
                "token_usage": response.metadata.token_usage,
            },
            indent=2,
        ),
    )


if __name__ == "__main__":
    main()
