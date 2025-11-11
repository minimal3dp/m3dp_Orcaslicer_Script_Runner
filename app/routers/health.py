"""Health check and root endpoints."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint providing API information."""
    settings = get_settings()
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "operational"}


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
