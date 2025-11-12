"""Tests for upload limits and error codes (e.g., oversized files).

This module focuses on verifying that oversized uploads return HTTP 413
(Payload Too Large) as documented.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so 'app' package is importable when running tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@contextmanager
def temporary_max_upload_size(bytes_value: int):
    """Temporarily set MAX_UPLOAD_SIZE env var and clear settings cache."""
    from app.config import get_settings

    old = os.environ.get("MAX_UPLOAD_SIZE")
    os.environ["MAX_UPLOAD_SIZE"] = str(bytes_value)
    # Clear cached settings so new value is picked up by services
    get_settings.cache_clear()
    try:
        yield
    finally:
        # Restore original value and clear cache again
        if old is None:
            os.environ.pop("MAX_UPLOAD_SIZE", None)
        else:
            os.environ["MAX_UPLOAD_SIZE"] = old
        get_settings.cache_clear()


def test_oversized_upload_returns_413():
    # Use small limit to avoid creating huge payloads during tests
    with temporary_max_upload_size(1024):  # 1 KiB
        from app.main import app

        client = TestClient(app)
        # Create a 2 KiB payload with valid G-code patterns that exceeds the temporary limit
        # Repeat valid G-code lines to exceed size without being too large for the test
        gcode_line = b";LAYER_CHANGE\nG1 X0 Y0 Z0.2 E1 F1800\nM106 S255\n"
        content = gcode_line * 50  # ~2 KiB of valid G-code
        files = {"file": ("too_big.gcode", content, "text/plain")}
        data = {"start_at_layer": 0, "extrusion_multiplier": 1.05}

        resp = client.post("/api/v1/upload", files=files, data=data)
        assert resp.status_code == status.HTTP_413_CONTENT_TOO_LARGE, resp.text

    body = resp.json()
    # ProblemDetails shape: title/status/detail
    assert (
        body["title"].lower().startswith("file too large") or "too large" in body["detail"].lower()
    )
    assert body["status"] == status.HTTP_413_CONTENT_TOO_LARGE
    assert "exceeds maximum allowed size" in body["detail"].lower()
