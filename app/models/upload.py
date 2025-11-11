"""Models for file upload operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for successful file upload."""

    job_id: str = Field(description="Unique identifier for the processing job")
    filename: str = Field(description="Original filename of uploaded file")
    file_size: int = Field(description="Size of uploaded file in bytes")
    created_at: datetime = Field(description="Timestamp when upload was received")
    status: str = Field(default="pending", description="Initial job status")
    message: str = Field(default="File uploaded successfully", description="Status message")


class ValidationError(BaseModel):
    """Model for file validation errors."""

    error: str = Field(description="Error type")
    message: str = Field(description="Detailed error message")
    details: dict | None = Field(default=None, description="Additional error details")
