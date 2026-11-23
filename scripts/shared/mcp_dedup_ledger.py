"""scripts/shared/mcp_dedup_ledger.py — Call-ledger state machine of the dedup store.

The ledger operations of DedupStore: typed acquisition, owner leases,
finalization, reconciliation, reads, and the retention purge. Split from
shared/mcp_dedup.py by the scripts/ module size gate (24576 B). These methods
run on the `_conn` / `_lock` / `_lease_seconds` / `_max_attempts` attributes
that the shared.mcp_dedup.DedupStore subclass initializes in its __init__;
all sqlite3 connection handling stays in shared/mcp_dedup.py.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from collections.abc import Mapping
from typing import Any

from shared.execution_snapshot import snapshot_json, snapshots_equal
from shared.mcp_call_state_contract import (
    RECONCILE_OUTCOMES,
    agent_state_for,
)
from shared.mcp_dedup_rows import (
    AcquisitionResult,
    CallStateView,
    DedupLeaseConflict,
    DedupMetricsView,
    DedupRow,
    _row_from_record,
    classify_result,
)

logger = logging.getLogger(__name__)


class DedupLedger:
    """Ledger methods shared by the DedupStore handle.

    Base class only: the subclass owns the sqlite connection lifecycle and
    identity classification. Required subclass attributes (initialized before
    any ledger method runs): `_conn` (isolation_level=None), `_lock`,
    `_lease_seconds`, `_max_attempts`.
    """

    _conn: sqlite3.Connection
    _lock: threading.Lock
    _lease_seconds: int
    _max_attempts: int

    # Read bounds for the metrics view (mcpdl005 REQ-004): reporting limits, not thresholds (D-6).
    DEDUP_READ_TIMEOUT_SECONDS = 10
    MAX_METRICS_ROW_STATES = 32

    # --- write helpers -------------------------------------------------
    def _write_txn(self, statements: list[tuple[str, tuple[Any, ...]]]) -> int:
        """Run statements in one BEGIN IMMEDIATE transaction; return last rowcount."""
        with self._lock:
            rowcount = 0
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                for sql, params in statements:
                    rowcount = self._conn.execute(sql, params).rowcount
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        return rowcount

    def _append_history(
        self,
        key: str,
        attempt_number: int,
        owner_id: str | None,
        outcome: str,
        detail: str | None,
        now: float,
    ) -> tuple[str, tuple[Any, ...]]:
        return (
            "INSERT INTO call_attempt_history (key, attempt_number, owner_id,"
            " outcome, detail, recorded_epoch) VALUES (?, ?, ?, ?, ?, ?)",
            (key, attempt_number, owner_id, outcome, detail, now),
        )

    # --- acquisition ----------------------------------------------------
    def try_acquire_execution(
        self,
        key: str,
        tool_name: str,
        args_hash: str,
        snapshot: Mapping[str, str],
        owner_id: str,
        *,
        now_epoch: float | None = None,
    ) -> AcquisitionResult:
        """One typed acquisition (D-1): read, classify, insert-or-deny in a
        single BEGIN IMMEDIATE transaction. Handler execution never holds the
        write lock. Never resets a terminal row and never grants a retry on
        lease expiry alone (REQ-002/REQ-003)."""
        now = time.time() if now_epoch is None else now_epoch
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._fetch_locked(key)
                result = self._acquire_locked(
                    row, key, tool_name, args_hash, snapshot, owner_id, now
                )
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        return result

    def _acquire_locked(
        self,
        row: DedupRow | None,
        key: str,
        tool_name: str,
        args_hash: str,
        snapshot: Mapping[str, str],
        owner_id: str,
        now: float,
    ) -> AcquisitionResult:
        def result(
            status: str, attempt: int, *, stored: DedupRow | None = None
        ) -> AcquisitionResult:
            return AcquisitionResult(
                status=status,
                key=key,
                tool_name=stored.tool_name if stored else tool_name,
                args_hash=stored.args_hash if stored else args_hash,
                owner_id=owner_id
                if status == "acquired"
                else (stored.owner_id if stored else None),
                attempt_number=stored.attempt_number if stored else attempt,
                lease_expires_epoch=(
                    now + self._lease_seconds if status == "acquired" else None
                ),
                snapshot=dict(stored.snapshot) if stored else dict(snapshot),
                result=stored.result
                if stored and status == "replay_completed"
                else None,
            )

        if row is None:
            self._conn.execute(
                "INSERT INTO dedup_call_state (key, tool_name, args_hash, status,"
                " owner_id, lease_expires_epoch, attempt_number, snapshot_json,"
                " created_epoch, updated_epoch, result_json)"
                " VALUES (?, ?, ?, 'pending', ?, ?, 1, ?, ?, ?, NULL)",
                (
                    key,
                    tool_name,
                    args_hash,
                    owner_id,
                    now + self._lease_seconds,
                    snapshot_json(snapshot),
                    now,
                    now,
                ),
            )
            self._conn.execute(
                *self._append_history(key, 1, owner_id, "attempt", None, now)
            )
            return result("acquired", 1)

        if row.tool_name != tool_name or row.args_hash != args_hash:
            return result("contract_mismatch", row.attempt_number, stored=row)

        if row.status == "pending":
            if row.lease_expires_epoch is not None and row.lease_expires_epoch > now:
                return result("in_progress", row.attempt_number, stored=row)
            if row.attempt_number >= self._max_attempts:
                return result("outcome_unknown", row.attempt_number, stored=row)
            # Expired lease: classification only; a further attempt requires the
            # reconciliation path (reconcile_execution), never this call (AC-3).
            return result("reconciliation_required", row.attempt_number, stored=row)

        if row.status == "interrupted":
            if row.attempt_number >= self._max_attempts:
                return result("outcome_unknown", row.attempt_number, stored=row)
            attempt = row.attempt_number + 1
            # The recovery path re-opens the ledger row for a new attempt; the
            # terminal snapshot_json is deliberately left untouched (REQ-004:
            # it is only rewritten when the new attempt finalizes as completed).
            self._conn.execute(
                "UPDATE dedup_call_state SET status='pending', owner_id=?, "
                "lease_expires_epoch=?, attempt_number=?, "
                "updated_epoch=? WHERE key=? AND status='interrupted'",
                (owner_id, now + self._lease_seconds, attempt, now, key),
            )
            self._conn.execute(
                *self._append_history(
                    key, attempt, owner_id, "attempt", "post-recovery", now
                )
            )
            reopened = self._fetch_locked(key)
            return result("acquired", attempt, stored=reopened)

        if row.status == "completed":
            truncated = isinstance(row.result, dict) and bool(
                row.result.get("truncated")
            )
            if (
                row.result is not None
                and not truncated
                and snapshots_equal(row.snapshot, snapshot)
            ):
                out = result("replay_completed", row.attempt_number, stored=row)
                return AcquisitionResult(
                    status=out.status,
                    key=out.key,
                    tool_name=out.tool_name,
                    args_hash=out.args_hash,
                    owner_id=None,
                    attempt_number=out.attempt_number,
                    lease_expires_epoch=None,
                    snapshot=out.snapshot,
                    result=row.result,
                )
            return result("replay_unavailable", row.attempt_number, stored=row)

        # failed: terminal evidence, never re-attempted through the store.
        return result("replay_unavailable", row.attempt_number, stored=row)

    # --- lease / finalization ------------------------------------------
    def renew_lease(
        self, key: str, owner_id: str, *, now_epoch: float | None = None
    ) -> float:
        """Heartbeat: extend the lease of the exact owner's live pending row.

        Returns the new lease expiry. Zero-row updates raise DedupLeaseConflict:
        a stale, superseded, or finished owner never regains the row (REQ-002).
        """
        now = time.time() if now_epoch is None else now_epoch
        expiry = now + self._lease_seconds
        rowcount = self._write_txn(
            [
                (
                    "UPDATE dedup_call_state SET lease_expires_epoch=?, updated_epoch=?"
                    " WHERE key=? AND status='pending' AND owner_id=?"
                    " AND lease_expires_epoch > ?",
                    (expiry, now, key, owner_id, now),
                )
            ]
        )
        if rowcount != 1:
            raise DedupLeaseConflict(
                f"renew_lease updated {rowcount} rows: key={key} owner={owner_id} "
                "no longer holds a live lease"
            )
        return expiry

    def record_completed(
        self,
        key: str,
        snapshot: Mapping[str, str],
        result: Any,
        owner_id: str,
        *,
        now_epoch: float | None = None,
        external_ref: str | None = None,
    ) -> None:
        """Owner-conditional finalization; exactly one updated row (REQ-004).

        Result metadata is classified once at store time (REQ-003):
        `secure_reference` is stored only when `external_ref` is supplied.
        """
        now = time.time() if now_epoch is None else now_epoch
        stored = classify_result(result)
        result_class = "secure_reference" if external_ref else stored.result_class
        self._finalize(
            key,
            "completed",
            [
                (
                    "UPDATE dedup_call_state SET status='completed', snapshot_json=?,"
                    " updated_epoch=?, result_json=?, result_sha256=?,"
                    " result_size_bytes=?, result_class=?, external_ref=?,"
                    " lease_expires_epoch=NULL"
                    " WHERE key=? AND status='pending' AND owner_id=?"
                    " AND lease_expires_epoch > ?",
                    (
                        snapshot_json(snapshot),
                        now,
                        stored.payload,
                        stored.sha256,
                        stored.size_bytes,
                        result_class,
                        external_ref,
                        key,
                        owner_id,
                        now,
                    ),
                )
            ],
            owner_id,
            now,
        )

    def record_failed(
        self,
        key: str,
        error_class: str,
        owner_id: str,
        *,
        now_epoch: float | None = None,
    ) -> None:
        """Owner-conditional terminal failure; 'failed' is only produced here
        by an owner-finalized handler error (REQ-003). The result class is
        `replay_unavailable` with `result_code` = the error class (REQ-003)."""
        now = time.time() if now_epoch is None else now_epoch
        self._finalize(
            key,
            "failed",
            [
                (
                    "UPDATE dedup_call_state SET status='failed', updated_epoch=?,"
                    " result_json=?, result_class=?, result_code=?,"
                    " lease_expires_epoch=NULL"
                    " WHERE key=? AND status='pending' AND owner_id=?"
                    " AND lease_expires_epoch > ?",
                    (
                        now,
                        json.dumps({"error_class": error_class}),
                        "replay_unavailable",
                        error_class,
                        key,
                        owner_id,
                        now,
                    ),
                )
            ],
            owner_id,
            now,
            detail=error_class,
        )

    def mark_interrupted(
        self, key: str, owner_id: str, *, now_epoch: float | None = None
    ) -> None:
        """Owner-conditional voluntary interruption (dispatcher cancel path).

        The read-time classification of expired leases stays non-mutating;
        this write is the explicit owner-side signal.
        """
        now = time.time() if now_epoch is None else now_epoch
        self._finalize(
            key,
            "interrupted",
            [
                (
                    "UPDATE dedup_call_state SET status='interrupted', updated_epoch=?,"
                    " lease_expires_epoch=NULL"
                    " WHERE key=? AND status='pending' AND owner_id=?",
                    (now, key, owner_id),
                )
            ],
            owner_id,
            now,
        )

    def _finalize(
        self,
        key: str,
        outcome: str,
        statements: list[tuple[str, tuple[Any, ...]]],
        owner_id: str,
        now: float,
        detail: str | None = None,
    ) -> None:
        with self._lock:
            rowcount = 0
            attempt = 1
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._fetch_locked(key)
                for sql, params in statements:
                    rowcount = self._conn.execute(sql, params).rowcount
                if row is not None:
                    attempt = row.attempt_number
                if rowcount == 1:
                    self._conn.execute(
                        *self._append_history(
                            key, attempt, owner_id, outcome, detail, now
                        )
                    )
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        if rowcount != 1:
            raise DedupLeaseConflict(
                f"{outcome} updated {rowcount} rows: key={key} owner={owner_id} is not"
                " the live pending owner (terminal rows are immutable)"
            )

    def reconcile_execution(
        self, key: str, *, now_epoch: float | None = None
    ) -> DedupRow:
        """The reconciliation path for an expired lease (D-2, gated by
        max_attempts): move the stale pending row to 'interrupted' and append
        the decision to the attempt history. A live lease refuses.
        """
        now = time.time() if now_epoch is None else now_epoch
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._fetch_locked(key)
                if row is None:
                    self._conn.rollback()
                    raise DedupLeaseConflict(
                        f"reconcile_execution: no row for key={key}"
                    )
                if row.status != "pending":
                    self._conn.rollback()
                    raise DedupLeaseConflict(
                        f"reconcile_execution: key={key} is '{row.status}', not a"
                        " stale pending row"
                    )
                if (
                    row.lease_expires_epoch is not None
                    and row.lease_expires_epoch > now
                ):
                    self._conn.rollback()
                    raise DedupLeaseConflict(
                        f"reconcile_execution: key={key} still holds a live lease"
                        f" (expires {row.lease_expires_epoch:.0f}); only an expired"
                        " lease can be recovered (REQ-003)"
                    )
                if row.attempt_number >= self._max_attempts:
                    self._conn.rollback()
                    raise DedupLeaseConflict(
                        f"reconcile_execution: key={key} exhausted attempts"
                        f" ({row.attempt_number}/{self._max_attempts}); outcome"
                        " remains unknown"
                    )
                self._conn.execute(
                    "UPDATE dedup_call_state SET status='interrupted', updated_epoch=?,"
                    " lease_expires_epoch=NULL WHERE key=? AND status='pending'",
                    (now, key),
                )
                self._conn.execute(
                    *self._append_history(
                        key,
                        row.attempt_number,
                        row.owner_id,
                        "reconciled",
                        "lease_expired",
                        now,
                    )
                )
                reconciled = self._fetch_locked(key)
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        assert reconciled is not None
        logger.warning(
            "dedup reconciliation key=%s attempt=%d owner=%s -> interrupted",
            key[:12],
            reconciled.attempt_number,
            reconciled.owner_id,
        )
        return reconciled

    # --- reads -----------------------------------------------------------
    def _fetch_locked(self, key: str) -> DedupRow | None:
        rec = self._conn.execute(
            "SELECT key, tool_name, args_hash, status, owner_id, lease_expires_epoch,"
            " attempt_number, snapshot_json, created_epoch, updated_epoch, result_json,"
            " result_sha256, result_size_bytes, result_class, result_code, external_ref"
            " FROM dedup_call_state WHERE key = ?",
            (key,),
        ).fetchone()
        return _row_from_record(rec) if rec is not None else None

    def get_execution(self, key: str) -> DedupRow | None:
        """Pure read of one ledger row (observability/tests; no acquire-then-record
        pattern — acquisition is only through try_acquire_execution)."""
        with self._lock:
            return self._fetch_locked(key)

    def get_dedup_metrics_view(self) -> DedupMetricsView:
        """Read-only view bound to this ledger, for the health metrics read (REQ-004)."""
        return DedupMetricsView(self)

    def call_state_view(
        self, key: str, *, now_epoch: float | None = None
    ) -> CallStateView | None:
        """Read-only control-API projection of one row (REQ-001); None for an
        unknown key. `lease_live` is a pending row with an unexpired lease;
        `attempts_exhausted` is `attempt_number >= max_attempts`;
        `agent_state` comes from the shared mapping; `error_code` is
        `handler_failed` for failed rows, else `none`."""
        now = time.time() if now_epoch is None else now_epoch
        with self._lock:
            row = self._fetch_locked(key)
            if row is None:
                return None
            lease_live = row.status == "pending" and (
                row.lease_expires_epoch is not None and row.lease_expires_epoch > now
            )
        agent_state = agent_state_for(row.status, lease_live)
        return CallStateView(
            key=row.key,
            tool_name=row.tool_name,
            ledger_status=row.status,
            attempt_number=row.attempt_number,
            lease_live=lease_live,
            lease_expires_epoch=row.lease_expires_epoch,
            result_class=row.result_class,
            result_code=row.result_code,
            result_size_bytes=row.result_size_bytes,
            result_sha256=row.result_sha256,
            external_ref=row.external_ref,
            attempts_exhausted=row.attempt_number >= self._max_attempts,
            agent_state=agent_state,
            reconciliation_required=agent_state == "reconciliation_required",
            error_code="handler_failed" if row.status == "failed" else "none",
        )

    def append_reconcile_evidence(
        self,
        key: str,
        outcome: str,
        digest: str,
        *,
        now_epoch: float | None = None,
    ) -> None:
        """Append one reconcile decision to the attempt history (REQ-004):
        outcome `reconcile_decision`, detail `<outcome>:<digest>`. It never
        touches `dedup_call_state`; the decision and a non-sensitive digest are
        recorded without sensitive payloads."""
        if outcome not in RECONCILE_OUTCOMES:
            raise ValueError(
                f"append_reconcile_evidence: outcome {outcome!r} is not in "
                "RECONCILE_OUTCOMES"
            )
        now = time.time() if now_epoch is None else now_epoch
        self._write_txn(
            [
                (
                    "INSERT INTO call_attempt_history (key, attempt_number, owner_id,"
                    " outcome, detail, recorded_epoch)"
                    " SELECT ?, COALESCE(MAX(attempt_number), 1), NULL, ?, ?, ?"
                    " FROM call_attempt_history WHERE key = ?",
                    (key, "reconcile_decision", f"{outcome}:{digest}", now, key),
                )
            ]
        )

    def clear(self, key: str) -> None:
        """Delete the row for a key (used for dry-run outcomes that must not
        leave replayable state behind)."""
        self._write_txn([("DELETE FROM dedup_call_state WHERE key = ?", (key,))])

    def _legal_hold_states(self) -> tuple[str, ...]:
        """States the sweep must skip (REQ-003), read from the store's own config so
        purge_expired() and its only caller keep their signatures. No config means no hold."""
        config = getattr(self, "_config", None)
        return tuple(getattr(config, "legal_hold_states", ())) if config else ()

    def purge_expired(
        self, retention_days: int, *, now_epoch: float | None = None
    ) -> int:
        """Delete terminal (completed/failed/interrupted) rows older than
        retention, and attempt history older than retention.

        Pending rows are never purged here; their expiry path is classification.
        Rows in a configured legal-hold state are excluded (REQ-003); with no hold the
        emitted SQL is byte-identical to before, and a held row is not counted as purged —
        that is what makes it visible as held rather than as retained at large.
        """
        now = time.time() if now_epoch is None else now_epoch
        cutoff = now - retention_days * 86400
        hold = self._legal_hold_states()
        sql = (
            "DELETE FROM dedup_call_state"
            " WHERE status IN ('completed', 'failed', 'interrupted')"
            " AND updated_epoch < ?"
        )
        params: tuple[Any, ...] = (cutoff,)
        if hold:
            sql += f" AND status NOT IN ({', '.join('?' for _ in hold)})"
            params += tuple(hold)
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                cur = self._conn.execute(sql, params)
                purged_rows = cur.rowcount
                cur = self._conn.execute(
                    "DELETE FROM call_attempt_history WHERE recorded_epoch < ?",
                    (cutoff,),
                )
                purged_history = cur.rowcount
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        if purged_rows or purged_history:
            logger.info(
                "dedup purged %d terminal rows and %d history entries (cutoff=%.0f)",
                purged_rows,
                purged_history,
                cutoff,
            )
        return purged_rows
