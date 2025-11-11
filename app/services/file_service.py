"""File handling and validation service."""

import re
from pathlib import Path
from typing import BinaryIO

from app.config import get_settings


class FileValidationError(Exception):
    """Custom exception for file validation errors."""

    pass


class FileService:
    """Service for file operations and validation."""

    def __init__(self):
        """Initialize file service with settings."""
        self.settings = get_settings()

    def validate_file_size(self, file_size: int) -> None:
        """Validate file size against configured maximum.

        Args:
            file_size: Size of file in bytes

        Raises:
            FileValidationError: If file size exceeds maximum
        """
        if file_size > self.settings.MAX_UPLOAD_SIZE:
            max_mb = self.settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise FileValidationError(
                f"File size ({actual_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)"
            )

        if file_size == 0:
            raise FileValidationError("File is empty")

    def validate_file_extension(self, filename: str) -> None:
        """Validate file has allowed extension.

        Args:
            filename: Name of the file

        Raises:
            FileValidationError: If file extension is not allowed
        """
        file_ext = Path(filename).suffix.lower()

        if not file_ext:
            raise FileValidationError("File has no extension")

        if file_ext not in self.settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(self.settings.ALLOWED_EXTENSIONS)
            raise FileValidationError(
                f"File extension '{file_ext}' not allowed. Allowed extensions: {allowed}"
            )

    def validate_filename(self, filename: str) -> None:
        """Validate filename is safe and doesn't contain dangerous characters.

        Args:
            filename: Name of the file

        Raises:
            FileValidationError: If filename is invalid or unsafe
        """
        if not filename:
            raise FileValidationError("Filename is empty")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            raise FileValidationError("Filename contains invalid path characters")

        # Check for null bytes
        if "\0" in filename:
            raise FileValidationError("Filename contains null bytes")

        # Validate filename characters (alphanumeric, dash, underscore, dot, space)
        if not re.match(r"^[\w\s.-]+$", filename):
            raise FileValidationError(
                "Filename contains invalid characters. Use only letters, numbers, spaces, dash, underscore, and dot"
            )

    def validate_gcode_content(self, file_content: bytes) -> None:
        """Perform basic validation that file appears to be G-code.

        Args:
            file_content: First chunk of file content to validate

        Raises:
            FileValidationError: If content doesn't appear to be valid G-code
        """
        try:
            # Decode first part of file
            content_str = file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise FileValidationError(f"Unable to decode file as text: {e}") from e

        # Check for common G-code patterns in first 2KB
        gcode_patterns = [
            r"G[0-9]+",  # G-code commands (G0, G1, etc.)
            r"M[0-9]+",  # M-code commands
            r"X[0-9.-]+",  # X coordinate
            r"Y[0-9.-]+",  # Y coordinate
            r"Z[0-9.-]+",  # Z coordinate
            r";",  # Comments (common in G-code)
        ]

        pattern_matches = sum(1 for pattern in gcode_patterns if re.search(pattern, content_str))

        if pattern_matches < 3:
            raise FileValidationError(
                "File doesn't appear to contain valid G-code. Expected G-code commands and coordinates."
            )

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing/replacing unsafe characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Get the file extension
        path = Path(filename)
        name = path.stem
        ext = path.suffix

        # Replace spaces with underscores, remove other unsafe chars
        name = re.sub(r"[^\w.-]", "_", name)

        # Remove multiple consecutive underscores
        name = re.sub(r"_+", "_", name)

        # Trim underscores from ends
        name = name.strip("_")

        # Limit length (filesystem limits, leaving room for UUID prefix)
        max_length = 100
        if len(name) > max_length:
            name = name[:max_length]

        return f"{name}{ext}"

    def save_upload(self, job_id: str, filename: str, file_obj: BinaryIO) -> tuple[Path, int]:
        """Save uploaded file to upload directory.

        Args:
            job_id: Unique job identifier
            filename: Sanitized filename
            file_obj: File object to save

        Returns:
            Tuple of (file_path, file_size)

        Raises:
            FileValidationError: If save fails
        """
        try:
            # Create filename with job ID prefix
            safe_filename = self.sanitize_filename(filename)
            file_path = self.settings.UPLOAD_DIR / f"{job_id}_{safe_filename}"

            # Write file in chunks to handle large files
            file_size = 0
            chunk_size = 8192  # 8KB chunks

            with file_path.open("wb") as f:
                while True:
                    chunk = file_obj.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    file_size += len(chunk)

            return file_path, file_size

        except OSError as e:
            raise FileValidationError(f"Failed to save file: {e}") from e

    def get_upload_path(self, job_id: str, filename: str) -> Path:
        """Get the full path for an uploaded file.

        Args:
            job_id: Job identifier
            filename: Original filename

        Returns:
            Path object for the uploaded file
        """
        safe_filename = self.sanitize_filename(filename)
        return self.settings.UPLOAD_DIR / f"{job_id}_{safe_filename}"

    def get_output_path(self, job_id: str, filename: str) -> Path:
        """Get the full path for a processed output file.

        Args:
            job_id: Job identifier
            filename: Original filename

        Returns:
            Path object for the output file
        """
        safe_filename = self.sanitize_filename(filename)
        # Add "_processed" suffix before extension
        path = Path(safe_filename)
        processed_filename = f"{path.stem}_processed{path.suffix}"
        return self.settings.OUTPUT_DIR / f"{job_id}_{processed_filename}"

    def delete_file(self, file_path: Path) -> bool:
        """Safely delete a file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted, False if file didn't exist
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except OSError:
            return False
