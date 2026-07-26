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
from agent.context import ConversationState
from agent.repository_gateway import RepositoryGateway
from agent.tool_runner import (
    _apply_turn_char_limit,
    _build_tool_meta,
    _compute_serial_overhead,
    _estimate_parallel_time,
    _execute_with_dag,
    execute_all_tool_calls,
    execute_one_tool_call,
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
        "  serial_tool_calls": False,
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
        "tool_results_turn_max_chars": 0,
        # memory_embed_enabled now defaults to True; embed_url must be non-empty
        # to satisfy AgentConfig.__post_init__'s cross-field validation.
        "embed_url": "http://127.0.0.1:9999",
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
    ctx.services_required.runtime_tools = None
    ctx.services_required.tools = MagicMock()
    ctx.services_required.tools.execute = AsyncMock(
        return_value=ToolCallResult(
            output="result", is_error=False, request_id="req-1", server_key=""
        )
    )
    ctx.stats = MagicMock()
    ctx.stats.stat_tool_calls = 0
    ctx.stats.stat_tool_errors = 0
    ctx.conv = MagicMock()
    ctx.conv.history = []
    # Bind the real ConversationState.append_message/extend_messages so calls
    # made through ctx.conv.append_message(...)/extend_messages(...) actually
    # mutate ctx.conv.history (with the same validation/sanitization behavior
    # as production), instead of being swallowed as a no-op MagicMock call.
    ctx.conv.append_message = ConversationState.append_message.__get__(ctx.conv)
    ctx.conv.extend_messages = ConversationState.extend_messages.__get__(ctx.conv)
    ctx.session = MagicMock()
    ctx.session.session_id = None
    ctx.workflow.workflow_id = "wf-test-id"
    return ctx


def _tc(name: str, args: str = "{}") -> dict:
    return {"id": f"call_{name}", "function": {"name": name, "arguments": args}}


class TestBuildToolMeta:
    def test_trigger_workflow_generates_write_toolspec(self) -> None:
        meta = _build_tool_meta([{"function": {"name": "trigger_workflow"}}])
        spec = meta["trigger_workflow"]
        assert spec.is_write is True
        assert spec.resource_scope == "trigger_workflow"

    def test_rag_delete_document_generates_write_toolspec(self) -> None:
        meta = _build_tool_meta([{"function": {"name": "rag_delete_document"}}])
        spec = meta["rag_delete_document"]
        assert spec.is_write is True
        assert spec.resource_scope == "rag_delete_document"

    def test_index_paths_and_refresh_index_generate_write_toolspec(self) -> None:
        meta = _build_tool_meta(
            [
                {"function": {"name": "index_paths"}},
                {"function": {"name": "refresh_index"}},
            ]
        )
        assert meta["index_paths"].is_write is True
        assert meta["index_paths"].requires_serial is False
        assert meta["refresh_index"].is_write is True
        assert meta["refresh_index"].requires_serial is False

    def test_github_write_tools_do_not_enter_parallel_read_group(self) -> None:
        meta = _build_tool_meta(
            [
                {"function": {"name": "github_create_pull_request"}},
                {"function": {"name": "github_delete_file"}},
            ]
        )
        assert meta["github_create_pull_request"].is_write is True
        assert meta["github_delete_file"].is_write is True

    def test_git_write_tools_do_not_enter_parallel_read_group(self) -> None:
        meta = _build_tool_meta([{"function": {"name": "git_commit"}}])
        assert meta["git_commit"].is_write is True

    def test_read_only_tools_remain_parallel(self) -> None:
        meta = _build_tool_meta(
            [
                {"function": {"name": "search_docs"}},
                {"function": {"name": "get_workflow_status"}},
                {"function": {"name": "rag_run_pipeline"}},
            ]
        )
        for name in ("search_docs", "get_workflow_status", "rag_run_pipeline"):
            assert meta[name].is_write is False
            assert meta[name].requires_serial is False

    def test_explicit_tool_definition_metadata_is_respected(self) -> None:
        meta = _build_tool_meta(
            [
                {
                    "function": {
                        "name": "trigger_workflow",
                        "resource_scope": "custom_scope",
                        "is_write": False,
                    }
                }
            ]
        )
        spec = meta["trigger_workflow"]
        assert spec.resource_scope == "custom_scope"
        assert spec.is_write is False


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

    @pytest.mark.asyncio
    async def test_long_output_truncated_without_summarize(self) -> None:
        long_text = "x" * 5000
        cfg = _cfg(tool_result_max_llm_chars=100)
        ctx = _make_ctx(cfg)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=long_text, is_error=False, request_id="req-1", server_key=""
            )
        )

        with patch("rag.llm_client.summarize_tool_result") as mock_summarize:
            result = await execute_one_tool_call(ctx, _tc("shell_run"), 0)
            assert mock_summarize.call_count == 0
            _, _, _, _, _, llm_text = result
            assert len(llm_text) <= 100 + len("\n... (truncated)")

    @pytest.mark.asyncio
    async def test_short_output_passes_through_unchanged(self) -> None:
        short_text = "hello world"
        cfg = _cfg(tool_result_max_llm_chars=4000)
        ctx = _make_ctx(cfg)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=short_text, is_error=False, request_id="req-1", server_key=""
            )
        )

        result = await execute_one_tool_call(ctx, _tc("shell_run"), 0)
        _, _, _, _, _, llm_text = result
        assert llm_text == short_text

    @pytest.mark.asyncio
    async def test_error_output_truncated_only_no_summarize(self) -> None:
        cfg = _cfg(tool_result_max_llm_chars=10)
        ctx = _make_ctx(cfg)
        long_error_text = "e" * 50
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=long_error_text, is_error=True, request_id="req-1", server_key=""
            )
        )

        _tc_id, _name, _args, _text, is_error, llm_text = await execute_one_tool_call(
            ctx, _tc("read_text_file"), 0
        )

        assert is_error
        assert llm_text == long_error_text[:10] + "\n... (truncated)"

    @pytest.mark.asyncio
    async def test_summarize_tool_result_never_called_even_when_enabled(self) -> None:
        """The summarize path was removed; these config keys no longer exist."""
        cfg = _cfg(
            tool_result_max_llm_chars=4000,
        )
        ctx = _make_ctx(cfg)
        text_over_old_threshold = "y" * 100
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=text_over_old_threshold,
                is_error=False,
                request_id="req-1",
                server_key="",
            )
        )

        _tc_id, _name, _args, _text, _is_error, llm_text = await execute_one_tool_call(
            ctx, _tc("read_text_file"), 0
        )

        assert llm_text == text_over_old_threshold


class TestExecuteAllToolCalls:
    @pytest.mark.asyncio
    async def test_approved_calls_executed_and_collected(self) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

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
        ctx.session.save_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_calls_execute_without_gateway(self) -> None:
        """Without gateway, all tool calls execute directly (no batch approval denial)."""
        cfg = _cfg()
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
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()

        await execute_all_tool_calls(ctx, [], 0)

        ctx.services_required.tools.execute.assert_not_called()
        ctx.session.save_many.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_write_tool_requires_approval_without_gateway(self) -> None:
        """Write tool without gateway should require approval before execution."""
        cfg = _cfg()
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
        cfg = _cfg()
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
        cfg = _cfg()
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
        cfg = _cfg()
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

    @pytest.mark.asyncio
    async def test_tool_result_and_denied_messages_routed_through_conv_helpers(
        self,
    ) -> None:
        """Regression: both history mutation sites route through
        ConversationState.append_message()/extend_messages() and produce the
        same role/tool_call_id/content shape as the previous raw
        history.append()/history.extend() calls.
        """
        cfg = _cfg()
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
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            return_value=([read_call], ["call_write"]),
        ):
            await execute_all_tool_calls(ctx, [write_call, read_call], 0)

        assert ctx.conv.history == [
            {
                "role": "tool",
                "tool_call_id": "call_read_text_file",
                "content": "result",
            },
            {
                "role": "tool",
                "tool_call_id": "call_write",
                "content": "Tool execution denied by user.",
            },
        ]


class TestRunApprovalGateEndToEnd:
    @pytest.mark.asyncio
    async def test_run_approval_checks_invoked_exactly_once_through_gateway(
        self,
    ) -> None:
        """Regression: _run_approval_gate() is the sole approval gate for the
        batch. A risky write tool call must trigger exactly one interactive
        approval prompt end-to-end, through both tool_runner's batch-level
        gate and a real (non-mocked-away) RepositoryGateway.execute() ->
        _gate_write(). If _gate_write() ever regains its own redundant
        approval check, this test fails because the prompt would be invoked
        twice.
        """
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.conv.plan_mode = False

        executor = AsyncMock()
        executor.execute = AsyncMock(
            return_value=ToolCallResult(
                output="written", is_error=False, request_id="req-1", server_key=""
            )
        )
        gateway = RepositoryGateway(executor=executor, cfg=cfg, audit_logger=None)
        ctx.services_required.gateway = gateway

        write_call = {
            "id": "call_write",
            "function": {"name": "write_file", "arguments": "{}"},
        }

        with patch(
            "agent.tool_approval._prompt_user_approval",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_prompt:
            await execute_all_tool_calls(ctx, [write_call], 0)

        mock_prompt.assert_awaited_once()
        executor.execute.assert_awaited_once_with("write_file", {})


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


class TestApplyTurnCharLimit:
    def test_apply_turn_char_limit_over_limit_returns_hint_with_sizes(self) -> None:
        llm_text = "line1\nline2\nline3"
        result = _apply_turn_char_limit(llm_text, turn_chars=0, limit=5)
        assert str(len(llm_text)) in result
        assert str(len(llm_text.splitlines())) in result
        assert "5" in result
        assert llm_text not in result

    def test_apply_turn_char_limit_under_limit_returns_text_unchanged(self) -> None:
        llm_text = "short text"
        result = _apply_turn_char_limit(llm_text, turn_chars=0, limit=4000)
        assert result == llm_text

    def test_apply_turn_char_limit_exact_boundary_returns_text_unchanged(self) -> None:
        llm_text = "12345"
        turn_chars = 5
        limit = turn_chars + len(llm_text)
        result = _apply_turn_char_limit(llm_text, turn_chars=turn_chars, limit=limit)
        assert result == llm_text


class TestExecuteStandardSerialization:
    # serial_tool_calls=True routes execute_all_tool_calls() to _execute_standard()
    # directly; _execute_with_dag() records serialization events via its own
    # resource-scope mechanism and is covered separately.
    @pytest.mark.asyncio
    async def test_side_effect_tool_records_serialization_event(self) -> None:
        """When a side-effect tool triggers serial execution, a serialization event is stored."""
        cfg = _cfg(serial_tool_calls=True)
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
        cfg = _cfg(serial_tool_calls=True)
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
        cfg = _cfg(serial_tool_calls=True)
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


class TestExecuteOneToolCallValidation:
    @pytest.mark.asyncio
    async def test_validation_failure_returns_error_result(self) -> None:
        """When argument validation fails, an error result is returned without execution."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        }
        runtime_tool_mock.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("read_text_file", '{"path": "/tmp/f", "extra": "malicious"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "read_text_file"
        assert is_error is True
        assert "extra" in text
        assert "extra" in llm_text
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_passes_when_runtime_tools_is_none(self) -> None:
        """When no RuntimeToolRegistry is available, validation is skipped."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.runtime_tools = None

        tc = _tc("read_text_file", '{"path": "/tmp/f"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "read_text_file"
        assert is_error is False
        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f"}
        )

    @pytest.mark.asyncio
    async def test_validation_passes_for_unknown_tool(self) -> None:
        """When tool is not in registry, validation is skipped (lenient fallback)."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.side_effect = KeyError("unknown_tool")

        tc = _tc("unknown_tool", '{"path": "/tmp/f"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "unknown_tool"
        assert is_error is False
        ctx.services_required.tools.execute.assert_awaited_once_with(
            "unknown_tool", {"path": "/tmp/f"}
        )

    @pytest.mark.asyncio
    async def test_validation_passes_for_empty_schema(self) -> None:
        """When schema is empty, validation is skipped."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {}
        runtime_tool_mock.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("read_text_file", '{"any": "field"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "read_text_file"
        assert is_error is False
        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {"any": "field"}
        )

    @pytest.mark.asyncio
    async def test_validation_passes_when_allow_extra_fields_true(self) -> None:
        """Extra fields are allowed when allow_extra_fields=True on the RuntimeTool."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        }
        runtime_tool_mock.allow_extra_fields = True
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("read_text_file", '{"path": "/tmp/f", "extra": "allowed"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "read_text_file"
        assert is_error is False
        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f", "extra": "allowed"}
        )

    @pytest.mark.asyncio
    async def test_type_mismatch_rejected(self) -> None:
        """Type mismatches are rejected by jsonschema validation."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {
            "type": "object",
            "required": ["count"],
            "properties": {"count": {"type": "integer"}},
        }
        runtime_tool_mock.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("create_item", '{"count": "not_an_int"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, _, text, is_error, llm_text = result
        assert name == "create_item"
        assert is_error is True
        assert "Type mismatch" in text
        assert "Type mismatch" in llm_text
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_required_field_rejected(self) -> None:
        """Missing required fields are rejected."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {
            "type": "object",
            "required": ["path", "mode"],
            "properties": {"path": {"type": "string"}, "mode": {"type": "string"}},
        }
        runtime_tool_mock.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("read_text_file", '{"path": "/tmp/f"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, _, text, is_error, llm_text = result
        assert name == "read_text_file"
        assert is_error is True
        assert "Missing required fields" in text
        assert "mode" in text
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_failure_prevents_gateway_execute(self) -> None:
        """When the gateway dispatch path is active, a validation rejection must
        prevent gateway.execute() from being called."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.gateway = MagicMock()
        ctx.services_required.gateway.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        runtime_tool_mock = MagicMock()
        runtime_tool_mock.input_schema = {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}},
        }
        runtime_tool_mock.allow_extra_fields = False
        ctx.services_required.runtime_tools = MagicMock()
        ctx.services_required.runtime_tools.get.return_value = runtime_tool_mock

        tc = _tc("write_text_file", '{"path": "/tmp/f", "extra": "malicious"}')
        result = await execute_one_tool_call(ctx, tc, 0)

        _, name, args, text, is_error, llm_text = result
        assert name == "write_text_file"
        assert is_error is True
        assert "extra" in text
        ctx.services_required.gateway.execute.assert_not_called()
        ctx.services_required.tools.execute.assert_not_called()
