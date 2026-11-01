#!/usr/bin/env python3
"""scripts/agent/workflow/attempt_ops.py — Attempt operations for workflow.sqlite."""

import os
import secrets
import socket
import uuid
from datetime import timedelta

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now
from shared.json_utils import parse_iso_utc

from agent.workflow.models import AttemptRecord

_owner_id_cache: str | None = None


def get_owner_id() -> str:
    """Return this process's owner identity: hostname-pid-random.

    Built once per process (Plan Design 'Owner identity'). The random suffix
    is required because a bare PID can be reused by a later process, which
    would let a dead owner masquerade as a live one during recovery.
    """
    global _owner_id_cache
    if _owner_id_cache is None:
        _owner_id_cache = f"{socket.gethostname()}-{os.getpid()}-{secrets.token_hex(4)}"
    return _owner_id_cache


def lease_expires_from(started_at: str, lease_duration_sec: int) -> str:
    """Derive the lease deadline from a production timestamp plus a duration.

    The result uses the same ``Z`` format as ``started_at`` so both values
    round-trip through :func:`parse_iso_utc`.
    """
    expires = parse_iso_utc(started_at) + timedelta(seconds=lease_duration_sec)
    return expires.strftime("%Y-%m-%dT%H:%M:%SZ")


def start_attempt(
    db: SQLiteHelper,
    task_id: str,
    stage_id: str,
    lease_duration_sec: int | None = None,
) -> AttemptRecord:
    """Create a new running attempt record for the given task and stage.

    With ``lease_duration_sec`` set, the row is stamped with this process's
    ``owner_id`` and a ``lease_expires_at`` derived from ``started_at``
    (REQ-005). With ``None``, both lease columns stay NULL for legacy
    callers.
    """
    attempt_id = str(uuid.uuid4())
    now = _now()
    owner_id: str | None = None
    lease_expires_at: str | None = None
    if lease_duration_sec is not None:
        owner_id = get_owner_id()
        lease_expires_at = lease_expires_from(now, lease_duration_sec)
    db.execute(
        """

        INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at)
        VALUES (?, ?, ?, 'running', ?, ?, ?)
        """,
        (attempt_id, task_id, stage_id, now, owner_id, lease_expires_at),
    )
    db.commit()
    return AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        stage_id=stage_id,
        status="running",
        started_at=now,
    )


def finish_attempt(
    db: SQLiteHelper,
    attempt_id: str,
    status: str,
    error_msg: str | None = None,
    error_kind: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Mark an attempt as completed with the given status and optional error details."""
    db.execute(
        "UPDATE attempts SET status=?, ended_at=?, error_msg=?, error_kind=?, error_detail=? WHERE attempt_id=?",
        (status, _now(), error_msg, error_kind, error_detail, attempt_id),
    )
    db.commit()


def count_attempts(db: SQLiteHelper, task_id: str, stage_id: str) -> int:
    """Count the number of attempts for a specific task and stage combination."""
    rows = db.fetchall(
        "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
        (task_id, stage_id),
    )
    return int(rows[0][0])
