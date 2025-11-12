"""Application metrics for monitoring and observability.

This module provides Prometheus-compatible metrics for tracking:
- HTTP request metrics (count, duration, status codes)
- Upload metrics (file sizes, validation failures)
- Processing metrics (job queue depth, processing times, success/failure rates)
- Cleanup metrics (files deleted, bytes freed)
- System health metrics
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from prometheus_client import Counter, Gauge, Histogram, Info

if TYPE_CHECKING:
    from app.services.processing_service import ProcessingJob

# Application info
app_info = Info("app", "Application information")
app_info.info(
    {
        "name": "bricklayers_web",
        "version": "1.1.7",
        "description": "BrickLayers G-code post-processing web service",
    }
)

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Upload metrics
uploads_total = Counter(
    "uploads_total",
    "Total file uploads",
    ["status"],  # success, failed_validation, failed_size, failed_error
)

upload_file_size_bytes = Histogram(
    "upload_file_size_bytes",
    "Size of uploaded files in bytes",
    buckets=(
        100_000,  # 100KB
        500_000,  # 500KB
        1_000_000,  # 1MB
        5_000_000,  # 5MB
        10_000_000,  # 10MB
        25_000_000,  # 25MB
        50_000_000,  # 50MB
        100_000_000,  # 100MB
    ),
)

upload_validation_failures = Counter(
    "upload_validation_failures_total",
    "Total upload validation failures",
    ["reason"],  # file_too_large, invalid_extension, invalid_content, etc.
)

# Processing job metrics
processing_jobs_total = Counter(
    "processing_jobs_total",
    "Total processing jobs",
    ["status"],  # completed, failed, timeout
)

processing_jobs_active = Gauge(
    "processing_jobs_active",
    "Number of jobs currently being processed",
)

processing_jobs_pending = Gauge(
    "processing_jobs_pending",
    "Number of jobs waiting to be processed",
)

processing_duration_seconds = Histogram(
    "processing_duration_seconds",
    "Processing duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

processing_input_size_bytes = Histogram(
    "processing_input_size_bytes",
    "Size of input files processed in bytes",
    buckets=(
        100_000,  # 100KB
        500_000,  # 500KB
        1_000_000,  # 1MB
        5_000_000,  # 5MB
        10_000_000,  # 10MB
        25_000_000,  # 25MB
        50_000_000,  # 50MB
        100_000_000,  # 100MB
    ),
)

processing_output_size_bytes = Histogram(
    "processing_output_size_bytes",
    "Size of output files in bytes",
    buckets=(
        100_000,  # 100KB
        500_000,  # 500KB
        1_000_000,  # 1MB
        5_000_000,  # 5MB
        10_000_000,  # 10MB
        25_000_000,  # 25MB
        50_000_000,  # 50MB
        100_000_000,  # 100MB
    ),
)

# Download metrics
downloads_total = Counter(
    "downloads_total",
    "Total file downloads",
    ["status"],  # success, failed_not_found, failed_not_ready
)

# Cleanup metrics
cleanup_runs_total = Counter(
    "cleanup_runs_total",
    "Total cleanup service runs",
)

cleanup_files_deleted = Counter(
    "cleanup_files_deleted_total",
    "Total files deleted by cleanup service",
)

cleanup_bytes_freed = Counter(
    "cleanup_bytes_freed_total",
    "Total bytes freed by cleanup service",
)

cleanup_errors = Counter(
    "cleanup_errors_total",
    "Total errors during cleanup",
)

# System health metrics
system_memory_usage_bytes = Gauge(
    "system_memory_usage_bytes",
    "Current memory usage in bytes",
)

system_disk_usage_bytes = Gauge(
    "system_disk_usage_bytes",
    "Current disk usage in bytes for temp directories",
)


class MetricsTracker:
    """Helper class for tracking metrics with automatic timing."""

    @staticmethod
    def track_upload_success(file_size_bytes: int) -> None:
        """Track successful upload."""
        uploads_total.labels(status="success").inc()
        upload_file_size_bytes.observe(file_size_bytes)

    @staticmethod
    def track_upload_failure(reason: str) -> None:
        """Track failed upload."""
        uploads_total.labels(status=f"failed_{reason}").inc()
        upload_validation_failures.labels(reason=reason).inc()

    @staticmethod
    def track_processing_started(_job: ProcessingJob) -> float:
        """Track processing start and return start time."""
        processing_jobs_active.inc()
        return time.time()

    @staticmethod
    def track_processing_completed(
        start_time: float,
        input_size_bytes: int,
        output_size_bytes: int,
    ) -> None:
        """Track successful processing completion."""
        duration = time.time() - start_time
        processing_jobs_total.labels(status="completed").inc()
        processing_jobs_active.dec()
        processing_duration_seconds.observe(duration)
        processing_input_size_bytes.observe(input_size_bytes)
        processing_output_size_bytes.observe(output_size_bytes)

    @staticmethod
    def track_processing_failed(start_time: float, reason: str = "error") -> None:
        """Track failed processing."""
        duration = time.time() - start_time
        processing_jobs_total.labels(status=reason).inc()
        processing_jobs_active.dec()
        processing_duration_seconds.observe(duration)

    @staticmethod
    def track_download_success() -> None:
        """Track successful download."""
        downloads_total.labels(status="success").inc()

    @staticmethod
    def track_download_failure(reason: str) -> None:
        """Track failed download."""
        downloads_total.labels(status=f"failed_{reason}").inc()

    @staticmethod
    def update_job_queue_depth(pending_count: int) -> None:
        """Update job queue depth gauge."""
        processing_jobs_pending.set(pending_count)

    @staticmethod
    def track_cleanup_run(files_deleted: int, bytes_freed: int) -> None:
        """Track cleanup service run."""
        cleanup_runs_total.inc()
        cleanup_files_deleted.inc(files_deleted)
        cleanup_bytes_freed.inc(bytes_freed)

    @staticmethod
    def track_cleanup_error() -> None:
        """Track cleanup error."""
        cleanup_errors.inc()

    @staticmethod
    def update_system_metrics(memory_bytes: int, disk_bytes: int) -> None:
        """Update system health metrics."""
        system_memory_usage_bytes.set(memory_bytes)
        system_disk_usage_bytes.set(disk_bytes)


# Convenience instance
metrics = MetricsTracker()
