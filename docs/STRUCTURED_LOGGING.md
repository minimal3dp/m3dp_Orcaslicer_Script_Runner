# Structured Logging

## Overview

The application implements comprehensive structured logging with JSON formatting, request ID tracking, and performance metrics. This enables better observability in production and easier debugging during development.

## Features

### 1. Dual Logging Formats

**Production (JSON)**:
```json
{
  "timestamp": "2025-11-11T12:34:56.789Z",
  "level": "INFO",
  "logger": "app.routers.upload",
  "message": "File uploaded and queued: 3DBenchy.gcode",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "job_id": "abc123",
    "filename": "3DBenchy.gcode",
    "file_size_bytes": 1048576,
    "file_size_mb": 1.0,
    "start_at_layer": 5,
    "extrusion_multiplier": 1.2
  }
}
```

**Development (Human-Readable)**:
```
2025-11-11 12:34:56,789 [550e8400-e29b-41d4-a716-446655440000] INFO app.routers.upload - File uploaded and queued: 3DBenchy.gcode
```

### 2. Request ID Tracking

Every HTTP request gets a unique request ID that flows through all logs:

- Automatically generated UUID for each request
- Can be provided by client via `X-Request-ID` header
- Injected into all log records via `ContextVar`
- Returned in response `X-Request-ID` header
- Enables distributed tracing across services

### 3. Performance Metrics

**Automatic Request Timing**:
```json
{
  "timestamp": "2025-11-11T12:34:57.123Z",
  "level": "INFO",
  "logger": "app.middleware.logging",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "method": "POST",
    "path": "/api/v1/upload",
    "status_code": 201,
    "duration_ms": 334,
    "client_ip": "192.168.1.100"
  }
}
```

**Operation Timing with PerformanceLogger**:
```python
with PerformanceLogger(
    logger=logger,
    operation="process_gcode_abc123",
    extra_context={"job_id": "abc123", "filename": "test.gcode"}
):
    # ... your code ...
    pass

# Logs automatically:
# "Operation completed: process_gcode_abc123" with duration_ms
```

### 4. Contextual Metadata

All log messages include rich context:

**Upload Events**:
- `job_id`, `filename`, `file_size_bytes`, `file_size_mb`
- Processing parameters: `start_at_layer`, `extrusion_multiplier`

**Processing Events**:
- `job_id`, `filename`, `input_size_bytes`, `output_size_bytes`
- `duration_ms`, `size_change_percent`

**Download Events**:
- `job_id`, `filename`, `output_filename`
- `file_size_bytes`, `file_size_mb`

**Error Events**:
- `job_id`, `filename`, `error` message
- Stack traces (with `exc_info=True`)

## Configuration

### Environment Variables

```bash
# Enable JSON logging (default: false)
JSON_LOGS=true

# Set log level (default: INFO)
LOG_LEVEL=DEBUG
```

### Application Setup

```python
from app.logging_config import configure_logging

# Configure at application startup
configure_logging(
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    log_level=os.getenv("LOG_LEVEL", "INFO")
)
```

### Middleware Setup

```python
from app.middleware.logging import RequestLoggingMiddleware

# Add middleware to FastAPI app
app.add_middleware(RequestLoggingMiddleware)
```

## Usage Examples

### Basic Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Simple log
logger.info("Processing started")

# With context
logger.info(
    f"Processing started: {filename}",
    extra={
        "context": {
            "job_id": job_id,
            "filename": filename,
            "input_size_bytes": size
        }
    }
)
```

### Performance Logging

```python
from app.logging_config import PerformanceLogger

with PerformanceLogger(
    logger=logger,
    operation=f"process_{job_id}",
    extra_context={"job_id": job_id}
):
    # Your timed operation
    result = expensive_operation()
```

### Error Logging with Context

```python
try:
    process_file()
except Exception as e:
    logger.error(
        f"Processing failed: {filename}",
        extra={
            "context": {
                "job_id": job_id,
                "filename": filename,
                "error": str(e)
            }
        },
        exc_info=True  # Include stack trace
    )
```

### Accessing Request ID in Handlers

```python
from app.middleware.logging import get_request_id_from_request

async def my_handler(request: Request):
    request_id = get_request_id_from_request(request)
    # Use request_id if needed
```

## Benefits

### Production

1. **Machine-Parseable**: JSON logs can be ingested by log aggregation tools (ELK, Splunk, CloudWatch)
2. **Distributed Tracing**: Request IDs enable tracking across microservices
3. **Metrics**: Automatic performance metrics for monitoring and alerting
4. **Debugging**: Rich context in every log message

### Development

1. **Human-Readable**: Clear format with request IDs for following request flow
2. **Rich Context**: All relevant data in each log entry
3. **Performance Insights**: Automatic timing of operations
4. **Error Tracking**: Full stack traces with contextual information

## Log Analysis Examples

### Find All Logs for a Request

```bash
# Using jq with JSON logs
cat app.log | jq 'select(.request_id == "550e8400-e29b-41d4-a716-446655440000")'

# Using grep with human-readable logs
grep "550e8400-e29b-41d4-a716-446655440000" app.log
```

### Track Processing Performance

```bash
# Extract all processing durations
cat app.log | jq 'select(.message | contains("Operation completed")) | {operation: .context.operation, duration_ms: .context.duration_ms}'
```

### Monitor Error Rates

```bash
# Count errors by type
cat app.log | jq 'select(.level == "ERROR") | .context.error' | sort | uniq -c
```

### Analyze File Sizes

```bash
# Get upload size statistics
cat app.log | jq 'select(.message | contains("File uploaded")) | .context.file_size_mb' | jq -s 'add/length'
```

## Architecture

### Components

1. **`app/logging_config.py`**
   - `StructuredFormatter`: JSON formatter
   - `SimpleStructuredFormatter`: Human-readable formatter
   - `configure_logging()`: Application setup
   - `PerformanceLogger`: Context manager for timing
   - Metric helpers: `log_upload_metrics()`, `log_processing_metrics()`, `log_request_metrics()`

2. **`app/middleware/logging.py`**
   - `RequestLoggingMiddleware`: Request ID injection and metrics
   - Automatic request/response logging
   - Exception handling and logging

3. **Context Variables**
   - `request_id_var`: Current request ID (thread-safe, async-safe)
   - `user_id_var`: Future user context support

### Data Flow

```
1. Request arrives → RequestLoggingMiddleware
2. Generate/extract request ID
3. Store in ContextVar (request_id_var)
4. Store in request.state.request_id
5. Process request (all logs include request_id)
6. Log request metrics (method, path, status, duration)
7. Add X-Request-ID to response headers
8. Return response
```

## Future Enhancements

- OpenTelemetry integration for distributed tracing
- Metrics export to Prometheus
- Correlation with application performance monitoring (APM)
- User context tracking (when authentication added)
- Sampling for high-volume endpoints
