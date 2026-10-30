#!/usr/bin/env python3
"""scripts/agent/workflow/task_ops.py — Task CRUD operations for workflow.sqlite."""

import sqlite3
import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.errors import TaskNotFoundError, TaskTransitionError
from agent.workflow.models import TaskRecord, TaskStatus, is_task_transition_allowed

# Statuses a task may be claimed (moved to running) from; shared by claim_task
# and assert_resumable so the resume contract lives in this module only.
_CLAIMABLE_STATUSES: frozenset[TaskStatus] = frozenset(
    {TaskStatus.PENDING, TaskStatus.FAILED}
)


def create_task(
    db: SQLiteHelper,
    session_id: str | None,
    turn_number: int | None,
    workflow_version: str,
    workflow_id: str,
) -> TaskRecord:
    """Create a new task record.

    The `task_nonce` is a globally unique opaque identifier (UUID4) generated here
    for this task row; it is never derived from caller-supplied fields. `session_id` and
    `turn_number` are recorded metadata only; `turn_number` is a process-local counter
    (`agent/conversation_state_manager.py`, incremented in `append_user_message`) and is
    not part of task identity. The `tasks.task_nonce` UNIQUE constraint therefore
    stays inert (a backstop against a future key-derivation regression), and resume across
    a retained `workflow.sqlite` uses `task_id`, not this key.
    """
    task_nonce = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """

        INSERT INTO tasks
            (task_id, session_id, workflow_id, turn_number, workflow_version,
             status, task_nonce, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        (
            task_id,
            session_id,
            workflow_id,
            turn_number,
            workflow_version,
            task_nonce,
            now,
            now,
        ),
    )
    db.commit()
    return TaskRecord(
        task_id=task_id,
        session_id=session_id,
        turn_number=turn_number,
        workflow_version=workflow_version,
        status="pending",
        task_nonce=task_nonce,
        created_at=now,
        updated_at=now,
        workflow_id=workflow_id,
    )


def _current_status(db: SQLiteHelper, task_id: str) -> str:
    """Return the persisted status of a task, raising TaskNotFoundError when absent."""
    rows = db.fetchall("SELECT status FROM tasks WHERE task_id=?", (task_id,))
    if not rows:
        raise TaskNotFoundError(task_id)
    return str(rows[0]["status"])


def transition_task_in_txn(
    db: SQLiteHelper,
    task_id: str,
    new_status: str,
    expected: str | None = None,
) -> None:
    """Validate and apply one task status change inside the caller's write transaction.

    The caller holds `begin_immediate()`; this function never commits. Raises
    TaskNotFoundError for an unknown task and TaskTransitionError for an unknown
    status, a disallowed edge, an `expected` mismatch, or a lost conditional update.
    """
    current = _current_status(db, task_id)
    try:
        new = TaskStatus(new_status)
        cur = TaskStatus(current)
    except ValueError as exc:
        raise TaskTransitionError(task_id, current, new_status) from exc
    if expected is not None and current != expected:
        raise TaskTransitionError(task_id, current, new_status)
    if not is_task_transition_allowed(cur, new):
        raise TaskTransitionError(task_id, current, new_status)
    cursor = db.execute(
        "UPDATE tasks SET status=?, updated_at=? WHERE task_id=? AND status=?",
        (new.value, _now(), task_id, current),
    )
    if cursor.rowcount != 1:
        raise TaskTransitionError(task_id, current, new_status)


def transition_task(
    db: SQLiteHelper,
    task_id: str,
    new_status: str,
    expected: str | None = None,
) -> None:
    """Apply one validated task status change in its own write transaction."""
    with db.begin_immediate():
        transition_task_in_txn(db, task_id, new_status, expected)


def update_task_status(db: SQLiteHelper, task_id: str, status: str) -> None:
    """Update the status of a task record in the database.

    Unconditional write kept for `WorkflowEngine.run()`, which still writes `running`
    for any task; it becomes `transition_task` once the engine claims through
    `claim_task`.
    """
    db.execute(
        "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
        (status, _now(), task_id),
    )
    db.commit()


def claim_task(db: SQLiteHelper, task_id: str) -> None:
    """Move a `pending` or `failed` task to `running`; reject every other status."""
    with db.begin_immediate():
        current = _current_status(db, task_id)
        if current not in _CLAIMABLE_STATUSES:
            raise TaskTransitionError(task_id, current, TaskStatus.RUNNING.value)
        transition_task_in_txn(db, task_id, TaskStatus.RUNNING.value, current)


def assert_resumable(task: TaskRecord) -> None:
    """Raise TaskTransitionError when a fetched task is not in a claimable status."""
    if task.status not in _CLAIMABLE_STATUSES:
        raise TaskTransitionError(task.task_id, task.status, TaskStatus.RUNNING.value)


def _row_to_task(r: sqlite3.Row) -> TaskRecord:
    """Convert a database row into a TaskRecord dataclass instance."""
    row = dict(r)
    return TaskRecord(
        task_id=row["task_id"],
        session_id=row["session_id"],
        turn_number=row["turn_number"],
        workflow_version=row["workflow_version"],
        status=row["status"],
        task_nonce=row["task_nonce"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        workflow_id=row.get("workflow_id") or "",
    )


def get_task_by_id(db: SQLiteHelper, task_id: str) -> TaskRecord | None:
    """Return the task record for the given task_id, or None if absent."""
    rows = db.fetchall("SELECT * FROM tasks WHERE task_id=?", (task_id,))
    if not rows:
        return None
    return _row_to_task(rows[0])


def get_task_count(db: SQLiteHelper, session_id: str) -> int:
    """Return the number of tasks associated with a session."""
    rows = db.fetchall(
        "SELECT COUNT(*) as cnt FROM tasks WHERE session_id=?", (session_id,)
    )
    return int(rows[0]["cnt"]) if rows else 0


def get_workflow_count(db: SQLiteHelper, session_id: str) -> int:
    """Return the number of distinct workflows for a session."""
    rows = db.fetchall(
        "SELECT COUNT(DISTINCT workflow_id) as cnt"
        " FROM tasks WHERE session_id=? AND workflow_id IS NOT NULL",
        (session_id,),
    )
    return int(rows[0]["cnt"]) if rows else 0
