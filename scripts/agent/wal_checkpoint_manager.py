#!/usr/bin/env python3
"""scripts/agent/wal_checkpoint_manager.py

WalCheckpointManager — WAL checkpoint and backup operations.

Responsibilities:
  - WAL checkpoint (PASSIVE → TRUNCATE fallback)
  - WAL file backup before closing connections
  - Path validation against allowed_root

Constants moved from AgentREPL class attributes per REQ-012.
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import time
import uuid
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

_WAL_CHECKPOINT_TIMEOUT_S: float = 30.0
_WAL_BACKUP_TIMEOUT_S: float = 10.0


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
        """Attempt a WAL checkpoint (PASSIVE, falling back to TRUNCATE).

        Returns ``(True, [])`` on PASSIVE/TRUNCATE success or when journal mode
        is not WAL; returns ``(False, errors)`` when TRUNCATE exhausts retries.
        """
        errors: list[tuple[str, str]] = []
        with SQLiteHelper("session").open(write_mode=True) as db:
            wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            if wal_mode.lower() != "wal":
                logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
                return True, errors
            _passive_start = time.monotonic()
            try:
                db.checkpoint("PASSIVE")
                elapsed = time.monotonic() - _passive_start
                if elapsed > 5:
                    logger.warning(
                        "WAL PASSIVE checkpoint took %s seconds, falling back to TRUNCATE",
                        round(elapsed, 2),
                    )
                else:
                    logger.info("WAL checkpoint completed (PASSIVE) on shutdown")
                    return True, errors
            except sqlite3.Error as passive_err:
                logger.warning(
                    "WAL PASSIVE checkpoint failed, falling back to TRUNCATE: %s",
                    passive_err,
                )
            for attempt in range(3):
                try:
                    db.checkpoint("TRUNCATE")
                    logger.info(
                        "WAL checkpoint completed (TRUNCATE) on shutdown after %d retries",
                        attempt + 1,
                    )
                    return True, errors
                except sqlite3.Error as truncate_err:
                    if attempt < 2:
                        logger.warning(
                            "WAL TRUNCATE checkpoint attempt %d failed, retrying: %s",
                            attempt + 1,
                            truncate_err,
                        )
                        time.sleep(2**attempt)
                    else:
                        logger.error(
                            "WAL TRUNCATE checkpoint failed after 3 attempts: %s",
                            truncate_err,
                        )
                        errors.append(
                            (
                                "wal_checkpoint_truncate",
                                f"{type(truncate_err).__name__}: {truncate_err}",
                            )
                        )
            return False, errors

    async def backup_sync(self) -> tuple[str | None, list[tuple[str, str]]]:
        """Copy the WAL file to a backup location.

        Returns ``(backup_path_or_None, errors)``.
        """
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
                    backup_dir = os.path.dirname(db_path) or "/tmp"
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
