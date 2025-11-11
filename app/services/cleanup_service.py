"""Background cleanup service for temporary files.

Removes upload and processed output files older than the configured
retention window (FILE_RETENTION_HOURS). Intended to run periodically
in a lightweight background thread.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


class CleanupService:
    """Service responsible for periodic deletion of old temporary files."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._interval_seconds = self.settings.CLEANUP_INTERVAL_MINUTES * 60
        self._retention = timedelta(hours=self.settings.FILE_RETENTION_HOURS)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # --- Core logic -----------------------------------------------------
    def _iter_target_dirs(self) -> Iterable[Path]:  # pragma: no cover (simple)
        yield self.settings.UPLOAD_DIR
        yield self.settings.OUTPUT_DIR

    def run_once(self) -> dict[str, int]:
        """Perform a single cleanup pass.

        Returns:
            Mapping of directory path string to number of files deleted.
        """
        now = datetime.now()
        deleted_counts: dict[str, int] = {}
        for directory in self._iter_target_dirs():
            if not directory.exists():
                continue
            deleted = 0
            for path in directory.iterdir():
                if not path.is_file():
                    continue
                try:
                    stat = path.stat()
                    age = now - datetime.fromtimestamp(stat.st_mtime)
                    if age > self._retention:
                        path.unlink(missing_ok=True)
                        deleted += 1
                except OSError as e:  # pragma: no cover - rare
                    logger.warning("Failed to examine/delete %s: %s", path, e)
            if deleted:
                logger.info("Cleanup removed %d files from %s", deleted, directory)
            deleted_counts[str(directory)] = deleted
        return deleted_counts

    def _loop(self) -> None:  # pragma: no cover (timing loop not unit tested)
        logger.info(
            "Cleanup background thread started (interval=%ss retention=%sh)",
            self._interval_seconds,
            self._retention.total_seconds() / 3600,
        )
        while not self._stop_event.wait(self._interval_seconds):
            try:
                self.run_once()
            except Exception as e:  # broad catch to prevent thread death
                logger.exception("Cleanup pass failed: %s", e)
        logger.info("Cleanup background thread stopping")

    # --- Public control -------------------------------------------------
    def start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_background(self) -> None:
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None


_cleanup_service: CleanupService | None = None


def get_cleanup_service() -> CleanupService:
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service
