# FastAPI Project Structure

This document describes the FastAPI project structure for the BrickLayers web application.

## Directory Structure

```
app/
├── main.py                 # Application entry point
├── config/                 # Configuration management
│   ├── __init__.py        # Package initialization
│   └── settings.py        # Application settings with environment variables
├── core/                  # Core business logic
│   ├── __init__.py
│   ├── api.py            # Public API exports
│   └── bricklayers_core.py  # BrickLayers processing engine
├── models/                # Pydantic models for validation
│   ├── __init__.py
│   └── processing.py     # Processing request/response schemas
├── routers/               # API endpoint routers
│   ├── __init__.py
│   └── health.py         # Health check and root endpoints
└── services/              # Business logic services
    └── __init__.py
```

## Architecture Overview

### Configuration (`app/config/`)

**Purpose**: Centralize all application configuration with environment variable support.

- **settings.py**: `Settings` class with all configuration parameters
  - Application info (name, version, debug mode)
  - API configuration (host, port, prefix)
  - CORS configuration (origins, methods, headers)
  - File upload limits and allowed extensions
  - Processing configuration (timeout, max concurrent jobs)
  - File cleanup settings
  - Logging configuration
  - BrickLayers default parameters

**Environment Variables**: All settings can be overridden via environment variables:
- `DEBUG`: Enable debug mode (default: False)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: *)
- `MAX_UPLOAD_SIZE`: Maximum upload size in bytes (default: 50MB)
- `UPLOAD_DIR`: Upload directory path (default: temp/uploads)
- `OUTPUT_DIR`: Output directory path (default: temp/outputs)
- `LOG_LEVEL`: Logging level (default: INFO)

### Models (`app/models/`)

**Purpose**: Define Pydantic schemas for request/response validation and documentation.

- **processing.py**:
  - `JobStatus`: Enum for job states (pending, processing, completed, failed)
  - `ProcessingRequest`: Parameters for G-code processing
    - `start_at_layer`: Layer to start BrickLayers (default: 3, min: 0)
    - `extrusion_multiplier`: Multiplier for brick layers (default: 1.05, range: 1.0-1.2)
  - `ProcessingResponse`: Job creation response with job_id, status, timestamp
  - `ErrorResponse`: Standardized error format

### Routers (`app/routers/`)

**Purpose**: Organize API endpoints into logical groups.

- **health.py**:
  - `GET /`: Root endpoint with API information
  - `GET /health`: Health check for monitoring

**Future routers**:
- `upload.py`: File upload endpoint
- `processing.py`: Processing status and job management
- `download.py`: Processed file download

### Services (`app/services/`)

**Purpose**: Implement business logic separate from HTTP handling.

**Planned services**:
- `file_service.py`: File validation, storage, cleanup
- `processing_service.py`: Job queue, BrickLayers processing orchestration
- `job_manager.py`: Job tracking and status management

### Core (`app/core/`)

**Purpose**: Core processing logic independent of web framework.

- **bricklayers_core.py**: G-code processing engine (v1.1.1)
- **api.py**: Public API exports for core functionality

## Application Flow

1. **Startup**:
   - Load settings from environment
   - Create upload/output directories
   - Initialize FastAPI app with CORS
   - Register routers

2. **Request Handling**:
   - Router receives request
   - Pydantic validates request data
   - Service layer implements business logic
   - Core engine processes G-code
   - Response formatted with Pydantic models

3. **Configuration**:
   - Singleton settings instance (`get_settings()`)
   - Cached for performance
   - Environment variables override defaults

## Running the Application

### Development Mode

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Environment Variables

```bash
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
export MAX_UPLOAD_SIZE=104857600  # 100MB
export DEBUG=false
uv run uvicorn app.main:app
```

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing Endpoints

```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health
```

## Development Notes

### Adding New Endpoints

1. Create router in `app/routers/`
2. Define models in `app/models/`
3. Implement service in `app/services/`
4. Register router in `app/main.py`

### Adding Configuration

1. Add setting to `Settings` class in `app/config/settings.py`
2. Document environment variable
3. Use via `get_settings()` in code

### CORS Configuration

Current configuration allows all origins (`*`) for development. For production:

```bash
export CORS_ORIGINS="https://production.com,https://app.production.com"
```

Or update `settings.py` default value.

## Next Steps

See TODO.md for remaining tasks:
- Task 1.1.3: Implement file upload endpoint
- Task 1.1.4: Implement processing logic
- Task 1.1.5: Implement file download endpoint
- Task 1.1.6: Add file cleanup management
