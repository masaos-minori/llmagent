"""tests/test_repository_gateway.py
Tests for RepositoryGateway: policy enforcement, approval bypass for reads,
audit emission, and denied results.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.repository_gateway import RepositoryGateway
from agent.tool_enums import OperationType
from agent.tool_exceptions import PolicyViolationError
from agent.tool_loop_guard import ToolLoopGuard
from agent.tool_preparation import PreparedToolCall
from agent.tool_runner import execute_one_tool_call
from shared.tool_spec import ToolSpec

from tests.agent._config_test_defaults import (
    ALL_APPROVAL_RISK_RULES,
    ALL_TOOL_NAMES,
    ALL_TOOL_SAFETY_TIERS,
    STRICT_PRODUCTION_OVERRIDES,
)


def _make_gateway(cfg=None, executor=None, audit_logger=None):
    if cfg is None:
        cfg = MagicMock()
    if executor is None:
        executor = AsyncMock()
    return RepositoryGateway(executor=executor, cfg=cfg, audit_logger=audit_logger)


def _make_ctx():
    workflow = SimpleNamespace(workflow_id=None)
    return SimpleNamespace(
        cfg=MagicMock(),
        services=SimpleNamespace(gateway=None, tools=AsyncMock()),
        services_required=SimpleNamespace(
            gateway=None, tools=AsyncMock(), runtime_tools=None
        ),
        turn=SimpleNamespace(current_turn_id="turn-1"),
        workflow=workflow,
    )


class TestReadBypass:
    @pytest.mark.asyncio
    async def test_read_tool_bypasses_policy(self) -> None:
        """Read-only tools skip policy check and approval."""
        executor = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=OperationType.READ,
        ):
            await gw.execute(ctx, "list_directory", {"path": "/tmp"})

        executor.execute.assert_awaited_once_with("list_directory", {"path": "/tmp"})


class TestWritePolicy:
    @pytest.mark.asyncio
    async def test_write_tool_blocked_by_policy(self) -> None:
        """Write tool blocked by check_preflight raises PolicyViolationError → denied result."""
        executor = AsyncMock()
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch(
                "agent.repository_gateway.check_preflight",
                side_effect=PolicyViolationError("deny", "blocked"),
            ),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/etc/passwd", "content": "x"}
            )

        assert result.is_error is True
        assert "Policy blocked" in result.output
        executor.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_write_tool_approved_and_executed(self) -> None:
        """Happy path: write tool passes policy and approval, result returned."""
        expected = MagicMock(is_error=False, output="written")
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=expected)
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
            )

        assert result is expected
        executor.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_gate_write_runs_policy_and_executes(self) -> None:
        """Write tool passes the policy gate and is executed."""
        expected = MagicMock(is_error=False, output="written")
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=expected)
        gw = _make_gateway(executor=executor)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
        ):
            result = await gw.execute(
                ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
            )

        assert result is expected
        executor.execute.assert_awaited_once_with(
            "write_file", {"path": "/tmp/x.txt", "content": "ok"}
        )


class TestAudit:
    @pytest.mark.asyncio
    async def test_audit_emitted_on_write(self) -> None:
        """Audit logger is called after a successful write."""
        audit = MagicMock()
        executor = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(executor=executor, audit_logger=audit)
        ctx = _make_ctx()

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch("agent.repository_gateway.check_preflight"),
        ):
            await gw.execute(ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"})

        audit.info.assert_called_once()
        call_args = audit.info.call_args[0]
        assert "write_file" in str(call_args)


def _make_denial_ctx(executor: AsyncMock) -> SimpleNamespace:
    """Extend `_make_ctx` per test (never mutate the shared helper) with the
    fields the tool_runner -> audit_tool_exec wiring needs (Scope)."""
    ctx = _make_ctx()
    ctx.workflow.workflow_id = "wf-test"
    ctx.workflow.current_task_id = "task-1"
    ctx.session = SimpleNamespace(session_id=None)
    ctx.services_required.audit_logger = MagicMock()
    ctx.services_required.gateway = _make_gateway(executor=executor)
    ctx.cfg.tool.masked_fields = []
    ctx.cfg.tool.tool_result_max_llm_chars = 4000
    ctx.cfg.approval.approval_resource_keys = {}
    return ctx


class TestDenialAuditEndToEnd:
    """Denied gateway writes reach the runner's audit call site (toolaudit001 REQ-003/REQ-004)."""

    @pytest.mark.asyncio
    async def test_denied_write_produces_one_tool_exec_record(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        executor = AsyncMock()
        ctx = _make_denial_ctx(executor)
        guard = ToolLoopGuard(ctx)

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch(
                "agent.repository_gateway.check_preflight",
                side_effect=PolicyViolationError("deny", "blocked"),
            ),
            caplog.at_level(logging.WARNING, logger="agent.repository_gateway"),
        ):
            _tc_id, _name, _args, _text, is_error, _llm = await execute_one_tool_call(
                ctx,
                PreparedToolCall(
                    call_id="call_write_file",
                    name="write_file",
                    args={"path": "/etc/passwd", "content": "x"},
                    spec=ToolSpec(call_id="call_write_file", name="write_file"),
                    original_call={},
                ),
                guard,
            )

        assert is_error is True
        assert executor.execute.await_count == 0
        ctx.services_required.audit_logger.info.assert_called_once()
        record = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert record["event"] == "tool_exec"
        assert record["error_type"] == "denied"
        assert record["is_error"] is True
        warnings = [
            r
            for r in caplog.records
            if r.name == "agent.repository_gateway"
            and r.levelno >= logging.WARNING
            and "gateway.policy_denied" in r.getMessage()
        ]
        assert len(warnings) == 1

    @pytest.mark.asyncio
    async def test_denied_without_workflow_id_skips_quietly(self) -> None:
        """No workflow_id: the denial skips the audit without raising (REQ-004)."""
        executor = AsyncMock()
        ctx = _make_denial_ctx(executor)
        ctx.workflow.workflow_id = None
        guard = ToolLoopGuard(ctx)

        with (
            patch(
                "agent.repository_gateway.classify_operation_type",
                return_value=OperationType.WRITE,
            ),
            patch(
                "agent.repository_gateway.check_preflight",
                side_effect=PolicyViolationError("deny", "blocked"),
            ),
        ):
            _tc_id, _name, _args, _text, is_error, _llm = await execute_one_tool_call(
                ctx,
                PreparedToolCall(
                    call_id="call_write_file",
                    name="write_file",
                    args={"path": "/etc/passwd", "content": "x"},
                    spec=ToolSpec(call_id="call_write_file", name="write_file"),
                    original_call={},
                ),
                guard,
            )

        assert is_error is True
        ctx.services_required.audit_logger.info.assert_not_called()


def _stub_registry(**tools: tuple[str, ...]) -> MagicMock:
    """Minimal registry stub: get(name) -> object with resource_scope_keys."""

    def _get(name: str) -> MagicMock:
        if name not in tools:
            raise KeyError(name)
        registered = MagicMock()
        registered.resource_scope_keys = tools[name]
        return registered

    stub = MagicMock()
    stub.get.side_effect = _get
    return stub


def _make_real_cfg(**overrides: object):
    """Build a minimal real AgentConfig (check_preflight needs real fields)."""
    return build_agent_config(
        {
            **STRICT_PRODUCTION_OVERRIDES,
            "allowed_tools": ALL_TOOL_NAMES,
            "context_char_limit": 8000,
            "context_compress_turns": 4,
            "llm_retry_base_delay": 1.0,
            "masked_fields": [],
            "plan_blocked_tools": [],
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "tool_dedup_max_repeats": 3,
            "tool_cycle_detect_window": 2,
            "tool_error_max_consecutive": 3,
            "embed_url": "http://127.0.0.1:9999",
            "mcp_servers": {
                "_dummy": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            "tool_safety_tiers": ALL_TOOL_SAFETY_TIERS,
            "approval_risk_rules": ALL_APPROVAL_RISK_RULES,
            **overrides,
        }
    )


class TestWriteGateDeclaredPathKeys:
    """REQ-003 (pathkeys001): _gate_write threads the runtime registry into
    check_preflight so declared resource_scope_keys and list elements are checked
    at the gateway write gate."""

    @pytest.mark.asyncio
    async def test_list_element_outside_allowed_root_denied(self) -> None:
        """Declared key `paths` list element outside allowed_root denies the write."""
        cfg = _make_real_cfg(
            allowed_tools=["write_file"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=MagicMock(is_error=False))
        gw = _make_gateway(cfg=cfg, executor=executor)
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = _stub_registry(write_file=("paths",))
        with patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=OperationType.WRITE,
        ):
            result = await gw.execute(
                ctx, "write_file", {"paths": ["/tmp/a", "/etc/shadow"]}
            )
        assert result.is_error is True
        assert "Policy blocked" in result.output
        executor.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_all_elements_inside_root_executes(self) -> None:
        """All elements inside allowed_root pass the gate and execute."""
        cfg = _make_real_cfg(
            allowed_tools=["write_file"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        expected = MagicMock(is_error=False, output="written")
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value=expected)
        gw = _make_gateway(cfg=cfg, executor=executor)
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = _stub_registry(write_file=("paths",))
        with patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=OperationType.WRITE,
        ):
            result = await gw.execute(
                ctx, "write_file", {"paths": ["/tmp/a", "/tmp/b"]}
            )
        assert result is expected
        executor.execute.assert_awaited_once_with(
            "write_file", {"paths": ["/tmp/a", "/tmp/b"]}
        )
