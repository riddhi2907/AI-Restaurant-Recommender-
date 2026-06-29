"""Application-wide logging configuration and runtime diagnostics."""

from __future__ import annotations

import logging
import os
import platform
import signal
import sys
import time
from contextlib import contextmanager
from typing import Iterator

from app.config import Settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(*, level: str | None = None) -> None:
    """Configure root and framework loggers once at process start."""
    global _configured
    if _configured:
        return

    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        framework_logger = logging.getLogger(logger_name)
        framework_logger.handlers.clear()
        framework_logger.propagate = True

    if log_level == "DEBUG":
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    _configured = True
    logging.getLogger(__name__).info("Logging configured (level=%s)", log_level)


def current_memory_mb() -> float | None:
    """Best-effort resident memory for the current process (Linux/Railway)."""
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        return None
    return None


def format_memory_mb(value: float | None) -> str:
    return f"{value:.1f}" if value is not None else "n/a"


def log_runtime_context(logger: logging.Logger) -> None:
    """Log environment details useful when diagnosing deploy crashes."""
    memory_mb = current_memory_mb()
    logger.info(
        "[runtime] python=%s platform=%s cwd=%s rss=%s MB",
        platform.python_version(),
        platform.platform(),
        os.getcwd(),
        format_memory_mb(memory_mb),
    )
    logger.info(
        "[runtime] pid=%s PORT=%s RAILWAY_ENVIRONMENT=%s",
        os.getpid(),
        os.getenv("PORT", "unset"),
        os.getenv("RAILWAY_ENVIRONMENT", "unset"),
    )


def log_startup_settings(logger: logging.Logger, settings: Settings) -> None:
    """Log non-secret configuration at startup."""
    logger.info(
        "[config] llm_model=%s groq_configured=%s cache_path=%s cache_exists=%s",
        settings.llm_model,
        settings.groq_configured,
        settings.dataset_cache_path,
        settings.dataset_cache_path.exists(),
    )
    logger.info(
        "[config] cors_origins=%s max_candidates=%d default_top_k=%d",
        list(settings.cors_origins),
        settings.max_candidates_for_llm,
        settings.default_top_k,
    )


def register_shutdown_signals(logger: logging.Logger) -> None:
    """Log OS signals — helpful when Railway stops or OOM-kills a container."""

    def _handle_signal(signum: int, _frame: object) -> None:
        try:
            name = signal.Signals(signum).name
        except ValueError:
            name = str(signum)
        logger.warning(
            "[shutdown] received signal %s (rss=%s MB)",
            name,
            format_memory_mb(current_memory_mb()),
        )

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handle_signal)
        except (ValueError, OSError):
            # Not available on all platforms or threads.
            pass


@contextmanager
def log_phase(logger: logging.Logger, phase: str) -> Iterator[None]:
    """Log begin/end of a startup phase with duration and memory usage."""
    started = time.perf_counter()
    memory_before = current_memory_mb()
    logger.info(
        "[startup] %s — begin (rss=%s MB)",
        phase,
        format_memory_mb(memory_before),
    )
    try:
        yield
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception(
            "[startup] %s — failed after %.1fs (rss=%s MB)",
            phase,
            elapsed,
            format_memory_mb(current_memory_mb()),
        )
        raise
    else:
        elapsed = time.perf_counter() - started
        logger.info(
            "[startup] %s — done in %.1fs (rss=%s MB, delta=%s MB)",
            phase,
            elapsed,
            format_memory_mb(current_memory_mb()),
            _memory_delta(memory_before),
        )


def _memory_delta(before: float | None) -> str:
    after = current_memory_mb()
    if before is None or after is None:
        return "n/a"
    return f"{after - before:+.1f}"
