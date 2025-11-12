"""File upload endpoint and processing queueing."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from app.models import ProblemDetails
from app.models.upload import UploadResponse
from app.services.file_service import FileService, FileTooLargeError, FileValidationError
from app.services.processing_service import get_processing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "File uploaded successfully and queued for processing",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "3DBenchy.gcode",
                        "file_size": 3145728,
                        "created_at": "2025-11-11T10:30:00",
                        "status": "pending",
                        "message": "File uploaded successfully and queued for processing",
                    }
                }
            },
        },
        400: {
            "model": ProblemDetails,
            "description": "Invalid file or parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_extension": {
                            "summary": "Invalid file extension",
                            "value": {
                                "type": "about:blank",
                                "title": "Invalid file extension",
                                "status": 400,
                                "detail": "File extension '.txt' not allowed. Allowed extensions: .gcode, .gco, .g",
                            },
                        },
                        "empty_file": {
                            "summary": "Empty file",
                            "value": {
                                "type": "about:blank",
                                "title": "Empty file",
                                "status": 400,
                                "detail": "File is empty",
                            },
                        },
                        "invalid_gcode": {
                            "summary": "Invalid G-code content",
                            "value": {
                                "type": "about:blank",
                                "title": "Invalid G-code content",
                                "status": 400,
                                "detail": "File doesn't appear to contain valid G-code. Expected G-code commands and coordinates.",
                            },
                        },
                    }
                }
            },
        },
        413: {
            "model": ProblemDetails,
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {
                        "type": "about:blank",
                        "title": "File too large",
                        "status": 413,
                        "detail": "File size (75.50MB) exceeds maximum allowed size (50.00MB)",
                    }
                }
            },
        },
        422: {
            "description": "Invalid parameter values",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "greater_than_equal",
                                "loc": ["body", "start_at_layer"],
                                "msg": "Input should be greater than or equal to 0",
                                "input": -1,
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "model": ProblemDetails,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "type": "about:blank",
                        "title": "Upload error",
                        "status": 500,
                        "detail": "Failed to process upload: Unexpected error details",
                    }
                }
            },
        },
    },
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="G-code file to process"),
    start_at_layer: int = Form(
        default=3, ge=0, description="Layer to start BrickLayers processing"
    ),
    extrusion_multiplier: float = Form(
        default=1.05,
        ge=1.0,
        le=1.2,
        description="Extrusion multiplier for brick layers",
    ),
) -> UploadResponse:
    """Upload a G-code file for BrickLayers processing.

    This endpoint accepts a G-code file and processing parameters, validates the file,
    saves it to temporary storage, and returns a job ID for tracking the processing.

    Args:
        file: G-code file to upload (.gcode, .gco, .g extensions)
        start_at_layer: Layer number to start applying BrickLayers (0-based, default: 3)
        extrusion_multiplier: Extrusion multiplier for brick layers (1.0-1.2, default: 1.05)

    Returns:
        UploadResponse with job_id and upload details

    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    file_service = FileService()

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    try:
        # Validate filename
        if not file.filename:
            raise FileValidationError("No filename provided")

        file_service.validate_filename(file.filename)
        file_service.validate_file_extension(file.filename)

        # Stream file to disk with incremental size validation (memory-efficient)
        # This validates size during streaming and returns first chunk for content validation
        _file_path, saved_size, first_chunk = await file_service.save_upload_streaming(
            job_id, file.filename, file.file, validate_size=True
        )

        # Validate G-code content from first chunk
        file_service.validate_gcode_content(first_chunk)

        # Register and queue processing in background
        processing_service = get_processing_service()
        processing_service.register_job(
            job_id=job_id,
            filename=file.filename,
            start_at_layer=start_at_layer,
            extrusion_multiplier=extrusion_multiplier,
        )
        # Use background task to enforce timeout without blocking request
        background_tasks.add_task(processing_service.process_with_timeout, job_id)
        logger.info(
            "Upload %s queued for processing (start_at_layer=%d, extrusion_multiplier=%.3f)",
            job_id,
            start_at_layer,
            extrusion_multiplier,
        )

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_size=saved_size,
            created_at=datetime.now(),
            status="pending",
            message="File uploaded successfully and queued for processing",
        )

    except FileTooLargeError as e:
        body = {
            "type": "about:blank",
            "title": "File too large",
            "status": status.HTTP_413_CONTENT_TOO_LARGE,
            "detail": str(e),
        }
        return JSONResponse(status_code=status.HTTP_413_CONTENT_TOO_LARGE, content=body)
    except FileValidationError as e:
        body = {
            "type": "about:blank",
            "title": "Invalid file or parameters",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": str(e),
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body)

    except Exception as e:
        # Clean up any partial upload
        try:
            upload_path = file_service.get_upload_path(job_id, file.filename or "")
            file_service.delete_file(upload_path)
        except Exception:
            pass

        body = {
            "type": "about:blank",
            "title": "Upload error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": f"Failed to process upload: {e}",
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)
