"""tests/agent/test_tool_run_recorder.py
Plan-shape tests for the round_exec record written by agent/tool_run_recorder.py:
the recorded mode and side-effect presence must follow the scheduler's plan and the
approved calls' metadata, not a constant or a serialization-event inference.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.tool_preparation import PreparedToolCall
from agent.tool_run_recorder import (
    _record_round_exec,
    _record_serialization_stats,
    _scheduling_mode,
    get_serialization_stats,
)
from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _call(
    name: str,
    *,
    scopes: tuple[str, ...] = (),
    is_write: bool = False,
    requires_serial: bool = False,
) -> PreparedToolCall:
    call_id = f"call_{name}"
    spec = ToolSpec(
        call_id=call_id,
        name=name,
        resource_scopes=scopes,
        requires_serial=requires_serial,
        is_write=is_write,
    )
    original = {"id": call_id, "function": {"name": name, "arguments": "{}"}}
    return PreparedToolCall(
        call_id=call_id, name=name, args={}, spec=spec, original_call=original
    )


def _record(
    calls: list[PreparedToolCall], *, force_serial: bool = False
) -> dict[str, Any]:
    """Plan the calls with the real scheduler, record the round, return the payload."""
    plan = build_execution_groups(
        [pc.original_call for pc in calls],
        {pc.call_id: pc.spec for pc in calls},
        force_serial=force_serial,
    )
    ctx = MagicMock()
    _record_round_exec(
        ctx, calls, plan.serialization_events, "round-1", 1.0, plan.batches
    )
    ctx.services_required.audit_logger.info.assert_called_once()
    payload: dict[str, Any] = json.loads(
        ctx.services_required.audit_logger.info.call_args[0][0]
    )
    assert payload["event"] == "round_exec"
    return payload


class TestRoundExecPlanShapes:
    def test_concurrent_read_only_plan_is_parallel(self) -> None:
        payload = _record([_call("read_a"), _call("read_b"), _call("read_c")])
        assert payload["mode"] == "parallel"
        assert payload["scheduling_mode"] == "dag_concurrent"
        assert payload["has_side_effect"] is False

    def test_sequential_write_plan_is_not_recorded_parallel(self) -> None:
        payload = _record(
            [
                _call("write_a", scopes=("file:/f",), is_write=True),
                _call("write_b", scopes=("file:/f",), is_write=True),
            ]
        )
        assert payload["mode"] == "serial"
        assert payload["scheduling_mode"] == "dag_sequential"
        assert payload["has_side_effect"] is True

    def test_single_unconflicted_write_is_side_effecting(self) -> None:
        payload = _record([_call("write_a", scopes=("file:/f",), is_write=True)])
        assert payload["has_side_effect"] is True
        assert payload["mode"] == "serial"
        assert payload["trigger_tool"] is None
        assert payload["serial_reason"] is None

    def test_forced_serial_read_only_plan_is_not_a_write(self) -> None:
        payload = _record([_call("read_a"), _call("read_b")], force_serial=True)
        assert payload["mode"] == "serial"
        assert payload["scheduling_mode"] == "dag_sequential"
        assert payload["has_side_effect"] is False

    def test_write_with_unconflicted_reads_runs_parallel_with_side_effect(self) -> None:
        payload = _record(
            [_call("write_a", scopes=("file:/f",), is_write=True), _call("read_a")]
        )
        assert payload["mode"] == "parallel"
        assert payload["has_side_effect"] is True

    def test_forced_serial_write_keeps_serialization_diagnostics(self) -> None:
        payload = _record(
            [_call("write_a", scopes=("file:/f",), is_write=True), _call("read_a")],
            force_serial=True,
        )
        assert payload["mode"] == "serial"
        assert payload["has_side_effect"] is True
        assert payload["trigger_tool"] == "write_a"
        assert payload["serial_reason"] == "forced_serial"
        assert payload["affected_tools"] == ["write_a", "read_a"]
        assert payload["tool_count"] == 2

    def test_empty_plan_is_serial_without_side_effect(self) -> None:
        payload = _record([])
        assert payload["mode"] == "serial"
        assert payload["scheduling_mode"] == "dag_sequential"
        assert payload["has_side_effect"] is False


class TestModeMatchesSchedulingMode:
    @pytest.mark.parametrize("force_serial", [False, True])
    @pytest.mark.parametrize(
        "calls",
        [
            [],
            [_call("read_a")],
            [_call("read_a"), _call("read_b")],
            [
                _call("write_a", scopes=("file:/f",), is_write=True),
                _call("write_b", scopes=("file:/f",), is_write=True),
            ],
            [
                _call("write_a", scopes=("file:/f",), is_write=True),
                _call("read_a"),
            ],
            [_call("barrier", requires_serial=True), _call("read_a")],
        ],
    )
    def test_mode_is_parallel_exactly_when_scheduling_mode_is_concurrent(
        self, calls: list[PreparedToolCall], force_serial: bool
    ) -> None:
        payload = _record(calls, force_serial=force_serial)
        assert (payload["mode"] == "parallel") == (
            payload["scheduling_mode"] == "dag_concurrent"
        )

    def test_scheduling_mode_reads_the_plan_batches(self) -> None:
        calls = [_call("read_a"), _call("read_b")]
        plan = build_execution_groups(
            [pc.original_call for pc in calls], {pc.call_id: pc.spec for pc in calls}
        )
        assert _scheduling_mode(plan.batches) == "dag_concurrent"
        assert _scheduling_mode(()) == "dag_sequential"


class TestSerializationCountersUnchanged:
    def test_counters_keep_their_meaning(self) -> None:
        plan = build_execution_groups(
            [pc.original_call for pc in (_call("w1", is_write=True), _call("r1"))],
            {pc.call_id: pc.spec for pc in (_call("w1", is_write=True), _call("r1"))},
            force_serial=True,
        )
        before = get_serialization_stats()
        _record_serialization_stats(plan.serialization_events)
        after = get_serialization_stats()
        assert after["total_events"] == before["total_events"] + 1
        assert after["total_tools_affected"] == before["total_tools_affected"] + 2
        assert after["tools_affected_last_round"] == 2
        _record_serialization_stats(())
        assert get_serialization_stats()["tools_affected_last_round"] == 0
