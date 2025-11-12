"""RFC 7807-like Problem Details model for standardized error responses."""

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ProblemDetails(BaseModel):
    """Standardized error response following RFC 7807-ish shape.

    Fields:
    - type: A URI reference that identifies the problem type.
    - title: Short, human-readable summary of the problem type.
    - status: HTTP status code.
    - detail: Human-readable explanation specific to this occurrence.
    - instance: A URI reference that identifies the specific occurrence.
    - errors: Optional validation error object or additional structured details.
    """

    type: HttpUrl | None = Field(
        default=None, description="A URI reference that identifies the problem type"
    )
    title: str = Field(description="Short, human-readable summary of the problem type")
    status: int = Field(description="HTTP status code")
    detail: str | None = Field(default=None, description="Human-readable details")
    instance: str | None = Field(default=None, description="URI identifying this occurrence")
    errors: dict[str, Any] | None = Field(
        default=None, description="Optional machine-readable error details (validation etc.)"
    )
