"""Structured logging configuration with JSON formatting and request ID tracking.

This module provides:
- JSON-formatted structured logging for production environments
- Request ID injection for tracing requests across services
- Context variables for adding metadata to logs
- Performance and metrics logging helpers
"""

import json
import logging
import sys
import time
from contextvars import ContextVar
from datetime import datetime
from typing import Any

# Context variables for request-scoped data
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Outputs log records as JSON objects with consistent fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - logger: Logger name (module path)
    - message: Log message
    - request_id: Optional request ID for tracing
    - context: Optional additional context data
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: LogRecord to format

        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add user ID if available
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add standard fields that might be useful
        if hasattr(record, "funcName"):
            log_data["function"] = record.funcName

        if hasattr(record, "lineno"):
            log_data["line"] = record.lineno

        return json.dumps(log_data)


class SimpleStructuredFormatter(logging.Formatter):
    """Human-readable structured formatter for development.

    Outputs logs with request IDs but in a more readable format than pure JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with request ID prefix.

        Args:
            record: LogRecord to format

        Returns:
            Formatted log string
        """
        request_id = request_id_var.get()
        prefix = f"[{request_id[:8]}] " if request_id else ""

        # Add context if present
        context = ""
        if hasattr(record, "context"):
            context = f" {record.context}"

        return f"{prefix}{record.levelname}: {record.name}: {record.getMessage()}{context}"


def configure_logging(
    *,
    json_logs: bool = False,
    log_level: str = "INFO",
) -> None:
    """Configure application-wide structured logging.

    Args:
        json_logs: Use JSON formatter (production) vs simple formatter (development)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on environment
    formatter = StructuredFormatter() if json_logs else SimpleStructuredFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def set_request_id(request_id: str) -> None:
    """Set request ID for current context.

    Args:
        request_id: Unique request identifier
    """
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get request ID from current context.

    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set user ID for current context.

    Args:
        user_id: User identifier
    """
    user_id_var.set(user_id)


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    """Log message with additional context data.

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **context: Additional context data to include
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)


class PerformanceLogger:
    """Context manager for logging operation performance metrics."""

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        **context: Any,
    ):
        """Initialize performance logger.

        Args:
            logger: Logger instance
            operation: Name of operation being measured
            **context: Additional context data
        """
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time: float | None = None

    def __enter__(self) -> "PerformanceLogger":
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Log performance metrics."""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            context = {
                "operation": self.operation,
                "duration_ms": round(duration_ms, 2),
                **self.context,
            }

            if exc_type:
                context["error"] = str(exc_val)
                log_with_context(
                    self.logger,
                    logging.ERROR,
                    f"Operation '{self.operation}' failed after {duration_ms:.2f}ms",
                    **context,
                )
            else:
                log_with_context(
                    self.logger,
                    logging.INFO,
                    f"Operation '{self.operation}' completed in {duration_ms:.2f}ms",
                    **context,
                )


def log_upload_metrics(
    logger: logging.Logger,
    job_id: str,
    filename: str,
    file_size: int,
    duration_ms: float,
) -> None:
    """Log file upload metrics.

    Args:
        logger: Logger instance
        job_id: Job identifier
        filename: Uploaded filename
        file_size: File size in bytes
        duration_ms: Upload duration in milliseconds
    """
    log_with_context(
        logger,
        logging.INFO,
        f"File uploaded: {filename}",
        job_id=job_id,
        filename=filename,
        file_size_bytes=file_size,
        file_size_mb=round(file_size / (1024 * 1024), 2),
        duration_ms=round(duration_ms, 2),
        throughput_mbps=round((file_size / (1024 * 1024)) / (duration_ms / 1000), 2)
        if duration_ms > 0
        else 0,
    )


def log_processing_metrics(
    logger: logging.Logger,
    job_id: str,
    status: str,
    duration_ms: float,
    input_size: int | None = None,
    output_size: int | None = None,
    error: str | None = None,
) -> None:
    """Log G-code processing metrics.

    Args:
        logger: Logger instance
        job_id: Job identifier
        status: Processing status (completed, failed, timeout)
        duration_ms: Processing duration in milliseconds
        input_size: Optional input file size in bytes
        output_size: Optional output file size in bytes
        error: Optional error message
    """
    context: dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "duration_ms": round(duration_ms, 2),
        "duration_seconds": round(duration_ms / 1000, 2),
    }

    if input_size:
        context["input_size_mb"] = round(input_size / (1024 * 1024), 2)

    if output_size:
        context["output_size_mb"] = round(output_size / (1024 * 1024), 2)

    if input_size and output_size:
        context["size_change_percent"] = round(((output_size - input_size) / input_size) * 100, 2)

    if error:
        context["error"] = error

    level = logging.ERROR if status == "failed" else logging.INFO
    log_with_context(
        logger,
        level,
        f"Processing {status}: {job_id}",
        **context,
    )


def log_request_metrics(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str | None = None,
) -> None:
    """Log HTTP request metrics.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        client_ip: Optional client IP address
    """
    context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }

    if client_ip:
        context["client_ip"] = client_ip

    log_with_context(
        logger,
        logging.INFO,
        f"{method} {path} {status_code}",
        **context,
    )
