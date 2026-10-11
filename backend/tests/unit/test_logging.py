
"""Tests for structured JSON logging."""

import json
import logging

from app.api.middleware.request_id import request_id_var
from app.core.logging import JSONFormatter, RequestIDFilter
from app.core.logging import setup_logging


def test_request_id_filter_attaches_current_request_id() -> None:
    """The filter should attach the current request ID to a log record."""

    token = request_id_var.set("test-request-123")

    try:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        log_filter = RequestIDFilter()

        assert log_filter.filter(record) is True
        assert record.request_id == "test-request-123"
    finally:
        request_id_var.reset(token)


def test_json_formatter_outputs_valid_json() -> None:
    """The formatter should produce structured JSON with required fields."""

    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg="CRM request processed",
        args=(),
        exc_info=None,
    )
    record.request_id = "test-request-456"

    formatted = JSONFormatter().format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert data["message"] == "CRM request processed"
    assert data["request_id"] == "test-request-456"
    assert "timestamp" in data


def test_json_formatter_uses_default_request_id() -> None:
    """The formatter should use '-' when a record has no request ID."""

    record = logging.LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname=__file__,
        lineno=30,
        msg="Background task started",
        args=(),
        exc_info=None,
    )

    data = json.loads(JSONFormatter().format(record))

    assert data["level"] == "WARNING"
    assert data["request_id"] == "-"


def test_json_formatter_includes_exception_details() -> None:
    """The formatter should include exception details when present."""

    try:
        raise ValueError("Example failure")
    except ValueError:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=40,
            msg="Operation failed",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )

    data = json.loads(JSONFormatter().format(record))

    assert data["message"] == "Operation failed"
    assert "exception" in data
    assert "ValueError: Example failure" in data["exception"]


def test_setup_logging_configures_root_logger() -> None:
    """Logging setup should configure the root logger and JSON handler."""

    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = root_logger.handlers[:]

    try:
        setup_logging()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1

        handler = root_logger.handlers[0]

        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, JSONFormatter)
        assert any(
            isinstance(log_filter, RequestIDFilter)
            for log_filter in handler.filters
        )
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)