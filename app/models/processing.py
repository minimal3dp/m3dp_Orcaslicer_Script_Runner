"""Models for G-code processing operations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Processing job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingRequest(BaseModel):
    """Request model for G-code processing."""

    start_at_layer: int = Field(
        default=3, ge=0, description="Layer number to start BrickLayers processing (0-based)"
    )
    extrusion_multiplier: float = Field(
        default=1.05,
        ge=1.0,
        le=1.2,
        description="Extrusion multiplier for brick layers (1.0 - 1.2)",
    )


class ProcessingResponse(BaseModel):
    """Response model for job creation."""

    job_id: str = Field(description="Unique identifier for the processing job")
    status: JobStatus = Field(description="Current status of the job")
    created_at: datetime = Field(description="Timestamp when job was created")
    message: str = Field(description="Human-readable status message")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type or code")
    message: str = Field(description="Detailed error message")
    detail: str | None = Field(default=None, description="Additional error details")
