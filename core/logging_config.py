"""Structured logging configuration with context variables and performance timing.

Provides:
- Context variables for correlation tracking (peer_id, party_id, session_id, correlation_id)
- Structured JSON logging format
- Performance timing decorators
- Centralized logger configuration
"""

import contextvars
import json
import logging
import sys
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

# Context variables for request/operation tracking
peer_id = contextvars.ContextVar("peer_id", default=None)
party_id = contextvars.ContextVar("party_id", default=None)
session_id = contextvars.ContextVar("session_id", default=None)
correlation_id = contextvars.ContextVar("correlation_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs with context variables."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON with context variables."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables if available
        peer_id_val = peer_id.get()
        if peer_id_val:
            log_data["peer_id"] = peer_id_val

        party_id_val = party_id.get()
        if party_id_val:
            log_data["party_id"] = party_id_val

        session_id_val = session_id.get()
        if session_id_val:
            log_data["session_id"] = session_id_val

        correlation_id_val = correlation_id.get()
        if correlation_id_val:
            log_data["correlation_id"] = correlation_id_val

        # Add exception info if present
        if record.exc_info and record.exc_text:
            log_data["exception"] = record.exc_text

        # Add performance metrics if present
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class PlainFormatter(logging.Formatter):
    """Human-readable formatter with context variables."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with context information."""
        # Build context string
        context_parts = []

        peer_id_val = peer_id.get()
        if peer_id_val:
            context_parts.append(f"peer={peer_id_val}")

        party_id_val = party_id.get()
        if party_id_val:
            context_parts.append(f"party={party_id_val}")

        session_id_val = session_id.get()
        if session_id_val:
            context_parts.append(f"session={session_id_val}")

        correlation_id_val = correlation_id.get()
        if correlation_id_val:
            context_parts.append(f"corr_id={correlation_id_val}")

        context_str = f"[{', '.join(context_parts)}] " if context_parts else ""

        # Build log message
        base_msg = (
            f"{record.levelname:8} {record.name:30} {context_str}{record.getMessage()}"
        )

        # Add location info if debug level
        if record.levelno >= logging.DEBUG:
            base_msg += f" ({record.filename}:{record.lineno})"

        # Add timing info if present
        if hasattr(record, "duration_ms"):
            base_msg += f" [took {record.duration_ms:.2f}ms]"

        # Add exception if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"

        return base_msg


def configure_logging(
    json_format: bool = False, level: int = logging.INFO, log_file: str | None = None
) -> logging.Logger:
    """Configure structured logging for the application.

    Args:
        json_format: If True, use JSON output format for structured logging
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file (if None, logs to stdout)

    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Choose formatter
    formatter_class = StructuredFormatter if json_format else PlainFormatter

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter_class())
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter_class())
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def timing_decorator(name: str | None = None) -> Callable:
    """Decorator to measure and log function execution time.

    Args:
        name: Optional custom name for the timed operation (defaults to function name)

    Returns:
        Decorated function that logs execution time
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            logger = get_logger(func.__module__)
            if not logger.isEnabledFor(logging.DEBUG):
                return func(*args, **kwargs)

            op_name = name or func.__name__
            start_time = time.perf_counter()

            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_record = logging.LogRecord(
                    name=logger.name,
                    level=logging.DEBUG,
                    pathname=func.__code__.co_filename,
                    lineno=func.__code__.co_firstlineno,
                    msg=f"Completed {op_name}",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                logger.handle(log_record)

        async def async_wrapper(*args, **kwargs) -> Any:
            logger = get_logger(func.__module__)
            if not logger.isEnabledFor(logging.DEBUG):
                return await func(*args, **kwargs)

            op_name = name or func.__name__
            start_time = time.perf_counter()

            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_record = logging.LogRecord(
                    name=logger.name,
                    level=logging.DEBUG,
                    pathname=func.__code__.co_filename,
                    lineno=func.__code__.co_firstlineno,
                    msg=f"Completed {op_name}",
                    args=(),
                    exc_info=None,
                )
                log_record.duration_ms = duration_ms
                logger.handle(log_record)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def set_context(
    peer_id_val: str | None = None,
    party_id_val: str | None = None,
    session_id_val: str | None = None,
    correlation_id_val: str | None = None,
) -> None:
    """Set context variables for the current task/thread.

    Args:
        peer_id_val: Peer identifier
        party_id_val: Party identifier
        session_id_val: Session identifier
        correlation_id_val: Correlation identifier for request tracing
    """
    if peer_id_val is not None:
        peer_id.set(peer_id_val)
    if party_id_val is not None:
        party_id.set(party_id_val)
    if session_id_val is not None:
        session_id.set(session_id_val)
    if correlation_id_val is not None:
        correlation_id.set(correlation_id_val)


def clear_context() -> None:
    """Clear all context variables."""
    peer_id.set(None)
    party_id.set(None)
    session_id.set(None)
    correlation_id.set(None)


def get_context() -> dict[str, str | None]:
    """Get current context variables.

    Returns:
        Dictionary with current context values
    """
    return {
        "peer_id": peer_id.get(),
        "party_id": party_id.get(),
        "session_id": session_id.get(),
        "correlation_id": correlation_id.get(),
    }
