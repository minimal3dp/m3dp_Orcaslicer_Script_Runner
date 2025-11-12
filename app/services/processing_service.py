"""Processing service to run BrickLayers in the background.

This module integrates the BrickLayers core with the FastAPI backend.
It manages processing jobs, runs them in a background thread with timeout
protection, and tracks job status and paths for later retrieval.
"""

from __future__ import annotations

import concurrent.futures
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.core import BrickLayersProcessor
from app.logging_config import PerformanceLogger
from app.metrics import metrics
from app.services.file_service import FileService

logger = logging.getLogger(__name__)


@dataclass
class ProcessingJob:
    job_id: str
    filename: str  # original filename
    start_at_layer: int
    extrusion_multiplier: float
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error: str | None = None
    upload_path: Path | None = None
    output_path: Path | None = None


class ProcessingService:
    """Singleton-like service that manages processing jobs."""

    _instance: ProcessingService | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.settings = get_settings()
        self.file_service = FileService()
        self._jobs: dict[str, ProcessingJob] = {}
        # Small thread pool for CPU-bound processing without blocking the event loop
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.settings.MAX_CONCURRENT_JOBS
        )

    @classmethod
    def get(cls) -> ProcessingService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = ProcessingService()
            return cls._instance

    def register_job(
        self,
        job_id: str,
        filename: str,
        start_at_layer: int,
        extrusion_multiplier: float,
    ) -> ProcessingJob:
        """Register a job in memory before queuing it."""
        upload_path = self.file_service.get_upload_path(job_id, filename)
        output_path = self.file_service.get_output_path(job_id, filename)

        job = ProcessingJob(
            job_id=job_id,
            filename=filename,
            start_at_layer=start_at_layer,
            extrusion_multiplier=extrusion_multiplier,
            status="pending",
            upload_path=upload_path,
            output_path=output_path,
        )
        self._jobs[job_id] = job
        logger.info(
            f"Registered processing job: {filename}",
            extra={
                "context": {
                    "job_id": job_id,
                    "filename": filename,
                    "start_at_layer": start_at_layer,
                    "extrusion_multiplier": extrusion_multiplier,
                }
            },
        )
        return job

    def get_job(self, job_id: str) -> ProcessingJob | None:
        return self._jobs.get(job_id)

    def _run_processing(self, job: ProcessingJob) -> None:
        """Worker function that performs the processing for a job."""
        assert job.upload_path is not None
        assert job.output_path is not None

        job.status = "processing"
        job.updated_at = datetime.now()

        input_size = job.upload_path.stat().st_size
        start_time = metrics.track_processing_started(job)

        logger.info(
            f"Processing started: {job.filename}",
            extra={
                "context": {
                    "job_id": job.job_id,
                    "filename": job.filename,
                    "input_size_bytes": input_size,
                    "start_at_layer": job.start_at_layer,
                    "extrusion_multiplier": job.extrusion_multiplier,
                }
            },
        )

        try:
            with PerformanceLogger(
                logger=logger,
                operation=f"process_gcode_{job.job_id}",
                extra_context={
                    "job_id": job.job_id,
                    "filename": job.filename,
                    "input_size_bytes": input_size,
                },
            ):
                processor = BrickLayersProcessor(
                    extrusion_global_multiplier=job.extrusion_multiplier,
                    start_at_layer=job.start_at_layer,
                    verbosity=0,
                )

                # Stream input and output to avoid loading entire file in memory
                with job.upload_path.open("r", encoding="utf-8", errors="ignore") as infile:
                    gcode_stream = (line for line in infile)
                    with job.output_path.open("w", encoding="utf-8") as outfile:
                        for line in processor.process_gcode(gcode_stream):
                            outfile.write(line)

            job.status = "completed"
            job.updated_at = datetime.now()
            output_size = job.output_path.stat().st_size

            # Track successful processing
            metrics.track_processing_completed(start_time, input_size, output_size)

            logger.info(
                f"Processing completed: {job.filename}",
                extra={
                    "context": {
                        "job_id": job.job_id,
                        "filename": job.filename,
                        "output_filename": job.output_path.name,
                        "input_size_bytes": input_size,
                        "output_size_bytes": output_size,
                        "size_change_percent": round(
                            ((output_size - input_size) / input_size) * 100, 2
                        ),
                    }
                },
            )
        except Exception as e:
            job.status = "failed"
            job.updated_at = datetime.now()
            job.error = str(e)

            # Track failed processing
            metrics.track_processing_failed(start_time, "error")

            logger.error(
                f"Processing failed: {job.filename}",
                extra={
                    "context": {
                        "job_id": job.job_id,
                        "filename": job.filename,
                        "error": str(e),
                    }
                },
                exc_info=True,
            )

    def queue_job(self, job_id: str) -> concurrent.futures.Future:
        """Submit job to executor and wrap with timeout handling at the caller."""
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Unknown job_id: {job_id}")
        return self._executor.submit(self._run_processing, job)

    def process_with_timeout(self, job_id: str) -> None:
        """Start processing and enforce timeout; mark job failed on TimeoutError."""
        future = self.queue_job(job_id)
        try:
            future.result(timeout=self.settings.PROCESSING_TIMEOUT)
        except concurrent.futures.TimeoutError:
            # We cannot forcefully kill the thread; mark as failed and log.
            job = self.get_job(job_id)
            if job is not None:
                job.status = "failed"
                job.updated_at = datetime.now()
                job.error = f"Processing timed out after {self.settings.PROCESSING_TIMEOUT} seconds"

                # Track timeout (note: start_time not available here, will be tracked in _run_processing if needed)
                # For now, just log the timeout
                logger.error(
                    f"Processing timed out: {job.filename}",
                    extra={
                        "context": {
                            "job_id": job_id,
                            "filename": job.filename,
                            "timeout_seconds": self.settings.PROCESSING_TIMEOUT,
                        }
                    },
                )


# Convenience accessor
def get_processing_service() -> ProcessingService:
    return ProcessingService.get()
