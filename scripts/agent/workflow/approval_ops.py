#!/usr/bin/env python3
"""agent/workflow/approval_ops.py — Approval operations for workflow.sqlite."""

import uuid

from agent.workflow.models import ApprovalRecord
from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now


def request_approval(
    db: SQLiteHelper, task_id: str, workflow_id: str = "", stage_id: str | None = None
) -> ApprovalRecord:
    """Insert a pending approval gate for a task (or specific stage)."""
    approval_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """

        INSERT INTO approvals (approval_id, task_id, workflow_id, stage_id, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (approval_id, task_id, workflow_id, stage_id, now),
    )
    db.commit()
    return ApprovalRecord(
        approval_id=approval_id,
        task_id=task_id,
        stage_id=stage_id,
        status="pending",
        reason=None,
        created_at=now,
        resolved_at=None,
        workflow_id=workflow_id,
    )


def resolve_approval(
    db: SQLiteHelper, approval_id: str, status: str, reason: str | None = None
) -> None:
    """Set approval status to 'approved' or 'rejected'."""
    db.execute(
        "UPDATE approvals SET status=?, reason=?, resolved_at=? WHERE approval_id=?",
        (status, reason, _now(), approval_id),
    )
    db.commit()


def get_latest_approval(db: SQLiteHelper, task_id: str) -> ApprovalRecord | None:
    """Return the most recent approval record for a task, regardless of status.

    Not filtered to status='pending' — callers that need only pending records
    should filter on the returned record's .status, or use
    find_pending_approval_by_session() / find_latest_pending_approval() /
    find_approval_by_id() for status-scoped lookups.
    """
    rows = db.fetchall(
        "SELECT * FROM approvals WHERE task_id=? ORDER BY created_at DESC LIMIT 1",
        (task_id,),
    )
    if not rows:
        return None
    r = rows[0]
    return ApprovalRecord(
        approval_id=r["approval_id"],
        task_id=r["task_id"],
        stage_id=r["stage_id"],
        status=r["status"],
        reason=r["reason"],
        created_at=r["created_at"],
        resolved_at=r["resolved_at"],
        workflow_id=r["workflow_id"] if "workflow_id" in r.keys() else "",
    )


def find_pending_approval_by_session(
    db: SQLiteHelper, session_id: str
) -> tuple[str, ApprovalRecord] | None:
    """Return (task_id, approval) for the most recent pending-approval task in this session, or None."""
    rows = db.fetchall(
        """

        SELECT t.task_id, a.approval_id, a.workflow_id, a.stage_id, a.reason, a.created_at, a.resolved_at
        FROM tasks t
        JOIN approvals a ON t.task_id = a.task_id
        WHERE t.session_id = ?
          AND t.status = 'pending_approval'
          AND a.status = 'pending'
        ORDER BY a.created_at DESC, a.rowid DESC
        LIMIT 1
        """,
        (session_id,),
    )
    if not rows:
        return None
    r = rows[0]
    return r["task_id"], ApprovalRecord(
        approval_id=r["approval_id"],
        task_id=r["task_id"],
        stage_id=r["stage_id"],
        status="pending",
        reason=r["reason"],
        created_at=r["created_at"],
        resolved_at=r["resolved_at"],
        workflow_id=r["workflow_id"] if "workflow_id" in r.keys() else "",
    )


def count_pending_approvals(db: SQLiteHelper) -> int:
    """Return the count of globally pending approvals."""
    rows = db.fetchall(
        """

        SELECT COUNT(*)
        FROM tasks t
        JOIN approvals a ON t.task_id = a.task_id
        WHERE t.status = 'pending_approval'
          AND a.status = 'pending'
        """,
        (),
    )
    return int(rows[0][0])


def find_approval_by_id(db: SQLiteHelper, approval_id: str) -> ApprovalRecord | None:
    """Return the ApprovalRecord for the given approval_id, or None if absent."""
    rows = db.fetchall(
        "SELECT * FROM approvals WHERE approval_id=?",
        (approval_id,),
    )
    if not rows:
        return None
    r = rows[0]
    return ApprovalRecord(
        approval_id=r["approval_id"],
        task_id=r["task_id"],
        stage_id=r["stage_id"],
        status=r["status"],
        reason=r["reason"],
        created_at=r["created_at"],
        resolved_at=r["resolved_at"],
        workflow_id=r["workflow_id"] if "workflow_id" in r.keys() else "",
    )


def find_latest_pending_approval(db: SQLiteHelper) -> tuple[str, ApprovalRecord] | None:
    """Return (task_id, approval) for the most recent globally pending approval, or None."""
    rows = db.fetchall(
        """

        SELECT t.task_id, a.approval_id, a.workflow_id, a.stage_id, a.reason, a.created_at, a.resolved_at
        FROM tasks t
        JOIN approvals a ON t.task_id = a.task_id
        WHERE t.status = 'pending_approval'
          AND a.status = 'pending'
        ORDER BY a.created_at DESC, a.rowid DESC
        LIMIT 1
        """,
        (),
    )
    if not rows:
        return None
    r = rows[0]
    return r["task_id"], ApprovalRecord(
        approval_id=r["approval_id"],
        task_id=r["task_id"],
        stage_id=r["stage_id"],
        status="pending",
        reason=r["reason"],
        created_at=r["created_at"],
        resolved_at=r["resolved_at"],
        workflow_id=r["workflow_id"] if "workflow_id" in r.keys() else "",
    )
