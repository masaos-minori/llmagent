"""scripts/eventbus/offsets.py"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class CorruptOffsetError(ValueError):
    """Raised when offset file content is corrupted."""

    pass


def _validate_consumer_identity(offsets_dir: str, consumer_id: str) -> None:
    """Validate that the consumer_id matches any existing .map entry.

    Raises ValueError if a collision is detected.
    """
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    map_path = dir_path / f"{safe_id}.map"

    if map_path.exists():
        try:
            stored_id = map_path.read_text().strip()
            if stored_id and stored_id != consumer_id:
                logger.error(
                    "Consumer ID collision detected: %s and %s both map to %s",
                    consumer_id,
                    stored_id,
                    safe_id,
                )
                raise ValueError(
                    f"Consumer ID collision: {consumer_id} conflicts with existing {stored_id}"
                )
        except FileNotFoundError:
            pass


def read_offset(offsets_dir: str, consumer_id: str) -> int:
    """Read the last committed sequence offset for a consumer from disk."""
    safe_id = _sanitize_consumer_id(consumer_id)
    path = Path(offsets_dir) / safe_id
    try:
        return int(path.read_text().strip())
    except FileNotFoundError:
        return 0
    except ValueError:
        raise CorruptOffsetError(f"Offset file contains invalid content: {path}")


def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    """Write the current sequence offset for a consumer to disk.

    Enforces non-decreasing offset semantics: if seq is less than or equal
    to the currently committed offset, the write is silently skipped and a
    warning is logged. This prevents duplicate message delivery caused by
    out-of-order acknowledgments.

    Also detects Consumer ID collisions using .map files.
    """
    # REQ-001: Validate consumer identity BEFORE checking offset advancement
    _validate_consumer_identity(offsets_dir, consumer_id)

    current = read_offset(offsets_dir, consumer_id)
    if seq <= current:
        logger.warning("offset not advanced: seq=%d <= current=%d", seq, current)
        return

    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    # REQ-002: Atomic writes via temp file + os.replace()
    # Write offset file first, then map file (REQ-003)
    fd, tmp_offset_path = tempfile.mkstemp(dir=str(dir_path), prefix=".offset_tmp_")
    try:
        os.write(fd, str(seq).encode())
        os.fsync(fd)
        os.close(fd)

        # Atomic replace for offset file
        os.replace(tmp_offset_path, dir_path / safe_id)

        # Write map file similarly
        fd_map, tmp_map_path = tempfile.mkstemp(dir=str(dir_path), prefix=".map_tmp_")
        try:
            os.write(fd_map, consumer_id.encode())
            os.fsync(fd_map)
            os.close(fd_map)

            # Atomic replace for map file
            os.replace(tmp_map_path, dir_path / f"{safe_id}.map")
        except Exception:
            # REQ-003: Rollback — delete offset file if map file write fails
            try:
                os.unlink(dir_path / safe_id)
            except OSError:
                pass
            raise

        logger.debug("offset written consumer=%s seq=%d", consumer_id, seq)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_offset_path)
        except OSError:
            pass
        raise


def _sanitize_consumer_id(consumer_id: str) -> str:
    """Sanitize consumer_id for use as an offset filename.

    Replacement order matters: '..' first, then '.', then '/'.
    This avoids double-replacement of '..' (e.g., '..' becomes '_' not '__').
    Single '.' is also replaced (not only '..'), '/' is replaced, all occurrences
    are replaced across the full string.
    Returns 'default' if the sanitized result is empty.
    """
    safe_id = consumer_id.replace("..", "_").replace(".", "_").replace("/", "_")
    return safe_id if safe_id else "default"
