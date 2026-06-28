"""tests/test_plugin_ci_strict.py
Tests for CI-aware plugin_strict default in config_builders.py.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

from agent.config import build_agent_config


def _cfg(**overrides: Any) -> dict[str, Any]:
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
    return defaults


class TestPluginStrictCIDefault:
    def test_ci_env_set_enables_strict_when_not_in_config(self) -> None:
        with patch.dict(os.environ, {"CI": "true"}):
            result = build_agent_config(_cfg())
        assert result.tool.plugin_strict is True

    def test_no_ci_env_defaults_to_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        with patch.dict(os.environ, env, clear=True):
            result = build_agent_config(_cfg())
        assert result.tool.plugin_strict is False

    def test_explicit_false_overrides_ci_env(self) -> None:
        with patch.dict(os.environ, {"CI": "true"}):
            result = build_agent_config(_cfg(plugin_strict=False))
        assert result.tool.plugin_strict is False

    def test_explicit_true_overrides_no_ci(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        with patch.dict(os.environ, env, clear=True):
            result = build_agent_config(_cfg(plugin_strict=True))
        assert result.tool.plugin_strict is True
