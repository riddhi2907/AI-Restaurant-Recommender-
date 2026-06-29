"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import health, metadata, recommendations
from app.config import settings
from app.data.loader import DatasetLoadError
from app.data.store import get_restaurant_store
from app.logging_config import (
    configure_logging,
    log_runtime_context,
    log_startup_settings,
    register_shutdown_signals,
)

configure_logging()
logger = logging.getLogger(__name__)


async def _load_store_in_background(app: FastAPI) -> None:
    """Load dataset without blocking server startup (Railway healthcheck)."""
    app.state.dataset_loading = True
    app.state.dataset_load_error = None
    app.state.store = None

    started = time.perf_counter()
    try:
        logger.info("[startup] dataset_loader — scheduling background load")
        store = await asyncio.to_thread(get_restaurant_store)
        app.state.store = store
        logger.info(
            "[startup] dataset_loader — ready with %d restaurants in %.1fs",
            store.count,
            time.perf_counter() - started,
        )
    except DatasetLoadError as exc:
        app.state.dataset_load_error = str(exc)
        logger.error(
            "[startup] dataset_loader — failed after %.1fs: %s",
            time.perf_counter() - started,
            exc,
        )
    except MemoryError:
        app.state.dataset_load_error = (
            "Out of memory while loading restaurant dataset. "
            "Bundle data/cache/restaurants.parquet in the repo or use a Railway volume cache."
        )
        logger.exception(
            "[startup] dataset_loader — out of memory after %.1fs",
            time.perf_counter() - started,
        )
    except Exception as exc:
        app.state.dataset_load_error = str(exc)
        logger.exception(
            "[startup] dataset_loader — unexpected error after %.1fs",
            time.perf_counter() - started,
        )
    finally:
        app.state.dataset_loading = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[startup] application lifespan — begin")
    log_runtime_context(logger)
    log_startup_settings(logger, settings)
    register_shutdown_signals(logger)

    load_task = asyncio.create_task(_load_store_in_background(app))
    logger.info("[startup] HTTP server accepting requests while dataset loads in background")

    yield

    logger.info("[shutdown] application lifespan — begin teardown")
    load_task.cancel()
    try:
        await load_task
    except asyncio.CancelledError:
        logger.warning("[shutdown] dataset background load cancelled during teardown")
    app.state.store = None
    app.state.dataset_loading = False
    logger.info("[shutdown] application lifespan — complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Zomato AI Restaurant Recommender API",
        description="REST API for AI-powered restaurant recommendations.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
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
