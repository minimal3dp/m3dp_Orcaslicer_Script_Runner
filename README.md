# BrickLayers Web Application

Process G-code files with the BrickLayers post-processing script via a simple FastAPI backend. Upload a G-code file, the server runs BrickLayers in the background, and you can download the processed result when it’s ready.

## Features

- Upload G-code files (.gcode, .gco, .g) with validation
- Background processing using the BrickLayers engine
- **Job priorities** (0=high, 1=normal, 2=low) for workflow control
- **Job cancellation** with cooperative graceful handling
- Job lifecycle and status endpoint
- Download processed G-code when complete
- **Structured logging** with JSON output and request tracking
- **Prometheus metrics** for monitoring and observability
- Configurable limits (file size, timeout, concurrency)

## Project structure

- `app/main.py` – FastAPI app setup and router registration
- `app/routers/upload.py` – POST /api/v1/upload
- `app/routers/jobs.py` – GET /api/v1/status/{job_id}, GET /api/v1/download/{job_id}
- `app/models/processing.py` – Request/response schemas and JobStatus
- `app/services/file_service.py` – File validation and storage helpers
- `app/services/processing_service.py` – Background processing and job tracking
- `app/core/bricklayers_core.py` – BrickLayers processing engine

## API overview

- POST `/api/v1/upload`
	- Form fields: `file` (G-code), `start_at_layer` (int, default 3), `extrusion_multiplier` (float, 1.0–1.2, default 1.05), `priority` (int, 0-2, default 1)
	- Response: `202 Accepted` with `{ job_id, status, priority, ... }`
	- Errors: `400` for validation errors; `413` if file exceeds `MAX_UPLOAD_SIZE`

- GET `/api/v1/status/{job_id}`
	- Response: `200 OK` with `{ job_id, status, priority, cancel_requested, created_at, started_at, completed_at, error, ... }`

- POST `/api/v1/cancel/{job_id}`
	- Cancels a pending or processing job
	- Response: `200 OK` with `{ job_id, status, message }`
	- Errors: `404` if job not found; `409` if job already completed/failed

- GET `/api/v1/download/{job_id}`
	- Response: `200 OK` streaming processed G-code with Content-Disposition filename
	- Errors: `409` if not completed; `404` if job/file missing

- GET `/metrics`
	- Prometheus-compatible metrics endpoint for monitoring

See [docs/BACKGROUND_JOBS.md](docs/BACKGROUND_JOBS.md) for detailed API documentation.

## Run locally

Requirements: Python 3.12+, [uv](https://github.com/astral-sh/uv)

Optional quickstart commands:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -q

# Start the API
uv run uvicorn app.main:app --reload --port 8000

# Open docs
open http://127.0.0.1:8000/docs
```

## Testing

- Integration tests live in `tests/`
- Example: `tests/test_upload_process_download.py` verifies upload → status → download
- Run tests with `uv run pytest`

## Configuration

Configure via environment variables (defaults in `app/config/settings.py`):

- `MAX_UPLOAD_SIZE` (bytes) – default 50MB
- `PROCESSING_TIMEOUT` (seconds) – default 15 minutes
- `MAX_CONCURRENT_JOBS` – default 5
- `UPLOAD_DIR`, `OUTPUT_DIR` – default `temp/uploads`, `temp/outputs`
- `FILE_RETENTION_HOURS` – age after which temp files are deleted by the cleanup task (default 24h)
- `CLEANUP_INTERVAL_MINUTES` – how often the cleanup task runs (default 60m)
- `JSON_LOGS` (true/false) – enable JSON-formatted structured logging (default false)
- `LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR) – logging verbosity (default INFO)
- CORS settings via `CORS_ORIGINS`, `CORS_ALLOW_*`

## Documentation

- [BACKGROUND_JOBS.md](docs/BACKGROUND_JOBS.md) - Job priorities, cancellation, and management
- [STRUCTURED_LOGGING.md](docs/STRUCTURED_LOGGING.md) - Logging infrastructure and best practices
- [METRICS.md](docs/METRICS.md) - Prometheus metrics, queries, and dashboards
- [BACKGROUND_JOBS_EVALUATION.md](docs/BACKGROUND_JOBS_EVALUATION.md) - Task queue evaluation and decision rationale

## Notes and known gaps

- Cleanup behavior:
	- After a successful download, the original uploaded file is removed.
	- A background cleanup task periodically deletes files older than `FILE_RETENTION_HOURS` from upload and output directories.

## License

This project integrates the BrickLayers script. See `scripts/BrickLayers/` for license details.
