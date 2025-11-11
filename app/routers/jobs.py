"""Job status and download endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.processing import ErrorResponse, JobStatus, JobStatusResponse
from app.services.processing_service import get_processing_service

router = APIRouter(prefix="/api/v1", tags=["jobs"])
logger = logging.getLogger(__name__)


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse, "description": "Job not found"}},
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Return current status for a processing job."""
    svc = get_processing_service()
    job = svc.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "Job not found"}
        )
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
        200: {"content": {"text/plain": {}}},
        404: {"model": ErrorResponse, "description": "Job or file not found"},
        409: {"model": ErrorResponse, "description": "Job not completed"},
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
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "Job not found"}
        )
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "not_ready",
                "message": f"Job status is {job.status}, not ready for download",
            },
        )
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "file_missing", "message": "Processed file not found"},
        )

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
