"""Rate limiting middleware for the BrickLayers application.

This module provides rate limiting functionality to protect against abuse
and denial-of-service attacks.
"""

import hashlib
import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config.settings import get_settings
from app.models.processing import ProblemDetails

settings = get_settings()
logger = logging.getLogger(__name__)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_GLOBAL] if settings.RATE_LIMIT_ENABLED else [],
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors.

    Args:
        request: The incoming request
        exc: The rate limit exceeded exception

    Returns:
        JSONResponse with RFC 7807 problem details
    """
    logger.warning(
        f"Rate limit exceeded: {request.url.path}",
        extra={
            "context": {
                "ip_address": get_remote_address(request),
                "endpoint": str(request.url.path),
                "limit": str(exc),
            }
        },
    )

    problem = ProblemDetails(
        type="https://example.com/errors/rate-limit",
        title="Rate Limit Exceeded",
        status=429,
        detail=f"Too many requests. {exc}. Please try again later.",
        instance=str(request.url.path),
    )

    response = JSONResponse(
        status_code=429,
        content=problem.model_dump(exclude_none=True),
    )

    # Add rate limit headers
    response.headers["Retry-After"] = "60"  # Suggest 60 seconds wait

    return response


def get_api_key_identifier(request: Request) -> str:
    """Extract API key identifier for rate limiting.

    If API authentication is enabled and request has valid key,
    use key name instead of IP address for rate limiting.

    Args:
        request: The incoming request

    Returns:
        API key name or IP address
    """
    if not settings.API_AUTH_ENABLED:
        return get_remote_address(request)

    # Check for API key in headers
    api_key = request.headers.get(settings.API_KEY_HEADER)
    if not api_key:
        return get_remote_address(request)

    # Hash the key to find matching key name
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    for key_name, stored_hash in settings.API_KEYS.items():
        if stored_hash == key_hash:
            return f"api_key:{key_name}"

    # Invalid key, use IP address
    return get_remote_address(request)


# Alternative key function that uses API keys when available
limiter_with_api_keys = Limiter(
    key_func=get_api_key_identifier,
    default_limits=[settings.RATE_LIMIT_GLOBAL] if settings.RATE_LIMIT_ENABLED else [],
)
