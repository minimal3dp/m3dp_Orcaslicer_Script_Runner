"""Application configuration settings.

This module defines all configuration settings for the BrickLayers web application.
Settings can be overridden via environment variables.
"""

import os
from functools import lru_cache
from pathlib import Path


class Settings:
    """Application settings with environment variable overrides."""

    def __init__(self):
        """Initialize settings and create necessary directories."""
        # Application Info
        self.APP_NAME: str = "BrickLayers Web Application"
        self.APP_VERSION: str = "0.1.0"
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

        # API Configuration
        self.API_V1_PREFIX: str = "/api/v1"
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # CORS Configuration
        self.CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
        self.CORS_ALLOW_CREDENTIALS: bool = True
        self.CORS_ALLOW_METHODS: list[str] = ["*"]
        self.CORS_ALLOW_HEADERS: list[str] = ["*"]

        # File Upload Configuration
        self.MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 50MB
        self.ALLOWED_EXTENSIONS: set[str] = {".gcode", ".gco", ".g"}
        self.UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "temp/uploads"))
        self.OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "temp/outputs"))

        # Processing Configuration
        self.PROCESSING_TIMEOUT: int = int(os.getenv("PROCESSING_TIMEOUT", str(15 * 60)))  # 15 min
        self.MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

        # File Cleanup Configuration
        self.FILE_RETENTION_HOURS: int = int(os.getenv("FILE_RETENTION_HOURS", "24"))
        self.CLEANUP_INTERVAL_MINUTES: int = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "60"))

        # Logging Configuration
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        self.LOG_LEVEL: str = log_level_str if log_level_str in valid_levels else "INFO"

        # BrickLayers Default Parameters
        self.DEFAULT_START_AT_LAYER: int = 3
        self.DEFAULT_EXTRUSION_MULTIPLIER: float = 1.05
        self.MIN_EXTRUSION_MULTIPLIER: float = 1.0
        self.MAX_EXTRUSION_MULTIPLIER: float = 1.2

        # Create necessary directories
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
