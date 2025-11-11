"""
BrickLayers Web Application - Main FastAPI Application

This module serves as the entry point for the BrickLayers web application.
It provides a REST API for uploading G-code files, processing them with
the BrickLayers post-processing script, and downloading the results.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application instance
app = FastAPI(
    title="BrickLayers Web Application",
    description="Upload G-code files and apply BrickLayers post-processing",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "BrickLayers Web Application API",
        "version": "0.1.0",
        "status": "online",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


# TODO: Add routes for:
# - File upload (/upload)
# - Processing status (/status/{job_id})
# - File download (/download/{job_id})
# - Parameter configuration
