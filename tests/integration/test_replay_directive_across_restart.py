"""tests/integration/test_replay_directive_across_restart.py

Cross-restart replay-directive test for issue mcpai004 (REQ-002, REQ-006, AC-005).

One child process writes the tool-call rows through the shared store and exits; the parent
opens the same store afterwards, which is the restarted process. The directive it
reconstructs from the persisted `interrupted` rows must carry the child's original logical
call id, a finalized row must not be listed again, and two rows that match one reissue must
be rejected rather than picked. Only tmp_path stores are used, so nothing reaches a path
under /opt/llm (AC-006).

Run 5x for the flakiness check:
    for i in {1..5}; do uv run pytest tests/integration/test_replay_directive_across_restart.py -m integration; done
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from agent.context import TurnState, WorkflowState
from agent.tool_preparation import (
    ReplayDirective,
    _canonical_args_hash,
    prepare_tool_calls,
)
from agent.workflow.state_store import StateStore
from db.config import DbConfig
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.integration.conftest import CrashedChildRunner
from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

pytestmark = pytest.mark.integration

_TASK = "restart-task"
_TOOL = "restart-tool"
_SERVER_KEY = "restart-server"
_ARGS = {"path": "/a"}
_ARGS_HASH = _canonical_args_hash(_ARGS)
# Fixed values rather than wall-clock: the child backdates each row from the base epoch the
# test passes, so the oldest-first order is decided by the test, not by insertion timing, and
# the timeout classification cannot see a row that is not yet past the cutoff.
_BASE_EPOCH = 1_700_000_000.0
_BACKDATE_SEC = 120.0
_TIMEOUT_SEC = 60.0
# The LLM-side call id of the reissued call. It is not the logical call id: the assertion is
# that the execution context carries the child's id, not this one (REQ-002).
_REISSUE_CALL_ID = "call_after_restart"
_ORIGINAL_ID = "0199e2f3-0000-7000-8000-0000000000a1"
_SECOND_ID = "0199e2f3-0000-7000-8000-0000000000a2"

# One child per asserted boundary. It records each row through the store, backdates it past
# the timeout so the guarded transition makes it `interrupted` — the state a restarted process
# sees at turn entry — and reports the point it reached before exiting.
_CHILD_PLANT_SCRIPT = """
import json, sys, time
from db.config import DbConfig
from agent.workflow.state_store import StateStore

payload = json.loads(sys.argv[1])
cfg = DbConfig(
    rag_db_path=payload["rag_db_path"],
    session_db_path=payload["session_db_path"],
    workflow_db_path=payload["workflow_db_path"],
)
store = StateStore(db_config=cfg)
try:
    for index, call_id in enumerate(payload["call_ids"]):
        store.record_tool_call(
            payload["task_id"], call_id, payload["tool"], "retryable", payload["args_hash"]
        )
        store.get_connection().execute(
            "UPDATE tool_call_state SET created_at=? WHERE idempotency_key=?",
            (payload["base_epoch"] - payload["backdate_sec"] + index, call_id),
        )
    store.get_connection().commit()
    store.classify_stale_pending(payload["task_id"], payload["timeout_sec"])
    print("planted", flush=True)
finally:
    store.close()
"""


def _db_config(tmp_path: Path) -> DbConfig:
    """The config the `tmp_sqlite_db` fixture built the schema under.

    The child must use the same paths so both processes open the same file, and the parent's
    store is opened after the child exits, which is the restart the test is about.
    """
    return DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=str(tmp_path / "session.sqlite"),
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
    )


def _payload(tmp_path: Path, call_ids: list[str]) -> str:
    """argv payload for one child: the store config unchanged plus the rows to plant."""
    return json.dumps(
        {
            "rag_db_path": _db_config(tmp_path).rag_db_path,
            "session_db_path": _db_config(tmp_path).session_db_path,
            "workflow_db_path": _db_config(tmp_path).workflow_db_path,
            "task_id": _TASK,
            "tool": _TOOL,
            "args_hash": _ARGS_HASH,
            "call_ids": call_ids,
            "base_epoch": _BASE_EPOCH,
            "backdate_sec": _BACKDATE_SEC,
            "timeout_sec": _TIMEOUT_SEC,
        }
    )


@dataclass(frozen=True)
class _PrepServices:
    """The one service `prepare_tool_calls` reads."""

    runtime_tools: RuntimeToolRegistry


@dataclass(frozen=True)
class _PrepContext:
    """The three reads `prepare_tool_calls` makes: `services_required.runtime_tools`,
    `workflow.current_task_id`, `turn.replay_directives`.

    Real state objects with a real registry: the boundary under test is the persisted row, so
    no other part of the Agent runtime is needed here.
    """

    services_required: _PrepServices
    workflow: WorkflowState
    turn: TurnState


def _context(directives: list[ReplayDirective]) -> _PrepContext:
    registry = RuntimeToolRegistry(
        tools={
            _TOOL: build_fixture_runtime_tool(
                _TOOL,
                _SERVER_KEY,
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                },
            )
        },
        allowed_servers=frozenset({_SERVER_KEY}),
    )
    return _PrepContext(
        services_required=_PrepServices(runtime_tools=registry),
        workflow=WorkflowState(current_task_id=_TASK),
        turn=TurnState(replay_directives=directives),
    )


def _reissue() -> dict[str, Any]:
    """The reissued call, with byte-identical arguments to the interrupted call."""
    return {
        "id": _REISSUE_CALL_ID,
        "function": {"name": _TOOL, "arguments": json.dumps(_ARGS)},
    }


def _directive(row: Any) -> ReplayDirective:
    """The directive the engine builds from one persisted row, at turn entry."""
    return ReplayDirective(
        original_call_id=row.idempotency_key,
        task_id=row.task_id,
        tool=row.tool,
        args_hash=row.args_hash,
    )


async def test_directive_survives_the_restart_and_reconnects_the_reissue(
    tmp_path: Path, tmp_sqlite_db: str, crashed_child: CrashedChildRunner
) -> None:
    """AC-005: the directive a restarted process reconstructs carries the child's id."""
    child = await crashed_child.start(
        _CHILD_PLANT_SCRIPT, [_payload(tmp_path, [_ORIGINAL_ID])]
    )
    await child.wait_for_point("planted")
    # The writing process is gone: the parent's store is the restarted process's handle, and
    # everything it sees comes from disk.
    assert await child.wait() == 0

    store = StateStore(db_config=_db_config(tmp_path))
    try:
        rows = store.reconstruct_replay_directives(_TASK)
        assert [r.idempotency_key for r in rows] == [_ORIGINAL_ID]
        row = rows[0]
        assert (row.state, row.retry_class, row.args_hash, row.tool) == (
            "interrupted",
            "retryable",
            _ARGS_HASH,
            _TOOL,
        )

        directive = _directive(row)
        prepared, failures = prepare_tool_calls(_context([directive]), [_reissue()])
        assert failures == []
        assert prepared[0].context is not None
        # REQ-002: the prepared call carries the original id, not a fresh one.
        assert prepared[0].context.call_id == _ORIGINAL_ID
        assert prepared[0].context.args_hash == _ARGS_HASH
        # REQ-001: the directive is consumed by this call.
        assert directive.consumed

        # REQ-006: consumption is recorded durably by the row leaving the replayable states,
        # so the restarted process lists no directive for it.
        store.finalize_tool_call(_ORIGINAL_ID, "completed")
        assert store.reconstruct_replay_directives(_TASK) == []
    finally:
        store.close()


async def test_two_matching_rows_are_rejected_rather_than_picked(
    tmp_path: Path, tmp_sqlite_db: str, crashed_child: CrashedChildRunner, caplog
) -> None:
    """REQ-003: two persisted rows that match one reissue are a structured ambiguity, not a choice."""
    child = await crashed_child.start(
        _CHILD_PLANT_SCRIPT, [_payload(tmp_path, [_ORIGINAL_ID, _SECOND_ID])]
    )
    await child.wait_for_point("planted")
    assert await child.wait() == 0

    store = StateStore(db_config=_db_config(tmp_path))
    try:
        rows = store.reconstruct_replay_directives(_TASK)
        assert [r.idempotency_key for r in rows] == [_ORIGINAL_ID, _SECOND_ID]
        directives = [_directive(r) for r in rows]

        prepared, failures = prepare_tool_calls(_context(directives), [_reissue()])
        # The call never reaches dispatch.
        assert prepared == []
        assert len(failures) == 1
        reason = failures[0][3]
        assert "2 replay directives match" in reason
        assert _ORIGINAL_ID in reason and _SECOND_ID in reason
        assert "kind=ambiguity" in caplog.text
        assert not any(d.consumed for d in directives)
    finally:
        store.close()
