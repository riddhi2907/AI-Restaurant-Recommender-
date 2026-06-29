"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, metadata, recommendations
from app.config import settings
from app.data.loader import DatasetLoadError
from app.data.store import get_restaurant_store

logger = logging.getLogger(__name__)


async def _load_store_in_background(app: FastAPI) -> None:
    """Load dataset without blocking server startup (Railway healthcheck)."""
    app.state.dataset_loading = True
    app.state.dataset_load_error = None
    app.state.store = None

    try:
        logger.info("Loading restaurant dataset in background...")
        store = await asyncio.to_thread(get_restaurant_store)
        app.state.store = store
        logger.info("Loaded %d restaurants", store.count)
    except DatasetLoadError as exc:
        app.state.dataset_load_error = str(exc)
        logger.error("Failed to load dataset: %s", exc)
    except Exception as exc:
        app.state.dataset_load_error = str(exc)
        logger.exception("Unexpected error loading restaurant dataset")
    finally:
        app.state.dataset_loading = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_task = asyncio.create_task(_load_store_in_background(app))

    yield

    load_task.cancel()
    try:
        await load_task
    except asyncio.CancelledError:
        pass
    app.state.store = None
    app.state.dataset_loading = False


def create_app() -> FastAPI:
    app = FastAPI(
        title="Zomato AI Restaurant Recommender API",
        description="REST API for AI-powered restaurant recommendations.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(metadata.router)
    app.include_router(recommendations.router)

    return app


app = create_app()
