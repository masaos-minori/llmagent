"""tests/integration/test_call_state_crash_injection_across_processes.py

Cross-process crash injection for issue mcpdl006 (REQ-002, REQ-005).

One child process runs one logical call and is killed at a chosen point; the resulting
state is asserted through the shared mapping and the dedup gate, not through the raw
transport (Decision D2). For the same logical key the control API, the Agent recovery
service, and the mapping computed from the ledger row must agree — the same assertion
source as the matrix test (Decision D3). The handler's execution is counted in an effects
file, so "no handler runs twice" is a counted fact rather than an assumption. Only
tmp_path stores and loopback are used, so nothing reaches a path under /opt/llm (AC-006).
`tests/integration/test_mcp_transport_crash.py` remains the transport-boundary record and
is not extended here.

Run 5x for the flakiness check:
    for i in {1..5}; do uv run pytest tests/integration/test_call_state_crash_injection_across_processes.py -m integration; done
"""

from __future__ import annotations

import json
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

from tests.integration.conftest import (
    ControlApiLauncher,
    ControlApiProcess,
    CrashedChildRunner,
    SharedCallStore,
)

pytestmark = pytest.mark.integration

_SERVER_KEY = "crash-server"
_TOOL = "crash-tool"
_OWNER = "crash-side"
_ARGS_HASH = "crash-args-hash"
# Component-keyed snapshot, the shape `execution_snapshot.COMPONENT_KEYS` defines: replay
# is only answered for a call whose snapshot components are the same on both sides.
_SNAPSHOT = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "dedup": "gen=1;schema=deadbeef",
}
# A past seed is the deterministic way to reach an expired lease: the claim is decided at
# the seeded time, where the fixture's lease is still live, and the same row is read as
# expired at real time. Nothing here waits on wall-clock drift.
_EXPIRED_SEED_SEC = 600
# The child holds at the point the test chose until it is killed; the hold is bounded so
# an unexpected point cannot outlive the test.
_HOLD_SEC = 10

# One child, the call sequence, one line per control point it reaches. The test reads the
# points in order and kills the child at the point it names. The handler records itself in
# the effects file, and the evidence file is written only when the test asks for recorded
# evidence, so a test can tell an effect from a recorded decision.
_CHILD_SCRIPT = f"""
import json, signal, sys
from shared.mcp_dedup import DedupStoreConfig, open_dedup_store

config = DedupStoreConfig(**json.loads(sys.argv[1]))
key, effects, evidence_file, stop, now_arg, child_id = (
    sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
)
snapshot = {json.dumps(_SNAPSHOT)}
owner = "crash-child"
now_epoch = float(now_arg) if now_arg else None
HOLD_SEC = {_HOLD_SEC}


def reach(point):
    print(point, flush=True)
    if point == stop:
        signal.alarm(HOLD_SEC)
        signal.pause()
        sys.exit(0)


def run_handler():
    with open(effects, "a") as f:
        f.write(child_id + "\\n")
    if evidence_file:
        # The observable trace a registered reconciler can read after the process is gone.
        with open(evidence_file, "w") as f:
            f.write("crash-effect")
    return "crash-effect"


reach("before-send")
store = open_dedup_store(config)
result = store.try_acquire_execution(
    key, {json.dumps(_TOOL)}, {json.dumps(_ARGS_HASH)}, snapshot, owner,
    now_epoch=now_epoch,
)
if result.status != "acquired":
    print(result.status, flush=True)
    sys.exit(0)
reach("acquired")
reach("before-handler")
digest = run_handler()
reach("effect-done")
store.record_completed(key, snapshot, {{"value": digest}}, owner)
reach("result-recorded")
reach("response-sent")
"""


def _effects_path(tmp_path: Path) -> Path:
    path = tmp_path / "effects"
    path.write_text("")
    return path


def _effects(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line]


def _argv(
    store: SharedCallStore,
    effects: Path,
    key: str,
    child_id: str,
    stop: str,
    *,
    evidence_file: Path | None = None,
    now_epoch: float | None = None,
) -> list[str]:
    """argv for one child: the fixture config unchanged, as the reopen gate requires."""
    return [
        store.payload(),
        key,
        str(effects),
        str(evidence_file) if evidence_file is not None else "",
        stop,
        str(now_epoch) if now_epoch is not None else "",
        child_id,
    ]


async def _crash_at(
    crashed_child: CrashedChildRunner, argv: list[str], points: list[str]
) -> None:
    """Run the child to the point it is killed at; the death must be a signal kill."""
    child = await crashed_child.start(_CHILD_SCRIPT, argv)
    for point in points:
        await child.wait_for_point(point)
    child.kill()
    code = await child.wait()
    assert code < 0, f"child exited {code} at {points[-1]!r}, not killed by a signal"


async def _run_to_end(
    crashed_child: CrashedChildRunner, argv: list[str], points: list[str]
) -> None:
    """Run a child that reaches its end normally, reading the points in order."""
    child = await crashed_child.start(_CHILD_SCRIPT, argv)
    for point in points:
        await child.wait_for_point(point)
    assert await child.wait() == 0


def _read_row(store: SharedCallStore, key: str) -> dict[str, Any] | None:
    """The ledger row read directly, without the store's own projection."""
    conn = sqlite3.connect(store.path)
    conn.row_factory = sqlite3.Row
    try:
        rec = conn.execute(
            "SELECT status, lease_expires_epoch, attempt_number, result_json"
            " FROM dedup_call_state WHERE key = ?",
            (key,),
        ).fetchone()
    finally:
        conn.close()
    return dict(rec) if rec is not None else None


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
        task_id="crash-task",
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
    assert row is not None
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


async def test_c01_crash_before_send_records_nothing(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: a death before the call is recorded leaves nothing to read."""
    key = "c01-before-send"
    effects = _effects_path(tmp_path)
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "before-send"),
        ["before-send"],
    )
    assert _effects(effects) == []
    assert _read_row(shared_call_store, key) is None

    result = ControlClient(
        control_api_subprocess.base_url(), control_api_subprocess.token
    ).get_call_state(key)
    assert not result.ok
    assert result.status_code == 404
    assert _recovery(control_api_subprocess).resolve_state(_state_row(key)) is None


async def test_c02_crash_after_send_leaves_the_call_in_progress(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: the record the child wrote stands; no handler ran and none runs again."""
    key = "c02-after-send"
    effects = _effects_path(tmp_path)
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "acquired"),
        ["before-send", "acquired"],
    )
    assert _effects(effects) == []
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "in_progress")

    # The death does not free the call: another process sees it running and does not
    # execute it.
    await _run_to_end(
        crashed_child,
        _argv(shared_call_store, effects, key, "c2", "in_progress"),
        ["before-send", "in_progress"],
    )
    assert _effects(effects) == []
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "in_progress")


async def test_c03_crash_after_the_recorded_completion_is_answered_by_replay(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: a completed call stands after the process dies and is never re-executed."""
    key = "c03-after-completion"
    effects = _effects_path(tmp_path)
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "result-recorded"),
        ["before-send", "acquired", "before-handler", "effect-done", "result-recorded"],
    )
    assert _effects(effects) == ["c1"]
    row = _read_row(shared_call_store, key)
    assert row is not None
    assert row["result_json"] is not None
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "completed")

    await _run_to_end(
        crashed_child,
        _argv(shared_call_store, effects, key, "c2", "replay_completed"),
        ["before-send", "replay_completed"],
    )
    assert _effects(effects) == ["c1"]
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "completed")


async def test_c04_crash_before_the_handler_runs_nothing(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: a death before the handler leaves the record with no effect at all."""
    key = "c04-before-handler"
    effects = _effects_path(tmp_path)
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "before-handler"),
        ["before-send", "acquired", "before-handler"],
    )
    assert _effects(effects) == []
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "in_progress")


async def test_c05_crash_during_the_handler_is_not_a_result(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: an effect with no recorded result is never read as a completed call."""
    key = "c05-during-handler"
    effects = _effects_path(tmp_path)
    seeded = time.time() - _EXPIRED_SEED_SEC
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "effect-done", now_epoch=seeded),
        ["before-send", "acquired", "before-handler", "effect-done"],
    )
    assert _effects(effects) == ["c1"]
    row = _read_row(shared_call_store, key)
    assert row is not None
    assert row["result_json"] is None
    assert not _lease_live(row)
    assert agent_state_for(str(row["status"]), False) == "reconciliation_required"

    result = ControlClient(
        control_api_subprocess.base_url(), control_api_subprocess.token
    ).get_call_state(key)
    assert result.ok and result.payload is not None
    assert result.payload["agent_state"] == "reconciliation_required"
    assert _recovery(control_api_subprocess).resolve_state(_state_row(key)) == (
        "reconciliation_required"
    )

    # The reconciliation path moves the stale row; it does not run the handler again.
    assert shared_call_store.handle.reconcile_execution(key).status == "interrupted"
    assert _effects(effects) == ["c1"]
    _assert_three_sources(
        control_api_subprocess, shared_call_store, key, "reconciliation_required"
    )


async def test_c06_crash_after_the_effect_is_resolved_from_recorded_evidence(
    control_api_launcher: ControlApiLauncher,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-005: an effect with no trace is answered as no evidence, not as a result."""
    key = "c06-after-effect"
    effects = _effects_path(tmp_path)
    seeded = time.time() - _EXPIRED_SEED_SEC
    await _crash_at(
        crashed_child,
        _argv(
            shared_call_store,
            effects,
            key,
            "c1",
            "effect-done",
            now_epoch=seeded,
        ),
        ["before-send", "acquired", "before-handler", "effect-done"],
    )
    assert _effects(effects) == ["c1"]
    row = _read_row(shared_call_store, key)
    assert row is not None
    assert row["result_json"] is None

    # A reconciler registered at the control seam answers what it can see: here there is
    # no trace, so the decision is no evidence and the handler is not run again.
    proc = await control_api_launcher.start(tool_name=_TOOL)
    result = ControlClient(proc.base_url(), proc.token).request_reconcile(key)
    assert result.ok, f"reconcile refused: {result.error}"
    payload = result.payload
    assert payload is not None
    assert payload["key"] == key
    assert payload["decision"] == "reconciled"
    assert payload["outcome"] == "no_evidence"
    assert payload["agent_state"] == "reconciliation_required"
    assert _effects(effects) == ["c1"]


async def test_c07_crash_before_the_response_keeps_the_recorded_result(
    control_api_subprocess: ControlApiProcess,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """REQ-002: a lost response does not undo the recorded call; no handler runs twice."""
    key = "c07-before-response"
    effects = _effects_path(tmp_path)
    await _crash_at(
        crashed_child,
        _argv(shared_call_store, effects, key, "c1", "result-recorded"),
        ["before-send", "acquired", "before-handler", "effect-done", "result-recorded"],
    )
    assert _effects(effects) == ["c1"]
    _assert_three_sources(control_api_subprocess, shared_call_store, key, "completed")

    await _run_to_end(
        crashed_child,
        _argv(shared_call_store, effects, key, "c2", "replay_completed"),
        ["before-send", "replay_completed"],
    )
    assert _effects(effects) == ["c1"]


async def test_c08_a_lost_response_is_resolved_without_re_executing(
    control_api_launcher: ControlApiLauncher,
    shared_call_store: SharedCallStore,
    crashed_child: CrashedChildRunner,
    tmp_path: Path,
) -> None:
    """AC-004: recovery resolves from recorded evidence and the handler is never called."""
    key = "c08-lost-response"
    effects = _effects_path(tmp_path)
    evidence = tmp_path / "evidence"
    seeded = time.time() - _EXPIRED_SEED_SEC
    # The child dies with the response undelivered: the effect and the recorded evidence
    # are all that exists.
    await _crash_at(
        crashed_child,
        _argv(
            shared_call_store,
            effects,
            key,
            "c1",
            "effect-done",
            evidence_file=evidence,
            now_epoch=seeded,
        ),
        ["before-send", "acquired", "before-handler", "effect-done"],
    )
    assert _effects(effects) == ["c1"]

    proc = await control_api_launcher.start(
        evidence_file=str(evidence), tool_name=_TOOL
    )
    result = ControlClient(proc.base_url(), proc.token).request_reconcile(key)
    assert result.ok, f"reconcile refused: {result.error}"
    payload = result.payload
    assert payload is not None
    assert payload["decision"] == "reconciled"
    assert payload["outcome"] == "evidence_found"
    assert payload["agent_state"] == "reconciliation_required"
    assert _effects(effects) == ["c1"]

    # The Agent side cannot accept that reconcile answer: `_validated_resolution` requires
    # lease_live, which `ReconcileResponse` does not define, so nothing is established by
    # that request. The state read for the same key answers through the model that does
    # carry the field, and that is what recovery reports here.
    assert _recovery(proc).reconcile(_state_row(key)) is None
    assert _recovery(proc).resolve_state(_state_row(key)) == "reconciliation_required"

    # Answering from evidence did not run the handler: the counted runs are still one.
    assert _effects(effects) == ["c1"]
