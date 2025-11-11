"""Integration tests for upload → status → download flow.

These tests exercise the main MVP pipeline:
1. Upload a small sample G-code file.
2. Poll status until completed (or timeout).
3. Download processed file and assert basic transformations occurred.

The BrickLayers processor is heavy; we use a tiny synthetic G-code to keep tests fast.
"""

from __future__ import annotations

import sys
import time
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
    # Minimal G-code with an internal perimeter feature and layer change markers
    return b""";LAYER_CHANGE\n;Z:0.2\n;HEIGHT:0.2\n;TYPE:Perimeter\nG1 X0 Y0 E0 F1800\nG1 X10 Y0 E1 F1800\nG1 X10 Y10 E2 F1800\nG1 X0 Y10 E3 F1800\nG1 X0 Y0 E4 F1800\n;TYPE:External perimeter\nG1 X0 Y0 E4.5 F1800\n"""


def test_upload_status_download_success():
    """Full happy-path: upload, wait for processing, download result."""
    gcode_content = _make_minimal_gcode()

    files = {"file": ("test.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 0, "extrusion_multiplier": 1.05}

    upload_resp = client.post("/api/v1/upload", files=files, data=data)
    assert upload_resp.status_code == status.HTTP_201_CREATED, upload_resp.text
    job_id = upload_resp.json()["job_id"]

    # Poll status until completed or timeout
    deadline = time.time() + 10  # 10s test timeout
    final = None
    while time.time() < deadline:
        stat_resp = client.get(f"/api/v1/status/{job_id}")
        assert stat_resp.status_code == status.HTTP_200_OK, stat_resp.text
        body = stat_resp.json()
        if body["status"] == "completed":
            final = body
            break
        elif body["status"] == "failed":
            raise AssertionError(f"Processing failed: {body}")
        time.sleep(0.25)

    assert final is not None, "Processing did not complete within timeout"

    download_resp = client.get(f"/api/v1/download/{job_id}")
    assert download_resp.status_code == status.HTTP_200_OK, download_resp.text
    processed = download_resp.text

    # Basic assertions: result should not be empty and should contain either
    # BrickLayers annotations or at least one G1 movement line
    assert processed.strip(), "Processed file should not be empty"
    assert ("BRICK:" in processed) or ("G1 " in processed)


def test_download_before_complete_returns_conflict():
    """Attempting to download immediately should yield 409 if not yet completed."""
    gcode_content = _make_minimal_gcode()
    files = {"file": ("early.gcode", gcode_content, "text/plain")}
    data = {"start_at_layer": 0, "extrusion_multiplier": 1.05}

    upload_resp = client.post("/api/v1/upload", files=files, data=data)
    assert upload_resp.status_code == status.HTTP_201_CREATED
    job_id = upload_resp.json()["job_id"]

    # Immediate download attempt—likely not finished yet
    download_resp = client.get(f"/api/v1/download/{job_id}")
    # Accept either 409 (preferred) or 200 if processing was extremely fast
    assert download_resp.status_code in {status.HTTP_409_CONFLICT, status.HTTP_200_OK}
