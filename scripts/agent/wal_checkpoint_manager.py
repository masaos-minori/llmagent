#!/usr/bin/env python3
"""scripts/agent/wal_checkpoint_manager.py

WalCheckpointManager — WAL checkpoint and backup operations.

Responsibilities:
  - WAL checkpoint (PASSIVE → TRUNCATE fallback)
  - WAL file backup before closing connections
  - Path validation against allowed_root

Both steps run on a worker thread (asyncio.to_thread) so the caller's wait_for bound can
fire while SQLite and the retry backoff are still blocking. Each step is given the deadline
the shutdown budget leaves and the interrupt event a second SIGINT sets, so the worker stops
at the deadline instead of being abandoned by the bound: the retry loop checks the deadline
before every attempt and sleeps on the interrupt event instead of sleeping blindly, and the
installed progress handler aborts a statement that is already running. A worker that ignores
both is still abandoned by the caller's bound, and a half-finished checkpoint leaves the WAL
to be replayed or checkpointed on the next open. The bound itself is owned by
ResourceShutdownCoordinator.

The backup is published through a ``.partial`` file in the destination directory: copy,
flush, fsync, size check, then os.replace. A copy that fails, stops early, or is interrupted
leaves no file under the final name.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import sqlite3
import tempfile
import threading
import time
import uuid
from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

from db.helper import SQLiteHelper

from agent.secrets_masker import _mask_secrets, redact_path
from agent.shutdown_budget import ShutdownOutcome

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# TRUNCATE attempts the checkpoint makes before it reports failure.
_MAX_TRUNCATE_ATTEMPTS: Final = 3

# Per-process uniqueness token in the backup name (REQ-009): the timestamp alone can
# collide when two processes close in the same second.
_PROCESS_TOKEN: Final = uuid.uuid4().hex[:8]

# Absolute-path tokens inside an error message, such as the database file SQLite could not open.
_ABSOLUTE_PATH_RE: Final = re.compile(r"/[^\s\"']+")


def format_sqlite_error(exc: BaseException) -> str:
    """Render a failure as the error type name plus a masked, path-reduced message.

    Absolute paths in the message are replaced by their logical identifier, so a log line
    never carries the database file path. The type name stays visible because the checkpoint
    policy distinguishes `sqlite3.OperationalError` from other `sqlite3.Error` subclasses.
    """
    message = _ABSOLUTE_PATH_RE.sub(lambda match: redact_path(match.group(0)), str(exc))
    return f"{type(exc).__name__}: {_mask_secrets(message)}"


def _deadline_spent(deadline: float | None) -> bool:
    """Return True when a monotonic deadline has already passed (None is no deadline)."""
    return deadline is not None and time.monotonic() >= deadline


def _remaining_of(deadline: float | None) -> float:
    """Return the seconds left until a monotonic deadline; infinity when there is none."""
    if deadline is None:
        return float("inf")
    return max(0.0, deadline - time.monotonic())


def _backoff_sleep(
    attempt: int, deadline: float | None, stop: threading.Event | None
) -> bool:
    """Sleep the attempt backoff, clamped to the deadline. Return True if a stop was seen.

    The sleep waits on the interrupt event when one is given, so a second SIGINT ends the
    backoff immediately instead of after the full exponential delay.
    """
    seconds = min(float(2**attempt), _remaining_of(deadline))
    if seconds <= 0.0:
        return False
    if stop is not None:
        return stop.wait(timeout=seconds)
    time.sleep(seconds)
    return False


def _interrupted_error(attempt: int) -> tuple[str, str]:
    """Record that a checkpoint attempt was stopped by a shutdown interrupt request."""
    return (
        "wal_checkpoint_interrupted",
        "TRUNCATE checkpoint stopped on a shutdown interrupt request "
        f"during attempt {attempt + 1}",
    )


def _stop_seen(stop: threading.Event | None, exc: BaseException | None = None) -> bool:
    """True when a stop was requested, or the SQLite error is the progress-handler abort.

    The progress handler aborts a running statement with ``sqlite3.OperationalError:
    interrupted``, which is a different failure from a lock and must not be retried.
    """
    if stop is not None and stop.is_set():
        return True
    return exc is not None and "interrupted" in str(exc).lower()


def _stop_reason(
    deadline: float | None, stop: threading.Event | None, attempt: int
) -> tuple[str, str] | None:
    """Return the record for a retry the deadline or an interrupt stopped, else None."""
    if _deadline_spent(deadline):
        return (
            "wal_checkpoint_deadline",
            "TRUNCATE retry stopped at the shutdown deadline before attempt "
            f"{attempt + 1} of {_MAX_TRUNCATE_ATTEMPTS}",
        )
    if stop is not None and stop.is_set():
        return _interrupted_error(attempt)
    return None


def wal_step_outcome(errors: Iterable[tuple[str, str]]) -> ShutdownOutcome:
    """Map the error labels these steps record onto the shutdown outcome vocabulary.

    This module owns the labels, so it owns what they mean to the shutdown report: a step
    that stopped at its own deadline is ``timed_out``; a step whose SQLite work was aborted
    mid-statement is ``outcome_unknown``, because it cannot describe the WAL state it left;
    anything else is a plain failure.
    """
    labels = [label for label, _ in errors]
    if any(label.endswith("_interrupted") for label in labels):
        return ShutdownOutcome.OUTCOME_UNKNOWN
    if any(label.endswith("_deadline") for label in labels):
        return ShutdownOutcome.TIMED_OUT
    return ShutdownOutcome.FAILED


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

    async def checkpoint_sync(
        self,
        *,
        deadline: float | None = None,
        stop: threading.Event | None = None,
    ) -> tuple[bool, list[tuple[str, str]]]:
        """Attempt a WAL checkpoint (PASSIVE, falling back to TRUNCATE) off the event loop.

        ``deadline`` is a monotonic instant: the TRUNCATE retry loop checks it before every
        attempt and clamps every backoff sleep to it, so the retries cannot run past the
        shutdown budget (REQ-008). ``stop`` is the interrupt event a second SIGINT sets; it
        both aborts the statement in flight through the connection progress handler and ends
        a backoff early.

        Returns ``(True, [])`` on PASSIVE/TRUNCATE success or when journal mode
        is not WAL; returns ``(False, errors)`` when PASSIVE copied nothing over a
        non-empty WAL, TRUNCATE exhausts retries, or the step stopped at the deadline
        or on an interrupt request.
        """
        return await asyncio.to_thread(self._checkpoint_step, deadline, stop)

    def _checkpoint_step(
        self, deadline: float | None, stop: threading.Event | None
    ) -> tuple[bool, list[tuple[str, str]]]:
        """Blocking checkpoint body; the connection never leaves this worker thread."""
        errors: list[tuple[str, str]] = []
        with SQLiteHelper("session", db_config=self._ctx.cfg.db).open(
            write_mode=True
        ) as db:
            if stop is not None:
                db.interrupt_when(stop)
            try:
                wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
                if wal_mode.lower() != "wal":
                    logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
                    return True, errors
                try:
                    counts = db.checkpoint("PASSIVE")
                except sqlite3.Error as passive_err:
                    if _stop_seen(stop, passive_err):
                        errors.append(_interrupted_error(0))
                        return False, errors
                    logger.warning(
                        "WAL PASSIVE checkpoint failed, falling back to TRUNCATE: %s",
                        format_sqlite_error(passive_err),
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
                for attempt in range(_MAX_TRUNCATE_ATTEMPTS):
                    stop_reason = _stop_reason(deadline, stop, attempt)
                    if stop_reason is not None:
                        errors.append(stop_reason)
                        return False, errors
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
                        if _stop_seen(stop, truncate_err):
                            errors.append(_interrupted_error(attempt))
                            return False, errors
                        failure = format_sqlite_error(truncate_err)
                    if failure is None:
                        logger.info(
                            "WAL checkpoint completed (TRUNCATE) on shutdown after %d retries",
                            attempt + 1,
                        )
                        return True, errors
                    if attempt < _MAX_TRUNCATE_ATTEMPTS - 1:
                        logger.warning(
                            "WAL TRUNCATE checkpoint attempt %d failed, retrying: %s",
                            attempt + 1,
                            failure,
                        )
                        if _backoff_sleep(attempt, deadline, stop):
                            errors.append(_interrupted_error(attempt))
                            return False, errors
                    else:
                        logger.error(
                            "WAL TRUNCATE checkpoint failed after %d attempts: %s",
                            _MAX_TRUNCATE_ATTEMPTS,
                            failure,
                        )
                        errors.append(("wal_checkpoint_truncate", failure))
                return False, errors
            finally:
                if stop is not None:
                    try:
                        db.interrupt_when(None)
                    except Exception as clear_err:  # noqa: BLE001 — the handler is cleanup; the closing connection clears it anyway
                        logger.debug(
                            "could not clear the checkpoint progress handler: %s",
                            clear_err,
                        )

    async def backup_sync(
        self,
        *,
        deadline: float | None = None,
        stop: threading.Event | None = None,
    ) -> tuple[str | None, list[tuple[str, str]]]:
        """Copy the WAL file to a backup location off the event loop.

        ``deadline`` is a monotonic instant checked before the copy starts, and ``stop`` is
        the interrupt event a second SIGINT sets; either one that has already passed or been
        set stops the step before it writes anything (REQ-008).

        Returns ``(backup_path_or_None, errors)``. The path is returned only for a backup
        that was published: a copy that failed, mismatched its size, or was interrupted
        leaves no file under the final name (REQ-009).
        """
        return await asyncio.to_thread(self._backup_step, deadline, stop)

    def _backup_step(
        self, deadline: float | None, stop: threading.Event | None
    ) -> tuple[str | None, list[tuple[str, str]]]:
        """Blocking backup body; the connection never leaves this worker thread."""
        errors: list[tuple[str, str]] = []
        wal_backup_path: str | None = None
        try:
            with SQLiteHelper("session", db_config=self._ctx.cfg.db).open(
                write_mode=True
            ) as db:
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
                    if _deadline_spent(deadline):
                        logger.warning(
                            "WAL backup skipped: the shutdown deadline of %s was already spent",
                            deadline,
                        )
                        errors.append(
                            (
                                "wal_backup_deadline",
                                "backup not started: the shutdown deadline was spent",
                            )
                        )
                        return wal_backup_path, errors
                    if stop is not None and stop.is_set():
                        logger.warning(
                            "WAL backup skipped: a shutdown interrupt request was already set"
                        )
                        errors.append(
                            (
                                "wal_backup_interrupted",
                                "backup not started: a shutdown interrupt request was set",
                            )
                        )
                        return wal_backup_path, errors
                    # The artifact belongs to the database file, not to the session that
                    # happened to be closing (REQ-009): no session identifier in the name.
                    final_path = os.path.join(
                        backup_dir,
                        f"{os.path.basename(db_path)}-wal-backup-{int(time.time())}-{_PROCESS_TOKEN}",
                    )
                    wal_backup_path = self._publish_backup(wal_file, final_path, errors)
                    if wal_backup_path is not None:
                        logger.warning("WAL file backed up to %s", wal_backup_path)
        except Exception as backup_err:  # noqa: BLE001 — backup is best-effort during shutdown; failure must be recorded, not propagated
            logger.error(
                "Failed to backup WAL file: %s", format_sqlite_error(backup_err)
            )
            errors.append(("wal_backup", format_sqlite_error(backup_err)))
        return wal_backup_path, errors

    def _publish_backup(
        self, wal_file: str, final_path: str, errors: list[tuple[str, str]]
    ) -> str | None:
        """Copy to ``<final>.partial``, verify the size, then os.replace to the final name.

        The temporary file lives in the same directory as the final name so os.replace is
        atomic on the same filesystem, and it is removed on every failure: a partial backup
        is never visible under the name a later reader would trust (REQ-009, AC-3).
        """
        partial_path = f"{final_path}.partial"
        try:
            with open(wal_file, "rb") as src, open(partial_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
            source_size = os.path.getsize(wal_file)
            copied_size = os.path.getsize(partial_path)
            if copied_size != source_size:
                logger.error(
                    "WAL backup size mismatch: copied %d of %d bytes",
                    copied_size,
                    source_size,
                )
                errors.append(
                    (
                        "wal_backup_size_mismatch",
                        f"copied {copied_size} of {source_size} bytes",
                    )
                )
                return None
            os.replace(partial_path, final_path)
            return final_path
        finally:
            if os.path.exists(partial_path):
                try:
                    os.unlink(partial_path)
                except OSError as unlink_err:
                    logger.error(
                        "could not remove the partial backup %s: %s",
                        partial_path,
                        unlink_err,
                    )
