"""scripts/eventbus/offsets.py"""

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
    """Write the current sequence offset for a consumer to disk.

    Enforces non-decreasing offset semantics: if seq is less than or equal
    to the currently committed offset, the write is silently skipped and a
    warning is logged. This prevents duplicate message delivery caused by
    out-of-order acknowledgments.

    Also detects Consumer ID collisions using .map files.
    """
    current = read_offset(offsets_dir, consumer_id)
    if seq <= current:
        logger.warning("offset not advanced: seq=%d <= current=%d", seq, current)
        return
    safe_id = _sanitize_consumer_id(consumer_id)
    dir_path = Path(offsets_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    # Collision Detection
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

    path = dir_path / safe_id
    path.write_text(str(seq))
    map_path.write_text(consumer_id)
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
