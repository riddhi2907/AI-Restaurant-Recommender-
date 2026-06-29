"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, metadata, recommendations
from app.config import settings
from app.data.loader import DatasetLoadError
from app.data.store import get_restaurant_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading restaurant dataset...")
    try:
        app.state.store = get_restaurant_store()
        logger.info("Loaded %d restaurants", app.state.store.count)
    except DatasetLoadError as exc:
        logger.error("Failed to load dataset: %s", exc)
        app.state.store = None
    except Exception:
        logger.exception("Unexpected error loading restaurant dataset")
        app.state.store = None

    yield

    app.state.store = None


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
