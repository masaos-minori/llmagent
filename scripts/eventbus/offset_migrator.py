"""Offset migrator: legacy offset migration with isolated file I/O."""

from __future__ import annotations

import logging
from pathlib import Path
from sqlite3 import Connection

logger = logging.getLogger(__name__)


def migrate_legacy_offsets(
    conn: Connection,
    offsets_dir: str,
) -> list[str]:
    """Migrate legacy file-based offsets into the consumer_offsets table.

    Reads each .map file under offsets_dir, recovers the original consumer_id
    from the .map companion file, reads its offset via read_offset(), and inserts
    a row into consumer_offsets using INSERT OR IGNORE (idempotent).

    For any offset file with no .map companion, falls back to the sanitized
    filename as consumer_id, logging a warning.

    Does NOT delete or modify any legacy files.

    Returns:
        List of consumer_ids that were migrated.
    """
    # Deferred import to avoid circular import with eventbus.offsets
    from eventbus.offsets import (
        _sanitize_consumer_id,  # noqa: PLC0415 — deferred import avoids a circular import with eventbus.offsets
    )

    migrated: list[str] = []
    dir_path = Path(offsets_dir)

    if not dir_path.exists():
        logger.warning("offsets_dir does not exist: %s", offsets_dir)
        return migrated

    # Collect all legacy files first for collision detection
    legacy_files = sorted(f.name for f in dir_path.iterdir() if f.is_file())

    # Build sanitized name mapping for collision detection (O(n))
    sanitized_names: dict[str, list[str]] = {}
    for fname in legacy_files:
        if fname.endswith(".map"):
            continue
        sanitized = _sanitize_consumer_id(fname.replace(".offset", ""))
        sanitized_names.setdefault(sanitized, []).append(fname)

    # Process each file
    for safe_id in legacy_files:
        if safe_id.endswith(".map"):
            continue
        map_file = dir_path / f"{safe_id}.map"
        try:
            stored_id = map_file.read_text().strip()
            if stored_id:
                consumer_id = stored_id
            else:
                # Empty .map file — fall back to sanitized filename
                consumer_id = _sanitize_consumer_id(safe_id)
                logger.warning(
                    "empty .map file for %s, using sanitized filename as consumer_id",
                    safe_id,
                )
        except FileNotFoundError:
            # No .map companion — use sanitized filename
            sanitized = _sanitize_consumer_id(safe_id)
            if len(sanitized_names[sanitized]) > 1:
                # Collision detected — refuse to proceed
                raise ValueError(
                    f"Collision detected: {sanitized} maps to multiple legacy files: "
                    f"{', '.join(sorted(sanitized_names[sanitized]))}"
                )
            consumer_id = sanitized
            logger.warning(
                "no .map companion for %s, using sanitized filename as consumer_id",
                safe_id,
            )

        # Read directly from the on-disk file rather than via read_offset(),
        # which re-sanitizes its consumer_id argument to build the path
        try:
            offset_val = int((dir_path / safe_id).read_text().strip())
        except (FileNotFoundError, ValueError):
            offset_val = 0
        if offset_val > 0:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO consumer_offsets(consumer_id, offset) VALUES (?, ?)",
                    (consumer_id, offset_val),
                )
                migrated.append(consumer_id)
                logger.debug(
                    "migrated offset: consumer=%s offset=%d",
                    consumer_id,
                    offset_val,
                )
            except (FileNotFoundError, ValueError, OSError) as exc:
                logger.warning(
                    "failed to migrate offset for consumer %s: %s",
                    consumer_id,
                    exc,
                )

    return migrated
