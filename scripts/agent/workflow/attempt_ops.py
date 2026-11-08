#!/usr/bin/env python3
"""scripts/agent/workflow/attempt_ops.py — Attempt operations for workflow.sqlite."""

import os
import secrets
import socket
from datetime import timedelta

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now
from shared.json_utils import parse_iso_utc

from agent.workflow.models import ATTEMPT_STATUSES

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


def finish_attempt(
    db: SQLiteHelper,
    attempt_id: str,
    status: str,
    error_msg: str | None = None,
    error_kind: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Mark an attempt as completed with the given status and optional error details.

    Raises:
        ValueError: if `status` is not in the `attempts.status` vocabulary.
    """
    if status not in ATTEMPT_STATUSES:
        raise ValueError(
            f"invalid attempts.status {status!r} (allowed: {sorted(ATTEMPT_STATUSES)})"
        )
    db.execute(
        "UPDATE attempts SET status=?, ended_at=?, error_msg=?, error_kind=?, error_detail=? WHERE attempt_id=?",
        (status, _now(), error_msg, error_kind, error_detail, attempt_id),
    )
    db.commit()
