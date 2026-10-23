#!/usr/bin/env python3
"""scripts/agent/wal_checkpoint_manager.py

WalCheckpointManager — WAL checkpoint and backup operations.

Responsibilities:
  - WAL checkpoint (PASSIVE → TRUNCATE fallback)
  - WAL file backup before closing connections
  - Path validation against allowed_root

Both steps run on a worker thread (asyncio.to_thread) so the caller's wait_for bound can
fire while SQLite and the retry backoff are still blocking. A step abandoned by that bound is
not rolled back: its worker keeps running, a half-finished checkpoint leaves the WAL to be
replayed or checkpointed on the next open, and a half-finished backup can leave a partial
copy next to the database. The bound itself is owned by ResourceShutdownCoordinator.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sqlite3
import tempfile
import time
import uuid
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class WalCheckpointManager:
    """WAL checkpoint and backup manager.

    Encapsulates WAL checkpoint (PASSIVE → TRUNCATE fallback) and WAL file
    backup logic extracted from AgentREPL._wal_checkpoint_sync / _wal_backup_sync.
    """

    def __init__(self, ctx: AgentContext) -> None:
        """Initialize with AgentContext reference."""
        self._ctx = ctx

    def _is_db_path_allowed(self, resolved_db_path: str) -> bool:
        """Return True when ``resolved_db_path`` is inside ``cfg.approval.allowed_root``."""
        allowed_root = self._ctx.cfg.approval.allowed_root
        if not allowed_root:
            return True
        resolved_root = os.path.realpath(allowed_root)
        return resolved_db_path == resolved_root or resolved_db_path.startswith(
            resolved_root + os.sep
        )

    async def checkpoint_sync(self) -> tuple[bool, list[tuple[str, str]]]:
        """Attempt a WAL checkpoint (PASSIVE, falling back to TRUNCATE) off the event loop.

        Returns ``(True, [])`` on PASSIVE/TRUNCATE success or when journal mode
        is not WAL; returns ``(False, errors)`` when PASSIVE copied nothing over a
        non-empty WAL or TRUNCATE exhausts retries.
        """
        return await asyncio.to_thread(self._checkpoint_step)

    def _checkpoint_step(self) -> tuple[bool, list[tuple[str, str]]]:
        """Blocking checkpoint body; the connection never leaves this worker thread."""
        errors: list[tuple[str, str]] = []
        with SQLiteHelper("session").open(write_mode=True) as db:
            wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            if wal_mode.lower() != "wal":
                logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
                return True, errors
            try:
                counts = db.checkpoint("PASSIVE")
            except sqlite3.Error as passive_err:
                logger.warning(
                    "WAL PASSIVE checkpoint failed, falling back to TRUNCATE: %s",
                    passive_err,
                )
            else:
                if int(counts.log_size) > 0 and int(counts.pages_checkpointed) == 0:
                    message = (
                        f"PASSIVE copied 0 of {int(counts.log_size)} WAL frames "
                        f"(busy={int(counts.busy)}): a reader is holding the WAL"
                    )
                    logger.warning("WAL checkpoint made no progress: %s", message)
                    errors.append(("wal_checkpoint_no_progress", message))
                    return False, errors
                logger.info("WAL checkpoint completed (PASSIVE) on shutdown")
                return True, errors
            for attempt in range(3):
                failure: str | None
                try:
                    counts = db.checkpoint("TRUNCATE")
                    failure = (
                        None
                        if int(counts.busy) == 0
                        else f"TRUNCATE blocked by a reader (busy={int(counts.busy)}, "
                        f"log_size={int(counts.log_size)}, "
                        f"pages_checkpointed={int(counts.pages_checkpointed)})"
                    )
                except sqlite3.Error as truncate_err:
                    failure = f"{type(truncate_err).__name__}: {truncate_err}"
                if failure is None:
                    logger.info(
                        "WAL checkpoint completed (TRUNCATE) on shutdown after %d retries",
                        attempt + 1,
                    )
                    return True, errors
                if attempt < 2:
                    logger.warning(
                        "WAL TRUNCATE checkpoint attempt %d failed, retrying: %s",
                        attempt + 1,
                        failure,
                    )
                    time.sleep(2**attempt)
                else:
                    logger.error(
                        "WAL TRUNCATE checkpoint failed after 3 attempts: %s", failure
                    )
                    errors.append(("wal_checkpoint_truncate", failure))
            return False, errors

    async def backup_sync(self) -> tuple[str | None, list[tuple[str, str]]]:
        """Copy the WAL file to a backup location off the event loop.

        Returns ``(backup_path_or_None, errors)``.
        """
        return await asyncio.to_thread(self._backup_step)

    def _backup_step(self) -> tuple[str | None, list[tuple[str, str]]]:
        """Blocking backup body; the connection never leaves this worker thread."""
        errors: list[tuple[str, str]] = []
        wal_backup_path: str | None = None
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                db_path = db.execute("PRAGMA database_list").fetchone()[2]
                if db_path:
                    resolved_db_path = os.path.realpath(db_path)
                    if not self._is_db_path_allowed(resolved_db_path):
                        logger.warning(
                            "WAL backup skipped: resolved db path %s is outside allowed_root %s",
                            resolved_db_path,
                            self._ctx.cfg.approval.allowed_root,
                        )
                        errors.append(
                            (
                                "wal_backup_path_rejected",
                                f"resolved db path {resolved_db_path} is outside allowed_root "
                                f"{self._ctx.cfg.approval.allowed_root!r}",
                            )
                        )
                        return wal_backup_path, errors
                    wal_file = f"{db_path}-wal"
                    backup_dir = os.path.dirname(db_path) or tempfile.gettempdir()
                    if not os.path.isdir(backup_dir) or not os.access(
                        backup_dir, os.W_OK
                    ):
                        logger.warning(
                            "WAL backup skipped: backup directory %s is not writable",
                            backup_dir,
                        )
                        errors.append(
                            (
                                "wal_backup_dir_not_writable",
                                f"backup directory not writable: {backup_dir}",
                            )
                        )
                        return wal_backup_path, errors
                    session_id = self._ctx.session.session_id
                    session_tag = (
                        str(session_id)
                        if session_id is not None
                        else uuid.uuid4().hex[:8]
                    )
                    wal_backup_path = os.path.join(
                        backup_dir,
                        f"{os.path.basename(db_path)}-wal-backup-{session_tag}-{int(time.time())}",
                    )
                    shutil.copy2(wal_file, wal_backup_path)
                    logger.warning("WAL file backed up to %s", wal_backup_path)
        except Exception as backup_err:  # noqa: BLE001 — backup is best-effort during shutdown; failure must be recorded, not propagated
            logger.error("Failed to backup WAL file: %s", backup_err)
            errors.append(("wal_backup", f"{type(backup_err).__name__}: {backup_err}"))
        return wal_backup_path, errors
