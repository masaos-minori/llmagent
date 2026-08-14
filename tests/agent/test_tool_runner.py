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
from agent.tool_preparation import PreparedToolCall
from agent.tool_runner import (
    _apply_turn_char_limit,
    _compute_serial_overhead,
    _estimate_parallel_time,
    _execute_with_dag,
    execute_all_tool_calls,
    execute_one_tool_call,
)
from shared.tool_spec import ToolSpec
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


def _default_runtime_tools() -> MagicMock:
    """Default stub for ctx.services_required.runtime_tools.

    Production guarantees this registry is populated before any tool call
    reaches execution (see agent/startup.py), and agent.tool_preparation.
    prepare_tool_calls() (run once, per batch, before approval) calls
    tool_spec_for_call() per raw call unconditionally — so tests unrelated to
    scheduling metadata need a registry that resolves any tool name to a
    permissive default ToolSpec (unscoped, non-write) rather than crashing.
    Tests that care about specific scheduling metadata override this via
    ctx.services_required.runtime_tools = _runtime_tools({...}) (see below)
    or a hand-built mock.
    """
    registry = MagicMock()

    def _spec_for_call(call_id: str, name: str, args: dict) -> ToolSpec:
        return ToolSpec(call_id=call_id, name=name, args=args, is_write=False)

    def _get(name: str) -> MagicMock:
        tool = MagicMock()
        tool.is_write = False
        tool.input_schema = {}
        tool.allow_extra_fields = True
        return tool

    registry.tool_spec_for_call = MagicMock(side_effect=_spec_for_call)
    registry.get = MagicMock(side_effect=_get)
    return registry


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg = cfg or _cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.services_required.audit_logger = None
    ctx.services_required.gateway = None
    ctx.services_required.runtime_tools = _default_runtime_tools()
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


def _pc(
    name: str,
    args: dict[str, Any],
    call_id: str | None = None,
    spec: ToolSpec | None = None,
    tc: dict | None = None,
) -> PreparedToolCall:
    """Build a PreparedToolCall for tests that exercise execute_one_tool_call(),

    _execute_with_dag(), or _execute_standard() directly, bypassing the real
    prepare_tool_calls() pipeline. call_id defaults to f"call_{name}" to match
    _tc()'s id convention, so existing assertions on specific call ids keep
    working when a _tc(name) call site is swapped for _pc(name, args).
    """
    resolved_call_id = call_id or f"call_{name}"
    return PreparedToolCall(
        call_id=resolved_call_id,
        name=name,
        args=args,
        spec=spec
        or ToolSpec(call_id=resolved_call_id, name=name, args=args, is_write=False),
        original_call=tc
        or {
            "id": resolved_call_id,
            "function": {"name": name, "arguments": "{}"},
        },
    )


def _runtime_tools(specs_by_name: dict[str, ToolSpec]) -> MagicMock:
    """Build a stub RuntimeToolRegistry-shaped mock.

    `tool_spec_for_call(call_id, name, args)` returns a per-call ToolSpec built
    from `specs_by_name[name]`'s scheduling metadata (resource_scopes,
    requires_serial, is_write), with `call_id`/`name`/`args` substituted from
    the actual call — mirroring RuntimeToolRegistry.tool_spec_for_call()'s
    real contract. `get(name)` raises KeyError for any name absent from
    `specs_by_name`, matching the real registry. Used by tests exercising the
    real agent.tool_preparation.prepare_tool_calls() pipeline (via
    execute_all_tool_calls()) that need specific scheduling metadata.
    """
    registry = MagicMock()

    def _spec_for_call(call_id: str, name: str, args: dict) -> ToolSpec:
        base = specs_by_name[name]
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args,
            resource_scopes=base.resource_scopes,
            requires_serial=base.requires_serial,
            is_write=base.is_write,
        )

    def _get(name: str) -> MagicMock:
        base = specs_by_name[name]
        tool = MagicMock()
        tool.is_write = base.is_write
        # Empty schema so prepare_tool_calls()'s argument validation (which
        # consults this registry) does not reject the call.
        tool.input_schema = {}
        tool.allow_extra_fields = True
        return tool

    registry.tool_spec_for_call = MagicMock(side_effect=_spec_for_call)
    registry.get = MagicMock(side_effect=_get)
    return registry


class TestRegressionNoLegacyMetadata:
    def test_build_tool_meta_and_shell_tools_removed_from_source(self) -> None:
        """Regression: the name-keyed, statically-derived scheduling metadata
        path (_build_tool_meta() and its SHELL_TOOLS import) must not
        reappear in tool_runner.py — scheduling metadata now flows entirely
        through RuntimeToolRegistry.tool_spec_for_call().
        """
        from pathlib import Path

        source = Path("scripts/agent/tool_runner.py").read_text()
        assert "_build_tool_meta" not in source
        assert "SHELL_TOOLS" not in source

    def test_validate_tool_args_removed_from_source(self) -> None:
        """Regression: the lenient-fallback _validate_tool_args() (and its
        ctx.cfg.tool.tool_definitions gateway-fallback loop) must not reappear
        — argument validation now happens exactly once, fail-closed, in
        agent.tool_preparation.prepare_tool_calls(), before approval.
        """
        from pathlib import Path

        source = Path("scripts/agent/tool_runner.py").read_text()
        assert "_validate_tool_args" not in source


class TestExecuteWithDag:
    @pytest.mark.asyncio
    async def test_single_tool_returns_one_result(self) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        pc = _pc(
            "read_text_file",
            {},
            spec=ToolSpec(
                call_id="call_read_text_file", name="read_text_file", is_write=False
            ),
        )
        results = await _execute_with_dag(ctx, [pc], 0)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_write_first_before_read_in_group_order(self) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        write_pc = _pc(
            "write_file",
            {},
            spec=ToolSpec(call_id="call_write_file", name="write_file", is_write=True),
        )
        read_pc = _pc(
            "read_text_file",
            {},
            spec=ToolSpec(
                call_id="call_read_text_file", name="read_text_file", is_write=False
            ),
        )
        call_order: list[str] = []

        async def _record_exec(name: str, _args: dict) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(ctx, [read_pc, write_pc], 0)
        # write_file should execute before read_text_file in the group order
        write_idx = call_order.index("write_file")
        read_idx = call_order.index("read_text_file")
        assert write_idx < read_idx

    @pytest.mark.asyncio
    async def test_serial_barrier_executes_solo(self) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        shell_pc = _pc(
            "shell_run",
            {},
            spec=ToolSpec(
                call_id="call_shell_run",
                name="shell_run",
                requires_serial=True,
                is_write=False,
            ),
        )
        read_pc = _pc(
            "read_text_file",
            {},
            spec=ToolSpec(
                call_id="call_read_text_file", name="read_text_file", is_write=False
            ),
        )
        call_order: list[str] = []

        async def _record_exec(name: str, _args: dict) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(ctx, [shell_pc, read_pc], 0)
        assert call_order[0] == "shell_run"

    @pytest.mark.asyncio
    async def test_empty_approved_calls_returns_empty(self) -> None:
        ctx = _make_ctx()
        results = await _execute_with_dag(ctx, [], 0)
        assert results == []

    @pytest.mark.asyncio
    async def test_two_scope_groups_all_execute(self) -> None:
        """Two tools with different resource scopes both execute within the same round."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        write_pc = _pc(
            "write_file",
            {},
            spec=ToolSpec(
                call_id="call_write_file",
                name="write_file",
                resource_scopes=("filesystem:file",),
                is_write=True,
            ),
        )
        github_pc = _pc(
            "github_push_files",
            {},
            spec=ToolSpec(
                call_id="call_github_push_files",
                name="github_push_files",
                resource_scopes=("github_repo:github",),
                is_write=True,
            ),
        )
        read_pc = _pc(
            "read_text_file",
            {},
            spec=ToolSpec(
                call_id="call_read_text_file", name="read_text_file", is_write=False
            ),
        )
        executed: list[str] = []

        async def _record(name: str, _args: dict) -> ToolCallResult:
            executed.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record)
        results = await _execute_with_dag(ctx, [write_pc, github_pc, read_pc], 0)
        assert len(results) == 3
        assert set(executed) == {"write_file", "github_push_files", "read_text_file"}

    @pytest.mark.asyncio
    async def test_results_sorted_to_original_call_order(self) -> None:
        """Results are returned in the original approved_calls order."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        read_pc = _pc(
            "read_text_file",
            {},
            spec=ToolSpec(
                call_id="call_read_text_file", name="read_text_file", is_write=False
            ),
        )
        write_pc = _pc(
            "write_file",
            {},
            spec=ToolSpec(call_id="call_write_file", name="write_file", is_write=True),
        )
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req", server_key=""
            )
        )
        results = await _execute_with_dag(ctx, [read_pc, write_pc], 0)
        assert len(results) == 2
        # tc_id at index 0 should be "call_read_text_file"
        assert results[0][0] == "call_read_text_file"
        assert results[1][0] == "call_write_file"

    @pytest.mark.asyncio
    async def test_tool_meta_is_keyed_by_call_id_not_tool_name(self) -> None:
        """Regression: the dict passed to build_execution_groups() must be
        keyed by each call's call_id, not its tool name — two approved calls
        invoking the same tool name must be able to carry distinct per-call
        ToolSpecs (e.g. distinct resource_scopes from distinct args)."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        pc1 = _pc(
            "write_file",
            {},
            call_id="call_1",
            spec=ToolSpec(call_id="call_1", name="write_file", is_write=True),
        )
        pc2 = _pc(
            "write_file",
            {},
            call_id="call_2",
            spec=ToolSpec(call_id="call_2", name="write_file", is_write=True),
        )

        with patch(
            "agent.tool_runner.build_execution_groups",
            wraps=__import__(
                "agent.tool_scheduler", fromlist=["build_execution_groups"]
            ).build_execution_groups,
        ) as mock_build:
            await _execute_with_dag(ctx, [pc1, pc2], 0)

        passed_tool_meta = mock_build.call_args[0][1]
        assert set(passed_tool_meta.keys()) == {"call_1", "call_2"}
        assert "write_file" not in passed_tool_meta

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
            result = await execute_one_tool_call(ctx, _pc("shell_run", {}), 0)
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

        result = await execute_one_tool_call(ctx, _pc("shell_run", {}), 0)
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
            ctx, _pc("read_text_file", {}), 0
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
            ctx, _pc("read_text_file", {}), 0
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
            side_effect=lambda ctx, prepared: (prepared, []),
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
            side_effect=lambda ctx, prepared: (prepared, []),
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
            side_effect=lambda ctx, prepared: (
                [pc for pc in prepared if pc.call_id != "call_write"],
                ["call_write"],
            ),
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
            side_effect=lambda ctx, prepared: (
                [pc for pc in prepared if pc.call_id != "call_write"],
                ["call_write"],
            ),
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


def _write_registry(is_write_by_name: dict[str, bool]) -> MagicMock:
    """Build a stub RuntimeToolRegistry-shaped mock for `prepare_tool_calls()`.

    Stubs both `.get(name)` (schema/extra-fields lookup, consulted during
    preparation's argument validation) and `.tool_spec_for_call(call_id, name,
    args)` (the actual source of `PreparedToolCall.spec.is_write`, resolved
    once during preparation — `_execute_standard()` itself does no registry
    lookup). Both raise KeyError for any name absent from `is_write_by_name`,
    matching the real registry's unregistered-tool behavior.
    """
    registry = MagicMock()

    def _get(name: str) -> MagicMock:
        if name not in is_write_by_name:
            raise KeyError(name)
        tool = MagicMock()
        tool.is_write = is_write_by_name[name]
        # Empty schema/no-extra-fields so validate_tool_arguments() (also
        # consulted via this same registry during preparation) treats every
        # call as passing validation — this helper exists to test
        # _execute_standard()'s side-effect/serialization decision, not
        # argument validation.
        tool.input_schema = {}
        tool.allow_extra_fields = True
        return tool

    def _tool_spec_for_call(call_id: str, name: str, args: dict[str, Any]) -> ToolSpec:
        if name not in is_write_by_name:
            raise KeyError(name)
        return ToolSpec(
            call_id=call_id, name=name, args=args, is_write=is_write_by_name[name]
        )

    registry.get = MagicMock(side_effect=_get)
    registry.tool_spec_for_call = MagicMock(side_effect=_tool_spec_for_call)
    return registry


class TestExecuteStandardSerialization:
    # serial_tool_calls=True routes execute_all_tool_calls() to _execute_standard()
    # directly; _execute_with_dag() records serialization events via its own
    # resource-scope mechanism and is covered separately.
    @pytest.mark.asyncio
    async def test_side_effect_tool_records_serialization_event(self) -> None:
        """When a registered write tool triggers serial execution, a serialization event is stored."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"write_file": True})
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = None

        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
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
        """When the sole registered tool is not a write tool, no serialization event is recorded."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"read_text_file": False})
        ctx.stats.stat_serialization_events = []

        read_call = _tc("read_text_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ):
            await execute_all_tool_calls(ctx, [read_call], 0)

        assert ctx.stats.stat_serialization_events == []

    @pytest.mark.asyncio
    async def test_unregistered_tool_rejected_during_preparation(self) -> None:
        """A tool absent from the registry is now rejected fail-closed during
        the preparation phase (prepare_tool_calls) — it never reaches
        _execute_standard()'s side-effect/serialization logic at all, unlike
        the old lenient fallback this replaces."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({})
        ctx.stats.stat_serialization_events = []

        unknown_call = _tc("unknown_tool", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ):
            await execute_all_tool_calls(ctx, [unknown_call], 0)

        assert ctx.stats.stat_serialization_events == []
        ctx.services_required.tools.execute.assert_not_called()
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[-1]["role"] == "tool"
        assert "unregistered tool" in ctx.conv.history[-1]["content"]

    @pytest.mark.asyncio
    async def test_no_registry_rejected_during_preparation(self) -> None:
        """When ctx.services_required.runtime_tools is None, prepare_tool_calls()
        rejects every call fail-closed (a "configuration" failure) before
        approval or execution — it no longer falls through to
        _execute_standard() treating the call as a side effect."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = None
        ctx.stats.stat_serialization_events = []

        read_call = _tc("read_text_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ):
            await execute_all_tool_calls(ctx, [read_call], 0)

        assert ctx.stats.stat_serialization_events == []
        ctx.services_required.tools.execute.assert_not_called()
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[-1]["role"] == "tool"
        assert "RuntimeToolRegistry is not available" in ctx.conv.history[-1]["content"]

    @pytest.mark.asyncio
    async def test_side_effect_calls_diagnostic_save(self) -> None:
        """When diagnostics are wired, save_serialization_event is called."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"write_file": True})
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = MagicMock()

        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=lambda ctx, prepared: (prepared, []),
        ):
            await execute_all_tool_calls(ctx, [write_call], 0)

        ctx.diagnostics.save_serialization_event.assert_called_once()
        call_kwargs = ctx.diagnostics.save_serialization_event.call_args[1]
        assert call_kwargs["trigger_tool"] == "write_file"
        assert call_kwargs["mode"] == "serial"
        assert call_kwargs["reason"] == "side_effect"
