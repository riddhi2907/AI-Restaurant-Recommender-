"""Tests for logging configuration."""

import logging

import app.logging_config as logging_config
from app.logging_config import configure_logging, log_phase


def test_configure_logging_sets_level():
    logging_config._configured = False
    configure_logging(level="DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_is_idempotent():
    logging_config._configured = False
    configure_logging(level="INFO")
    configure_logging(level="DEBUG")
    assert logging.getLogger().level == logging.INFO


def test_log_phase_logs_success(caplog):
    logger = logging.getLogger("test.logging")
    with caplog.at_level(logging.INFO, logger="test.logging"):
        with log_phase(logger, "test.phase"):
            pass

    messages = [record.message for record in caplog.records]
    assert any("test.phase — begin" in message for message in messages)
    assert any("test.phase — done" in message for message in messages)
