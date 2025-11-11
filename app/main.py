"""
BrickLayers Web Application - Main FastAPI Application

This module serves as the entry point for the BrickLayers web application.
It provides a REST API for uploading G-code files, processing them with
the BrickLayers post-processing script, and downloading the results.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health_router, jobs_router, upload_router
from app.services.cleanup_service import get_cleanup_service

# Initialize settings
settings = get_settings()

# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Upload G-code files and apply BrickLayers post-processing",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

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


@app.on_event("startup")
def _startup_cleanup():  # pragma: no cover - FastAPI lifecycle
    get_cleanup_service().start_background()


@app.on_event("shutdown")
def _shutdown_cleanup():  # pragma: no cover - FastAPI lifecycle
    get_cleanup_service().stop_background()


# Background cleanup thread started on startup; see CleanupService for implementation.
