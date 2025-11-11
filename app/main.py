"""
BrickLayers Web Application - Main FastAPI Application

This module serves as the entry point for the BrickLayers web application.
It provides a REST API for uploading G-code files, processing them with
the BrickLayers post-processing script, and downloading the results.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health_router

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

# TODO: Add routes for:
# - File upload (/upload)
# - Processing status (/status/{job_id})
# - File download (/download/{job_id})
