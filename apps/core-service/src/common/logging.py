"""Structured logging configuration for the core service."""

import contextvars
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any

from fastapi import Request

# Context variable for request ID (for distributed tracing)
request_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
organization_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("organization_id", default=None)
user_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data: dict[str, Any] = {
            "time": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        # Add context variables if available
        request_id = request_id_context.get()
        if request_id:
            log_data["request_id"] = request_id

        org_id = organization_id_context.get()
        if org_id:
            log_data["organization_id"] = org_id

        user_id = user_id_context.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, msg: str, **kwargs: Any) -> None:
    """
    Log a message with additional context.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        msg: Log message
        **kwargs: Additional context fields
    """
    log_fn = getattr(logger, level.lower())
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    record.extra = kwargs
    log_fn(msg, extra=kwargs)


# Middleware for request logging


async def logging_middleware(request: Request, call_next: Any) -> Any:
    """
    Middleware to add request context to logs and log request/response.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    # Extract or generate request ID
    request_id = request.headers.get("X-Request-ID", request.headers.get("X-Correlation-ID"))
    if not request_id:
        import uuid

        request_id = str(uuid.uuid4())

    # Set context variables
    request_id_context.set(request_id)

    # Extract organization and user from headers (set by API Gateway)
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        organization_id_context.set(org_id)

    user_id = request.headers.get("X-User-ID")
    if user_id:
        user_id_context.set(user_id)

    # Log request start
    logger = get_logger(__name__)
    start_time = time.time()

    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
        },
    )

    # Process request
    try:
        response = await call_next(request)

        # Log request completion
        duration = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as exc:
        # Log error
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
                "error": str(exc),
            },
            exc_info=True,
        )
        raise

    finally:
        # Clear context
        request_id_context.set(None)
        organization_id_context.set(None)
        user_id_context.set(None)
