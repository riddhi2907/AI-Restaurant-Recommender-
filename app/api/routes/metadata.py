"""Metadata endpoints for UI dropdowns and autocomplete."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_store
from app.data.store import RestaurantStore

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/locations")
def list_locations(store: RestaurantStore = Depends(get_store)) -> list[str]:
    """Return distinct localities (e.g. Indiranagar, Bellandur) for the location dropdown."""
    return store.get_locations()


@router.get("/cuisines")
def list_cuisines(store: RestaurantStore = Depends(get_store)) -> list[str]:
    """Return distinct cuisines for autocomplete."""
    return store.get_cuisines()
