"""Job status and download endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from app.models import ProblemDetails
from app.models.processing import JobStatus, JobStatusResponse
from app.services.processing_service import get_processing_service

router = APIRouter(prefix="/api/v1", tags=["jobs"])
logger = logging.getLogger(__name__)


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    responses={
        200: {
            "description": "Job status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "pending": {
                            "summary": "Job pending",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "filename": "3DBenchy.gcode",
                                "status": "pending",
                                "created_at": "2025-11-11T10:30:00",
                                "updated_at": "2025-11-11T10:30:00",
                                "error": None,
                            },
                        },
                        "processing": {
                            "summary": "Job processing",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "filename": "3DBenchy.gcode",
                                "status": "processing",
                                "created_at": "2025-11-11T10:30:00",
                                "updated_at": "2025-11-11T10:30:15",
                                "error": None,
                            },
                        },
                        "completed": {
                            "summary": "Job completed",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "filename": "3DBenchy.gcode",
                                "status": "completed",
                                "created_at": "2025-11-11T10:30:00",
                                "updated_at": "2025-11-11T10:30:45",
                                "error": None,
                            },
                        },
                        "failed": {
                            "summary": "Job failed",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "filename": "3DBenchy.gcode",
                                "status": "failed",
                                "created_at": "2025-11-11T10:30:00",
                                "updated_at": "2025-11-11T10:30:30",
                                "error": "Processing timeout exceeded",
                            },
                        },
                    }
                }
            },
        },
        404: {
            "model": ProblemDetails,
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {
                        "type": "about:blank",
                        "title": "Job not found",
                        "status": 404,
                        "detail": "Job not found",
                    }
                }
            },
        },
    },
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Return current status for a processing job."""
    svc = get_processing_service()
    job = svc.get_job(job_id)
    if job is None:
        body = {
            "type": "about:blank",
            "title": "Job not found",
            "status": 404,
            "detail": "Job not found",
        }
        return JSONResponse(status_code=404, content=body)
    return JobStatusResponse(
        job_id=job.job_id,
        filename=job.filename,
        status=JobStatus(job.status),
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error,
    )


@router.get(
    "/download/{job_id}",
    responses={
        200: {
            "description": "Processed G-code file download",
            "content": {
                "text/plain": {
                    "example": "; Processed by BrickLayers\nG1 X0 Y0 Z0.2 E1 F1800\n...",
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment with processed filename",
                    "schema": {
                        "type": "string",
                        "example": 'attachment; filename="3DBenchy_processed.gcode"',
                    },
                }
            },
        },
        404: {
            "model": ProblemDetails,
            "description": "Job or file not found",
            "content": {
                "application/json": {
                    "examples": {
                        "job_not_found": {
                            "summary": "Job does not exist",
                            "value": {
                                "type": "about:blank",
                                "title": "Job not found",
                                "status": 404,
                                "detail": "Job not found",
                            },
                        },
                        "file_missing": {
                            "summary": "Processed file missing",
                            "value": {
                                "type": "about:blank",
                                "title": "Processed file not found",
                                "status": 404,
                                "detail": "Processed file not found",
                            },
                        },
                    }
                }
            },
        },
        409: {
            "model": ProblemDetails,
            "description": "Job not completed",
            "content": {
                "application/json": {
                    "examples": {
                        "still_processing": {
                            "summary": "Job still processing",
                            "value": {
                                "type": "about:blank",
                                "title": "Job not ready",
                                "status": 409,
                                "detail": "Job status is processing, not ready for download",
                            },
                        },
                        "job_pending": {
                            "summary": "Job not started",
                            "value": {
                                "type": "about:blank",
                                "title": "Job not ready",
                                "status": 409,
                                "detail": "Job status is pending, not ready for download",
                            },
                        },
                    }
                }
            },
        },
    },
)
async def download_processed_file(job_id: str):
    """Stream processed G-code file if job completed and perform post-download cleanup.

    Cleanup strategy (current): Delete original upload file immediately after successful
    response is prepared; retain processed output for potential re-download until a future
    retention mechanism is implemented.
    """
    svc = get_processing_service()
    job = svc.get_job(job_id)
    if job is None:
        body = {
            "type": "about:blank",
            "title": "Job not found",
            "status": 404,
            "detail": "Job not found",
        }
        return JSONResponse(status_code=404, content=body)
    if job.status != JobStatus.COMPLETED:
        body = {
            "type": "about:blank",
            "title": "Job not ready",
            "status": 409,
            "detail": f"Job status is {job.status}, not ready for download",
        }
        return JSONResponse(status_code=409, content=body)
    if not job.output_path or not Path(job.output_path).exists():
        body = {
            "type": "about:blank",
            "title": "Processed file not found",
            "status": 404,
            "detail": "Processed file not found",
        }
        return JSONResponse(status_code=404, content=body)

    # Prepare response first (do not delete processed output yet to allow potential re-downloads)
    response = FileResponse(
        path=str(job.output_path),
        media_type="text/plain",
        filename=f"{Path(job.filename).stem}_processed.gcode",
    )

    # Post-download cleanup: remove original uploaded file to save space
    if job.upload_path and Path(job.upload_path).exists():
        try:
            Path(job.upload_path).unlink()
            logger.info("Upload file cleaned after download for job %s", job.job_id)
        except OSError as e:
            logger.warning("Failed to delete upload file for job %s: %s", job.job_id, e)

    logger.info("Download served for job %s -> %s", job.job_id, job.output_path)
    return response
