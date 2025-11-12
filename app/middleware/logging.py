"""Middleware for request tracking and logging.

Provides:
- Request ID generation and injection
- Request/response logging with metrics
- Context propagation for structured logging
"""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging_config import log_request_metrics, set_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking and structured logging.

    Generates unique request IDs, injects them into request context,
    and logs request/response metrics.
    """

    def __init__(self, app: ASGIApp):
        """Initialize middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        import logging

        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """Process request with ID generation and logging.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Process request
        try:
            response: Response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request metrics
            client_ip = request.client.host if request.client else None
            log_request_metrics(
                self.logger,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "context": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "error": str(e),
                    }
                },
            )
            raise


def get_request_id_from_request(request: Request) -> str | None:
    """Extract request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID if available
    """
    return getattr(request.state, "request_id", None)
