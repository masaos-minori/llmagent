from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_offset(offsets_dir: str, consumer_id: str) -> int:
    """Read the last committed sequence offset for a consumer from disk."""
    safe_id = _sanitize_consumer_id(consumer_id)
    path = Path(offsets_dir) / safe_id
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    """Write the current sequence offset for a consumer to disk."""
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / safe_id
    path.write_text(str(seq))
    logger.debug("offset written consumer=%s seq=%d", consumer_id, seq)


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
