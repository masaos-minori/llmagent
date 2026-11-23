"""scripts/shared/mcp_dedup_rows.py — Ledger records and the typed error taxonomy.

The ledger row/acquisition records, the stored-result cap, read-time lease
classification, and the typed store/lease errors (REQ-002/REQ-006). Split from
shared/mcp_dedup.py by the scripts/ module size gate (24576 B); re-exported
through the shared.mcp_dedup facade.

The metrics view at the end of this file is the read-only projection of one
ledger for the health `details` block (mcpdl005 REQ-004): it borrows the
ledger's lock and connection and issues no write.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.mcp_dedup_ledger import DedupLedger

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


class DedupMetricsView:
    """Read-only projection of one ledger for the health `details` block (REQ-004).

    Bound to the ledger's own `_lock` and `_conn`, so the metrics read uses the store's
    configured busy_timeout and no second connection. Every helper issues one SELECT or one file
    stat and returns a JSON-safe value — counts and the store path, never `snapshot_json`,
    `result_json`, key values, or owner ids. No write and no `BEGIN IMMEDIATE`, so a read cannot
    mutate the ledger or extend a lease. A helper returns None when the lock is not acquired within
    the ledger's `DEDUP_READ_TIMEOUT_SECONDS`; the reported status never gates store or dispatcher
    behaviour (owner decision D-6).
    """

    def __init__(self, ledger: DedupLedger) -> None:
        self._ledger = ledger
        self._wait_ms = 0

    @property
    def db_path(self) -> str:
        """The store path, the same value the store's public property exposes."""
        return str(getattr(self._ledger, "db_path", ""))

    def lock_wait_ms(self) -> int:
        """Milliseconds this pass spent acquiring the lock; read it last."""
        return self._wait_ms

    def _acquire(self) -> bool:
        """Acquire the ledger lock within the read bound, accumulating the elapsed wait.

        The wait is recorded on a failed attempt too, so `lock_wait_ms` reports what the pass
        actually spent waiting, not only the successful acquisitions.
        """
        started = time.monotonic()
        acquired = self._ledger._lock.acquire(
            timeout=self._ledger.DEDUP_READ_TIMEOUT_SECONDS
        )
        self._wait_ms += int((time.monotonic() - started) * 1000)
        return acquired

    def _count(self, sql: str, params: tuple[Any, ...]) -> int | None:
        """One COUNT under the ledger lock; None when the read bound is exceeded."""
        if not self._acquire():
            return None
        try:
            rec = self._ledger._conn.execute(sql, params).fetchone()
            return int(rec[0]) if rec is not None else None
        finally:
            self._ledger._lock.release()

    def row_states(self) -> dict[str, int] | None:
        """Per-status counts, at most `MAX_METRICS_ROW_STATES` distinct states."""
        if not self._acquire():
            return None
        try:
            return {
                rec[0]: int(rec[1])
                for rec in self._ledger._conn.execute(
                    "SELECT status, COUNT(*) FROM dedup_call_state GROUP BY status LIMIT ?",
                    (self._ledger.MAX_METRICS_ROW_STATES,),
                )
            }
        finally:
            self._ledger._lock.release()

    def pending_overdue(self, now_epoch: float) -> int | None:
        """Pending rows whose lease is past `now_epoch`."""
        return self._count(
            "SELECT COUNT(*) FROM dedup_call_state"
            " WHERE status = 'pending' AND lease_expires_epoch < ?",
            (now_epoch,),
        )

    def created_since(self, floor_epoch: float) -> int | None:
        """Rows with `created_epoch` at or after `floor_epoch`."""
        return self._count(
            "SELECT COUNT(*) FROM dedup_call_state WHERE created_epoch >= ?",
            (floor_epoch,),
        )

    def held_past_retention(self, now_epoch: float, retention_days: int) -> int | None:
        """Held rows past the retention age: what the sweep left behind (REQ-003).

        0 when no hold is configured; None when the lock is not acquired within the read bound,
        the same contract as the other helpers.
        """
        if not self._acquire():
            return None
        held = tuple(self._ledger._legal_hold_states())
        try:
            if not held:
                return 0
            placeholders = ", ".join("?" for _ in held)
            sql = f"SELECT COUNT(*) FROM dedup_call_state WHERE status IN ({placeholders}) AND updated_epoch < ?"  # nosec B608 — the placeholder list is generated from the validated LEGAL_HOLD_STATES names, every value bound through ? parameters
            rec = self._ledger._conn.execute(
                sql,
                (*held, now_epoch - retention_days * 86400),
            ).fetchone()
            return int(rec[0]) if rec is not None else None
        finally:
            self._ledger._lock.release()

    def wal_size_bytes(self) -> int | None:
        """Size of the store's `-wal` file; 0 when the file does not exist."""
        if not self._acquire():
            return None
        try:
            return int(Path(f"{self.db_path}-wal").stat().st_size)
        except OSError:
            return 0
        finally:
            self._ledger._lock.release()
