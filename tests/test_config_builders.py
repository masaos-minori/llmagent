"""tests/test_config_builders.py
Unit tests for agent/config_builders.py:
_build_llm_config, _build_rag_config, _build_approval_config, _build_memory_config,
_build_tool_config, build_agent_config, and load_config error handling.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from agent.config_builders import (
    ConfigLoadError,
    _build_approval_config,
    _build_llm_config,
    _build_memory_config,
    _build_rag_config,
    _build_tool_config,
    build_agent_config,
    load_config,
)
from agent.config_dataclasses import AgentConfig

# Minimal config satisfying _build_mcp_servers (needs at least one HTTP server with url).
_MIN_CFG: dict = {
    "mcp_servers": {
        "test-server": {"transport": "http", "url": "http://127.0.0.1:9999"}
    }
}

_PROD_CFG: dict = {
    **_MIN_CFG,
    "security_profile": "production",
    "plugin_strict": True,
    "tool_definitions_strict": True,
    "routing_drift_strict": True,
}


# ── _build_llm_config ─────────────────────────────────────────────────────────


class TestBuildLLMConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_llm_config({})
        assert cfg.llm_url == ""
        assert cfg.http_timeout == 30.0
        assert cfg.llm_max_retries == 3
        assert cfg.llm_temperature == 0.2
        assert cfg.llm_max_tokens == 1024

    def test_overrides_are_applied(self) -> None:
        cfg = _build_llm_config({"llm_url": "http://llm.local", "llm_max_tokens": 512})
        assert cfg.llm_url == "http://llm.local"
        assert cfg.llm_max_tokens == 512

    def test_type_coercion_for_numeric_fields(self) -> None:
        cfg = _build_llm_config({"llm_max_retries": "5", "llm_temperature": "0.5"})
        assert cfg.llm_max_retries == 5
        assert cfg.llm_temperature == 0.5


# ── _build_rag_config ─────────────────────────────────────────────────────────


class TestBuildRAGConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_rag_config({})
        assert cfg.web_search_max_results == 5
        assert cfg.embed_url == ""
        assert cfg.use_semantic_cache is False
        assert cfg.semantic_cache_threshold == 0.92
        assert cfg.semantic_cache_max_size == 100
        assert cfg.use_refiner is False
        assert cfg.refiner_max_tokens == 512
        assert cfg.refiner_timeout == 30.0
        assert cfg.refiner_max_chars_per_chunk == 300

    def test_overrides_are_applied(self) -> None:
        cfg = _build_rag_config(
            {"web_search_max_results": 10, "use_semantic_cache": True}
        )
        assert cfg.web_search_max_results == 10
        assert cfg.use_semantic_cache is True


# ── _build_tool_config ────────────────────────────────────────────────────────


class TestBuildToolConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_tool_config({}, system_prompt_tool="")
        assert cfg.max_tool_turns == 5
        assert cfg.serial_tool_calls is False
        assert cfg.plugin_strict is False

    def test_system_prompt_tool_is_set(self) -> None:
        cfg = _build_tool_config({}, system_prompt_tool="You are an assistant.")
        assert cfg.system_prompt_tool == "You are an assistant."


# ── _build_memory_config ──────────────────────────────────────────────────────


class TestBuildMemoryConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_memory_config({})
        assert cfg.use_memory_layer is False
        assert cfg.memory_fts_limit == 50
        assert cfg.memory_rrf_k == 60
        assert cfg.memory_retention_days == 90


# ── _build_approval_config ────────────────────────────────────────────────────


class TestBuildApprovalConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_approval_config({})
        assert "write_file" in cfg.approval_risk_rules
        assert cfg.approval_risk_rules["delete_file"] == "high"
        assert cfg.gitops_force_push_blocked is True

    def test_invalid_risk_level_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="invalid levels"):
            _build_approval_config({"approval_risk_rules": {"write_file": "extreme"}})


# ── build_agent_config ────────────────────────────────────────────────────────


class TestBuildAgentConfig:
    def test_returns_agent_config_instance(self) -> None:
        cfg = build_agent_config(_MIN_CFG)
        assert isinstance(cfg, AgentConfig)

    def test_llm_defaults_reflected(self) -> None:
        cfg = build_agent_config(_MIN_CFG)
        assert cfg.llm.llm_url == ""
        assert cfg.rag.web_search_max_results == 5

    def test_security_profile_production_sets_watchdog(self) -> None:
        cfg = build_agent_config(_PROD_CFG)
        assert cfg.mcp.mcp_watchdog_interval == 30.0

    def test_security_profile_local_disables_watchdog(self) -> None:
        cfg = build_agent_config({**_MIN_CFG, "security_profile": "local"})
        assert cfg.mcp.mcp_watchdog_interval == 0.0

    def test_mcp_watchdog_interval_override_respected(self) -> None:
        cfg = build_agent_config(
            {
                **_PROD_CFG,
                "mcp_watchdog_interval": 60.0,
            }
        )
        assert cfg.mcp.mcp_watchdog_interval == 60.0

    def test_none_cfg_override_calls_load_config(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.return_value = _MIN_CFG
            cfg = build_agent_config(None)
        assert isinstance(cfg, AgentConfig)

    def test_config_with_workflow_mode_key_raises(self) -> None:
        with pytest.raises(ConfigLoadError, match="workflow_mode"):
            build_agent_config({**_MIN_CFG, "workflow_mode": "auto"})

    def test_config_with_workflow_require_approval_key_raises(self) -> None:
        with pytest.raises(ConfigLoadError, match="workflow_require_approval"):
            build_agent_config({**_MIN_CFG, "workflow_require_approval": False})

    def test_config_with_github_server_url_key_raises(self) -> None:
        with pytest.raises(ConfigLoadError, match="github_server_url"):
            build_agent_config({**_MIN_CFG, "github_server_url": "http://old"})

    def test_config_with_github_server_url_key_message_mentions_replacement(
        self,
    ) -> None:
        with pytest.raises(ConfigLoadError, match="mcp_servers.github"):
            build_agent_config({**_MIN_CFG, "github_server_url": "http://old"})


# ── load_config ───────────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_raises_on_os_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = OSError("no config file")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()

    def test_raises_on_value_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = ValueError("bad TOML")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()

    def test_raises_on_type_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = TypeError("wrong type")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()
