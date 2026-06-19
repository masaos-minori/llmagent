"""
tests/test_tool_runner.py
Unit tests for tool_runner.py: DAG execution, standard execution, and entry point.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config import AgentConfig, build_agent_config
from agent.tool_runner import (
    _execute_with_dag,
    execute_all_tool_calls,
)
from shared.tool_executor import ToolCallResult


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
        "auto_inject_notes": False,
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
    ctx.services.audit_logger = None
    ctx.services.tools = MagicMock()
    ctx.services.tools.execute = AsyncMock(
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
        ctx.services.tools.execute = AsyncMock(
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

        ctx.services.tools.execute = AsyncMock(side_effect=_record_exec)
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

        ctx.services.tools.execute = AsyncMock(side_effect=_record_exec)
        await _execute_with_dag(ctx, [_tc("shell_run"), _tc("read_text_file")], 0)
        assert call_order[0] == "shell_run"

    @pytest.mark.asyncio
    async def test_empty_approved_calls_returns_empty(self) -> None:
        ctx = _make_ctx()
        results = await _execute_with_dag(ctx, [], 0)
        assert results == []


class TestExecuteAllToolCalls:
    @pytest.mark.asyncio
    async def test_approved_calls_executed_and_collected(self) -> None:
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services.audit_logger = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )
        ctx.tool_result_store.store = MagicMock(return_value=1)

        with patch("agent.tool_runner.run_approval_checks") as mock_approval:
            mock_approval.return_value = (
                [_tc("read_text_file", '{"path": "/tmp/f"}')],
                [],
            )
            await execute_all_tool_calls(ctx, [_tc("read_text_file")], 0)

        ctx.services.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f"}
        )
        ctx.tool_result_store.store.assert_called_once()
        ctx.session.save_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_denied_calls_appended_to_history(self) -> None:
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services.audit_logger = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )

        denied_id = "call_denied_1"
        approved = [_tc("read_text_file", '{"path": "/tmp/f"}')]
        with patch("agent.tool_runner.run_approval_checks") as mock_approval:
            mock_approval.return_value = (approved, [denied_id])
            await execute_all_tool_calls(
                ctx,
                [
                    {
                        "id": denied_id,
                        "function": {"name": "write_file", "arguments": "{}"},
                    }
                ],
                0,
            )

        denied_msgs = [
            entry for entry in ctx.conv.history if "denied" in entry.get("content", "")
        ]
        assert len(denied_msgs) == 1

    @pytest.mark.asyncio
    async def test_no_approved_no_denied_does_nothing(self) -> None:
        cfg = _cfg(use_tool_dag=True)
        ctx = _make_ctx(cfg)
        ctx.services.audit_logger = MagicMock()

        with patch("agent.tool_runner.run_approval_checks") as mock_approval:
            mock_approval.return_value = ([], [])
            await execute_all_tool_calls(ctx, [], 0)

        ctx.services.tools.execute.assert_not_called()
        ctx.session.save_many.assert_called_once_with([])
