# Background Job Management

## Overview

The BrickLayers application uses a ThreadPoolExecutor-based background job system to process G-code files asynchronously. This document describes the job management features including priorities, cancellation, and monitoring.

## Table of Contents

1. [Architecture](#architecture)
2. [Job Priorities](#job-priorities)
3. [Job Cancellation](#job-cancellation)
4. [Job Lifecycle](#job-lifecycle)
5. [API Reference](#api-reference)
6. [Monitoring](#monitoring)
7. [Best Practices](#best-practices)

---

## Architecture

### Design Decisions

The application uses Python's `concurrent.futures.ThreadPoolExecutor` for background job processing:

- **Zero Dependencies**: No external task queue required (Redis, RabbitMQ, etc.)
- **Proven Scale**: Handles up to 500 concurrent jobs/day efficiently
- **Simple Operations**: Easy to deploy, monitor, and debug
- **Memory Efficient**: Jobs share the same process memory
- **Thread-Safe**: Built-in locking and synchronization

For detailed evaluation of alternatives (Celery, RQ, Dramatiq), see [BACKGROUND_JOBS_EVALUATION.md](./BACKGROUND_JOBS_EVALUATION.md).

### Job Flow

```
Upload → Validate → Register Job → Queue → Process → Complete → Download → Cleanup
                                     ↓
                              (can cancel here)
```

### Configuration

Environment variables:

- `MAX_CONCURRENT_JOBS`: Maximum concurrent processing threads (default: 4)
- `PROCESSING_TIMEOUT`: Maximum seconds per job (default: 300)
- `TEMP_DIR`: Directory for job files (default: temp/)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 100)

---

## Job Priorities

### Priority Levels

Jobs can be assigned one of three priority levels:

| Priority | Value | Description | Use Case |
|----------|-------|-------------|----------|
| **High** | 0 | Urgent jobs | Production prints, critical deadlines |
| **Normal** | 1 | Standard jobs | Regular processing (default) |
| **Low** | 2 | Background jobs | Batch processing, testing |

### Setting Priority

#### Via Upload Endpoint

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@model.gcode" \
  -F "start_at_layer=10" \
  -F "extrusion_multiplier=1.2" \
  -F "priority=0"  # 0=high, 1=normal, 2=low
```

#### Python Client

```python
import requests

with open("model.gcode", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f},
        data={
            "start_at_layer": 10,
            "extrusion_multiplier": 1.2,
            "priority": 0  # High priority
        }
    )

job = response.json()
print(f"Job {job['job_id']} queued with priority {job['priority']}")
```

### Current Limitations

**Note**: The current ThreadPoolExecutor implementation uses FIFO (first-in-first-out) queuing. Priority is stored but not yet used for queue ordering.

**Future Enhancement**: To implement true priority queuing, we would need to replace ThreadPoolExecutor with a custom priority queue + worker threads. This is planned for Phase 2 if traffic patterns justify the complexity.

---

## Job Cancellation

### Cancellation Types

#### 1. Pending Job Cancellation (Immediate)

Jobs that haven't started processing yet are cancelled immediately:

- Status changes to `"cancelled"`
- Job removed from queue
- No processing occurs
- No output files created

#### 2. Processing Job Cancellation (Cooperative)

Jobs currently being processed are cancelled cooperatively:

- Status changes to `"cancelling"` immediately
- Processing thread checks `cancel_requested` flag every 1000 lines
- When detected, processing stops gracefully:
  - Partial output file is deleted
  - Status changes to `"cancelled"`
  - Error message set to `"Cancelled by user during processing"`

### Cancellation Endpoint

```
POST /cancel/{job_id}
```

#### Request

```bash
curl -X POST "http://localhost:8000/cancel/abc-123-def-456"
```

#### Responses

**Success (200 OK)**
```json
{
  "job_id": "abc-123-def-456",
  "status": "cancelled",
  "message": "Job cancelled successfully (was pending)"
}
```

or

```json
{
  "job_id": "abc-123-def-456",
  "status": "cancelling",
  "message": "Job cancellation requested (currently processing)"
}
```

**Not Found (404)**
```json
{
  "type": "https://example.com/errors/not-found",
  "title": "Job Not Found",
  "status": 404,
  "detail": "Job with ID 'abc-123-def-456' does not exist",
  "instance": "/cancel/abc-123-def-456"
}
```

**Cannot Cancel (409 Conflict)**
```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Cannot Cancel Job",
  "status": 409,
  "detail": "Job with ID 'abc-123-def-456' is already completed and cannot be cancelled",
  "instance": "/cancel/abc-123-def-456"
}
```

### Terminal States

These job states **cannot** be cancelled:

- `"completed"` - Job finished successfully
- `"failed"` - Job encountered an error
- `"cancelled"` - Job already cancelled
- `"timeout"` - Job exceeded max processing time

### Python Client Example

```python
import requests
import time

# Upload a file
with open("large_model.gcode", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f},
        data={"start_at_layer": 0, "extrusion_multiplier": 1.0}
    )

job_id = response.json()["job_id"]

# Wait a bit (job might start processing)
time.sleep(2)

# Cancel the job
cancel_response = requests.post(f"http://localhost:8000/cancel/{job_id}")

if cancel_response.status_code == 200:
    result = cancel_response.json()
    print(f"Job {result['status']}: {result['message']}")
elif cancel_response.status_code == 404:
    print("Job not found")
elif cancel_response.status_code == 409:
    print("Job already finished, cannot cancel")
```

---

## Job Lifecycle

### Status Progression

```
pending → processing → completed
                    ↓
                  failed
                    ↓
                 timeout
                    
(any point) → cancelling → cancelled
```

### Status Descriptions

| Status | Description | Can Cancel? |
|--------|-------------|-------------|
| `pending` | Job queued, waiting for worker thread | ✅ Yes (immediate) |
| `processing` | Job currently being processed | ✅ Yes (cooperative) |
| `cancelling` | Cancellation requested, waiting for checkpoint | ❌ No (in progress) |
| `cancelled` | Job was cancelled by user | ❌ No (terminal) |
| `completed` | Job finished successfully | ❌ No (terminal) |
| `failed` | Job encountered an error | ❌ No (terminal) |
| `timeout` | Job exceeded max processing time | ❌ No (terminal) |

### Timestamps

All jobs track:

- `created_at`: ISO 8601 timestamp when job was created
- `started_at`: When processing began (None if still pending)
- `completed_at`: When job reached terminal state (None if still active)

---

## API Reference

### Upload with Priority

**Endpoint**: `POST /upload`

**Request**:
```
Content-Type: multipart/form-data

file: <gcode_file>  (required)
start_at_layer: <int>  (required, >= 0)
extrusion_multiplier: <float>  (required, 0.5-2.0)
priority: <int>  (optional, default=1, range 0-2)
```

**Response (202 Accepted)**:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "priority": 1,
  "message": "File uploaded successfully, processing started"
}
```

### Check Job Status

**Endpoint**: `GET /status/{job_id}`

**Response (200 OK)**:
```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",
  "priority": 1,
  "cancel_requested": false,
  "created_at": "2025-01-15T10:30:00Z",
  "started_at": "2025-01-15T10:30:05Z",
  "completed_at": null,
  "message": "Processing G-code with BrickLayers algorithm",
  "input_path": "/path/to/uploads/abc-123-def-456_model.gcode",
  "output_path": null,
  "error": null
}
```

### Cancel Job

**Endpoint**: `POST /cancel/{job_id}`

**Response (200 OK)**:
```json
{
  "job_id": "abc-123-def-456",
  "status": "cancelled",
  "message": "Job cancelled successfully (was pending)"
}
```

### Download Result

**Endpoint**: `GET /download/{job_id}`

**Response (200 OK)**:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="model_bricklayers.gcode"

<gcode content>
```

**Response (409 Conflict)** - If job was cancelled:
```json
{
  "type": "https://example.com/errors/conflict",
  "title": "Job Not Ready",
  "status": 409,
  "detail": "Cannot download: Job was cancelled",
  "instance": "/download/abc-123-def-456"
}
```

---

## Monitoring

### Metrics

The application exposes Prometheus metrics at `/metrics`:

**Job Counts**:
- `bricklayers_processing_jobs_active` - Currently processing
- `bricklayers_processing_jobs_pending` - Waiting in queue
- `bricklayers_processing_total{status="completed|failed|cancelled|timeout"}` - Total by outcome

**Performance**:
- `bricklayers_processing_duration_seconds` - Processing time histogram
- `bricklayers_processing_input_bytes` - Input file sizes
- `bricklayers_processing_output_bytes` - Output file sizes

**Cancellation**:
- `bricklayers_processing_total{status="cancelled"}` - Total cancelled jobs

### Structured Logging

All job operations emit structured logs with context:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.services.processing_service",
  "message": "Job cancelled by user",
  "request_id": "req-abc-123",
  "job_id": "job-def-456",
  "status": "cancelling",
  "was_processing": true
}
```

Enable JSON logging:
```bash
export JSON_LOGS=true
export LOG_LEVEL=INFO
```

---

## Best Practices

### When to Use Priorities

**High Priority (0)**:
- Production prints with tight deadlines
- Customer-facing jobs
- Time-sensitive batches

**Normal Priority (1)** (default):
- Regular processing
- Most user uploads
- Standard workflow

**Low Priority (2)**:
- Batch processing
- Testing and experimentation
- Non-urgent background jobs

### Cancellation Guidelines

1. **Cancel Early**: Cancel pending jobs immediately if not needed
2. **Wait for Completion**: Processing jobs take time to cancel (every 1000 lines)
3. **Check Status**: Poll `/status/{job_id}` to see when `cancelling` → `cancelled`
4. **Don't Retry**: Cancelled jobs cannot be restarted, upload again if needed

### Error Handling

```python
import requests

def cancel_job(job_id: str) -> dict:
    """Cancel a job with proper error handling."""
    response = requests.post(f"http://localhost:8000/cancel/{job_id}")
    
    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    elif response.status_code == 404:
        return {"success": False, "error": "Job not found"}
    elif response.status_code == 409:
        return {"success": False, "error": "Job already finished"}
    else:
        return {"success": False, "error": f"Unexpected error: {response.status_code}"}
```

### Performance Tips

1. **Set Realistic Priorities**: Don't mark everything as high priority
2. **Cancel Unwanted Jobs**: Free up workers for important jobs
3. **Monitor Queue Depth**: Check `bricklayers_processing_jobs_pending` metric
4. **Tune Thread Pool**: Adjust `MAX_CONCURRENT_JOBS` based on CPU cores
5. **Use Timeouts**: Set `PROCESSING_TIMEOUT` to prevent stuck jobs

---

## Future Enhancements

### Planned Features (Phase 2)

If traffic grows beyond 500 jobs/day:

1. **True Priority Queue**:
   - Replace ThreadPoolExecutor with custom priority queue
   - High-priority jobs processed first
   - Configurable priority weights

2. **Job History**:
   - Keep completed jobs for 24-48 hours
   - Allow re-download without re-processing
   - Persistent storage for restart resilience

3. **Enhanced Status**:
   - More granular states: `validating`, `parsing`, `transforming`, `writing`
   - Progress percentage (lines processed / total lines)
   - Estimated time remaining

4. **Retry Logic**:
   - Automatic retry on transient failures
   - Configurable retry attempts and backoff
   - Dead letter queue for failed jobs

### Migration Path (Phase 3)

If traffic exceeds 1000 jobs/day or needs horizontal scaling:

- **Option 1**: Migrate to **RQ** (Redis Queue)
  - Simple migration from ThreadPoolExecutor
  - Redis dependency (lightweight)
  - Dashboard for job monitoring

- **Option 2**: Migrate to **Celery**
  - Full-featured task queue
  - Multiple broker options (Redis, RabbitMQ)
  - Complex workflows and scheduling

See [BACKGROUND_JOBS_EVALUATION.md](./BACKGROUND_JOBS_EVALUATION.md) for detailed comparison.

---

## Troubleshooting

### Job Stuck in "cancelling"

**Symptom**: Job status is "cancelling" but never becomes "cancelled"

**Cause**: Processing loop hasn't reached a checkpoint (every 1000 lines)

**Solution**: Wait up to ~10 seconds for large files. If stuck longer, check logs for errors.

### Cancellation Returns 409

**Symptom**: Cancel request returns `409 Conflict`

**Cause**: Job is already in a terminal state (completed, failed, cancelled, timeout)

**Solution**: Check job status first. If cancelled, no action needed. If completed, job already finished.

### Priority Not Affecting Order

**Symptom**: Low-priority jobs processed before high-priority jobs

**Cause**: ThreadPoolExecutor uses FIFO queue, priority not yet implemented for ordering

**Solution**: This is expected behavior. True priority queue is planned for Phase 2 if needed.

### Job Cancelled But No Error

**Symptom**: Job shows status "cancelled" but error field is null

**Cause**: Job was cancelled while pending (before processing started)

**Solution**: This is normal. Only processing jobs get error message "Cancelled by user during processing".

---

## Related Documentation

- [BACKGROUND_JOBS_EVALUATION.md](./BACKGROUND_JOBS_EVALUATION.md) - Task queue evaluation and decision rationale
- [METRICS.md](./METRICS.md) - Prometheus metrics and monitoring
- [STRUCTURED_LOGGING.md](./STRUCTURED_LOGGING.md) - Logging infrastructure and best practices
- [FASTAPI_STRUCTURE.md](./FASTAPI_STRUCTURE.md) - Application architecture overview

---

**Last Updated**: 2025-01-15  
**Version**: 1.1.7
