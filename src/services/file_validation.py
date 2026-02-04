from __future__ import annotations

import hashlib
import magic  # python-magic
from pathlib import Path
from typing import Any, BinaryIO

import structlog

logger = structlog.get_logger(__name__)


class FileValidationError(Exception):
    pass


class FileSizeExceededError(FileValidationError):
    pass


class InvalidFileTypeError(FileValidationError):
    pass


class FileValidator:
    """Validates uploaded files for security and format compliance."""

    ALLOWED_MIME_TYPES = {
        "text/plain": [".txt"],
        "text/markdown": [".md"],
        "application/pdf": [".pdf"],
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, max_size: int = MAX_FILE_SIZE):
        self.max_size = max_size
        self.magic = magic.Magic(mime=True)

    def validate_size(self, file: BinaryIO, filename: str) -> int:
        """Validate file size and return size in bytes."""
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to start

        if size > self.max_size:
            raise FileSizeExceededError(
                f"File {filename} exceeds maximum size of {self.max_size} bytes"
            )

        logger.info("file_size_validated", filename=filename, size=size)
        return size

    def validate_mime_type(self, file: BinaryIO, filename: str) -> str:
        """Validate MIME type matches file extension."""
        file.seek(0)
        content_sample = file.read(2048)
        file.seek(0)

        detected_mime = self.magic.from_buffer(content_sample)

        file_ext = Path(filename).suffix.lower()

        if detected_mime not in self.ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(
                f"File type {detected_mime} not allowed for {filename}"
            )

        allowed_exts = self.ALLOWED_MIME_TYPES[detected_mime]
        if file_ext not in allowed_exts:
            raise InvalidFileTypeError(
                f"File extension {file_ext} does not match MIME type {detected_mime}"
            )

        logger.info(
            "mime_type_validated",
            filename=filename,
            detected_mime=detected_mime,
            extension=file_ext,
        )
        return detected_mime

    def compute_hash(self, file: BinaryIO) -> str:
        """Compute SHA256 hash of file content."""
        file.seek(0)
        hasher = hashlib.sha256()

        while chunk := file.read(8192):
            hasher.update(chunk)

        file.seek(0)
        return hasher.hexdigest()

    def validate_content(self, file: BinaryIO, filename: str) -> tuple[bool, str]:
        """
        Scan for malicious patterns (basic check).

        Returns:
            (is_safe, reason)
        """
        file.seek(0)
        content = file.read().decode('utf-8', errors='ignore')
        file.seek(0)

        # Check for suspicious patterns
        suspicious_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onclick=",
            "eval(",
            "exec(",
        ]

        for pattern in suspicious_patterns:
            if pattern.lower() in content.lower():
                logger.warning(
                    "suspicious_content_detected",
                    filename=filename,
                    pattern=pattern,
                )
                return False, f"Suspicious pattern detected: {pattern}"

        return True, "Content appears safe"

    def validate_file(
        self,
        file: BinaryIO,
        filename: str,
    ) -> dict[str, Any]:
        """
        Perform full validation.

        Returns validation metadata.
        """
        size = self.validate_size(file, filename)
        mime_type = self.validate_mime_type(file, filename)
        file_hash = self.compute_hash(file)
        is_safe, safety_reason = self.validate_content(file, filename)

        if not is_safe:
            raise FileValidationError(safety_reason)

        return {
            "filename": filename,
            "size": size,
            "mime_type": mime_type,
            "sha256": file_hash,
            "validated": True,
        }
