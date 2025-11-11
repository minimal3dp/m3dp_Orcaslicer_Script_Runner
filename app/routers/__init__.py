"""API routers package."""

from app.routers.health import router as health_router
from app.routers.upload import router as upload_router

__all__ = ["health_router", "upload_router"]
