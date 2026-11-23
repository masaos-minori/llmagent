"""scripts/shared/mcp_dedup_claim.py — acquisition and lease claim of the dedup store.

The claim half of the ledger state machine: the one typed acquisition
(`try_acquire_execution`), its locked classification body, the owner-lease renewal
the dispatcher heartbeat calls, and the single-transaction, history-append and
locked row-read helpers those paths share. Split from `shared/mcp_dedup_ledger.py`
by the scripts/ module size gate (24576 B); `shared.mcp_dedup_ledger.DedupLedger`
inherits this class, so the store's public API, the row vocabulary and every
existing call site are unchanged. These methods run on the `_conn` / `_lock` /
`_lease_seconds` / `_max_attempts` attributes that the shared.mcp_dedup.DedupStore
subclass initializes in its __init__; all sqlite3 connection handling stays in
shared/mcp_dedup.py.

Module family: shared leaf, never imports mcp_servers.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Mapping
from typing import Any

from shared.execution_snapshot import snapshot_json, snapshots_equal
from shared.mcp_dedup_rows import (
    AcquisitionResult,
    DedupLeaseConflict,
    DedupRow,
    _row_from_record,
)


class DedupClaim:
    """Claim and lease methods shared by the DedupStore handle.

    Base class only: the subclass owns the sqlite connection lifecycle and the
    remaining ledger operations. Required subclass attributes (initialized before
    any method here runs): `_conn` (isolation_level=None), `_lock`,
    `_lease_seconds`, `_max_attempts`.
    """

    _conn: sqlite3.Connection
    _lock: threading.Lock
    _lease_seconds: int
    _max_attempts: int

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
        allow_interrupted_recovery: bool = True,
    ) -> AcquisitionResult:
        """One typed acquisition (D-1): read, classify, insert-or-deny in a
        single BEGIN IMMEDIATE transaction. Handler execution never holds the
        write lock. Never resets a terminal row and never grants a retry on
        lease expiry alone (REQ-002/REQ-003). Recovery of an `interrupted` row
        requires the caller's permission (`allow_interrupted_recovery`)."""
        now = time.time() if now_epoch is None else now_epoch
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._fetch_locked(key)
                result = self._acquire_locked(
                    row,
                    key,
                    tool_name,
                    args_hash,
                    snapshot,
                    owner_id,
                    now,
                    allow_interrupted_recovery=allow_interrupted_recovery,
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
        *,
        allow_interrupted_recovery: bool = True,
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
            if not allow_interrupted_recovery:
                # Recovery outside the caller's declared retry policy is refused
                # here: no mutation, no history entry, attempt stays as stored
                # (REQ-004, AC-3).
                return result("reconciliation_required", row.attempt_number, stored=row)
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

    # --- lease renewal ---------------------------------------------------
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

    def _fetch_locked(self, key: str) -> DedupRow | None:
        rec = self._conn.execute(
            "SELECT key, tool_name, args_hash, status, owner_id, lease_expires_epoch,"
            " attempt_number, snapshot_json, created_epoch, updated_epoch, result_json,"
            " result_sha256, result_size_bytes, result_class, result_code, external_ref"
            " FROM dedup_call_state WHERE key = ?",
            (key,),
        ).fetchone()
        return _row_from_record(rec) if rec is not None else None
