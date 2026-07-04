"""
tests/test_tool_runner.py
Unit tests for tool_runner.py: DAG execution, standard execution, and entry point.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_runner import (
    _compute_serial_overhead,
    _estimate_parallel_time,
    _execute_with_dag,
    execute_all_tool_calls,
)
from shared.transport_dto import ToolCallResult


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_tool_summarize": False,
        "tool_summarize_threshold": 3000,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": "",
        "use_tool_dag": True,
        "tool_results_turn_max_chars": 0,
        "web_search_url": "http://127.0.0.1:8004",
        "github_server_url": "http://127.0.0.1:8006",
        "mcp_servers": {
            "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
        },
    }
    defaults.update(overrides)
    return build_agent_config(defaults)


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg = cfg or _cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.services_required.audit_logger = None
    ctx.services_required.gateway = None
    ctx.services_required.tools = MagicMock()
    ctx.services_required.tools.execute = AsyncMock(
        return_value=ToolCallResult(
            output="result", is_error=False, request_id="req-1", server_key=""
        )
    )
    ctx.stats = MagicMock()
    ctx.stats.stat_tool_calls = 0
    ctx.stats.stat_tool_errors = 0
    ctx.tool_result_store = MagicMock()
    ctx.tool_result_store.store = MagicMock(return_value=1)
    ctx.conv = MagicMock()
    ctx.conv.history = []
    ctx.session = MagicMock()
    ctx.session.session_id = None
    ctx.workflow.workflow_id = None
    return ctx


def _tc(name: str, args: str = "{}") -> dict:
    return {"id": f"call_{name}", "function": {"name": name, "arguments": args}}


class TestExecuteWithDag:
    @pytest.mark.asyncio
    async def test_single_tool_returns_one_result(self) -> None:
        cfg = _cfg(
            tool_definitions=[
                {
                    "function": {
                        "name": "read_text_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                }
            ]
        )
        ctx = _make_ctx(cfg)
        results = await _execute_with_dag(ctx, [_tc("read_text_file")], 0)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_write_first_before_read_in_group_order(self) -> None:
        cfg = _cfg(
            tool_definitions=[
                {
                    "function": {
                        "name": "write_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
                {
                    "function": {
                        "name": "read_text_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
            ]
        )
        ctx = _make_ctx(cfg)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )
        )
        call_order: list[str] = []

        async def _record_exec(name: str, _args: dict) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(ctx, [_tc("read_text_file"), _tc("write_file")], 0)
        # write_file should execute before read_text_file in the group order
        write_idx = call_order.index("write_file")
        read_idx = call_order.index("read_text_file")
        assert write_idx < read_idx

    @pytest.mark.asyncio
    async def test_serial_barrier_executes_solo(self) -> None:
        cfg = _cfg(
            tool_definitions=[
                {
                    "function": {
                        "name": "shell_run",
                        "resource_scope": "",
                        "requires_serial": True,
                    }
                },
                {
                    "function": {
                        "name": "read_text_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
            ]
        )
        ctx = _make_ctx(cfg)
        call_order: list[str] = []

        async def _record_exec(name: str, _args: dict) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(ctx, [_tc("shell_run"), _tc("read_text_file")], 0)
        assert call_order[0] == "shell_run"

    @pytest.mark.asyncio
    async def test_empty_approved_calls_returns_empty(self) -> None:
        ctx = _make_ctx()
        results = await _execute_with_dag(ctx, [], 0)
        assert results == []

    @pytest.mark.asyncio
    async def test_two_scope_groups_all_execute(self) -> None:
        """Two tools with different resource scopes both execute within the same round."""
        cfg = _cfg(
            tool_definitions=[
                {
                    "function": {
                        "name": "write_file",
                        "resource_scope": "file",
                        "requires_serial": False,
                    }
                },
                {
                    "function": {
                        "name": "github_push_files",
                        "resource_scope": "github",
                        "requires_serial": False,
                    }
                },
                {
                    "function": {
                        "name": "read_text_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
            ]
        )
        ctx = _make_ctx(cfg)
        executed: list[str] = []

        async def _record(name: str, _args: dict) -> ToolCallResult:
            executed.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record)
        results = await _execute_with_dag(
            ctx,
            [_tc("write_file"), _tc("github_push_files"), _tc("read_text_file")],
            0,
        )
        assert len(results) == 3
        assert set(executed) == {"write_file", "github_push_files", "read_text_file"}

    @pytest.mark.asyncio
    async def test_results_sorted_to_original_call_order(self) -> None:
        """Results are returned in the original approved_calls order."""
        cfg = _cfg(
            tool_definitions=[
                {
                    "function": {
                        "name": "read_text_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
                {
                    "function": {
                        "name": "write_file",
                        "resource_scope": "",
                        "requires_serial": False,
                    }
                },
            ]
        )
        ctx = _make_ctx(cfg)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req", server_key=""
            )
        )
        calls = [_tc("read_text_file"), _tc("write_file")]
        results = await _execute_with_dag(ctx, calls, 0)
        assert len(results) == 2
        # tc_id at index 0 should be "call_read_text_file"
        assert results[0][0] == "call_read_text_file"
        assert results[1][0] == "call_write_file"


class TestExecuteAllToolCalls:
    @pytest.mark.asyncio
    async def test_approved_calls_executed_and_collected(self) -> None:
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )
        ctx.tool_result_store.store = MagicMock(return_value=1)

        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([_tc("read_text_file", '{"path": "/tmp/f"}')], []),
        ):
            await execute_all_tool_calls(
                ctx, [_tc("read_text_file", '{"path": "/tmp/f"}')], 0
            )

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f"}
        )
        ctx.tool_result_store.store.assert_called_once()
        ctx.session.save_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_calls_execute_without_gateway(self) -> None:
        """Without gateway, all tool calls execute directly (no batch approval denial)."""
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        write_call = {
            "id": "call_1",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([write_call], []),
        ):
            await execute_all_tool_calls(
                ctx,
                [write_call],
                0,
            )

        ctx.services_required.tools.execute.assert_awaited_once_with("write_file", {})

    @pytest.mark.asyncio
    async def test_no_tool_calls_does_nothing(self) -> None:
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()

        await execute_all_tool_calls(ctx, [], 0)

        ctx.services_required.tools.execute.assert_not_called()
        ctx.session.save_many.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_write_tool_requires_approval_without_gateway(self) -> None:
        """Write tool without gateway should require approval before execution."""
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        write_call = {
            "id": "call_write",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        # Approval denies the write tool
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([], ["call_write"]),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        ctx.services_required.tools.execute.assert_not_called()
        # Denied call should appear as tool message in history
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[-1]["role"] == "tool"
        assert ctx.conv.history[-1]["content"] == "Tool execution denied by user."

    @pytest.mark.asyncio
    async def test_denied_tool_call_is_returned_as_tool_message(self) -> None:
        """Denied tool calls are returned to the LLM as tool messages."""
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        write_call = {
            "id": "call_write",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        read_call = _tc("read_text_file")
        # Approval denies write but allows read
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([read_call], ["call_write"]),
        ):
            await execute_all_tool_calls(ctx, [write_call, read_call], 0)

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {}
        )
        # Should have both the tool result and the denied message
        assert len(ctx.conv.history) == 2
        assert ctx.conv.history[-1]["role"] == "tool"
        assert ctx.conv.history[-1]["content"] == "Tool execution denied by user."

    @pytest.mark.asyncio
    async def test_plan_mode_blocked_tool_is_not_executed(self) -> None:
        """Plan-mode blocked tools are not executed."""
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )
        ctx.conv.plan_mode = True

        write_call = _tc("write_file")
        # Approval denies due to plan mode blocking
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([], [write_call["id"]]),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        ctx.services_required.tools.execute.assert_not_called()
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[-1]["role"] == "tool"
        assert ctx.conv.history[-1]["content"] == "Tool execution denied by user."

    @pytest.mark.asyncio
    async def test_execute_all_tool_calls_does_not_bypass_approval(self) -> None:
        """Direct calls to execute_all_tool_calls cannot bypass approval."""
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        write_call = {
            "id": "call_write",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        # Without gateway, approval still runs and denies
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([], ["call_write"]),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        ctx.services_required.tools.execute.assert_not_called()


class TestSerializationHelpers:
    def test_estimate_parallel_time_empty(self) -> None:
        assert _estimate_parallel_time({}) == 0.0

    def test_estimate_parallel_time_sums_values(self) -> None:
        assert _estimate_parallel_time({"a": 10.0, "b": 20.0}) == 30.0

    def test_compute_serial_overhead_zero_parallel(self) -> None:
        assert _compute_serial_overhead(100.0, 0.0) == 1.0

    def test_compute_serial_overhead_ratio(self) -> None:
        assert _compute_serial_overhead(30.0, 10.0) == 3.0

    def test_compute_serial_overhead_rounds_to_two(self) -> None:
        result = _compute_serial_overhead(10.0, 3.0)
        assert result == round(10.0 / 3.0, 2)


class TestExecuteStandardSerialization:
    @pytest.mark.asyncio
    async def test_side_effect_tool_records_serialization_event(self) -> None:
        """When a side-effect tool triggers serial execution, a serialization event is stored."""
        cfg = _cfg(serial_tool_calls=False, use_tool_dag=False)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = None

        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        # write_file is in WRITE_TOOLS and triggers is_side_effect=True
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([write_call], []),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        assert len(ctx.stats.stat_serialization_events) == 1
        event = ctx.stats.stat_serialization_events[0]
        assert event["trigger_tool"] == "write_file"
        assert event["mode"] == "serial"
        assert event["serial_reason"] == "side_effect"
        assert "elapsed_ms" in event
        assert "estimated_parallel_ms" in event
        assert "serial_overhead" in event

    @pytest.mark.asyncio
    async def test_no_side_effect_no_serialization_event(self) -> None:
        """When no side-effect tool is present, no serialization event is recorded."""
        cfg = _cfg(serial_tool_calls=False, use_tool_dag=False)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.stats.stat_serialization_events = []

        read_call = _tc("read_text_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([read_call], []),
        ):
            await execute_all_tool_calls(ctx, [read_call], 0)

        assert ctx.stats.stat_serialization_events == []

    @pytest.mark.asyncio
    async def test_side_effect_calls_diagnostic_save(self) -> None:
        """When diagnostics are wired, save_serialization_event is called."""
        cfg = _cfg(serial_tool_calls=False, use_tool_dag=False)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = MagicMock()

        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([write_call], []),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        ctx.diagnostics.save_serialization_event.assert_called_once()
        call_kwargs = ctx.diagnostics.save_serialization_event.call_args[1]
        assert call_kwargs["trigger_tool"] == "write_file"
        assert call_kwargs["mode"] == "serial"
        assert call_kwargs["reason"] == "side_effect"
