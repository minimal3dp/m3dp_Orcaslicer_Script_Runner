"""Tests for upload endpoint parameter validation and edge cases.

This module tests:
- Invalid parameter ranges (negative start_at_layer, out-of-range multiplier)
- Malformed requests (missing required fields)
- Edge cases (empty filenames, special characters, invalid extensions)
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so 'app' package is importable when running tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402

client = TestClient(app)


def _make_minimal_gcode() -> bytes:
    """Create minimal valid G-code for testing."""
    return b""";LAYER_CHANGE\n;Z:0.2\nG1 X0 Y0 E0 F1800\nG1 X10 Y10 E1 F1800\n"""


def test_negative_start_at_layer_rejected():
    """Negative start_at_layer should be rejected with 422."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("test.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": -1, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = resp.json()
    assert "detail" in body


def test_extrusion_multiplier_below_range_rejected():
    """Extrusion multiplier below 1.0 should be rejected with 422."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("test.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 0.5}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_extrusion_multiplier_above_range_rejected():
    """Extrusion multiplier above 1.2 should be rejected with 422."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("test.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 2.0}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_missing_file_rejected():
    """Request without file should be rejected with 422."""
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", data=data)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_file_extension_rejected():
    """File with invalid extension should be rejected with 400."""
    content = _make_minimal_gcode()
    files = {"file": ("test.txt", content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["status"] == status.HTTP_400_BAD_REQUEST
    assert "extension" in body["detail"].lower()


def test_empty_file_rejected():
    """Empty file should be rejected with 400."""
    files = {"file": ("test.gcode", b"", "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["status"] == status.HTTP_400_BAD_REQUEST
    assert "empty" in body["detail"].lower()


def test_non_gcode_content_rejected():
    """File without G-code patterns should be rejected with 400."""
    files = {"file": ("test.gcode", b"This is not G-code content", "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["status"] == status.HTTP_400_BAD_REQUEST
    assert "g-code" in body["detail"].lower()


def test_filename_with_path_traversal_rejected():
    """Filename with path traversal should be rejected with 400."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("../../../etc/passwd.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["status"] == status.HTTP_400_BAD_REQUEST


def test_filename_with_null_bytes_rejected():
    """Filename with null bytes should be rejected with 400."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("test\x00.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["status"] == status.HTTP_400_BAD_REQUEST


def test_valid_edge_case_parameters():
    """Boundary values for parameters should be accepted."""
    gcode_content = _make_minimal_gcode()

    # Test minimum valid values
    files = {"file": ("test.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 0, "extrusion_multiplier": 1.0}
    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_201_CREATED

    # Test maximum valid values
    files = {"file": ("test2.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 100, "extrusion_multiplier": 1.2}
    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_201_CREATED


def test_filename_with_spaces_accepted():
    """Filename with spaces should be accepted and sanitized."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("my test file.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["job_id"]
    assert body["filename"] == "my test file.gcode"


def test_filename_with_unicode_characters():
    """Filename with unicode characters should be handled appropriately."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("tëst_fîlé.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 3, "extrusion_multiplier": 1.05}

    resp = client.post("/api/v1/upload", files=files, data=data)
    # Should either accept or reject cleanly (not crash)
    assert resp.status_code in {
        status.HTTP_201_CREATED,
        status.HTTP_400_BAD_REQUEST,
    }
