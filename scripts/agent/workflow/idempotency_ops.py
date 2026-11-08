#!/usr/bin/env python3
"""scripts/agent/workflow/idempotency_ops.py — Idempotency operations for workflow.sqlite."""

import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.attempt_ops import get_owner_id, lease_expires_from
from agent.workflow.models import AttemptRecord


def is_event_processed(db: SQLiteHelper, event_id: str) -> bool:
    """Check whether an event has already been processed by looking up its ID."""
    rows = db.fetchall("SELECT 1 FROM processed_events WHERE event_id=?", (event_id,))
    return len(rows) > 0


def begin_stage_if_new(
    db: SQLiteHelper,
    event_id: str,
    task_id: str,
    stage_id: str,
    workflow_id: str | None = None,
    lease_duration_sec: int | None = None,
) -> AttemptRecord | None:
    """Atomically check event_id and start attempt if new.

    Note: 'processed_events' refers to events that have been STARTED,
    not necessarily completed. An attempt may be in progress when
    processed_events includes its event ID.

    Uses begin_immediate to hold the write lock across the check-then-insert.
    Returns AttemptRecord if the stage should run, None if already processed.
    No explicit commit() is called — begin_immediate handles the transaction.

    With ``lease_duration_sec`` set, the attempt row is stamped with this
    process's ``owner_id`` and a ``lease_expires_at`` derived from
    ``started_at`` inside the same transaction (REQ-005). With ``None``,
    both lease columns stay NULL for legacy callers.
    """
    # processed_events semantics:
    # - Contains event IDs for attempts that have been STARTED (not necessarily completed)
    # - A running attempt's event ID will be in processed_events even though the attempt
    #   is still in progress
    # - Recovery logic marks stale running attempts as failed and removes their event IDs
    attempt_id = str(uuid.uuid4())
    now = _now()
    owner_id: str | None = None
    lease_expires_at: str | None = None
    if lease_duration_sec is not None:
        owner_id = get_owner_id()
        lease_expires_at = lease_expires_from(now, lease_duration_sec)
    with db.begin_immediate():
        if is_event_processed(db, event_id):
            return None
        # Single-source attempts insert: this begin_immediate() transaction is the
        # only path that writes running attempts rows, stamped with lease columns here.
        db.execute(
            """

            INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, owner_id, lease_expires_at)
            VALUES (?, ?, ?, 'running', ?, ?, ?)
            """,
            (attempt_id, task_id, stage_id, now, owner_id, lease_expires_at),
        )
        db.execute(
            """

            INSERT INTO processed_events (event_id, task_id, stage_id, recorded_at, workflow_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, task_id, stage_id, now, workflow_id),
        )
    return AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        stage_id=stage_id,
        status="running",
        started_at=now,
    )
