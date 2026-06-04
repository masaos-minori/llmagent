"""
tests/test_agent_cmd_config.py
Unit tests for _ConfigMixin: _cmd_stats, _print_config_values (SSE section),
and ConfigReloadService.apply_config_dict (SSE hot-reload).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.commands.cmd_config import _ConfigMixin
from agent.services.config_reload import ConfigReloadService

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_ConfigMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.stats.stat_turns = 5
    ctx.stats.stat_tool_calls = 10
    ctx.stats.stat_tool_errors = 2
    ctx.stats.stat_semantic_cache_hits = 1
    ctx.stats.stat_latency = {}
    ctx.stats.stat_input_tokens = 1000
    ctx.stats.stat_output_tokens = 500
    ctx.conv.debug_mode = False
    ctx.conv.plan_mode = False
    ctx.conv.history = []
    ctx.session.session_id = "test-session"
    ctx.services.tools = None
    ctx.services.rag = None
    ctx.services.hist_mgr = None
    ctx.services.llm = None
    return ctx


def _make_llm_svc() -> MagicMock:
    llm = MagicMock()
    llm.stat_retries = 1
    llm.stat_reconnects = 2
    llm.stat_heartbeat_timeouts = 3
    llm.stat_partial_completions = 4
    llm.stat_parse_errors = 5
    return llm


# ── _cmd_stats ────────────────────────────────────────────────────────────────


class TestCmdStats:
    def test_cmd_stats_with_llm_service_prints_sse_stats(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services.llm = _make_llm_svc()
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "LLM reconnects" in out
        assert "HB timeouts" in out
        assert "Partial compl" in out
        assert "Parse errors" in out

    def test_cmd_stats_with_llm_service_shows_correct_values(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services.llm = _make_llm_svc()
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "2" in out  # reconnects
        assert "3" in out  # heartbeat_timeouts
        assert "4" in out  # partial_completions
        assert "5" in out  # parse_errors

    def test_cmd_stats_without_llm_service_shows_zeros(self, capsys: Any) -> None:
        ctx = _make_ctx()
        # services.llm is None
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        # All LLM stats should default to 0
        assert "LLM reconnects: 0" in out
        assert "HB timeouts   : 0" in out
        assert "Partial compl : 0" in out
        assert "Parse errors  : 0" in out


# ── _print_config_values ──────────────────────────────────────────────────────


class TestPrintConfigValues:
    def _make_cfg_ctx(self) -> MagicMock:
        ctx = _make_ctx()
        ctx.cfg.llm.llm_url = "http://llm"
        ctx.cfg.rag.web_search_url = "http://ws"
        ctx.cfg.mcp.github_url = "http://gh"
        ctx.cfg.tool.max_tool_turns = 5
        ctx.cfg.llm.http_timeout = 30.0
        ctx.cfg.rag.web_search_max_results = 10
        ctx.cfg.llm.context_char_limit = 8000
        ctx.cfg.llm.context_compress_turns = 4
        ctx.cfg.tool.tool_cache_ttl = 300.0
        ctx.cfg.llm.llm_max_retries = 3
        ctx.cfg.llm.llm_retry_base_delay = 1.0
        ctx.cfg.llm.llm_temperature = 0.2
        ctx.cfg.llm.llm_max_tokens = 1024
        ctx.cfg.llm.sse_heartbeat_timeout = 30.0
        ctx.cfg.llm.sse_malformed_retry = 2
        ctx.cfg.llm.sse_reconnect_max = 1
        ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = True
        ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = False
        ctx.cfg.tool.serial_tool_calls = False
        ctx.cfg.tool.use_tool_summarize = False
        ctx.cfg.tool.tool_summarize_threshold = 3000
        ctx.cfg.tool.auto_inject_notes = True
        ctx.cfg.rag.use_semantic_cache = False
        ctx.cfg.rag.semantic_cache_threshold = 0.92
        ctx.cfg.rag.semantic_cache_max_size = 100
        ctx.cfg.tool.tool_definitions_strict = False
        ctx.cfg.mcp.mcp_watchdog_interval = 0.0
        ctx.cfg.mcp.mcp_watchdog_max_restarts = 3
        ctx.cfg.approval.approval_risk_rules = {}
        ctx.cfg.approval.approval_protected_paths = []
        ctx.cfg.approval.approval_high_risk_branches = []
        ctx.cfg.approval.approval_dry_run_tools = ["write_file"]
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.tool.plan_blocked_tools = []
        return ctx

    def test_sse_settings_section_is_printed(self, capsys: Any) -> None:
        ctx = self._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "SSE stream settings" in out
        assert "sse_heartbeat_timeout" in out
        assert "sse_malformed_retry" in out
        assert "sse_reconnect_max" in out
        assert "llm_stream_retry_on_heartbeat_timeout" in out
        assert "llm_stream_retry_on_malformed_chunk" in out

    def test_dry_run_tools_printed(self, capsys: Any) -> None:
        ctx = self._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "dry_run_tools" in out
        assert "write_file" in out

    def test_empty_dry_run_tools_shows_none(self, capsys: Any) -> None:
        ctx = self._make_cfg_ctx()
        ctx.cfg.approval.approval_dry_run_tools = []
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "dry_run_tools" in out
        assert "(none)" in out


# ── _apply_config_params ──────────────────────────────────────────────────────

# _build_mcp_servers fallback raises ValueError on empty http URL; use stdio to bypass.
_DUMMY_MCP = {
    "mcp_servers": {
        "dummy": {
            "transport": "stdio",
            "cmd": ["echo"],
            "url": "",
            "openrc_service": "",
        }
    }
}


class TestApplyConfigDict:
    def test_sse_heartbeat_timeout_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {**_DUMMY_MCP, "sse_heartbeat_timeout": 60.0}
        )
        assert ctx.cfg.llm.sse_heartbeat_timeout == 60.0

    def test_sse_malformed_retry_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {**_DUMMY_MCP, "sse_malformed_retry": 5}
        )
        assert ctx.cfg.llm.sse_malformed_retry == 5

    def test_sse_reconnect_max_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {**_DUMMY_MCP, "sse_reconnect_max": 3}
        )
        assert ctx.cfg.llm.sse_reconnect_max == 3

    def test_llm_stream_retry_flags_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {
                **_DUMMY_MCP,
                "llm_stream_retry_on_heartbeat_timeout": False,
                "llm_stream_retry_on_malformed_chunk": True,
            }
        )
        assert ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout is False
        assert ctx.cfg.llm.llm_stream_retry_on_malformed_chunk is True

    def test_sse_params_propagated_to_llm_service(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        llm = MagicMock()
        ctx.services.llm = llm
        ctx.cfg.llm.sse_heartbeat_timeout = 45.0
        ctx.cfg.llm.sse_malformed_retry = 3
        ctx.cfg.llm.sse_reconnect_max = 2
        ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = False
        ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = True
        ConfigReloadService(ctx).apply_config_dict(
            {
                **_DUMMY_MCP,
                "sse_heartbeat_timeout": 45.0,
                "sse_malformed_retry": 3,
                "sse_reconnect_max": 2,
                "llm_stream_retry_on_heartbeat_timeout": False,
                "llm_stream_retry_on_malformed_chunk": True,
            }
        )
        # ConfigReloadService now uses apply_config() instead of direct attr writes
        llm.apply_config.assert_called_once()
        call_kwargs = llm.apply_config.call_args.kwargs
        assert call_kwargs.get("sse_heartbeat_timeout") == 45.0
        assert call_kwargs.get("sse_malformed_retry") == 3
        assert call_kwargs.get("sse_reconnect_max") == 2
        assert call_kwargs.get("stream_retry_on_heartbeat_timeout") is False
        assert call_kwargs.get("stream_retry_on_malformed_chunk") is True

    def test_approval_resource_keys_applied(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {**_DUMMY_MCP, "approval_resource_keys": {"github_push": "high"}}
        )
        assert ctx.cfg.approval.approval_resource_keys == {"github_push": "high"}

    def test_approval_dry_run_tools_applied(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {**_DUMMY_MCP, "approval_dry_run_tools": ["write_file", "delete_file"]}
        )
        assert ctx.cfg.approval.approval_dry_run_tools == ["write_file", "delete_file"]

    def test_hist_mgr_token_limit_synced(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        hist_mgr = MagicMock()
        ctx.services.hist_mgr = hist_mgr
        # Pre-set cfg values; _apply_config_params reads them to sync to hist_mgr
        ctx.cfg.llm.context_token_limit = 4000
        ctx.cfg.llm.tokenize_url = "http://llm/tok"
        ConfigReloadService(ctx).apply_config_dict({**_DUMMY_MCP})
        # ConfigReloadService now uses apply_config() instead of direct attr writes
        hist_mgr.apply_config.assert_called_once()
        call_kwargs = hist_mgr.apply_config.call_args.kwargs
        assert call_kwargs.get("token_limit") == 4000
        assert call_kwargs.get("tokenize_url") == "http://llm/tok"
