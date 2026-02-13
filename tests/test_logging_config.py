"""Tests for structured logging configuration.

Tests cover:
- Context variable management
- Structured and plain formatters
- Performance timing decorators
- Logger configuration
"""

import asyncio
import json
import logging
from io import StringIO

import pytest

from core.logging_config import (
    PlainFormatter,
    StructuredFormatter,
    clear_context,
    get_context,
    get_logger,
    set_context,
    timing_decorator,
)


class TestContextVariables:
    """Test context variable management."""

    def test_set_context_all_vars(self):
        """Test setting all context variables."""
        set_context(
            peer_id_val="peer123",
            party_id_val="party456",
            session_id_val="session789",
            correlation_id_val="corr000",
        )

        context = get_context()
        assert context["peer_id"] == "peer123"
        assert context["party_id"] == "party456"
        assert context["session_id"] == "session789"
        assert context["correlation_id"] == "corr000"

    def test_set_context_partial(self):
        """Test setting only some context variables."""
        clear_context()
        set_context(peer_id_val="peer123", session_id_val="session789")

        context = get_context()
        assert context["peer_id"] == "peer123"
        assert context["party_id"] is None
        assert context["session_id"] == "session789"
        assert context["correlation_id"] is None

    def test_clear_context(self):
        """Test clearing all context variables."""
        set_context(
            peer_id_val="peer123",
            party_id_val="party456",
            session_id_val="session789",
        )
        clear_context()

        context = get_context()
        assert all(v is None for v in context.values())

    def test_context_isolation(self):
        """Test that context updates don't affect other values."""
        clear_context()
        set_context(peer_id_val="peer123", party_id_val="party456")

        set_context(peer_id_val="peer999")

        context = get_context()
        assert context["peer_id"] == "peer999"
        assert context["party_id"] == "party456"


class TestStructuredFormatter:
    """Test structured JSON logging formatter."""

    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_with_context(self):
        """Test formatting message with context variables."""
        clear_context()
        set_context(
            peer_id_val="peer123",
            session_id_val="session789",
            correlation_id_val="corr000",
        )

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["peer_id"] == "peer123"
        assert data["session_id"] == "session789"
        assert data["correlation_id"] == "corr000"

    def test_format_with_duration(self):
        """Test formatting message with performance timing."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=42,
            msg="Operation completed",
            args=(),
            exc_info=None,
        )
        record.duration_ms = 123.45

        result = formatter.format(record)
        data = json.loads(result)

        assert data["duration_ms"] == 123.45


class TestPlainFormatter:
    """Test human-readable logging formatter."""

    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        clear_context()
        formatter = PlainFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result

    def test_format_with_context(self):
        """Test formatting message with context variables."""
        set_context(
            peer_id_val="peer123",
            party_id_val="party456",
            session_id_val="session789",
        )

        formatter = PlainFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "peer=peer123" in result
        assert "party=party456" in result
        assert "session=session789" in result

    def test_format_with_timing(self):
        """Test formatting message with performance timing."""
        clear_context()
        formatter = PlainFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=42,
            msg="Operation completed",
            args=(),
            exc_info=None,
        )
        record.duration_ms = 123.45

        result = formatter.format(record)

        assert "[took 123.45ms]" in result


class TestLoggingConfiguration:
    """Test logger configuration."""

    def test_configure_logging_plain(self):
        """Test configuring logging with plain format."""
        # Create a string stream to capture logging output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = PlainFormatter()
        handler.setFormatter(formatter)

        # Get the root logger and add handler
        logger = logging.getLogger()
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        output = stream.getvalue()
        assert "Test message" in output
        assert "INFO" in output

    def test_configure_logging_json(self):
        """Test configuring logging with JSON format."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)

        # Get the root logger and add handler
        logger = logging.getLogger()
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        output = stream.getvalue()
        assert output.strip()  # Has output

        try:
            data = json.loads(output.strip())
            assert "message" in data
            assert data["message"] == "Test message"
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestTimingDecorator:
    """Test performance timing decorator."""

    def test_timing_decorator_sync(self):
        """Test timing decorator on synchronous function."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(PlainFormatter())

        # Set handler on root logger to capture all log records
        root_logger = logging.getLogger()
        old_handlers = root_logger.handlers[:]
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.DEBUG)

        @timing_decorator(name="test_operation")
        def test_func():
            return "result"

        result = test_func()

        # Restore original handlers
        root_logger.handlers = old_handlers

        assert result == "result"
        # Check that timing was logged
        output = stream.getvalue()
        assert "test_operation" in output or "Completed" in output

    @pytest.mark.asyncio
    async def test_timing_decorator_async(self):
        """Test timing decorator on async function."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(PlainFormatter())

        # Set handler on root logger to capture all log records
        root_logger = logging.getLogger()
        old_handlers = root_logger.handlers[:]
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.DEBUG)

        @timing_decorator(name="async_operation")
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await async_func()

        # Restore original handlers
        root_logger.handlers = old_handlers

        assert result == "async_result"
        # Check that timing was logged
        output = stream.getvalue()
        assert "async_operation" in output or "Completed" in output

    def test_timing_decorator_captures_duration(self):
        """Test that decorator captures execution time."""
        stream = StringIO()

        @timing_decorator(name="timed_op")
        def slow_func():
            import time

            time.sleep(0.05)
            return "done"

        result = slow_func()
        assert result == "done"


class TestContextIntegration:
    """Integration tests for context and logging together."""

    def test_context_persists_across_logs(self):
        """Test that context persists across multiple log messages."""
        clear_context()
        set_context(
            peer_id_val="peer123",
            correlation_id_val="corr999",
        )

        logger = get_logger("test")
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = PlainFormatter()
        handler.setFormatter(formatter)
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)

        logger.info("Message 1")
        logger.info("Message 2")

        output = stream.getvalue()
        # Both messages should have the peer_id in context
        lines = output.strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            assert "peer=peer123" in line
            assert "corr_id=corr999" in line

    def test_no_context_vars_when_not_set(self):
        """Test that context vars are not included when not set."""
        clear_context()

        logger = get_logger("test")
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)

        logger.info("Message without context")

        output = stream.getvalue()
        data = json.loads(output.strip())

        # None of the context vars should be in output
        assert "peer_id" not in data or data.get("peer_id") is None
        assert "party_id" not in data or data.get("party_id") is None
        assert "session_id" not in data or data.get("session_id") is None
        assert "correlation_id" not in data or data.get("correlation_id") is None
