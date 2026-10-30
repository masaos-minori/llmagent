#!/usr/bin/env python3
"""scripts/agent/workflow/idempotency_ops.py — Completed-stage ledger for workflow.sqlite."""

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.attempt_ops import insert_attempt, mark_attempt_finished
from agent.workflow.errors import StageAlreadyRunningError
from agent.workflow.models import AttemptRecord, AttemptStatus


def is_event_processed(db: SQLiteHelper, event_id: str) -> bool:
    """Check whether a completed-stage ledger row exists for an event ID."""
    rows = db.fetchall("SELECT 1 FROM processed_events WHERE event_id=?", (event_id,))
    return len(rows) > 0


def is_stage_completed(db: SQLiteHelper, task_id: str, stage_id: str) -> bool:
    """Return True when a ledger row records a completed attempt of the stage."""
    rows = db.fetchall(
        "SELECT 1 FROM processed_events WHERE task_id=? AND stage_id=? LIMIT 1",
        (task_id, stage_id),
    )
    return len(rows) > 0


def begin_stage_if_new(
    db: SQLiteHelper,
    task_id: str,
    stage_id: str,
) -> AttemptRecord | None:
    """Start the next attempt of a stage unless the stage already completed.

    Returns None only when the ledger holds a completed attempt of the stage; raises
    StageAlreadyRunningError when another attempt of it is `running`; otherwise inserts
    a `running` attempt with the next persisted number and returns it. No ledger row is
    written at start, so a crash leaves nothing that suppresses a re-run. The caller
    holds no transaction: `begin_immediate()` serializes the check and the insert, and
    no explicit commit() is called.
    """
    with db.begin_immediate():
        if is_stage_completed(db, task_id, stage_id):
            return None
        running = db.fetchall(
            "SELECT 1 FROM attempts WHERE task_id=? AND stage_id=? AND status=?",
            (task_id, stage_id, AttemptStatus.RUNNING.value),
        )
        if len(running) > 0:
            raise StageAlreadyRunningError(task_id, stage_id)
        return insert_attempt(db, task_id, stage_id)


def complete_stage_attempt(
    db: SQLiteHelper, attempt: AttemptRecord, workflow_id: str | None = None
) -> None:
    """Mark an attempt `completed` and write its ledger row in one transaction."""
    event_id = f"{attempt.task_id}:{attempt.stage_id}:{attempt.attempt_number}"
    with db.begin_immediate():
        mark_attempt_finished(db, attempt.attempt_id, AttemptStatus.COMPLETED.value)
        db.execute(
            """

            INSERT INTO processed_events
                (event_id, task_id, stage_id, recorded_at, workflow_id, attempt_id,
                 attempt_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                attempt.task_id,
                attempt.stage_id,
                _now(),
                workflow_id,
                attempt.attempt_id,
                attempt.attempt_number,
            ),
        )
