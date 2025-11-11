from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure project root on path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.services.cleanup_service import get_cleanup_service  # noqa: E402


def test_cleanup_run_once_removes_old_files():
    settings = get_settings()

    # Create dummy old files in upload and output dirs
    upload_dir = settings.UPLOAD_DIR
    output_dir = settings.OUTPUT_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    old_file_u = upload_dir / "old_upload.gcode"
    old_file_o = output_dir / "old_output.gcode"
    recent_file_u = upload_dir / "recent_upload.gcode"
    recent_file_o = output_dir / "recent_output.gcode"

    for p in (old_file_u, old_file_o, recent_file_u, recent_file_o):
        p.write_text("G1 X0 Y0\n", encoding="utf-8")

    # Set mtime: old files older than retention, recent files now
    retention_seconds = get_settings().FILE_RETENTION_HOURS * 3600
    very_old = time.time() - (retention_seconds + 10)
    now = time.time()
    os.utime(old_file_u, (very_old, very_old))
    os.utime(old_file_o, (very_old, very_old))
    os.utime(recent_file_u, (now, now))
    os.utime(recent_file_o, (now, now))

    # Run cleanup once
    svc = get_cleanup_service()
    result = svc.run_once()

    # Old files deleted, recent remain
    assert not old_file_u.exists()
    assert not old_file_o.exists()
    assert recent_file_u.exists()
    assert recent_file_o.exists()

    # Result should include counts for both directories
    assert str(upload_dir) in result
    assert str(output_dir) in result
