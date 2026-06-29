"""HTTP middleware for request diagnostics."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/ready"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log API latency and surface server errors in deploy logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "[request] %s %s — unhandled error after %.0fms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        status_code = response.status_code
        message = "[request] %s %s — %d in %.0fms"
        args = (request.method, request.url.path, status_code, elapsed_ms)

        if status_code >= 500:
            logger.error(message, *args)
        elif status_code >= 400:
            logger.warning(message, *args)
        else:
            logger.info(message, *args)

        return response
