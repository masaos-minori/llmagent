"""tests/integration/test_call_state_matrix_across_processes.py

Cross-process call-state matrix for issue mcpdl006 (REQ-001, REQ-003, REQ-004).

For every transition `agent_state_for` defines, the same logical key is read from three
independent sources and must agree: the control API over HTTP, the Agent recovery service
reading that response, and the mapping computed from the ledger row read directly (Plan
Decision D3). The in-process fakes of tests/agent/test_mcp_call_recovery.py are not
reused; every assertion here crosses a process boundary. Only tmp_path stores and
loopback are used, so nothing reaches a path under /opt/llm (AC-006).

Run 5x for the flakiness check:
    for i in {1..5}; do uv run pytest tests/integration/test_call_state_matrix_across_processes.py -m integration; done
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest
from agent.mcp_call_recovery import McpCallRecoveryService
from agent.workflow.tool_call_state_ops import ToolCallState
from shared.http_transport import ControlClient
from shared.mcp_call_state_contract import agent_state_for
from shared.mcp_config import McpServerConfig, TransportType
from shared.mcp_dedup import DedupStoreError, open_dedup_store

from tests.integration.conftest import (
    ControlApiLauncher,
    ControlApiProcess,
    CrashedChildRunner,
    SharedCallStore,
    fingerprint_payload,
)

pytestmark = pytest.mark.integration

_SERVER_KEY = "matrix-server"
_TOOL = "matrix-tool"
_OWNER = "matrix-side"
_ARGS_HASH = "matrix-args-hash"
# Component-keyed snapshot, the shape `execution_snapshot.COMPONENT_KEYS` defines, so the
# tests use the same call identity the production contract hashes.
_SNAPSHOT = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "dedup": "gen=1;schema=deadbeef",
}
# Fixed values rather than wall-clock: an expired lease is seeded with a past now_epoch,
# and the fixture's long lease keeps live-lease classification stable between the write
# and the read.
_EXPIRED_SEED_SEC = 600

# One child per asserted boundary. It reports the store's own typed start state, or the
# typed acquisition result, and records its handler running in an effects file, so a test
# counts executions per logical call instead of trusting a printed label.
_CHILD_SCRIPT = """
import json, sys
from shared.mcp_dedup import DedupStoreConfig, DedupStoreError, open_dedup_store

config = DedupStoreConfig(**json.loads(sys.argv[1]))
mode, key, tool, args_hash, snapshot = (
    sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], json.loads(sys.argv[6])
)
effects, child_id, now_arg = sys.argv[7], sys.argv[8], sys.argv[9]
try:
    store = open_dedup_store(config)
except DedupStoreError as exc:
    print(exc.state, flush=True)
    sys.exit(0)
if mode == "identity":
    print(store.start_state, flush=True)
    sys.exit(0)
now_epoch = float(now_arg) if now_arg else None
result = store.try_acquire_execution(
    key, tool, args_hash, snapshot, "test-child", now_epoch=now_epoch
)
print(result.status, flush=True)
if result.status == "acquired":
    with open(effects, "a") as f:
        f.write(child_id + "\\n")
    print("handler-ran", flush=True)
else:
    print("no-handler", flush=True)
"""


def _effects_path(tmp_path: Path) -> Path:
    path = tmp_path / "effects"
    path.write_text("")
    return path


def _argv(
    store: SharedCallStore,
    effects: Path,
    mode: str,
    key: str,
    child_id: str,
    args_hash: str = _ARGS_HASH,
    payload: str | None = None,
    now_epoch: float | None = None,
) -> list[str]:
    """argv for one child: the fixture config unchanged unless the test drifts it."""
    return [
        payload or store.payload(),
        mode,
        key,
        _TOOL,
        args_hash,
        json.dumps(_SNAPSHOT),
        str(effects),
        child_id,
        str(now_epoch) if now_epoch is not None else "",
    ]


async def _run_child(
    crashed_child: CrashedChildRunner, argv: list[str], points: list[str]
) -> None:
    child = await crashed_child.start(_CHILD_SCRIPT, argv)
    for point in points:
        await child.wait_for_point(point)
    await child.wait()


def _effects(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line]


def _claim(
    store: SharedCallStore,
    key: str,
    *,
    args_hash: str = _ARGS_HASH,
    now_epoch: float | None = None,
) -> str:
    """Agent-side acquisition through the fixture handle, unchanged contract."""
    return store.handle.try_acquire_execution(
        key, _TOOL, args_hash, _SNAPSHOT, _OWNER, now_epoch=now_epoch
    ).status


def _read_row(store: SharedCallStore, key: str) -> dict[str, Any]:
    """The ledger row read directly, without the store's own projection."""
    conn = sqlite3.connect(store.path)
    conn.row_factory = sqlite3.Row
    try:
        rec = conn.execute(
            "SELECT status, lease_expires_epoch, attempt_number, args_hash"
            " FROM dedup_call_state WHERE key = ?",
            (key,),
        ).fetchone()
    finally:
        conn.close()
    if rec is None:
        raise AssertionError(f"no ledger row for {key!r}")
    return dict(rec)


def _lease_live(row: dict[str, Any]) -> bool:
    expiry = row["lease_expires_epoch"]
    return (
        row["status"] == "pending"
        and expiry is not None
        and float(expiry) > time.time()
    )


def _state_row(key: str) -> ToolCallState:
    """The Agent-side row the recovery service is asked about, for the same key."""
    now = time.time()
    return ToolCallState(
        idempotency_key=key,
        task_id="matrix-task",
        tool=_TOOL,
        state="outcome_unknown",
        retry_class="none",
        created_at=now,
        updated_at=now,
    )


def _recovery(proc: ControlApiProcess) -> McpCallRecoveryService:
    """Agent recovery service pointed at the running control-API child."""
    config = McpServerConfig(
        transport=TransportType.HTTP,
        url=proc.base_url(),
        control_auth_token=proc.token,
        key=_SERVER_KEY,
    )
    return McpCallRecoveryService(
        {_SERVER_KEY: config}, lambda tool: _SERVER_KEY if tool == _TOOL else None
    )


def _assert_three_sources(
    proc: ControlApiProcess, store: SharedCallStore, key: str, expected: str
) -> None:
    """The same logical key must read the same state from all three sources (D3)."""
    row = _read_row(store, key)
    assert agent_state_for(str(row["status"]), _lease_live(row)) == expected

    result = ControlClient(proc.base_url(), proc.token).get_call_state(key)
    assert result.ok, f"control read refused: {result.error}"
    payload = result.payload
    assert payload is not None
    assert payload["key"] == key
    assert payload["agent_state"] == expected
    assert payload["ledger_status"] == row["status"]
    assert payload["lease_live"] is _lease_live(row)

    assert _recovery(proc).resolve_state(_state_row(key)) == expected


async def test_x01_pending_live_lease_is_in_progress(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """REQ-001: the Agent side holds a live lease; both layers say in_progress."""
    key = "x01-pending-live"
    assert _claim(shared_call_store, key) == "acquired"
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "in_progress")


async def test_x02_pending_expired_lease_is_reconciliation_required(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """REQ-001: a deterministically expired lease maps to reconciliation_required."""
    key = "x02-pending-expired"
    seeded = time.time() - _EXPIRED_SEED_SEC
    assert _claim(shared_call_store, key, now_epoch=seeded) == "acquired"
    _assert_three_sources(
        control_api_subprocess, shared_call_store, key, "reconciliation_required"
    )


async def test_x03_completed_stays_completed(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """REQ-001: an owner-finalized row maps to completed on both sides."""
    key = "x03-completed"
    assert _claim(shared_call_store, key) == "acquired"
    shared_call_store.handle.record_completed(key, _SNAPSHOT, {"value": 1}, _OWNER)
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "completed")


async def test_x04_failed_stays_failed(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """REQ-001: an owner-finalized handler failure maps to failed, with its fixed code."""
    key = "x04-failed"
    assert _claim(shared_call_store, key) == "acquired"
    shared_call_store.handle.record_failed(key, "handler_error", _OWNER)
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "failed")
    resolution = _recovery(control_api_subprocess).resolve(_state_row(key))
    assert resolution is not None
    assert resolution.error_code == "handler_failed"


async def test_x05_interrupted_is_reconciliation_required(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """REQ-001: a row moved by the reconciliation path maps to reconciliation_required."""
    key = "x05-interrupted"
    seeded = time.time() - _EXPIRED_SEED_SEC
    assert _claim(shared_call_store, key, now_epoch=seeded) == "acquired"
    # Read at the real time the same call is classified as stale; the second look
    # classifies only, and the row moves through the reconciliation path.
    assert _claim(shared_call_store, key) == "reconciliation_required"
    moved = shared_call_store.handle.reconcile_execution(key)
    assert moved.status == "interrupted"
    _assert_three_sources(
        control_api_subprocess, shared_call_store, key, "reconciliation_required"
    )


async def test_x06_unknown_ledger_state_refuses_on_both_sides(
    control_api_subprocess: ControlApiProcess, shared_call_store: SharedCallStore
) -> None:
    """Totality branch: the mapping raises for a word it does not define, and the store
    schema refuses the same word, so no boundary can invent a state."""
    key = "x06-unknown-state"
    with pytest.raises(ValueError):
        agent_state_for("not_a_state", False)

    conn = sqlite3.connect(shared_call_store.path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO dedup_call_state (key, tool_name, args_hash, status,"
                " owner_id, lease_expires_epoch, attempt_number, snapshot_json,"
                " created_epoch, updated_epoch, result_json) VALUES (?, ?, ?,"
                " 'not_a_state', ?, NULL, 1, '{}', ?, ?, NULL)",
                (key, _TOOL, _ARGS_HASH, _OWNER, time.time(), time.time()),
            )
    finally:
        conn.close()

    # The client reports a refusal as a status code and establishes nothing; it does not
    # read the body, so the Agent side is left with no state for the key.
    result = ControlClient(
        control_api_subprocess.base_url(), control_api_subprocess.token
    ).get_call_state(key)
    assert not result.ok
    assert result.status_code == 404
    assert result.payload is None
    assert _recovery(control_api_subprocess).resolve_state(_state_row(key)) is None


async def test_x07_the_same_key_written_by_the_other_process(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """The row the child wrote is read through the same mapping by the Agent side."""
    key = "x07-cross-side"
    effects = _effects_path(tmp_path)
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "claim", key, "c1"),
        ["acquired", "handler-ran"],
    )
    assert _effects(effects) == ["c1"]
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "in_progress")


async def test_x10_two_children_one_logical_key_run_at_most_once(
    crashed_child: CrashedChildRunner,
    shared_call_store: SharedCallStore,
    tmp_path: Path,
) -> None:
    """AC-002: the second claim on the same logical call is refused, never executed."""
    effects = _effects_path(tmp_path)
    key = "x10-one-execution"
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "claim", key, "c1"),
        ["acquired", "handler-ran"],
    )
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "claim", key, "c2"),
        ["in_progress", "no-handler"],
    )
    assert _effects(effects) == ["c1"]


async def test_x11_an_unclassifiable_outcome_is_never_rerun(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """At the attempt bound nothing is classified, so nothing is executed again."""
    effects = _effects_path(tmp_path)
    key = "x11-never-rerun"
    seeded = time.time() - _EXPIRED_SEED_SEC
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "claim", key, "c1", now_epoch=seeded),
        ["acquired", "handler-ran"],
    )
    assert shared_call_store.handle.reconcile_execution(key).status == "interrupted"
    conn = sqlite3.connect(shared_call_store.path)
    conn.execute(
        "UPDATE dedup_call_state SET attempt_number = ? WHERE key = ?",
        (shared_call_store.config.max_attempts, key),
    )
    conn.commit()
    conn.close()

    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "claim", key, "c2"),
        ["outcome_unknown", "no-handler"],
    )
    assert _effects(effects) == ["c1"]
    row = _read_row(shared_call_store, key)
    assert row["status"] == "interrupted"
    assert int(row["attempt_number"]) == shared_call_store.config.max_attempts
    _assert_three_sources(
        control_api_subprocess, shared_call_store, key, "reconciliation_required"
    )


async def test_x12_store_loss_refuses_reopen_across_the_boundary(
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-006: the child cannot open a deleted store; the open is a typed refusal."""
    effects = _effects_path(tmp_path)
    Path(shared_call_store.path).unlink()
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "identity", "x12", "c1"),
        ["lost"],
    )
    with pytest.raises(DedupStoreError) as exc:
        open_dedup_store(shared_call_store.config)
    assert exc.value.state == "lost"


async def test_x13_foreign_store_at_the_path_is_refused(
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-006: a foreign store replacing the path is typed, not silently accepted."""
    effects = _effects_path(tmp_path)
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir()
    foreign_config = dataclasses.replace(
        shared_call_store.config, db_path=str(foreign_dir / "store.sqlite")
    )
    foreign = open_dedup_store(foreign_config)
    foreign.close()
    Path(shared_call_store.path).unlink()
    shutil.copy(foreign_config.db_path, shared_call_store.path)

    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "identity", "x13", "c1"),
        ["replaced"],
    )
    with pytest.raises(DedupStoreError) as exc:
        open_dedup_store(shared_call_store.config)
    assert exc.value.state == "replaced"


async def test_x14_drifted_shape_and_state_store_are_refused(
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_sqlite_db: str,
    tmp_path: Path,
) -> None:
    """REQ-006: the Agent-side state store and a drifted ledger shape never open."""
    effects = _effects_path(tmp_path)
    conn = sqlite3.connect(shared_call_store.path)
    conn.execute("ALTER TABLE dedup_call_state ADD COLUMN drifted TEXT")
    conn.commit()
    conn.close()
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "identity", "x14", "c1"),
        ["schema_mismatch"],
    )

    state_store = dataclasses.replace(shared_call_store.config, db_path=tmp_sqlite_db)
    await _run_child(
        crashed_child,
        _argv(
            shared_call_store,
            effects,
            "identity",
            "x14",
            "c2",
            payload=fingerprint_payload(state_store),
        ),
        ["legacy_or_unverified"],
    )
    with pytest.raises(DedupStoreError) as exc:
        open_dedup_store(state_store)
    assert exc.value.state == "legacy_or_unverified"


async def test_x15_drifted_config_fingerprint_is_refused(
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-007: a process whose semantics drifted from the store cannot reopen it."""
    effects = _effects_path(tmp_path)
    drifted = dataclasses.replace(
        shared_call_store.config,
        lease_seconds=shared_call_store.config.lease_seconds + 60,
    )
    await _run_child(
        crashed_child,
        _argv(
            shared_call_store,
            effects,
            "identity",
            "x15",
            "c1",
            payload=fingerprint_payload(drifted),
        ),
        ["identity_mismatch"],
    )
    # The unchanged config still opens: the refusal is the drift, not the store.
    await _run_child(
        crashed_child,
        _argv(shared_call_store, effects, "identity", "x15", "c2"),
        ["healthy"],
    )


async def test_x16_fail_closed_boundaries_across_the_process(
    control_api_launcher: ControlApiLauncher,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-004: unavailable store and tampered arguments are refused; independent calls
    that share arguments each execute exactly once (AC-003, AC-005)."""
    # A control path with no state store open answers with the fixed code and the Agent
    # side establishes nothing, leaving its row as it was.
    unavailable = await control_api_launcher.start(config_json="none")
    key = "x16-unavailable-store"
    assert _claim(shared_call_store, key) == "acquired"
    result = ControlClient(unavailable.base_url(), unavailable.token).get_call_state(
        key
    )
    # The client reports a refusal as a status code only; nothing is established and the
    # row the Agent side wrote is unchanged.
    assert not result.ok
    assert result.status_code == 503
    assert result.payload is None
    assert _recovery(unavailable).resolve_state(_state_row(key)) is None
    assert _read_row(shared_call_store, key)["status"] == "pending"

    # The arguments the approval grant hashed are the stored ones; tampering with them
    # cannot re-run the call.
    effects = _effects_path(tmp_path)
    key = "x16-tampered-arguments"
    assert _claim(shared_call_store, key) == "acquired"
    await _run_child(
        crashed_child,
        _argv(
            shared_call_store, effects, "claim", key, "c1", args_hash="tampered-hash"
        ),
        ["contract_mismatch", "no-handler"],
    )
    assert _effects(effects) == []
    assert _read_row(shared_call_store, key)["args_hash"] == _ARGS_HASH

    # Two independent logical calls with identical arguments are independent calls: each
    # executes exactly once (AC-003).
    for child_id in ("c2", "c3"):
        await _run_child(
            crashed_child,
            _argv(
                shared_call_store,
                effects,
                "claim",
                f"x16-independent-{child_id}",
                child_id,
            ),
            ["acquired", "handler-ran"],
        )
    assert sorted(_effects(effects)) == ["c2", "c3"]
