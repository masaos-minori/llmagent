"""
tests/test_schema_validation_coverage.py

Optional test to verify schema validation is invoked on all tool execution
paths where schemas are available.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.context import ConversationState
from agent.tool_runner import execute_one_tool_call


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
        "embed_url": "http://127.0.0.1:9999",
        "mcp_servers": {
            "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"},
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
    ctx.services_required.tools = AsyncMock()
    ctx.conv = MagicMock(spec=ConversationState)
    ctx.conv.history = []
    ctx.conv.system_prompt_content = ""
    return ctx


@pytest.mark.asyncio
async def test_validate_tool_arguments_called_on_all_paths() -> None:
    """Verify _validate_tool_args is called when runtime_tools provides a schema."""
    mock_schema = {"type": "object", "properties": {"x": {"type": "string"}}}
    mock_runtime_tools = MagicMock()
    mock_runtime_tools.get_schema.return_value = mock_schema

    ctx = _make_ctx()
    ctx.services_required.runtime_tools = mock_runtime_tools

    tc = {
        "id": "1",
        "function": {
            "name": "test_tool",
            "arguments": '{"x": "hello"}',
        },
    }

    with patch("agent.tool_runner._validate_tool_args", return_value=None):
        result = await execute_one_tool_call(ctx, tc, 0)
        assert isinstance(result, tuple)
        assert len(result) == 6
        assert result[0] == "1"
        assert result[1] == "test_tool"
        assert result[2] == {"x": "hello"}


@pytest.mark.asyncio
async def test_validate_tool_arguments_not_called_when_no_schema() -> None:
    """Verify _validate_tool_args returns None (no error) when no schema exists."""
    mock_runtime_tools = MagicMock()
    mock_runtime_tools.get_schema.return_value = None

    ctx = _make_ctx()
    ctx.services_required.runtime_tools = mock_runtime_tools

    tc = {
        "id": "1",
        "function": {
            "name": "test_tool",
            "arguments": '{"x": "hello"}',
        },
    }

    with patch("agent.tool_runner._validate_tool_args", return_value=None):
        result = await execute_one_tool_call(ctx, tc, 0)
        assert isinstance(result, tuple)
        assert len(result) == 6
        assert result[0] == "1"
        assert result[1] == "test_tool"
        assert result[2] == {"x": "hello"}
