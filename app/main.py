"""
BrickLayers Web Application - Main FastAPI Application

This module serves as the entry point for the BrickLayers web application.
It provides a REST API for uploading G-code files, processing them with
the BrickLayers post-processing script, and downloading the results.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.routers import health_router, jobs_router, metrics_router, upload_router
from app.services.cleanup_service import get_cleanup_service

# Initialize settings
settings = get_settings()

# Configure structured logging
configure_logging(
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Manage application lifespan: startup and shutdown events.

    This replaces the deprecated @app.on_event decorators with the modern
    lifespan context manager pattern.
    """
    # Startup: start background cleanup service
    get_cleanup_service().start_background()
    yield
    # Shutdown: stop background cleanup service
    get_cleanup_service().stop_background()


# Create FastAPI application instance with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="Upload G-code files and apply BrickLayers post-processing",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add request logging middleware (before CORS)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(jobs_router)
app.include_router(metrics_router)
