"""Concurrency races for the dedup lease contract (mcpdl002 Plan Phase 1, row 10).

Test-first evidence: written against the lease/owner contract that row 01 will
implement (REQ-001..REQ-003; AC-1..AC-3). Against the pre-change store the
suite fails by design (the acquisition API, lease columns, and typed conflict do
not exist yet); from Phase 2 on it is a passing regression member.

Coverage split (row 10 owns multi-caller races only):
- 100 concurrent in-process callers on one key (asyncio.to_thread)
- multi-connection ownership within one process (separate store handles)
- multi-process claim races via short-lived subprocesses on one DB path
- heartbeat-extends-lease vs stale recovery
- finalize-vs-recovery race
- kill-during-dispatch leaves an expired pending row that only reconciles

All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.
Determinism: fixed lease constants, bounded fixed-duration waits tied to the
lease value, subprocess timeouts; no unbounded sleeps.
"""

from __future__ import annotations

import asyncio
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
import shared.mcp_dedup as mcp_dedup
from shared.mcp_dedup import DedupStore

_SNAP = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "user_version": "42",
}

# Fixed lease scheduling constants (bounded-duration policy, Plan Risks).
LEASE_SECONDS = 2
SHORT_LEASE_SECONDS = 1
MAX_ATTEMPTS = 3
_SUBPROCESS_TIMEOUT = 30


def _scripts_dir() -> str:
    return str(Path(__file__).resolve().parents[2] / "scripts")


def _open_store(
    path: str | Path,
    *,
    lease_seconds: int = LEASE_SECONDS,
    max_attempts: int = MAX_ATTEMPTS,
) -> DedupStore:
    """Open a store handle with the lease contract parameters (row 01 API)."""
    return DedupStore(
        str(path),
        lease_seconds=lease_seconds,
        max_attempts=max_attempts,
        busy_timeout_ms=5000,
    )


def _lease_conflict() -> type[Exception]:
    """Typed ownership-conflict error surfaced through the store module."""
    return mcp_dedup.DedupLeaseConflict


def _db_rows(path: str | Path) -> dict[str, tuple[str, str | None, int]]:
    """Direct read of the ledger rows: key -> (status, owner_id, attempt_number)."""
    conn = sqlite3.connect(str(path))
    try:
        return {
            str(rec[0]): (str(rec[1]), rec[2], int(rec[3]))
            for rec in conn.execute(
                "SELECT key, status, owner_id, attempt_number FROM dedup_call_state"
            )
        }
    finally:
        conn.close()


def _child_acquire_code(path: str, owner_id: str, lease_seconds: int) -> str:
    return (
        "import sys; sys.path.insert(0, " + repr(_scripts_dir()) + ");"
        "from shared.mcp_dedup import DedupStore;"
        "s = DedupStore("
        + repr(str(path))
        + ", lease_seconds="
        + repr(lease_seconds)
        + ", max_attempts="
        + repr(MAX_ATTEMPTS)
        + ", busy_timeout_ms=5000);"
        "r = s.try_acquire_execution('race-key', 'write_file', 'hash1', "
        + repr(_SNAP)
        + ", "
        + repr(owner_id)
        + ");"
        "print(r.status);"
        "s.close()"
    )


class TestSingleKeyAcquisition:
    def test_100_concurrent_callers_exactly_one_acquired(self, tmp_path):
        """AC-1: concurrent callers on one key; exactly one owner is granted."""
        store = _open_store(tmp_path / "dedup.sqlite")

        async def _run() -> list[object]:
            async def call(i: int) -> object:
                return await asyncio.to_thread(
                    store.try_acquire_execution,
                    "k1",
                    "write_file",
                    "hash1",
                    _SNAP,
                    f"owner-{i}",
                )

            return await asyncio.gather(*(call(i) for i in range(100)))

        try:
            results = asyncio.run(_run())
            acquired = [r for r in results if r.status == "acquired"]
            assert len(acquired) == 1, f"acquired count={len(acquired)}"
            assert acquired[0].attempt_number == 1
            for r in results:
                if r is acquired[0]:
                    continue
                # The live lease blocks every other caller; expiry never grants.
                assert r.status in ("in_progress", "reconciliation_required")
        finally:
            store.close()

    def test_multi_process_claim_race_exactly_one_winner(self, tmp_path):
        """REQ-001: cross-process BEGIN IMMEDIATE claim race; one winner."""
        path = tmp_path / "dedup.sqlite"
        _open_store(path).close()  # first initialization happens in the parent

        procs = [
            subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    _child_acquire_code(path, owner, SHORT_LEASE_SECONDS),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for owner in ("proc-a", "proc-b")
        ]
        statuses: list[str] = []
        for proc in procs:
            stdout, stderr = proc.communicate(timeout=_SUBPROCESS_TIMEOUT)
            assert proc.returncode == 0, f"child failed: {stderr}"
            statuses.append(stdout.strip())
        assert statuses.count("acquired") == 1, f"statuses={statuses}"
        assert statuses.count("in_progress") == 1, f"statuses={statuses}"


class TestOwnerConditionalLease:
    def test_non_owner_heartbeat_and_finalize_conflict_typed(self, tmp_path):
        """AC-1/AC-2: separate handles on one file; only the owner may renew/finalize."""
        path = tmp_path / "dedup.sqlite"
        owner_store = _open_store(path)
        other_store = _open_store(path)
        try:
            result = owner_store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert result.status == "acquired"
            assert result.owner_id == "owner-A"

            # A second caller sees the live lease, never acquires.
            blocked = other_store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-B"
            )
            assert blocked.status == "in_progress"

            # Non-owner heartbeat and finalization fail with the typed conflict.
            with pytest.raises(_lease_conflict()):
                other_store.renew_lease("k1", "owner-B")
            with pytest.raises(_lease_conflict()):
                other_store.record_completed("k1", _SNAP, "done", "owner-B")
            with pytest.raises(_lease_conflict()):
                other_store.record_failed("k1", "timeout", "owner-B")
            with pytest.raises(_lease_conflict()):
                other_store.mark_interrupted("k1", "owner-B")

            # The owner path succeeds.
            renewed = owner_store.renew_lease("k1", "owner-A")
            assert renewed > time.time()
            owner_store.record_completed("k1", _SNAP, "done", "owner-A")
            assert _db_rows(path)["k1"][0] == "completed"
        finally:
            owner_store.close()
            other_store.close()

    def test_heartbeat_blocks_stale_recovery(self, tmp_path):
        """AC-3: renew_lease extends the lease so expiry never reaches classification."""
        store = _open_store(
            tmp_path / "dedup.sqlite", lease_seconds=SHORT_LEASE_SECONDS
        )
        try:
            acquired = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert acquired.status == "acquired"
            deadline = time.time() + SHORT_LEASE_SECONDS + 0.6
            while time.time() < deadline:
                store.renew_lease("k1", "owner-A")
                time.sleep(0.2)
            # Past the original lease window the heartbeat keeps ownership live.
            blocked = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-B"
            )
            assert blocked.status == "in_progress"
        finally:
            store.close()

    def test_expired_lease_only_reconciles_never_grants(self, tmp_path):
        """AC-3: lease expiry alone yields reconciliation_required, not acquired."""
        store = _open_store(
            tmp_path / "dedup.sqlite", lease_seconds=SHORT_LEASE_SECONDS
        )
        try:
            acquired = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert acquired.status == "acquired"
            time.sleep(SHORT_LEASE_SECONDS + 0.6)
            expired = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-B"
            )
            assert expired.status == "reconciliation_required"
            # The stored row is unchanged pending; attempt number does not advance.
            status, owner, attempt = _db_rows(path_of(store))["k1"]
            assert status == "pending"
            assert owner == "owner-A"
            assert attempt == 1
        finally:
            store.close()


class TestFinalizeVsRecoveryRace:
    def test_recovery_finalizes_last_heartbeat_winner_and_blocks_old_owner(
        self, tmp_path
    ):
        """AC-1/AC-3: after reconciliation the new attempt owner finalizes;
        the old owner's finalization raises the typed conflict."""
        store = _open_store(
            tmp_path / "dedup.sqlite", lease_seconds=SHORT_LEASE_SECONDS
        )
        try:
            first = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert first.status == "acquired"
            time.sleep(SHORT_LEASE_SECONDS + 0.6)
            # Reconciliation path (gated by max_attempts) recovers the stale row.
            store.reconcile_execution("k1")
            second = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-B"
            )
            assert second.status == "acquired"
            assert second.attempt_number == 2
            store.renew_lease("k1", "owner-B")
            store.record_completed("k1", _SNAP, "done-by-B", "owner-B")
            # The old owner can no longer finalize the row.
            with pytest.raises(_lease_conflict()):
                store.record_completed("k1", _SNAP, "done-by-A", "owner-A")
            with pytest.raises(_lease_conflict()):
                store.renew_lease("k1", "owner-A")
        finally:
            store.close()

    def test_old_owner_finalize_on_reconciled_row_raises_conflict(self, tmp_path):
        """AC-2: reconciliation moves the row out of the old owner's reach."""
        store = _open_store(
            tmp_path / "dedup.sqlite", lease_seconds=SHORT_LEASE_SECONDS
        )
        try:
            acquired = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert acquired.status == "acquired"
            time.sleep(SHORT_LEASE_SECONDS + 0.6)
            store.reconcile_execution("k1")
            with pytest.raises(_lease_conflict()):
                store.record_failed("k1", "timeout", "owner-A")
            with pytest.raises(_lease_conflict()):
                store.mark_interrupted("k1", "owner-A")
        finally:
            store.close()

    def test_reconcile_refused_while_lease_live(self, tmp_path):
        """AC-3: only an expired lease can be recovered; a live lease refuses."""
        store = _open_store(tmp_path / "dedup.sqlite", lease_seconds=LEASE_SECONDS)
        try:
            acquired = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-A"
            )
            assert acquired.status == "acquired"
            with pytest.raises(_lease_conflict()):
                store.reconcile_execution("k1")
        finally:
            store.close()


class TestKillDuringDispatch:
    def test_killed_owner_leaves_expired_pending_reconciles_only(self, tmp_path):
        """REQ-003/AC-3: a killed handler leaves an expired pending row that only
        classifies to reconciliation_required (outcome-unknown semantics)."""
        path = tmp_path / "dedup.sqlite"
        _open_store(path).close()
        code = (
            "import sys, os; sys.path.insert(0, " + repr(_scripts_dir()) + ");"
            "from shared.mcp_dedup import DedupStore;"
            "s = DedupStore("
            + repr(str(path))
            + ", lease_seconds="
            + repr(SHORT_LEASE_SECONDS)
            + ", max_attempts="
            + repr(MAX_ATTEMPTS)
            + ", busy_timeout_ms=5000);"
            "r = s.try_acquire_execution('k1', 'write_file', 'hash1', "
            + repr(_SNAP)
            + ", 'owner-crashed');"
            "print(r.status, flush=True); os._exit(0)"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        assert proc.stdout.strip() == "acquired"
        assert _db_rows(path)["k1"][0] == "pending"

        time.sleep(SHORT_LEASE_SECONDS + 0.6)
        store = _open_store(path)
        try:
            result = store.try_acquire_execution(
                "k1", "write_file", "hash1", _SNAP, "owner-next"
            )
            assert result.status == "reconciliation_required"
        finally:
            store.close()


def path_of(store: DedupStore) -> str:
    """Resolved DB path of an open store handle (regression-support accessor)."""
    return store.db_path
