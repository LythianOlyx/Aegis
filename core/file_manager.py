"""
Aegis – File Manager
====================
Handles file reading, chunking, size formatting, and MIME type detection
for encrypted file transfers.

All file I/O is designed to run in background threads.
"""

from __future__ import annotations

import mimetypes
import os
from typing import Generator, Optional, Tuple

# ─────────────────── Constants ───────────────────────────
DEFAULT_CHUNK_SIZE: int = 4 * 1024 * 1024  # 4 MiB per chunk
MAX_FILE_SIZE: int = 100 * 1024 * 1024      # 100 MiB hard limit

# Allowlisted MIME types for safety
ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/webm",
    "audio/mpeg", "audio/ogg", "audio/wav",
    "application/pdf",
    "text/plain",
    "application/zip",
    "application/x-7z-compressed",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})


class FileTooLargeError(Exception):
    """Raised when a file exceeds the maximum allowed size."""


class UnsupportedFileTypeError(Exception):
    """Raised when a file's MIME type is not in the allowlist."""


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size string.

    Parameters
    ----------
    size_bytes : int

    Returns
    -------
    str
        e.g. ``"3.14 MiB"``
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KiB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MiB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GiB"


def detect_mime_type(file_path: str) -> str:
    """Detect MIME type from file extension.

    Parameters
    ----------
    file_path : str

    Returns
    -------
    str
        MIME type string, e.g. ``"image/png"``.
    """
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def validate_file(
    file_path: str,
    max_size: int = MAX_FILE_SIZE,
    check_mime: bool = True,
) -> Tuple[int, str]:
    """Validate a file before upload.

    Parameters
    ----------
    file_path : str
        Absolute or relative path.
    max_size : int
        Maximum allowed size in bytes.
    check_mime : bool
        If ``True``, enforce MIME allowlist.

    Returns
    -------
    Tuple[int, str]
        ``(file_size_bytes, mime_type)``

    Raises
    ------
    FileNotFoundError
    FileTooLargeError
    UnsupportedFileTypeError
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    size: int = os.path.getsize(file_path)
    if size > max_size:
        raise FileTooLargeError(
            f"File size {format_file_size(size)} exceeds limit "
            f"{format_file_size(max_size)}."
        )

    mime: str = detect_mime_type(file_path)
    if check_mime and mime not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"File type '{mime}' is not allowed."
        )

    return size, mime


def read_file_bytes(file_path: str) -> bytes:
    """Read entire file as bytes (for small-to-medium files).

    Parameters
    ----------
    file_path : str

    Returns
    -------
    bytes
    """
    with open(file_path, "rb") as fp:
        return fp.read()


def read_file_chunks(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Generator[bytes, None, None]:
    """Yield file content in fixed-size chunks (for large files).

    Parameters
    ----------
    file_path : str
    chunk_size : int

    Yields
    ------
    bytes
    """
    with open(file_path, "rb") as fp:
        while True:
            chunk = fp.read(chunk_size)
            if not chunk:
                break
            yield chunk


def write_file_bytes(file_path: str, data: bytes) -> None:
    """Write bytes to a file, creating directories as needed.

    Parameters
    ----------
    file_path : str
    data : bytes
    """
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(file_path, "wb") as fp:
        fp.write(data)


def get_file_name(file_path: str) -> str:
    """Extract the file name from a path.

    Parameters
    ----------
    file_path : str

    Returns
    -------
    str
    """
    return os.path.basename(file_path)


def get_downloads_dir() -> str:
    """Return a platform-appropriate downloads directory.

    Returns
    -------
    str
    """
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads", "Aegis")
    os.makedirs(downloads, exist_ok=True)
    return downloads


def safe_filename(original_name: str) -> str:
    """Sanitize a filename by removing dangerous characters.

    Parameters
    ----------
    original_name : str

    Returns
    -------
    str
        Safe filename.
    """
    keep = set("abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789._-")
    cleaned = "".join(c if c in keep else "_" for c in original_name)
    # Collapse multiple underscores
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unnamed_file"
