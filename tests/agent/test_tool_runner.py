"""
tests/test_tool_runner.py
Unit tests for tool_runner.py: DAG execution, standard execution, and entry point.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.context import ConversationState, TurnState
from agent.repository_gateway import RepositoryGateway
from agent.shared.models import ApprovalGrant
from agent.tool_enums import ApprovalDecisionType
from agent.tool_exceptions import ToolExecutorUnavailableError
from agent.tool_loop_guard import ToolLoopGuard
from agent.tool_policy import PolicyViolationError
from agent.tool_preparation import (
    PreparedToolCall,
    ReplayDirective,
    _canonical_args_hash,
    prepare_tool_calls,
)
from agent.tool_run_recorder import get_serialization_stats
from agent.tool_runner import (
    _apply_turn_char_limit,
    _collect_tool_result_msgs,
    _emit_tool_result,
    _execute_with_dag,
    _finalize_state,
    _record_pending_state,
    execute_all_tool_calls,
    execute_one_tool_call,
)
from agent.tool_scheduler import ExecutionPlan, ScheduledBatch, ScheduledGroup
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS, READ_TOOLS
from shared.tool_executor_helpers import tool_hash_key
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult, ToolExecutionContext

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    PERMISSIVE_ALLOWED_ROOT,
    SHIPPED_DB_PATH_KEYS,
)
from tests.agent._producer_registry import make_producer_registry


def _cfg(**overrides: Any) -> AgentConfig:
    """Build an AgentConfig for tool_runner.py unit tests.

    This intentionally bypasses ProductionConfigValidator (patched below):
    only tool_safety_tiers and approval_risk_rules are deliberately empty,
    which is a different concern from whether the resulting config would be
    accepted as production-ready. allowed_tools/allowed_root are non-empty
    because the fail-closed guards (REQ-002, REQ-003) deny every call when
    either is empty.
    """
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": list(ALL_TOOL_NAMES),
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": PERMISSIVE_ALLOWED_ROOT,
        "tool_results_turn_max_chars": 0,
        # memory_embed_enabled now defaults to True; memory_embed_url must be non-empty
        # to satisfy MemoryConfig.__post_init__'s cross-field validation.
        "memory_embed_url": "http://127.0.0.1:9999",
        # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
        **SHIPPED_DB_PATH_KEYS,
        "mcp_servers": {
            "_dummy": {
                "transport": "http",
                "url": "http://127.0.0.1:9999",
                "auth_token": "test-token",
            }
        },
    }
    defaults.update(overrides)
    with patch("agent.config_builders.ProductionConfigValidator") as mock_validator:
        mock_validator.return_value.validate.return_value.errors = []
        mock_validator.return_value.validate.return_value.warnings = []
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
        # Declared-metadata mock (agentcfg003 REQ-007): names outside the
        # shipped classification are unregistered (KeyError -> UNKNOWN
        # fail-closed); known tools carry the policy fields the middleware reads.
        if name not in READ_TOOLS | ALL_SIDE_EFFECTING_TOOLS:
            raise KeyError(name)
        side_effecting = name in ALL_SIDE_EFFECTING_TOOLS
        tool = MagicMock()
        tool.is_write = side_effecting
        tool.side_effect_class = "external_state" if side_effecting else "read_only"
        tool.retry_policy = (
            "same_logical_call_only" if side_effecting else "safe_read_retry"
        )
        tool.agent_safety_tier = "WRITE_DANGEROUS" if side_effecting else "READ_ONLY"
        tool.input_schema = {"type": "object", "properties": {}}
        tool.allow_extra_fields = True
        return tool

    registry.tool_spec_for_call = MagicMock(side_effect=_spec_for_call)
    registry.get = MagicMock(side_effect=_get)
    return registry


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg = cfg or _cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    # mcpdl001 REQ-007 fail-closed: side-effecting calls raise when the audit
    # logger is None, so the generic fixture carries a mock; audit-sensitive
    # tests override this attribute explicitly.
    ctx.services_required.audit_logger = MagicMock()
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
    ctx.conv = ConversationState()
    ctx.session = MagicMock()
    ctx.session.session_id = None
    # Tool-result persist routes through the turn's atomic boundary (SEQ-08);
    # expose an awaitable save_phase_grouped so complete_round()'s round path
    # resolves it without a real session/DB.
    ctx.turn.persistence_boundary = _persistence_boundary_mock()
    ctx.workflow.workflow_id = "wf-test-id"
    # mcpai007 REQ-004: the audit writers read the workflow task id from context.
    ctx.workflow.current_task_id = "test-task-id"
    return ctx


def _persistence_boundary_mock() -> MagicMock:
    """A stand-in TurnPersistence with awaitable write methods.

    Lets execute_all_tool_calls route its round persist through
    ``ctx.turn.persistence_boundary`` (SEQ-08) without a real session/DB.
    """
    boundary = MagicMock()
    boundary.save = AsyncMock(return_value=None)
    boundary.save_many = AsyncMock(return_value=None)
    boundary.save_phase_grouped = AsyncMock(return_value=None)
    boundary.replace_messages = AsyncMock(return_value=None)
    return boundary


def _tc(name: str, args: str = "{}") -> dict:
    return {"id": f"call_{name}", "function": {"name": name, "arguments": args}}


def _pc(
    name: str,
    args: dict[str, Any],
    call_id: str | None = None,
    spec: ToolSpec | None = None,
    tc: dict | None = None,
    *,
    context: bool = True,
    grant: bool = True,
    execution_mode: str = "applied",
) -> PreparedToolCall:
    """Build a PreparedToolCall for tests that exercise execute_one_tool_call()

    or _execute_with_dag() directly, bypassing the real prepare_tool_calls()
    pipeline. call_id defaults to f"call_{name}" to match _tc()'s id
    convention, so existing assertions on specific call ids keep working when
    a _tc(name) call site is swapped for _pc(name, args).

    mcpdl001 shape: the fixture carries the execution context and approval
    grant the real pipeline produces — the context call_id equals call_id so
    state-row keys stay deterministic. context=False / grant=False build the
    id-less / ungranted shapes the fail-closed gates deny (REQ-003/REQ-006).
    execution_mode carries the mode resolved at preparation (mcpai005 REQ-009).
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
        context=(
            ToolExecutionContext(
                call_id=resolved_call_id,
                tool=name,
                args_hash=_canonical_args_hash(args),
                operation="call_tool",
                execution_mode=execution_mode,
            )
            if context
            else None
        ),
        grant=(
            ApprovalGrant(
                tool=name,
                args_hash=_canonical_args_hash(args),
                mode=ApprovalDecisionType.APPROVED.value,
                issued_at=time.time(),
                expires_at=time.time() + 300.0,
            )
            if grant
            else None
        ),
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
        # Zero-argument schema so prepare_tool_calls()'s argument validation (which
        # consults this registry) does not reject the call.
        tool.input_schema = {"type": "object", "properties": {}}
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
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_conflicting_writes_execute_in_group_order(self) -> None:
        """Two writes sharing a resource scope form one sequential
        ScheduledGroup and must execute in that group's order; an unrelated
        read has nothing to conflict with and is pooled into the concurrent
        group instead (no ordering guarantee against it) — there is no more
        separate "write-first" bucket that always precedes every read
        regardless of conflicts."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        write_a_pc = _pc(
            "write_file",
            {},
            call_id="call_write_a",
            spec=ToolSpec(
                call_id="call_write_a",
                name="write_file",
                resource_scopes=("filesystem:/shared",),
                is_write=True,
            ),
        )
        write_b_pc = _pc(
            "edit_file",
            {},
            call_id="call_write_b",
            spec=ToolSpec(
                call_id="call_write_b",
                name="edit_file",
                resource_scopes=("filesystem:/shared",),
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
        call_order: list[str] = []

        async def _record_exec(
            name: str, _args: dict, *, context: object | None = None
        ) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(
            ctx,
            [write_a_pc, write_b_pc, read_pc],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        # The conflicting write pair must execute in group order.
        assert call_order.index("write_file") < call_order.index("edit_file")
        # The unrelated read still executes (no ordering guarantee against it).
        assert "read_text_file" in call_order

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

        async def _record_exec(
            name: str, _args: dict, *, context: object | None = None
        ) -> ToolCallResult:
            call_order.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(
            ctx, [shell_pc, read_pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert call_order[0] == "shell_run"

    @pytest.mark.asyncio
    async def test_empty_approved_calls_returns_empty(self) -> None:
        ctx = _make_ctx()
        results = await _execute_with_dag(
            ctx, [], guard=ToolLoopGuard(ctx), collected={}
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_two_scope_groups_all_execute(self) -> None:
        """Two tools with different resource scopes both execute within the same round."""
        cfg = _cfg(approval_github_allowed_repos=["org/repo"])
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
            {"owner": "org", "repo": "repo"},
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

        async def _record(
            name: str, _args: dict, *, context: object | None = None
        ) -> ToolCallResult:
            executed.append(name)
            return ToolCallResult(
                output="ok", is_error=False, request_id="req", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record)
        results = await _execute_with_dag(
            ctx, [write_pc, github_pc, read_pc], guard=ToolLoopGuard(ctx), collected={}
        )
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
        results = await _execute_with_dag(
            ctx, [read_pc, write_pc], guard=ToolLoopGuard(ctx), collected={}
        )
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
            await _execute_with_dag(
                ctx, [pc1, pc2], guard=ToolLoopGuard(ctx), collected={}
            )

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
            result = await execute_one_tool_call(
                ctx, _pc("shell_run", {}), guard=ToolLoopGuard(ctx)
            )
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

        result = await execute_one_tool_call(
            ctx, _pc("shell_run", {}), guard=ToolLoopGuard(ctx)
        )
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
            ctx, _pc("read_text_file", {}), guard=ToolLoopGuard(ctx)
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
            ctx, _pc("read_text_file", {}), guard=ToolLoopGuard(ctx)
        )

        assert llm_text == text_over_old_threshold


class TestExecuteOneToolCallRecordsOnGuard:
    """Each produced non-error result is recorded on the passed guard, before truncation."""

    @staticmethod
    def _ctx(max_repeats: int = 5) -> MagicMock:
        ctx = _make_ctx(_cfg())
        ctx.cfg.tool.tool_empty_result_max_repeats = max_repeats
        ctx.diagnostics = None
        return ctx

    @pytest.mark.asyncio
    async def test_gateway_bypass_path_records_the_result(self) -> None:
        ctx = self._ctx()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="", is_error=False, request_id="r", server_key=""
            )
        )
        guard = ToolLoopGuard(ctx)

        await execute_one_tool_call(ctx, _pc("read_text_file", {}), guard=guard)

        assert guard._empty_result_counts == {"read_text_file": 1}

    @pytest.mark.asyncio
    async def test_gateway_path_records_the_result(self) -> None:
        ctx = self._ctx()
        ctx.services_required.gateway = MagicMock()
        ctx.services_required.gateway.execute = AsyncMock(
            return_value=ToolCallResult(
                output="", is_error=False, request_id="r", server_key=""
            )
        )
        guard = ToolLoopGuard(ctx)

        await execute_one_tool_call(ctx, _pc("read_text_file", {}), guard=guard)

        assert guard._empty_result_counts == {"read_text_file": 1}

    @pytest.mark.asyncio
    async def test_error_result_is_not_recorded(self) -> None:
        ctx = self._ctx()
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="", is_error=True, request_id="r", server_key=""
            )
        )
        guard = ToolLoopGuard(ctx)

        await execute_one_tool_call(ctx, _pc("read_text_file", {}), guard=guard)

        assert guard._empty_result_counts == {}

    @pytest.mark.asyncio
    async def test_empty_result_is_recorded_from_the_untruncated_output(self) -> None:
        ctx = self._ctx()
        ctx.cfg.tool.tool_result_max_llm_chars = 5
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[
                ToolCallResult(
                    output="x" * 50, is_error=False, request_id="r", server_key=""
                ),
                ToolCallResult(
                    output="", is_error=False, request_id="r", server_key=""
                ),
            ]
        )
        guard = ToolLoopGuard(ctx)

        await execute_one_tool_call(ctx, _pc("read_text_file", {}), guard=guard)
        await execute_one_tool_call(ctx, _pc("read_text_file", {}), guard=guard)

        # A non-empty (even truncated) result resets the count; the empty one starts it.
        assert guard._empty_result_counts == {"read_text_file": 1}

    @pytest.mark.parametrize("serial", [True, False])
    @pytest.mark.asyncio
    async def test_both_group_shapes_record_every_result(self, serial: bool) -> None:
        ctx = self._ctx()
        ctx.cfg.tool.serial_tool_calls = serial
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="", is_error=False, request_id="r", server_key=""
            )
        )
        guard = ToolLoopGuard(ctx)

        await _execute_with_dag(
            ctx,
            [_pc("read_text_file", {"i": i}, call_id=f"c{i}") for i in range(3)],
            guard=guard,
            force_serial=serial,
            collected={},
        )

        assert guard._empty_result_counts == {"read_text_file": 3}

    @pytest.mark.asyncio
    async def test_collector_no_longer_reads_a_guard_from_ctx(self) -> None:
        ctx = self._ctx()
        ctx.guard = ToolLoopGuard(ctx)  # the old, never-assigned attribute
        results: list[tuple[str, str, dict[str, Any], str, bool, str]] = [
            ("c1", "read_text_file", {}, "", False, "")
        ]

        await _collect_tool_result_msgs(ctx, results, 0, None)

        assert ctx.guard._empty_result_counts == {}


def _declared(*names: str) -> list[dict]:
    return [_tc(name) for name in names]


def _tool_history_ids(ctx: MagicMock) -> list[str]:
    return [m["tool_call_id"] for m in ctx.conv.history if m.get("role") == "tool"]


def _saved_tool_ids(ctx: MagicMock) -> list[str]:
    rows = ctx.turn.persistence_boundary.save_phase_grouped.call_args.args[0]
    return [row[3] for row in rows]


def _saved_text(ctx: MagicMock, call_id: str) -> str:
    rows = ctx.turn.persistence_boundary.save_phase_grouped.call_args.args[0]
    return str(next(row[1] for row in rows if row[3] == call_id))


def _grant_for(pc: PreparedToolCall) -> ApprovalGrant:
    now = time.time()
    return ApprovalGrant(
        tool=pc.name,
        args_hash=pc.context.args_hash if pc.context else "",
        mode=ApprovalDecisionType.APPROVED.value,
        issued_at=now,
        expires_at=now + 300.0,
    )


def _approve_issuing_grants(
    ctx: Any, prepared: list[PreparedToolCall]
) -> tuple[list[PreparedToolCall], list[str]]:
    """Approval stand-in mirroring row 02: approved calls carry their grant."""
    return [dataclasses.replace(pc, grant=_grant_for(pc)) for pc in prepared], []


def _approve_all() -> Any:
    return patch(
        "agent.tool_approval.run_approval_checks",
        new_callable=AsyncMock,
        side_effect=_approve_issuing_grants,
    )


def _ok(output: str = "result") -> ToolCallResult:
    return ToolCallResult(output=output, is_error=False, request_id="r", server_key="")


class TestBatchFailureTotality:
    """Every declared tool_call id is answered exactly once.

    A call that raises DURING execution is converted into an error row (the
    round completes); only a BaseException such as asyncio.CancelledError, or a
    failure before execution (approval, completion), leaves the round raised.
    """

    @staticmethod
    def _assert_paired(ctx: MagicMock, declared: list[str]) -> None:
        assert sorted(_tool_history_ids(ctx)) == sorted(declared)
        assert sorted(_saved_tool_ids(ctx)) == sorted(declared)
        ctx.turn.persistence_boundary.save_phase_grouped.assert_called_once()

    @pytest.mark.asyncio
    async def test_executor_unavailable_yields_error_row_not_raise(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools = None
        calls = _declared("read_text_file", "list_directory")

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, [c["id"] for c in calls])
        text = _saved_text(ctx, calls[0]["id"])
        assert "Tool execution failed" in text
        assert "ToolExecutorUnavailableError" in text

    @pytest.mark.asyncio
    async def test_policy_violation_yields_error_row_not_raise(self) -> None:
        ctx = _make_ctx()
        calls = _declared("shell_run")

        with (
            _approve_all(),
            patch(
                "agent.tool_runner.check_preflight",
                side_effect=PolicyViolationError("denied", "denied by policy"),
            ),
        ):
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, [calls[0]["id"]])
        text = _saved_text(ctx, calls[0]["id"])
        assert "Tool execution failed" in text
        assert "PolicyViolationError" in text

    @pytest.mark.asyncio
    async def test_resolver_value_error_yields_error_row_not_raise(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=ValueError("unregistered tool")
        )
        calls = _declared("read_text_file")

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, [calls[0]["id"]])
        text = _saved_text(ctx, calls[0]["id"])
        assert "Tool execution failed" in text
        assert "unregistered tool" in text

    @pytest.mark.asyncio
    async def test_gathered_group_yields_one_error_and_one_real_row(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[RuntimeError("boom"), _ok("real-output")]
        )
        calls = _declared("read_text_file", "list_directory")

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        # Exactly one error row and one real row survive; which call took the
        # raise is non-deterministic under gather, so assert on counts.
        texts = {c["id"]: _saved_text(ctx, c["id"]) for c in calls}
        error_ids = [cid for cid, t in texts.items() if "Tool execution failed" in t]
        real_ids = [cid for cid, t in texts.items() if "Tool execution failed" not in t]
        assert len(error_ids) == 1
        assert len(real_ids) == 1
        assert "RuntimeError" in texts[error_ids[0]]
        assert "boom" in texts[error_ids[0]]
        assert texts[real_ids[0]] == "real-output"

    @pytest.mark.asyncio
    async def test_sequential_group_continues_after_a_failure(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[
                RuntimeError("boom"),
                _ok("second-output"),
                _ok("third-output"),
            ]
        )
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "list_directory", "arguments": "{}"}},
            {"id": "c2", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, ["c0", "c1", "c2"])
        assert "Tool execution failed" in _saved_text(ctx, "c0")
        assert _saved_text(ctx, "c1") == "second-output"
        assert _saved_text(ctx, "c2") == "third-output"

    @pytest.mark.asyncio
    async def test_later_batch_runs_after_an_earlier_failure(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[RuntimeError("boom"), _ok("second-output")]
        )
        pcs = [
            _pc("read_text_file", {"i": 1}, call_id="c1"),
            _pc("list_directory", {"i": 2}, call_id="c2"),
        ]
        collected: dict[str, tuple] = {}

        plan = ExecutionPlan(
            batches=(
                ScheduledBatch(
                    groups=(
                        ScheduledGroup(
                            calls=(pcs[0].spec,), sequential=True, reason="test"
                        ),
                    ),
                ),
                ScheduledBatch(
                    groups=(
                        ScheduledGroup(
                            calls=(pcs[1].spec,), sequential=True, reason="test"
                        ),
                    ),
                ),
            ),
            serialization_events=(),
        )

        with patch("agent.tool_runner.build_execution_groups", return_value=plan):
            results = await _execute_with_dag(
                ctx, pcs, guard=ToolLoopGuard(ctx), collected=collected
            )

        assert [r[0] for r in results] == ["c1", "c2"]
        assert results[0][4] is True  # c1 raised -> captured as an error row
        assert "Tool execution failed" in results[0][3]
        assert results[1][4] is False  # c2 succeeded -> its real output survives
        assert results[1][1] == "list_directory"

    @pytest.mark.asyncio
    async def test_error_row_carries_marker_class_and_message(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=RuntimeError("kaboom")
        )
        pc = _pc("read_text_file", {"i": 1}, call_id="c1")
        collected: dict[str, tuple] = {}

        await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        row = collected["c1"]
        assert row[0] == "c1"  # tool_call_id preserved
        assert row[1] == "read_text_file"
        assert row[4] is True  # is_error
        assert "[Tool execution failed:" in row[3]
        assert "RuntimeError" in row[3]
        assert "kaboom" in row[3]

    @pytest.mark.asyncio
    async def test_error_row_llm_copy_respects_the_char_limit(self) -> None:
        ctx = _make_ctx(_cfg(tool_result_max_llm_chars=20))
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=RuntimeError("x" * 500)
        )
        pc = _pc("read_text_file", {"i": 1}, call_id="c1")
        collected: dict[str, tuple] = {}

        await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        llm_text = collected["c1"][5]
        assert len(llm_text) <= 20 + len("\n... (truncated)")
        assert "... (truncated)" in llm_text

    @pytest.mark.asyncio
    async def test_cancellation_still_propagates_not_converted(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[asyncio.CancelledError("stop"), _ok()]
        )
        calls = _declared("read_text_file", "list_directory")

        with _approve_all(), pytest.raises(asyncio.CancelledError):
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

    @pytest.mark.asyncio
    async def test_approval_gate_raises_before_any_execution(self) -> None:
        ctx = _make_ctx()
        calls = _declared("read_text_file", "list_directory")

        with (
            patch(
                "agent.tool_approval.run_approval_checks",
                new_callable=AsyncMock,
                side_effect=RuntimeError("approval down"),
            ),
            pytest.raises(RuntimeError, match="approval down"),
        ):
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, [c["id"] for c in calls])
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_plain_exception_still_attempts_best_effort_completion(self) -> None:
        ctx = _make_ctx()
        with (
            patch(
                "agent.tool_runner.complete_round",
                new_callable=AsyncMock,
            ) as complete_round,
            patch(
                "agent.tool_approval.run_approval_checks",
                new_callable=AsyncMock,
                side_effect=RuntimeError("approval down"),
            ),
        ):
            with pytest.raises(RuntimeError, match="approval down"):
                await execute_all_tool_calls(
                    ctx,
                    _declared("read_text_file", "list_directory"),
                    0,
                    guard=ToolLoopGuard(ctx),
                )

        # A non-cancellation BaseException still best-effort completes the round.
        complete_round.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_failing_completion_still_raises(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools = None
        ctx.turn.persistence_boundary.save_phase_grouped.side_effect = RuntimeError(
            "db down"
        )

        # The per-call failure is now converted to an error row, so the round
        # completes; the surviving exception is the completion (save_phase_grouped)
        # one.
        with _approve_all(), pytest.raises(RuntimeError, match="db down"):
            await execute_all_tool_calls(
                ctx, _declared("read_text_file"), 0, guard=ToolLoopGuard(ctx)
            )

    @pytest.mark.asyncio
    async def test_normal_round_synthesizes_nothing(self) -> None:
        ctx = _make_ctx()
        calls = _declared("read_text_file", "list_directory")

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        self._assert_paired(ctx, [c["id"] for c in calls])
        assert "not executed" not in " ".join(_saved_text(ctx, c["id"]) for c in calls)


class TestCompletedResultsSurviveAFailure:
    @pytest.mark.asyncio
    async def test_first_result_kept_and_failed_call_becomes_error_row(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[_ok("first-output"), RuntimeError("boom")]
        )
        calls = _declared("read_text_file", "list_directory")

        # The failing call is converted to an error row; the round completes.
        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))

        assert _saved_text(ctx, calls[0]["id"]) == "first-output"
        failed_text = _saved_text(ctx, calls[1]["id"])
        assert "Tool execution failed" in failed_text
        assert "RuntimeError" in failed_text
        assert _saved_tool_ids(ctx) == [c["id"] for c in calls]  # original order


class TestMidRoundGuardStop:
    @pytest.mark.asyncio
    async def test_a_trip_skips_the_rest_and_answers_it_with_the_guard_stop_reason(
        self,
    ) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        ctx.cfg.tool.tool_empty_result_max_repeats = 2
        ctx.diagnostics = MagicMock()
        ctx.services_required.tools.execute = AsyncMock(return_value=_ok(""))
        calls = [
            {"id": f"c{i}", "function": {"name": "read_text_file", "arguments": "{}"}}
            for i in range(3)
        ]
        guard = ToolLoopGuard(ctx)

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=guard)

        assert ctx.services_required.tools.execute.await_count == 2
        assert "stopped by a loop guard" in _saved_text(ctx, "c2")
        assert _saved_tool_ids(ctx) == ["c0", "c1", "c2"]
        # The mid-round scan records nothing: the single hint comes from the
        # post-round check.
        ctx.diagnostics.save.assert_not_called()
        assert guard.check_empty_result_repeat({"role": "assistant"}) is not None
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_a_trip_ends_the_remaining_calls_of_one_sequential_group(
        self,
    ) -> None:
        ctx = _make_ctx(_cfg())
        ctx.cfg.tool.tool_empty_result_max_repeats = 2
        ctx.services_required.tools.execute = AsyncMock(return_value=_ok(""))
        pcs = [
            _pc(
                "write_file",
                {"i": i},
                call_id=f"w{i}",
                spec=ToolSpec(
                    call_id=f"w{i}",
                    name="write_file",
                    resource_scopes=("filesystem:/shared",),
                    is_write=True,
                ),
            )
            for i in range(3)
        ]
        collected: dict[str, tuple] = {}

        results = await _execute_with_dag(
            ctx, pcs, guard=ToolLoopGuard(ctx), collected=collected
        )

        assert ctx.services_required.tools.execute.await_count == 2
        assert sorted(collected) == ["w0", "w1"]
        assert [r[0] for r in results] == ["w0", "w1"]


class TestCancellationDispatchState:
    """AC-001..AC-003 (plan 20261101-144325): the hint a cancelled round
    synthesizes per missing call reflects that call's dispatch state.

    Cancelled mid-execution: the call had been dispatched → outcome-unknown
    text. Never dispatched (later serial call, or cancelled before the
    execution phase): the call provably never ran → "not executed" text.
    A completed round keeps its real rows untouched (AC-003 characterization).
    """

    @pytest.mark.asyncio
    async def test_cancellation_skips_completion_no_synthesized_rows(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_execute(
            name: str, args: dict, *, context: object | None = None
        ) -> ToolCallResult:
            started.set()
            await block.wait()  # never set: the round is cancelled while here
            return _ok("never-reached")

        ctx.services_required.tools.execute = blocking_execute
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        task = asyncio.create_task(
            execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
        )
        with _approve_all():
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # Completion is skipped on cancellation: nothing is persisted or synthesized.
        ctx.turn.persistence_boundary.save_phase_grouped.assert_not_called()

    @pytest.mark.asyncio
    async def test_completed_round_keeps_real_results_and_synthesizes_nothing(
        self,
    ) -> None:
        ctx = _make_ctx(_cfg())
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
        # AC-003: dispatched_ids must be drained by completed calls (discard on
        # write), so a completed round carries no synthesized row at all.
        assert _saved_text(ctx, "c0") == "result"
        assert _saved_text(ctx, "c1") == "result"
        assert _saved_tool_ids(ctx) == ["c0", "c1"]

    @pytest.mark.asyncio
    async def test_cancellation_before_any_dispatch_skips_completion(self) -> None:
        ctx = _make_ctx(_cfg())
        approval_started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_approval(
            ctx: Any, prepared: list[Any]
        ) -> tuple[list[Any], list[str]]:
            approval_started.set()
            await block.wait()  # cancelled while awaiting approval
            return prepared, []

        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        task = asyncio.create_task(
            execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
        )
        with patch("agent.tool_approval.run_approval_checks", new=blocking_approval):
            await approval_started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # No completion runs on cancellation: nothing is persisted or synthesized.
        ctx.turn.persistence_boundary.save_phase_grouped.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancellation_skips_best_effort_completion(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_execute(
            name: str, args: dict, *, context: object | None = None
        ) -> ToolCallResult:
            started.set()
            await block.wait()  # never set: the round is cancelled while here
            return _ok("never-reached")

        ctx.services_required.tools.execute = blocking_execute
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        with (
            patch(
                "agent.tool_runner.complete_round",
                new_callable=AsyncMock,
            ) as complete_round,
            _approve_all(),
        ):
            task = asyncio.create_task(
                execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
            )
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # Completion is skipped on cancellation: complete_round is not awaited.
        complete_round.assert_not_awaited()


class TestStatsForRealVsSynthesizedRows:
    @pytest.mark.asyncio
    async def test_every_failed_call_increments_stats_and_failed_keys(self) -> None:
        # A raised call is now an error row that reaches stats (REQ-009/AC-7),
        # unlike the pre-fix behavior where it aborted the round.
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        ctx.cfg.tool.tool_empty_result_max_repeats = 5
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=[RuntimeError("boom-a"), RuntimeError("boom-b")]
        )
        calls = _declared("read_text_file", "list_directory")
        failed: set[str] = set()
        guard = ToolLoopGuard(ctx)

        with _approve_all():
            await execute_all_tool_calls(ctx, calls, 0, failed, guard=guard)

        assert ctx.stats.stat_tool_calls == 2
        assert ctx.stats.stat_tool_errors == 2
        assert len(failed) == 2

    @pytest.mark.asyncio
    async def test_never_rans_synthesized_row_skips_stats(self) -> None:
        """dupcallid001 amendment: the original scenario relied on two calls sharing
        the `_tc`-derived id `call_read_text_file` — a duplicate id is now rejected in
        preparation, so the guard-stop synthesized row is produced by unique-id calls
        instead (the empty-result guard trips mid-round and never dispatches the last).
        """
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        ctx.cfg.tool.tool_empty_result_max_repeats = 2
        ctx.services_required.tools.execute = AsyncMock(return_value=_ok(""))
        calls = [
            _tc("read_text_file"),
            _tc("list_directory"),
            {
                "id": "call_read_2",
                "function": {"name": "read_text_file", "arguments": "{}"},
            },
            {
                "id": "call_read_3",
                "function": {"name": "read_text_file", "arguments": "{}"},
            },
        ]
        failed: set[str] = set()

        with _approve_all():
            await execute_all_tool_calls(
                ctx, calls, 0, failed, guard=ToolLoopGuard(ctx)
            )

        # The empty-result guard trips after the second empty `read_text_file` result
        # and `_run_plan_batches` never dispatches `call_read_3`. Only the three
        # executed rows hit stats; the guard-stop synthesized row bypasses stats
        # (see complete_round).
        assert ctx.services_required.tools.execute.await_count == 3
        assert ctx.stats.stat_tool_calls == 3
        assert ctx.stats.stat_tool_errors == 0
        assert failed == set()
        synthesized = [
            m
            for m in ctx.conv.history
            if m.get("role") == "tool" and m.get("tool_call_id") == "call_read_3"
        ]
        assert len(synthesized) == 1
        assert "loop guard" in synthesized[0]["content"]


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

        with _approve_all():
            await execute_all_tool_calls(
                ctx,
                [_tc("read_text_file", '{"path": "/tmp/f"}')],
                0,
                guard=ToolLoopGuard(ctx),
            )

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f"}, context=ANY
        )
        ctx.turn.persistence_boundary.save_phase_grouped.assert_called_once()

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
        with _approve_all():
            await execute_all_tool_calls(
                ctx,
                [write_call],
                0,
                guard=ToolLoopGuard(ctx),
            )

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "write_file", {}, context=ANY
        )

    @pytest.mark.asyncio
    async def test_no_tool_calls_does_nothing(self) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()

        await execute_all_tool_calls(ctx, [], 0, guard=ToolLoopGuard(ctx))

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
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

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
                [
                    dataclasses.replace(pc, grant=_grant_for(pc))
                    for pc in prepared
                    if pc.call_id != "call_write"
                ],
                ["call_write"],
            ),
        ):
            await execute_all_tool_calls(
                ctx, [write_call, read_call], 0, guard=ToolLoopGuard(ctx)
            )

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {}, context=ANY
        )
        # Should have both the tool result and the denied message
        assert len(ctx.conv.history) == 2
        assert ctx.conv.history[-1]["role"] == "tool"
        assert ctx.conv.history[-1]["content"] == "Tool execution denied by user."

    @pytest.mark.asyncio
    async def test_call_without_id_is_answered_in_batch_position(self) -> None:
        """A raw call lacking an id is rejected in place; the round still completes."""
        ctx = _make_ctx(_cfg())
        no_id_call = {"function": {"name": "read_text_file", "arguments": "{}"}}
        valid_call = _tc("read_text_file")

        with _approve_all():
            await execute_all_tool_calls(
                ctx, [no_id_call, valid_call], 0, guard=ToolLoopGuard(ctx)
            )

        ctx.services_required.tools.execute.assert_awaited_once_with(
            "read_text_file", {}, context=ANY
        )
        assert len(ctx.conv.history) == 2
        assert ctx.conv.history[0]["tool_call_id"] == ""
        assert ctx.conv.history[0]["content"] == "tool call is missing an id"
        assert ctx.conv.history[1]["tool_call_id"] == "call_read_text_file"

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
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

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
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

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
                [
                    dataclasses.replace(pc, grant=_grant_for(pc))
                    for pc in prepared
                    if pc.call_id != "call_write"
                ],
                ["call_write"],
            ),
        ):
            await execute_all_tool_calls(
                ctx, [write_call, read_call], 0, guard=ToolLoopGuard(ctx)
            )

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
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

        mock_prompt.assert_awaited_once()
        executor.execute.assert_awaited_once_with("write_file", {})


class TestExecuteAllToolCallsDuplicateCallId:
    """Round-level regression (REQ-001/REQ-003; AC-001/AC-002/AC-003): two calls
    sharing one id execute neither call twice nor with the other call's arguments,
    never reach the approval prompt, and each declared occurrence gets one
    consistent rejection answer in history and persisted rows.
    """

    @pytest.mark.asyncio
    async def test_duplicate_id_round_executes_nothing_and_answers_both_rows(
        self,
    ) -> None:
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = MagicMock()
        executed: list[tuple[str, dict]] = []

        def _record(name: str, args: dict) -> ToolCallResult:
            executed.append((name, args))
            return ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )

        ctx.services_required.tools.execute = AsyncMock(side_effect=_record)

        dup_calls = [
            {
                "id": "call_dup",
                "function": {
                    "name": "read_text_file",
                    "arguments": '{"path": "/tmp/a"}',
                },
            },
            {
                "id": "call_dup",
                "function": {
                    "name": "read_text_file",
                    "arguments": '{"path": "/tmp/b"}',
                },
            },
        ]

        gate_seen: list[list[Any]] = []

        def _gate(_ctx: Any, prepared: list[Any]) -> tuple[list[Any], list[Any]]:
            gate_seen.append(list(prepared))
            return prepared, []

        with patch(
            "agent.tool_approval.run_approval_checks",
            new_callable=AsyncMock,
            side_effect=_gate,
        ):
            await execute_all_tool_calls(ctx, dup_calls, 0, guard=ToolLoopGuard(ctx))

        # AC-001: nothing ran — not the shared id twice, not with either arg set.
        assert executed == []
        # AC-002: the batch gate ran once but no occurrence reached it.
        assert gate_seen == [[]]

        # AC-003/REQ-003: each declared occurrence is answered with one rejection row.
        dup_rows = [
            m
            for m in ctx.conv.history
            if m.get("role") == "tool" and m.get("tool_call_id") == "call_dup"
        ]
        assert len(dup_rows) == 2
        for row in dup_rows:
            assert (
                "duplicate tool call id 'call_dup' appears 2 times in this round"
                in row["content"]
            )

        saved_rows = ctx.turn.persistence_boundary.save_phase_grouped.call_args.args[0]
        saved_dup = [row for row in saved_rows if row[3] == "call_dup"]
        assert len(saved_dup) == 2
        for row in saved_dup:
            assert (
                "duplicate tool call id 'call_dup' appears 2 times in this round"
                in row[1]
            )


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
    once during preparation — `_execute_with_dag()` itself does no registry
    lookup). Both raise KeyError for any name absent from `is_write_by_name`,
    matching the real registry's unregistered-tool behavior.
    """
    registry = MagicMock()

    def _get(name: str) -> MagicMock:
        if name not in is_write_by_name:
            raise KeyError(name)
        tool = MagicMock()
        tool.is_write = is_write_by_name[name]
        # Zero-argument schema with extra fields allowed so validate_tool_arguments()
        # (also consulted via this same registry during preparation) treats every
        # call as passing validation — this helper exists to test
        # force_serial's side-effect/serialization decision, not
        # argument validation.
        tool.input_schema = {"type": "object", "properties": {}}
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
    # serial_tool_calls=True now feeds force_serial=True into the single
    # _execute_with_dag() path (build_execution_groups()'s force_serial
    # short-circuit) instead of selecting a separate _execute_standard()
    # function — that function no longer exists. The class name/tests are
    # kept in place because the *observable* contract (still serializes, still
    # records a serialization event with a specific reason, still calls
    # diagnostics) is unchanged; only serial_reason and the round_event dict's
    # populated fields change.
    @pytest.mark.asyncio
    async def test_side_effect_tool_records_serialization_event(self) -> None:
        """When a registered write tool triggers forced-serial execution, a
        serialization event is stored via force_serial."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"write_file": True})
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = None

        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        with _approve_all():
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

        assert len(ctx.stats.stat_serialization_events) == 1
        event = ctx.stats.stat_serialization_events[0]
        assert event["trigger_tool"] == "write_file"
        assert event["mode"] == "serial"
        assert event["serial_reason"] == "forced_serial"
        assert "elapsed_ms" in event
        # The DAG path's round_event dict does not populate these two fields —
        # they were specific to the now-deleted _execute_standard()'s own bookkeeping.
        assert "estimated_parallel_ms" not in event
        assert "serial_overhead" not in event

    @pytest.mark.asyncio
    async def test_no_side_effect_no_serialization_event(self) -> None:
        """A single read-only call under force_serial=True still produces
        exactly one single-call phase, with nothing else to conflict with —
        no event fires because no concurrency was actually prevented (and, per
        the force_serial event rule, no write call triggered it either)."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"read_text_file": False})
        ctx.stats.stat_serialization_events = []

        read_call = _tc("read_text_file", '{"path": "/tmp/f"}')
        with _approve_all():
            await execute_all_tool_calls(ctx, [read_call], 0, guard=ToolLoopGuard(ctx))

        assert ctx.stats.stat_serialization_events == []

    @pytest.mark.asyncio
    async def test_unregistered_tool_rejected_during_preparation(self) -> None:
        """A tool absent from the registry is now rejected fail-closed during
        the preparation phase (prepare_tool_calls) — it never reaches
        _execute_with_dag()'s scheduling/serialization logic at all, unlike
        the old lenient fallback this replaces."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({})
        ctx.stats.stat_serialization_events = []

        unknown_call = _tc("unknown_tool", '{"path": "/tmp/f"}')
        with _approve_all():
            await execute_all_tool_calls(
                ctx, [unknown_call], 0, guard=ToolLoopGuard(ctx)
            )

        assert ctx.stats.stat_serialization_events == []
        ctx.services_required.tools.execute.assert_not_called()
        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[-1]["role"] == "tool"
        assert "unregistered tool" in ctx.conv.history[-1]["content"]

    @pytest.mark.asyncio
    async def test_no_registry_rejected_during_preparation(self) -> None:
        """When ctx.services_required.runtime_tools is None, prepare_tool_calls()
        rejects every call fail-closed (a "configuration" failure) before
        approval or execution — it never reaches _execute_with_dag() at
        all."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = None
        ctx.stats.stat_serialization_events = []

        read_call = _tc("read_text_file", '{"path": "/tmp/f"}')
        with _approve_all():
            await execute_all_tool_calls(ctx, [read_call], 0, guard=ToolLoopGuard(ctx))

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
        with _approve_all():
            await execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))

        ctx.diagnostics.save_serialization_event.assert_called_once()
        call_kwargs = ctx.diagnostics.save_serialization_event.call_args[1]
        assert call_kwargs["trigger_tool"] == "write_file"
        assert call_kwargs["mode"] == "serial"
        assert call_kwargs["reason"] == "forced_serial"

    @pytest.mark.asyncio
    async def test_force_serial_overrides_scope_based_grouping_end_to_end(self) -> None:
        """serial_tool_calls=True on a batch of same-scope writes that would
        otherwise concurrently-group under force_serial=False still records a
        single forced_serial event covering every call in the batch — proving
        ctx.cfg.tool.serial_tool_calls actually reaches the planner as
        force_serial, not just a scheduler-level unit-test concern."""
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _write_registry({"write_file": True})
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = None

        write_call_1 = {
            "id": "call_write_1",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        write_call_2 = {
            "id": "call_write_2",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        with _approve_all():
            await execute_all_tool_calls(
                ctx, [write_call_1, write_call_2], 0, guard=ToolLoopGuard(ctx)
            )

        assert len(ctx.stats.stat_serialization_events) == 1
        event = ctx.stats.stat_serialization_events[0]
        assert event["serial_reason"] == "forced_serial"
        assert event["affected_count"] == 2

    @pytest.mark.asyncio
    async def test_results_restored_to_original_order_despite_concurrent_grouping(
        self,
    ) -> None:
        """A batch where an unrelated read and a conflicting same-scope write
        pair land in different ScheduledGroups within the same batch (which
        run concurrently via asyncio.gather, in no particular relative
        order): execute_all_tool_calls() must still collect/save results in
        the original tool_calls order, exercising
        results.sort(key=lambda r: call_order.get(r[0], 0)) under the new
        ExecutionPlan-based iteration."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.audit_logger = None
        ctx.services_required.runtime_tools = _runtime_tools(
            {
                "read_text_file": ToolSpec(
                    call_id="", name="read_text_file", is_write=False
                ),
                "write_file": ToolSpec(
                    call_id="",
                    name="write_file",
                    resource_scopes=("filesystem:/shared",),
                    is_write=True,
                ),
            }
        )
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )
        )

        read_call = _tc("read_text_file")
        write_call_1 = {
            "id": "call_write_1",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        write_call_2 = {
            "id": "call_write_2",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        with _approve_all():
            await execute_all_tool_calls(
                ctx,
                [read_call, write_call_1, write_call_2],
                0,
                guard=ToolLoopGuard(ctx),
            )

        assert [entry["tool_call_id"] for entry in ctx.conv.history] == [
            "call_read_text_file",
            "call_write_1",
            "call_write_2",
        ]


class TestGatewayBypassGapResolution:
    @pytest.mark.asyncio
    async def test_gateway_bypass_gap_documented_as_safe(self) -> None:
        """Verify the gateway-bypass gap is documented as safe per Option B.

        The investigation confirmed:
        1. No production code path ever produces gateway=None after initialization
           (factory.py creates RepositoryGateway unconditionally).
        2. The approval gate independently enforces check_preflight.
        3. Read-only tools already bypass the gateway in the normal path too.

        This test verifies the comment documenting this safety justification exists.
        """
        source = Path("scripts/agent/tool_runner.py").read_text()
        assert "Gateway-bypass safety justification:" in source
        assert "factory.py creates RepositoryGateway unconditionally" in source

    @pytest.mark.asyncio
    async def test_execute_via_gateway_when_present(self) -> None:
        """When gateway is present, execute goes through it."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        executor = AsyncMock()
        executor.execute = AsyncMock(
            return_value=ToolCallResult(
                output="written", is_error=False, request_id="req-1", server_key=""
            )
        )
        gateway = RepositoryGateway(executor=executor, cfg=cfg, audit_logger=None)
        ctx.services_required.gateway = gateway

        pc = _pc(
            "read_text_file",
            {},
            call_id="call_r",
            spec=ToolSpec(call_id="call_r", name="read_text_file", is_write=False),
        )
        result = await execute_one_tool_call(ctx, pc, guard=ToolLoopGuard(ctx))

        executor.execute.assert_awaited_once_with("read_text_file", {})
        assert result[0] == "call_r"

    @pytest.mark.asyncio
    async def test_execute_via_tools_when_gateway_none(self) -> None:
        """When gateway is None, execute falls back to direct tools.execute()."""
        cfg = _cfg()
        ctx = _make_ctx(cfg)
        ctx.services_required.gateway = None
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        pc = _pc("read_text_file", args={}, call_id="call_r")
        result = await execute_one_tool_call(ctx, pc, guard=ToolLoopGuard(ctx))

        ctx.services_required.tools.execute.assert_called_once()
        assert result[0] == "call_r"


# ── Characterization tests for the paths the suite left uncovered ─────────────
#
# These lock behavior the refactor of scripts/agent/tool_runner.py must preserve:
# the fail-closed executor guard, the gateway-bypass preflight denial, the
# transport-failure diagnostics write, the failed-call hash key, the long-result
# display substitution, the DAG bucket debug lines, and the stats snapshot copy.


class TestExecutorUnavailableGuard:
    @pytest.mark.asyncio
    async def test_none_tool_executor_raises_unavailable_error(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.tools = None

        with pytest.raises(
            ToolExecutorUnavailableError,
            match="Tool executor is not available",
        ):
            await execute_one_tool_call(
                ctx,
                _pc("read_text_file", {}, call_id="call_r"),
                guard=ToolLoopGuard(ctx),
            )


class TestGatewayBypassPreflightDenial:
    @pytest.mark.asyncio
    async def test_policy_violation_is_logged_and_reraised(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A non-READ call on the gateway-bypass path never reaches tools.execute()."""
        ctx = _make_ctx()
        ctx.services_required.gateway = None
        pc = _pc("shell_run", {"command": "ls"}, call_id="call_s")

        with (
            caplog.at_level(logging.WARNING, logger="agent.tool_runner"),
            patch(
                "agent.tool_runner.check_preflight",
                side_effect=PolicyViolationError("denied", "denied by policy"),
            ),
        ):
            with pytest.raises(PolicyViolationError, match="denied by policy"):
                await execute_one_tool_call(ctx, pc, guard=ToolLoopGuard(ctx))

        assert any(
            "tool_runner.policy_denied tool='shell_run' reason=denied by policy"
            in r.message
            for r in caplog.records
        )
        ctx.services_required.tools.execute.assert_not_called()


class TestTransportFailureDiagnostics:
    @pytest.mark.asyncio
    async def test_transport_error_is_saved_to_diagnostics(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.gateway = None
        ctx.session.session_id = "sess-1"
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="x" * 900,
                is_error=True,
                request_id="req-1",
                server_key="mcp-git",
                source="mcp",
                error_type="transport",
            )
        )
        pc = _pc("read_text_file", {}, call_id="call_r")

        _, _, _, text, is_error, _ = await execute_one_tool_call(
            ctx, pc, guard=ToolLoopGuard(ctx)
        )

        assert is_error is True
        assert len(text) == 900
        ctx.diagnostics.save_transport_failure.assert_called_once_with(
            session_id="sess-1",
            tool_name="read_text_file",
            server_key="mcp-git",
            error_msg="x" * 500,
            call_id="call_r",
            request_id="req-1",
            task_id="test-task-id",
            turn_id="test-turn-id",
        )

    @pytest.mark.asyncio
    async def test_tool_level_error_does_not_write_transport_diagnostics(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.gateway = None
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="bad args",
                is_error=True,
                request_id="req-1",
                server_key="mcp-git",
                source="mcp",
                error_type="tool",
            )
        )
        pc = _pc("read_text_file", {}, call_id="call_r")

        await execute_one_tool_call(ctx, pc, guard=ToolLoopGuard(ctx))

        ctx.diagnostics.save_transport_failure.assert_not_called()


class TestRunnerDedupStateAudit:
    """mcpai007 REQ-003, AC-1: the runner writes the audit line through the
    bridge, so the dispatcher dedup state reaches the payload only when the result carries one.
    dedup state reaches the payload only when the result carries one."""

    @staticmethod
    async def _payload(result: ToolCallResult) -> dict:
        ctx = _make_ctx()
        ctx.services_required.gateway = None
        ctx.services_required.tools.execute = AsyncMock(return_value=result)
        pc = _pc("read_text_file", {}, call_id="call_d")
        await execute_one_tool_call(ctx, pc, guard=ToolLoopGuard(ctx))
        payload: dict[str, Any] = json.loads(
            ctx.services_required.audit_logger.info.call_args[0][0]
        )
        return payload

    @pytest.mark.asyncio
    async def test_non_empty_dedup_state_reaches_the_audit_payload(self) -> None:
        payload = await self._payload(
            ToolCallResult(
                output="replayed",
                is_error=False,
                request_id="req-2",
                server_key="mcp-git",
                source="mcp",
                dedup_state="replayed",
            )
        )
        assert payload["dedup_state"] == "replayed"
        assert payload["idempotency_key"] == "call_d"

    @pytest.mark.asyncio
    async def test_empty_dedup_state_does_not_add_the_key(self) -> None:
        payload = await self._payload(
            ToolCallResult(
                output="result",
                is_error=False,
                request_id="req-2",
                server_key="mcp-git",
                source="mcp",
            )
        )
        assert "dedup_state" not in payload


class TestFailedResultHashKey:
    @pytest.mark.asyncio
    async def test_failed_result_records_its_hash_key(self) -> None:
        ctx = _make_ctx()
        failed_keys: set[str] = set()
        results = [("call_1", "read_text_file", {"path": "/a"}, "boom", True, "boom")]

        tool_msgs = await _collect_tool_result_msgs(ctx, results, 0, failed_keys)

        assert failed_keys == {tool_hash_key("read_text_file", {"path": "/a"})}
        assert tool_msgs == [("tool", "boom", None, "call_1")]

    @pytest.mark.asyncio
    async def test_absent_failed_keys_container_is_tolerated(self) -> None:
        ctx = _make_ctx()
        results: list[tuple[str, str, dict[str, Any], str, bool, str]] = [
            ("call_1", "read_text_file", {}, "boom", True, "boom")
        ]

        tool_msgs = await _collect_tool_result_msgs(ctx, results, 0, None)

        assert tool_msgs == [("tool", "boom", None, "call_1")]


class TestLongResultDisplay:
    def test_long_result_is_replaced_with_line_and_char_counts(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        text = "\n".join(["a" * 60] * 12)
        assert len(text) > 500

        with (
            caplog.at_level(logging.INFO, logger="agent.tool_runner"),
            patch("agent.tool_runner.emit_tool_result") as mock_emit,
        ):
            _emit_tool_result(text, "read_text_file")

        mock_emit.assert_called_once_with(
            "read_text_file",
            f"{len(text.splitlines())} lines / {len(text)} chars (truncated)",
        )
        assert any(
            "Tool result read_text_file (full): " in r.message for r in caplog.records
        )

    def test_short_result_is_emitted_verbatim(self) -> None:
        with patch("agent.tool_runner.emit_tool_result") as mock_emit:
            _emit_tool_result("short", "read_text_file")

        mock_emit.assert_called_once_with("read_text_file", "short")


class TestDagBucketDebugLines:
    @pytest.mark.asyncio
    async def test_each_call_is_labelled_with_its_scheduling_bucket(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx()
        serial_pc = _pc(
            "shell_run",
            {},
            call_id="call_s",
            spec=ToolSpec(
                call_id="call_s", name="shell_run", requires_serial=True, is_write=False
            ),
        )
        scoped_pc = _pc(
            "write_file",
            {},
            call_id="call_w",
            spec=ToolSpec(
                call_id="call_w",
                name="write_file",
                resource_scopes=("filesystem:/a", "filesystem:/b"),
                is_write=True,
            ),
        )
        unscoped_write_pc = _pc(
            "delete_file",
            {},
            call_id="call_d",
            spec=ToolSpec(call_id="call_d", name="delete_file", is_write=True),
        )
        parallel_pc = _pc(
            "read_text_file",
            {},
            call_id="call_r",
            spec=ToolSpec(call_id="call_r", name="read_text_file", is_write=False),
        )

        with caplog.at_level(logging.DEBUG, logger="agent.tool_run_recorder"):
            await _execute_with_dag(
                ctx,
                [serial_pc, scoped_pc, unscoped_write_pc, parallel_pc],
                guard=ToolLoopGuard(ctx),
                collected={},
            )

        assert {r.message for r in caplog.records if "DAG_BUCKET:" in r.message} == {
            "DAG_BUCKET: shell_run → serial_barrier",
            "DAG_BUCKET: write_file → resource_scope:filesystem:/a,filesystem:/b",
            "DAG_BUCKET: delete_file → resource_scope:global:write",
            "DAG_BUCKET: read_text_file → parallel",
        }

    @pytest.mark.asyncio
    async def test_bucket_labels_are_skipped_when_debug_is_disabled(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx()
        pc = _pc(
            "read_text_file",
            {},
            call_id="call_r",
            spec=ToolSpec(call_id="call_r", name="read_text_file", is_write=False),
        )

        with caplog.at_level(logging.INFO, logger="agent.tool_run_recorder"):
            await _execute_with_dag(ctx, [pc], guard=ToolLoopGuard(ctx), collected={})

        assert not [r for r in caplog.records if "DAG_BUCKET:" in r.message]


class TestSerializationStatsSnapshot:
    def test_stats_are_a_copy_of_the_module_counters(self) -> None:
        before = get_serialization_stats()

        snapshot = get_serialization_stats()
        snapshot["total_events"] = 999

        assert get_serialization_stats() == before


class FakeRecorder:
    """In-memory stand-in for the StateStore facade the adapter wires (row 05).

    Mirrors the agent.context.ToolCallRecorder Protocol signatures exactly, and
    logs every call as a (method, task_id, key, tool, retry_class, state, args_hash)
    tuple plus an event string into a shared list so tests can pin the ordering of
    record vs. executor vs. finalize (design decision in implementation
    procedure 20261101-110802_04).
    """

    def __init__(
        self,
        *,
        events: list[str] | None = None,
        fail_record: bool = False,
        fail_finalize: bool = False,
    ) -> None:
        self.calls: list[tuple[str, str, str, str, str, str, str]] = []
        self.events = events if events is not None else []
        self._fail_record = fail_record
        self._fail_finalize = fail_finalize

    def record_tool_call(
        self,
        task_id: str,
        call_id: str,
        tool: str,
        retry_class: str,
        args_hash: str,
    ) -> None:
        if self._fail_record:
            raise RuntimeError("recorder record down")
        self.events.append("record")
        self.calls.append(
            (
                "record_tool_call",
                task_id,
                call_id,
                tool,
                retry_class,
                "pending",
                args_hash,
            )
        )

    def finalize_tool_call(self, call_id: str, state: str) -> None:
        if self._fail_finalize:
            raise RuntimeError("recorder finalize down")
        self.events.append(f"finalize:{state}")
        self.calls.append(("finalize_tool_call", "", call_id, "", "", state, ""))

    def records(self) -> list[tuple[str, str, str, str, str, str, str]]:
        return [c for c in self.calls if c[0] == "record_tool_call"]

    def finalizes(self) -> list[tuple[str, str, str, str, str, str, str]]:
        return [c for c in self.calls if c[0] == "finalize_tool_call"]


def _state_ctx(recorder: FakeRecorder | None, session_id: str = "sess-42") -> MagicMock:
    """_make_ctx() wired for the tool_call_state producer (REQ-005 consumer side).

    current_task_id is set because _record_pending_state treats a None task
    context as unwired; the row key is each call's logical call id (mcpdl001
    REQ-003), pinned by the _pc fixture's context.
    """
    ctx = _make_ctx()
    ctx.session.session_id = session_id
    ctx.workflow.current_task_id = "task-1"
    ctx.workflow.tool_call_recorder = recorder
    return ctx


class TestToolCallStateProducer:
    """Producer tests for the tool_call_state recording in _recorded_call
    (plans/20261101-105136_toolstate001 plan.md REQ-001..REQ-004, REQ-006..REQ-008).

    Asserts against the FakeRecorder call log, not a real DB: the DB behavior of
    the record/finalize facade is already covered by
    tests/agent/workflow/test_workflow_state_store.py.
    """

    @pytest.mark.asyncio
    async def test_pending_recorded_before_dispatch(self) -> None:
        """REQ-001: the pending row is written before the executor is touched."""
        events: list[str] = []
        recorder = FakeRecorder(events=events)
        ctx = _state_ctx(recorder)

        def _exec(*_a: Any, **_k: Any) -> ToolCallResult:
            events.append("execute")
            return _ok()

        ctx.services_required.tools.execute = AsyncMock(side_effect=_exec)
        pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")
        collected: dict[str, tuple] = {}

        await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert events == [
            "record",
            "finalize:dispatch_starting",
            "finalize:dispatched",
            "execute",
            "finalize:completed",
        ]
        (recorded,) = recorder.records()
        assert recorded[1] == "task-1"
        assert recorded[3] == "read_text_file"
        assert recorded[5] == "pending"
        # mcpdl001 REQ-003: the row key is the logical call id; nothing derived
        assert pc.context is not None
        assert recorded[2] == pc.context.call_id == "c1"

    @pytest.mark.asyncio
    async def test_replay_directive_keys_the_row_with_the_original_id(self) -> None:
        """AC-001 at the recording boundary: a prepared call that matches a turn
        directive records the row under the directive's original id, and the recorded
        hash is the canonical hash the directive matched on."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.runtime_tools = make_producer_registry()
        args = {"path": "/tmp/r", "content": "x"}
        directive = ReplayDirective(
            original_call_id="0199e2f3-0000-7000-8000-000000000006",
            task_id="task-1",
            tool="write_file",
            args_hash=_canonical_args_hash(args),
        )
        ctx.turn.replay_directives = [directive]

        prepared, failures = prepare_tool_calls(
            ctx, [_tc("write_file", '{"path": "/tmp/r", "content": "x"}')]
        )
        assert failures == []
        await _execute_with_dag(ctx, prepared, guard=ToolLoopGuard(ctx), collected={})

        (recorded,) = recorder.records()
        assert recorded[2] == directive.original_call_id
        assert recorded[6] == _canonical_args_hash(args)
        assert directive.consumed

    @pytest.mark.asyncio
    async def test_completed_finalize_after_success(self) -> None:
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")
        collected: dict[str, tuple] = {}

        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert results[0][4] is False
        finals = recorder.finalizes()
        assert [f[5] for f in finals] == [
            "dispatch_starting",
            "dispatched",
            "completed",
        ]
        assert pc.context is not None
        assert all(f[2] == pc.context.call_id for f in finals)

    @pytest.mark.asyncio
    async def test_failed_finalize_after_executor_error(self) -> None:
        """REQ-002: a captured Exception finalizes the row as failed."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=RuntimeError("kaboom")
        )
        pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")
        collected: dict[str, tuple] = {}

        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert results[0][4] is True
        finals = recorder.finalizes()
        assert [f[5] for f in finals] == [
            "dispatch_starting",
            "dispatched",
            "failed",
        ]
        assert pc.context is not None
        assert all(f[2] == pc.context.call_id for f in finals)

    @pytest.mark.asyncio
    async def test_recorder_failure_is_non_fatal(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """mcpdl001 REQ-007 read-only half: for READ calls record and finalize
        failures stay logged best-effort, never fatal, and never leak recorder
        state into the tool result row (the side-effecting fail-closed half is
        TestFailClosedRecording)."""
        with caplog.at_level(logging.WARNING, logger="agent.tool_runner"):
            # Phase A: record raises -> no state_key, tool result untouched.
            recorder_a = FakeRecorder(fail_record=True)
            ctx = _state_ctx(recorder_a)
            collected: dict[str, tuple] = {}
            results = await _execute_with_dag(
                ctx,
                [_pc("read_text_file", {"path": "/tmp/a"}, call_id="ca")],
                guard=ToolLoopGuard(ctx),
                collected=collected,
            )
            assert (
                results[0][4] is False
            )  # success row: recorder failure is not an error row
            assert recorder_a.records() == []
            assert recorder_a.finalizes() == []
            assert any(
                "tool-call state record failed" in r.message for r in caplog.records
            )

            # Phase B: record lands, finalize raises -> pending stays, result normal.
            caplog.clear()
            recorder_b = FakeRecorder(fail_finalize=True)
            ctx = _state_ctx(recorder_b)
            results = await _execute_with_dag(
                ctx,
                [_pc("read_text_file", {"path": "/tmp/b"}, call_id="cb")],
                guard=ToolLoopGuard(ctx),
                collected=collected,
            )
            assert results[0][4] is False
            assert len(recorder_b.records()) == 1
            assert recorder_b.finalizes() == []  # the raising finalize wrote nothing
            assert any(
                "tool-call state finalize failed" in r.message for r in caplog.records
            )

    @pytest.mark.asyncio
    async def test_baseexception_leaves_pending(self) -> None:
        """REQ-004: a propagating CancelledError records pending, walks the row to
        'dispatched', and never writes a terminal state."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.tools.execute = AsyncMock(
            side_effect=asyncio.CancelledError("stop")
        )
        collected: dict[str, tuple] = {}

        with pytest.raises(asyncio.CancelledError):
            await _execute_with_dag(
                ctx,
                [_pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")],
                guard=ToolLoopGuard(ctx),
                collected=collected,
            )

        assert len(recorder.records()) == 1
        assert recorder.records()[0][5] == "pending"
        # No terminal state: the row is stale-classified from 'dispatched'
        # to outcome_unknown (never replayed, mcpdl001 AC-6).
        assert [f[5] for f in recorder.finalizes()] == [
            "dispatch_starting",
            "dispatched",
        ]

    @pytest.mark.asyncio
    async def test_unwired_recorder_is_noop(self) -> None:
        """REQ-008: recorder=None (the AgentContext default every existing test in
        this file relies on) leaves execution unchanged and writes no state."""
        ctx = _state_ctx(None)
        pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")
        collected: dict[str, tuple] = {}

        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert results[0][4] is False
        assert collected[pc.call_id] == results[0]
        # Defensive half: finalize is a no-op even when handed a key with the
        # recorder unwired again between record and finalize.
        _finalize_state(ctx, "some-key", "completed")

    @pytest.mark.asyncio
    async def test_retry_class_from_agent_local_classifier(self) -> None:
        """REQ-004/REQ-007: the recorded retry_class is resolved from the
        registered tool's declared retry_policy (its only authority, mcpdl003
        REQ-005): same_logical_call_only -> retryable,
        safe_read_retry -> non_retryable.
        """
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.runtime_tools = make_producer_registry()

        await _execute_with_dag(
            ctx,
            [_pc("write_file", {"path": "/tmp/w"}, call_id="cw")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        await _execute_with_dag(
            ctx,
            [_pc("read_text_file", {}, call_id="cr")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )

        recorded_write, recorded_read = recorder.records()
        assert recorded_write[4] == "retryable"
        assert recorded_read[4] == "non_retryable"

    @pytest.mark.asyncio
    async def test_retry_class_unknown_tool_is_non_retryable(self) -> None:
        """REQ-007 fail-safe: an unregistered tool defaults to non_retryable,
        never retryable — a future or unclassified tool is unreplayable until
        its declaration registers a retryable policy.
        """
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.runtime_tools = make_producer_registry()

        await _execute_with_dag(
            ctx,
            [_pc("tool_that_does_not_exist", {}, call_id="cu")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )

        (recorded_unknown,) = recorder.records()
        assert recorded_unknown[4] == "non_retryable"

    @pytest.mark.asyncio
    async def test_identical_content_distinct_calls_distinct_keys(self) -> None:
        """mcpdl001 REQ-003 / AC-3 (replaces the wfaudit002 task-scoping test):
        identical call content carried by two logical calls gets two rows — the
        derived-key collision is gone because the key is the per-call uuid7."""
        recorder = FakeRecorder()
        for call_id in ("cA", "cB"):
            ctx = _state_ctx(recorder)
            pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id=call_id)
            await _execute_with_dag(ctx, [pc], guard=ToolLoopGuard(ctx), collected={})
        key_a, key_b = (r[2] for r in recorder.records())
        assert key_a == "cA"
        assert key_b == "cB"
        assert key_a != key_b

    @pytest.mark.asyncio
    async def test_logical_id_retry_invariance(self) -> None:
        """mcpdl001 REQ-001/AC-1: a retried logical call reuses its execution
        context — the same prepared call maps to the same key on every pass."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        pc = _pc("read_text_file", {"path": "/tmp/a"}, call_id="c1")
        await _execute_with_dag(ctx, [pc], guard=ToolLoopGuard(ctx), collected={})
        await _execute_with_dag(ctx, [pc], guard=ToolLoopGuard(ctx), collected={})
        key1, key2 = (r[2] for r in recorder.records())
        assert pc.context is not None
        assert key1 == key2 == pc.context.call_id


class TestFailClosedRecording:
    """mcpdl001 REQ-005/REQ-007 (AC-5/AC-6): a side-effecting call is denied when
    its intent row or the mandatory audit record cannot be written; read-only
    calls keep the best-effort path (pinned by TestToolCallStateProducer)."""

    @pytest.mark.asyncio
    async def test_record_failure_denies_side_effecting_call(self) -> None:
        recorder = FakeRecorder(fail_record=True)
        ctx = _state_ctx(recorder)
        results = await _execute_with_dag(
            ctx,
            [_pc("write_file", {"path": "/tmp/w"}, call_id="cw")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        ctx.services_required.tools.execute.assert_not_called()
        assert recorder.records() == []
        assert recorder.finalizes() == []

    @pytest.mark.asyncio
    async def test_finalize_failure_denies_before_dispatch(self) -> None:
        """The dispatch_starting write gates dispatch: its failure denies the call
        before the executor is reached — no side effect on a dead row."""
        recorder = FakeRecorder(fail_finalize=True)
        ctx = _state_ctx(recorder)
        results = await _execute_with_dag(
            ctx,
            [_pc("write_file", {"path": "/tmp/w"}, call_id="cw")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        ctx.services_required.tools.execute.assert_not_called()
        assert len(recorder.records()) == 1
        assert recorder.finalizes() == []

    @pytest.mark.asyncio
    async def test_unwired_recorder_denies_side_effecting_call(self) -> None:
        ctx = _state_ctx(None)
        results = await _execute_with_dag(
            ctx,
            [_pc("write_file", {"path": "/tmp/w"}, call_id="cw")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_logical_id_denies_side_effecting_call(self) -> None:
        """AC-3: no logical call id, no side effect — even with a grant present."""
        ctx = _state_ctx(FakeRecorder())
        pc = _pc("write_file", {"path": "/tmp/w"}, call_id="cw", context=False)
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert results[0][4] is True
        ctx.services_required.tools.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_mandatory_audit_failure_surfaces_error_row(self) -> None:
        """REQ-007: AuditUnavailableError from the audit call lands as this
        call's tool-error row and finalizes the intent row failed."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.audit_logger = None
        results = await _execute_with_dag(
            ctx,
            [_pc("write_file", {"path": "/tmp/w"}, call_id="cw")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        assert [f[5] for f in recorder.finalizes()][-1] == "failed"

    @pytest.mark.asyncio
    async def test_intent_transitions_in_plan_order(self) -> None:
        """REQ-005: pending -> dispatch_starting -> dispatched ->
        response_received -> completed, driven by the result's dispatch_stage."""
        events: list[str] = []
        recorder = FakeRecorder(events=events)
        ctx = _state_ctx(recorder)
        stamped = ToolCallResult(
            output="result",
            is_error=False,
            request_id="r",
            server_key="",
            dispatch_stage="response",
        )

        def _exec(*_a: Any, **_k: Any) -> ToolCallResult:
            events.append("execute")
            return stamped

        ctx.services_required.tools.execute = AsyncMock(side_effect=_exec)
        await _execute_with_dag(
            ctx,
            [_pc("read_text_file", {}, call_id="c1")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert events == [
            "record",
            "finalize:dispatch_starting",
            "finalize:dispatched",
            "execute",
            "finalize:response_received",
            "finalize:completed",
        ]

    @pytest.mark.asyncio
    async def test_post_send_failure_leaves_row_dispatched(self) -> None:
        """AC-6: a post-send transport failure (dispatch_stage 'sent') leaves the
        row at 'dispatched' — no terminal state here, never replayed."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.diagnostics = None
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="boom",
                is_error=True,
                request_id="",
                server_key="",
                error_type="transport",
                dispatch_stage="sent",
            )
        )
        results = await _execute_with_dag(
            ctx,
            [_pc("read_text_file", {}, call_id="c1")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        assert [f[5] for f in recorder.finalizes()] == [
            "dispatch_starting",
            "dispatched",
        ]

    @pytest.mark.asyncio
    async def test_response_stage_failure_finalizes_failed(self) -> None:
        """A failure whose result carries dispatch_stage 'response' has a known
        outcome: response_received, then failed (not left for stale handling)."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="tool error",
                is_error=True,
                request_id="req-2",
                server_key="",
                error_type="tool",
                dispatch_stage="response",
            )
        )
        results = await _execute_with_dag(
            ctx,
            [_pc("read_text_file", {}, call_id="c1")],
            guard=ToolLoopGuard(ctx),
            collected={},
        )
        assert results[0][4] is True
        assert [f[5] for f in recorder.finalizes()] == [
            "dispatch_starting",
            "dispatched",
            "response_received",
            "failed",
        ]

    @pytest.mark.asyncio
    async def test_error_row_text_does_not_carry_internal_keys(self) -> None:
        """REQ-004: the denial text surfaced to the LLM names the tool, never an
        internal id or derived key."""
        ctx = _state_ctx(None)
        pc = _pc("write_file", {"path": "/tmp/w"}, call_id="cw")
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert results[0][4] is True
        assert "cw" not in results[0][3]
        assert "write_file" in results[0][3]


class TestGrantEnforcementAtExecution:
    """mcpdl001 REQ-006/AC-4: a non-READ call without its ApprovalGrant never
    reaches an executor, gatewayed or bypassed."""

    @pytest.mark.asyncio
    async def test_ungranted_write_denied_at_bypass(self) -> None:
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        pc = _pc("write_file", {"path": "/tmp/w"}, call_id="cw", grant=False)
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert results[0][4] is True
        assert "Grant denied" in results[0][3]
        ctx.services_required.tools.execute.assert_not_called()
        assert [f[5] for f in recorder.finalizes()][-1] == "failed"

    @pytest.mark.asyncio
    async def test_ungranted_write_denied_at_gateway(self) -> None:
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=_ok())
        gateway = RepositoryGateway(executor=executor, cfg=_cfg(), audit_logger=None)
        ctx = _state_ctx(FakeRecorder())
        ctx.services_required.gateway = gateway
        pc = _pc("shell_run", {"command": "ls"}, call_id="cs", grant=False)
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        assert results[0][4] is True
        assert "Grant denied" in results[0][3]
        executor.execute.assert_not_called()


class TestAttemptSideEffectFlag:
    """wfretry001 AC-6: tool_runner sets ctx.turn.attempt_side_effect before a
    non-READ call executes (REQ-006 set-before-execute contract)."""

    @staticmethod
    def _ctx_with_real_turn(
        gateway: Any = None, cfg: AgentConfig | None = None
    ) -> MagicMock:
        """_make_ctx with a real TurnState so the flag is a real dataclass field."""
        ctx = _make_ctx()
        ctx.turn = TurnState(current_turn_id="test-turn-id")
        ctx.services_required.gateway = gateway
        if cfg is not None:
            ctx.cfg = cfg
        return ctx

    @pytest.mark.asyncio
    async def test_non_read_gateway_call_sets_flag_before_execute(self) -> None:
        cfg = _cfg()
        # RepositoryGateway calls executor.execute(): pin the concrete result on
        # the execute attribute (the audit now actually writes the runner's
        # tool_exec event, REQ-007 fail-closed, so mock-chained fields would
        # leak into the JSON payload).
        executor = AsyncMock()
        executor.execute = AsyncMock(
            return_value=ToolCallResult(
                output="ran", is_error=False, request_id="req-1", server_key=""
            )
        )
        gateway = RepositoryGateway(executor=executor, cfg=cfg, audit_logger=None)
        ctx = self._ctx_with_real_turn(gateway=gateway)

        await execute_one_tool_call(
            ctx,
            _pc("shell_run", {"command": "ls"}, call_id="call_s"),
            guard=ToolLoopGuard(ctx),
        )

        executor.execute.assert_awaited_once_with("shell_run", {"command": "ls"})
        assert ctx.turn.attempt_side_effect is True

    @pytest.mark.asyncio
    async def test_read_gateway_call_leaves_flag_false(self) -> None:
        cfg = _cfg()
        executor = AsyncMock()
        executor.execute = AsyncMock(
            return_value=ToolCallResult(
                output="read", is_error=False, request_id="req-1", server_key=""
            )
        )
        gateway = RepositoryGateway(executor=executor, cfg=cfg, audit_logger=None)
        ctx = self._ctx_with_real_turn(gateway=gateway)

        await execute_one_tool_call(
            ctx,
            _pc("read_text_file", {}, call_id="call_r"),
            guard=ToolLoopGuard(ctx),
        )

        executor.execute.assert_awaited_once()
        assert ctx.turn.attempt_side_effect is False

    @pytest.mark.asyncio
    async def test_unclassified_tool_sets_flag(self) -> None:
        """UNKNOWN (registry raises KeyError) counts as a side effect (conservative):
        the flag is set before the call is attempted, and the call is then denied
        by the fail-closed root-jail check (REQ-007: an unregistered tool's declared
        scope cannot be verified, so the gateway-less fallback denies it)."""
        # `mystery_tool` is not a registered tool, so it must be allowed explicitly
        # to reach the registry-lookup path instead of the allowed_tools preflight.
        ctx = self._ctx_with_real_turn(
            cfg=_cfg(allowed_tools=[*ALL_TOOL_NAMES, "mystery_tool"])
        )
        registry = MagicMock()
        registry.get = MagicMock(side_effect=KeyError("mystery_tool"))
        ctx.services_required.runtime_tools = registry

        with pytest.raises(PolicyViolationError) as exc_info:
            await execute_one_tool_call(
                ctx,
                _pc("mystery_tool", {}, call_id="call_m"),
                guard=ToolLoopGuard(ctx),
            )

        assert exc_info.value.audit_decision == "denied_root_jail"
        assert ctx.turn.attempt_side_effect is True
        ctx.services_required.tools.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_gateway_branch_sets_flag_and_runs_preflight(self) -> None:
        """The gateway-bypass path sets the flag and still reaches check_preflight."""
        ctx = self._ctx_with_real_turn()
        with patch("agent.tool_runner.check_preflight") as preflight:
            await execute_one_tool_call(
                ctx,
                _pc("shell_run", {"command": "ls"}, call_id="call_s"),
                guard=ToolLoopGuard(ctx),
            )
        preflight.assert_called_once()
        assert ctx.turn.attempt_side_effect is True
        ctx.services_required.tools.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_flag_set_before_gateway_exception(self) -> None:
        """Set-before-execute: a failing non-READ call still leaves the flag set.

        The gateway call itself raises (the gateway's own error handling is tested
        in test_repository_gateway.py); what matters here is that the flag was set
        before the exception left _execute_prepared_call.
        """
        ctx = self._ctx_with_real_turn()
        gateway = MagicMock()
        gateway.execute = AsyncMock(side_effect=RuntimeError("gateway down"))
        ctx.services_required.gateway = gateway

        with pytest.raises(RuntimeError, match="gateway down"):
            await execute_one_tool_call(
                ctx,
                _pc("shell_run", {"command": "ls"}, call_id="call_s"),
                guard=ToolLoopGuard(ctx),
            )

        assert ctx.turn.attempt_side_effect is True


class TestPreviewCallsDoNotRecordState:
    """mcpai005 REQ-009: a preview-mode call writes no tool_call_state row and
    does not set the per-attempt side-effect flag."""

    @pytest.mark.asyncio
    async def test_preview_call_records_no_row_and_leaves_flag_unset(self) -> None:
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.turn = TurnState(current_turn_id="test-turn-id")
        pc = _pc(
            "shell_run",
            {"command": "echo hi", "dry_run": True},
            call_id="call_pre",
            execution_mode="preview",
        )
        collected: dict[str, tuple] = {}

        await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert collected["call_pre"][4] is False
        assert recorder.records() == []
        assert recorder.finalizes() == []
        assert ctx.turn.attempt_side_effect is False

    @pytest.mark.asyncio
    async def test_applied_call_of_the_same_tool_is_recorded_as_before(self) -> None:
        """The guard is mode-scoped: the same tool with `applied` still records."""
        recorder = FakeRecorder()
        ctx = _state_ctx(recorder)
        ctx.turn = TurnState(current_turn_id="test-turn-id")
        pc = _pc(
            "shell_run",
            {"command": "echo hi"},
            call_id="call_applied",
            execution_mode="applied",
        )
        collected: dict[str, tuple] = {}

        await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected=collected
        )

        assert [r[2] for r in recorder.records()] == ["call_applied"]
        assert ctx.turn.attempt_side_effect is True

    def test_preview_without_a_recorder_does_not_raise(self) -> None:
        """A side-effecting call without a recorder is fail-closed for an applied
        call; a preview writes nothing, so the intent gate does not fire."""
        ctx = _state_ctx(None)
        pc = _pc(
            "shell_run",
            {"command": "echo hi", "dry_run": True},
            call_id="call_pre_no_recorder",
            execution_mode="preview",
        )

        assert _record_pending_state(ctx, pc) is None


class TestToolCallSinkScrub:
    """The "Tool call" log line and the REPL tool-call emit carry scrubbed args
    (maskargs001 REQ-004)."""

    @staticmethod
    async def _run_shell_call(ctx: Any, args: dict[str, Any]) -> None:
        pc = _pc(
            "shell_run",
            args,
            call_id="call_scrub_shell",
            spec=ToolSpec(call_id="call_scrub_shell", name="shell_run", is_write=False),
        )
        results = await _execute_with_dag(
            ctx, [pc], guard=ToolLoopGuard(ctx), collected={}
        )
        await _collect_tool_result_msgs(ctx, results, 0, None)

    @pytest.mark.asyncio
    async def test_log_line_scrubs_free_form_secret(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx()  # masked_fields defaults to []
        with caplog.at_level(logging.INFO, logger="agent.tool_runner"):
            await self._run_shell_call(
                ctx, {"command": "export API_KEY=abcd12345678 && true"}
            )
        tool_call_records = [
            r for r in caplog.records if r.message.startswith("Tool call (")
        ]
        assert tool_call_records
        assert all("abcd12345678" not in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_emit_payload_scrubs_free_form_secret(self) -> None:
        ctx = _make_ctx()
        with patch("agent.tool_runner.emit_tool_call") as mock_emit:
            await self._run_shell_call(
                ctx, {"command": "export API_KEY=abcd12345678 && true"}
            )
        mock_emit.assert_called_once()
        emitted_name, emitted_json = mock_emit.call_args[0]
        assert emitted_name == "shell_run"
        assert "abcd12345678" not in emitted_json

    @pytest.mark.asyncio
    async def test_masked_fields_still_star_in_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx(_cfg(masked_fields=["content"]))
        with caplog.at_level(logging.INFO, logger="agent.tool_runner"):
            await self._run_shell_call(
                ctx, {"content": "abc12345678", "path": "/tmp/f"}
            )
        tool_call_messages = [
            r.message for r in caplog.records if r.message.startswith("Tool call (")
        ]
        assert tool_call_messages
        assert "'content': '***'" in tool_call_messages[0]
        assert "/tmp/f" in tool_call_messages[0]


class TestDiagnosticWritesOffEventLoop:
    """blockio001 REQ-004/REQ-005: diagnostics writes must not block the event loop.

    Each stub blocks on a threading.Event and records the calling thread. While the
    write is blocked the test proves the loop stays responsive (a loop.call_soon
    callback fires) and the post-write steps have not run yet. Before the seq 04/05
    offloads land, the write runs synchronously on the loop thread: the
    not-yet-observed assertion fails deterministically (the loop freezes until the
    stub's own Event.wait(5) timeout releases it) and the recorded caller is the
    main thread. The stub never time.sleeps on the loop (REQ-006(a)).
    """

    @staticmethod
    def _stub_writer() -> tuple[
        threading.Event, threading.Event, list[dict[str, Any]], Any
    ]:
        started = threading.Event()
        release = threading.Event()
        writes: list[dict[str, Any]] = []

        def blocking_save(*args: Any, **kwargs: Any) -> None:
            writes.append(
                {"args": args, "kwargs": kwargs, "thread": threading.current_thread()}
            )
            started.set()
            release.wait(5)

        return started, release, writes, blocking_save

    async def _await_write_started(self, started: threading.Event) -> None:
        """Poll until the stubbed write begins, always yielding to the loop."""
        for _ in range(5000):
            if started.is_set():
                return
            await asyncio.sleep(0.001)
        pytest.fail("stubbed diagnostics write never started")

    async def _assert_loop_responsive(self) -> None:
        """A callback scheduled on the running loop must fire while the write blocks."""
        loop = asyncio.get_running_loop()
        tick = asyncio.Event()
        loop.call_soon(tick.set)
        try:
            await asyncio.wait_for(tick.wait(), timeout=1.0)
        except TimeoutError:  # pragma: no cover - defensive; the stub self-releases
            pytest.fail("event loop was blocked by the diagnostics write")

    @pytest.mark.asyncio
    async def test_transport_failure_write_off_loop(self) -> None:
        ctx = _make_ctx()
        ctx.session.session_id = "sess-1"
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="boom",
                is_error=True,
                request_id="req-1",
                server_key="mcp-git",
                source="mcp",
                error_type="transport",
            )
        )
        started, release, writes, stub = self._stub_writer()
        ctx.diagnostics.save_transport_failure = stub
        order: list[str] = []
        guard = MagicMock()
        guard.observe_availability = MagicMock(
            side_effect=lambda result: order.append("observe")
        )

        task = asyncio.create_task(
            execute_one_tool_call(
                ctx, _pc("read_text_file", {}, call_id="call_r"), guard=guard
            )
        )
        try:
            await self._await_write_started(started)
            await self._assert_loop_responsive()
            # The post-write step has not run while the write is still blocked.
            assert guard.observe_availability.call_count == 0
            release.set()
            await asyncio.wait_for(task, timeout=15)
        finally:
            release.set()
        assert guard.observe_availability.call_count == 1
        assert order == ["observe"]
        assert writes, "save_transport_failure was not called"
        assert writes[0]["kwargs"] == {
            "session_id": "sess-1",
            "tool_name": "read_text_file",
            "server_key": "mcp-git",
            "error_msg": "boom",
            "call_id": "call_r",
            "request_id": "req-1",
            "task_id": "test-task-id",
            "turn_id": "test-turn-id",
        }
        assert writes[0]["thread"] is not threading.main_thread()

    @pytest.mark.asyncio
    async def test_non_transport_results_touch_no_diagnostics(self) -> None:
        for error_type, is_error in (("tool", True), ("", False)):
            ctx = _make_ctx()
            ctx.session.session_id = "sess-1"
            ctx.services_required.tools.execute = AsyncMock(
                return_value=ToolCallResult(
                    output="value",
                    is_error=is_error,
                    request_id="req-1",
                    server_key="mcp-git",
                    source="mcp",
                    error_type=error_type,
                )
            )
            await execute_one_tool_call(
                ctx, _pc("read_text_file", {}, call_id="call_r"), guard=MagicMock()
            )
            ctx.diagnostics.save_transport_failure.assert_not_called()
            ctx.diagnostics.save.assert_not_called()
            ctx.diagnostics.save_serialization_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_serialization_event_write_off_loop(self) -> None:
        cfg = _cfg(serial_tool_calls=True)
        ctx = _make_ctx(cfg)
        ctx.services_required.runtime_tools = _write_registry({"write_file": True})
        ctx.stats.stat_serialization_events = []
        ctx.stats.stat_serialization_total_overhead_ms = 0.0
        ctx.diagnostics = MagicMock()
        started, release, writes, stub = self._stub_writer()
        ctx.diagnostics.save_serialization_event = stub
        write_call = _tc("write_file", '{"path": "/tmp/f"}')
        with (
            patch(
                "agent.tool_approval.run_approval_checks",
                new_callable=AsyncMock,
                side_effect=lambda ctx, prepared: (prepared, []),
            ),
            patch(
                "agent.tool_runner._record_round_exec",
                side_effect=lambda *args, **kwargs: None,
            ) as round_exec,
        ):
            task = asyncio.create_task(
                execute_all_tool_calls(ctx, [write_call], 0, guard=ToolLoopGuard(ctx))
            )
            try:
                await self._await_write_started(started)
                await self._assert_loop_responsive()
                # Stats bookkeeping is loop-side and precedes the blocked write.
                assert len(ctx.stats.stat_serialization_events) == 1
                # The awaited save completes before the round-exec record runs.
                assert round_exec.call_count == 0
                release.set()
                await asyncio.wait_for(task, timeout=15)
            finally:
                release.set()
        assert round_exec.call_count == 1
        assert len(writes) == 1
        assert writes[0]["thread"] is not threading.main_thread()
        kwargs = writes[0]["kwargs"]
        assert kwargs["session_id"] is None
        assert kwargs["trigger_tool"] == "write_file"
        assert kwargs["affected_count"] == 1
        assert kwargs["mode"] == "serial"
        assert kwargs["reason"] == "forced_serial"
        assert isinstance(kwargs["round_id"], str)
        assert isinstance(kwargs["elapsed_ms"], float)


class TestFallbackPreflightDeclaredPathKeys:
    """REQ-003 (pathkeys001): the gateway-less fallback preflight in
    execute_one_tool_call threads the runtime registry, so declared
    resource_scope_keys and list elements are checked."""

    @staticmethod
    def _ctx_with_declared_paths() -> MagicMock:
        cfg = _cfg(allowed_root="/tmp")
        ctx = _make_ctx(cfg)
        registry = MagicMock()

        def _get(name: str) -> MagicMock:
            if name != "write_file":
                raise KeyError(name)
            tool = MagicMock()
            tool.is_write = True
            tool.side_effect_class = "local_write"
            tool.resource_scope_keys = {"paths": "path"}
            return tool

        registry.get = MagicMock(side_effect=_get)
        ctx.services_required.runtime_tools = registry
        return ctx

    @pytest.mark.asyncio
    async def test_list_element_outside_allowed_root_raises(self) -> None:
        """Declared key `paths` list element outside allowed_root raises the denial."""
        ctx = self._ctx_with_declared_paths()
        with pytest.raises(PolicyViolationError) as exc_info:
            await execute_one_tool_call(
                ctx,
                _pc("write_file", {"paths": ["/tmp/a", "/etc/shadow"]}),
                guard=ToolLoopGuard(ctx),
            )
        assert exc_info.value.audit_decision == "denied_root_jail"
        ctx.services_required.tools.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_all_elements_inside_root_executes(self) -> None:
        """All elements inside allowed_root pass the fallback gate and execute."""
        ctx = self._ctx_with_declared_paths()
        _id, _name, _args, full_text, is_error, _llm = await execute_one_tool_call(
            ctx,
            _pc("write_file", {"paths": ["/tmp/a", "/tmp/b"]}),
            guard=ToolLoopGuard(ctx),
        )
        assert is_error is False
        assert full_text == "result"
