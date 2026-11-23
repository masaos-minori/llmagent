"""scripts/shared/mcp_dedup_rows.py — Ledger records and the typed error taxonomy.

The ledger row/acquisition records, the stored-result cap, read-time lease
classification, and the typed store/lease errors (REQ-002/REQ-006). Split from
shared/mcp_dedup.py by the scripts/ module size gate (24576 B); re-exported
through the shared.mcp_dedup facade.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from shared.mcp_call_state_contract import RESULT_CLASSES
from shared.mcp_dedup_schema import RESULT_MAX_CHARS, RESULT_PREVIEW_CHARS


class DedupStoreError(Exception):
    """Typed store error taxonomy (REQ-006).

    `state` carries the start state that refused the open
    (lost | replaced | legacy_or_unverified | schema_mismatch | healthy |
    first_initialization for resolution refusals).
    """

    def __init__(self, state: str, message: str) -> None:
        self.state = state
        super().__init__(f"{state}: {message}")


class DedupLeaseConflict(Exception):
    """Typed ownership-conflict error: an owner-conditional write that
    updated zero rows (REQ-002/REQ-004)."""


@dataclass(frozen=True)
class DedupRow:
    key: str
    tool_name: str
    args_hash: str
    status: str
    owner_id: str | None
    lease_expires_epoch: float | None
    attempt_number: int
    snapshot: Mapping[str, str]
    created_epoch: float
    updated_epoch: float
    result: Any
    result_sha256: str | None = None
    result_size_bytes: int | None = None
    result_class: str | None = None
    result_code: str | None = None
    external_ref: str | None = None


def _row_from_record(rec: sqlite3.Row) -> DedupRow:
    raw_snapshot = rec["snapshot_json"]
    raw_result = rec["result_json"]
    try:
        snapshot = json.loads(raw_snapshot) if raw_snapshot else {}
    except json.JSONDecodeError:
        snapshot = {}
    try:
        result = json.loads(raw_result) if raw_result is not None else None
    except json.JSONDecodeError:
        result = raw_result
    return DedupRow(
        key=rec["key"],
        tool_name=rec["tool_name"],
        args_hash=rec["args_hash"],
        status=rec["status"],
        owner_id=rec["owner_id"],
        lease_expires_epoch=(
            float(rec["lease_expires_epoch"])
            if rec["lease_expires_epoch"] is not None
            else None
        ),
        attempt_number=int(rec["attempt_number"]),
        snapshot=snapshot,
        created_epoch=float(rec["created_epoch"]),
        updated_epoch=float(rec["updated_epoch"]),
        result=result,
        result_sha256=rec["result_sha256"],
        result_size_bytes=(
            int(rec["result_size_bytes"])
            if rec["result_size_bytes"] is not None
            else None
        ),
        result_class=rec["result_class"],
        result_code=rec["result_code"],
        external_ref=rec["external_ref"],
    )


# Redaction runs before preview creation (REQ-003): Bearer values, secret-like
# query parameters, and absolute filesystem paths are masked, then the preview
# is sliced. Only previews are redacted; a `complete` result replays exactly.
_BEARING_RE = re.compile(r"(?i)\bBearer\s+\S+")
_SECRET_QUERY_RE = re.compile(
    r"(?i)([?&])(sig|signature|token|key|secret|password)=[^&\s]+"
)
_ABS_PATH_RE = re.compile(r"(/(?:home|opt|var|tmp|root|Users))(?:/[^\s\"']*)?")


def redact_preview(text: str) -> str:
    """Mask sensitive shapes in a serialized payload before preview slicing."""
    text = _BEARING_RE.sub("Bearer <redacted>", text)
    text = _SECRET_QUERY_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}=<redacted>", text)
    return _ABS_PATH_RE.sub(lambda m: f"{m.group(1)}/<redacted>", text)


@dataclass(frozen=True)
class StoredResult:
    """Classification of one stored result payload (REQ-003).

    `payload` is what the ledger stores: the exact serialized text for
    `complete`, the truncated sentinel for `redacted_preview`. `sha256` and
    `size_bytes` always describe the full serialized payload (UTF-8).
    """

    payload: str
    sha256: str
    size_bytes: int
    result_class: str

    def __post_init__(self) -> None:
        if self.result_class not in RESULT_CLASSES:
            raise ValueError(
                f"StoredResult: result_class {self.result_class!r} is not in "
                "RESULT_CLASSES"
            )


def classify_result(result: Any) -> StoredResult:
    """Classify a result once at store time; redaction precedes the preview."""
    serialized = json.dumps(result, ensure_ascii=False)
    full_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    size_bytes = len(serialized.encode("utf-8"))
    if len(serialized) <= RESULT_MAX_CHARS:
        return StoredResult(
            payload=serialized,
            sha256=full_hash,
            size_bytes=size_bytes,
            result_class="complete",
        )
    preview = redact_preview(serialized)[:RESULT_PREVIEW_CHARS]
    sentinel = json.dumps(
        {"truncated": True, "sha256": full_hash, "preview": preview},
        ensure_ascii=False,
    )
    return StoredResult(
        payload=sentinel,
        sha256=full_hash,
        size_bytes=size_bytes,
        result_class="redacted_preview",
    )


def _cap_result(result: Any) -> str:
    return classify_result(result).payload


@dataclass(frozen=True)
class AcquisitionResult:
    """Outcome of `try_acquire_execution` (Plan D-5 vocabulary).

    `status` is one of ACQUISITION_STATES. `result` carries the stored replay
    payload only for `replay_completed`; `owner_id`/`lease_expires_epoch` are
    set for `acquired`.
    """

    status: str
    key: str
    tool_name: str
    args_hash: str
    owner_id: str | None
    attempt_number: int
    lease_expires_epoch: float | None
    snapshot: Mapping[str, str]
    result: Any = None


@dataclass(frozen=True)
class CallStateView:
    """Control-API projection of one ledger row (REQ-001), read-only.

    Carries only structured fields: no raw arguments, credentials, signed URLs,
    raw exceptions, or internal paths. `agent_state` is filled by the ledger
    through `agent_state_for` from the contract module.
    """

    key: str
    tool_name: str
    ledger_status: str
    attempt_number: int
    lease_live: bool
    lease_expires_epoch: float | None
    result_class: str | None
    result_code: str | None
    result_size_bytes: int | None
    result_sha256: str | None
    external_ref: str | None
    attempts_exhausted: bool
    agent_state: str
    reconciliation_required: bool
    error_code: str


def classify_interrupted(
    row: DedupRow,
    lease_seconds: int,
    *,
    now_epoch: float | None = None,
) -> str:
    """Read-time classification: a pending row whose lease has expired is
    'interrupted' (lease-state driven, REQ-003).

    Non-mutating: the stored row only changes through reconcile_execution or an
    owner's mark_interrupted, so repeated lookups never advance any epoch.
    """
    if row.status != "pending":
        return row.status
    now = time.time() if now_epoch is None else now_epoch
    if row.lease_expires_epoch is not None:
        expired = row.lease_expires_epoch <= now
    else:
        # Rows without a lease column value predate the lease contract: fall
        # back to the lease window measured from the row's creation.
        expired = now - row.created_epoch > lease_seconds
    return "interrupted" if expired else "pending"
