"""
tests/test_agent_cmd_config.py
Unit tests for _ConfigMixin: _cmd_stats, _print_config_values (SSE section),
and ConfigReloadService.apply_config_dict (SSE hot-reload).
"""

from __future__ import annotations

import os
import re
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_config import _ConfigMixin
from agent.commands.command_defs_list import _COMMANDS
from agent.prompt_source import load_prompt_source
from agent.services.config_pending_state import PendingConfigState
from agent.services.config_reload import ConfigReloadOutcome, ConfigReloadService
from agent.services.config_reload_transaction import ReloadStage
from agent.services.exceptions import (
    ConfigReloadCommitError,
    ConfigReloadRollbackError,
)

from tests.agent._config_test_defaults import reload_fixture_config, reload_fixture_ctx

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_ConfigMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx


def _make_ctx(**overrides: Any) -> MagicMock:
    """Reload-test ctx whose live config is what the startup entry point builds.

    The reload candidate is built through `build_agent_config` (REQ-002), so the
    config a reload test starts from must itself be a startup-built ``AgentConfig``.
    """
    ctx = MagicMock()
    ctx.cfg = reload_fixture_config(**overrides)
    ctx.stats.stat_turns = 5
    ctx.stats.stat_tool_calls = 10
    ctx.stats.stat_tool_errors = 2
    ctx.stats.stat_latency = {}
    ctx.stats.stat_input_tokens = 1000
    ctx.stats.stat_output_tokens = 500
    ctx.stats.stat_memory_consistency_failures = 0
    ctx.conv.debug_mode = False
    ctx.conv.plan_mode = False
    ctx.conv.history = []
    ctx.session.session_id = "test-session"
    ctx.services_required.tools = None
    ctx.services_required.rag = None
    ctx.services_required.hist_mgr = None
    ctx.services_required.llm = None
    # Also set services_required for _collect_stats compatibility
    ctx.services_required.tools = None
    ctx.services_required.rag = None
    ctx.services_required.hist_mgr = None
    ctx.services_required.llm = None
    return ctx


def _make_pending_ctx(**overrides: Any) -> Any:
    """Reload ctx that carries the container's real `PendingConfigState`.

    `factory.py` puts one `PendingConfigState` on `AppServices` and the display
    commands read it through the ctx, so a pending-display case must carry a real
    state rather than a MagicMock (REQ-009).  No live service is wired and the
    prompt already matches the source, so the reload commits nothing and the only
    thing the command has to report is what stayed pending.
    """
    ctx = reload_fixture_ctx(**overrides)
    ctx.conv.system_prompt_content = load_prompt_source().content(
        ctx.conv.system_prompt_name
    )
    for name in ("runtime_tools", "tools", "rag", "hist_mgr"):
        setattr(ctx.services_required, name, None)
    ctx.services = MagicMock()
    ctx.services.pending_config = PendingConfigState()
    return ctx


def _make_llm_svc() -> MagicMock:
    llm = MagicMock()
    llm.stat_reconnects = 2
    llm.stat_heartbeat_timeouts = 3
    llm.stat_partial_completions = 4
    llm.stat_parse_errors = 5
    return llm


# ── _cmd_stats ────────────────────────────────────────────────────────────────


class TestCmdStats:
    def test_cmd_stats_with_llm_service_prints_sse_stats(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services_required.llm = _make_llm_svc()
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "LLM reconnects" in out
        assert "HB timeouts" in out
        assert "Partial compl" in out
        assert "Parse errors" in out

    def test_cmd_stats_with_llm_service_shows_correct_values(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services_required.llm = _make_llm_svc()
        ctx.stats.stat_partial_completions = 4
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "2" in out  # reconnects
        assert "3" in out  # heartbeat_timeouts
        assert "4" in out  # partial_completions
        assert "5" in out  # parse_errors

    def test_cmd_stats_without_llm_service_shows_zeros(self, capsys: Any) -> None:
        ctx = _make_ctx()
        # services_required.llm is None
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        # All LLM stats should default to 0
        assert "LLM reconnects: 0" in out
        assert "HB timeouts   : 0" in out
        assert "Partial compl : 0" in out
        assert "Parse errors  : 0" in out

    def test_partial_completion_hint_shown_when_count_positive(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        llm = _make_llm_svc()
        ctx.stats.stat_partial_completions = 2
        ctx.services_required.llm = llm
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "session_diagnostics" in out

    def test_partial_completion_no_hint_when_zero(self, capsys: Any) -> None:
        ctx = _make_ctx()
        llm = _make_llm_svc()
        llm.stat_partial_completions = 0
        ctx.services_required.llm = llm
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "session_diagnostics" not in out
        assert "Partial compl : 0" in out

    def test_cmd_stats_shows_fallback_truncation(self, capsys: Any) -> None:
        ctx = _make_ctx()
        llm = _make_llm_svc()
        hist_mgr = MagicMock()
        hist_mgr.stat_compress_count = 3
        hist_mgr.stat_fallback_truncate_count = 2
        ctx.services_required.llm = llm
        ctx.services_required.hist_mgr = hist_mgr
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "Compress      : 3" in out
        assert "Fallback trunc: 2" in out

    def test_cmd_stats_fallback_truncation_zero_when_no_hist_mgr(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        # hist_mgr is None
        cmd = _FakeCmd(ctx)
        cmd._cmd_stats()
        out = capsys.readouterr().out
        assert "Fallback trunc: 0" in out

    def test_stats_hint_references_a_registered_command(self, capsys: Any) -> None:
        """The /stats RAG-consistency hint must point at a live top-level command.

        Regression guard: this must fail if the hint text drifts to reference a
        command name that has since been removed from _COMMANDS (as happened when
        the hint pointed at a since-removed command).
        """
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with patch("db.config.build_db_config"):  # succeeds -> rag_db_configured=True
            cmd._cmd_stats()
        out = capsys.readouterr().out

        hint_lines = [line for line in out.splitlines() if "Hint" in line]
        assert hint_lines, (
            "expected a Hint line to be printed when rag_db_configured=True"
        )

        match = re.search(r"(/\w[\w-]*)", hint_lines[0])
        assert match, f"no command token found in hint line: {hint_lines[0]!r}"
        command_token = match.group(1)

        registered_names = {c.name for c in _COMMANDS}
        assert command_token in registered_names, (
            f"/stats hint references {command_token!r}, which is not a registered command"
            f" in _COMMANDS: {sorted(registered_names)}"
        )


# ── _print_config_values ──────────────────────────────────────────────────────


class TestPrintConfigValues:
    def _make_cfg_ctx(self) -> MagicMock:
        ctx = _make_ctx()
        ctx.cfg.llm.llm_url = "http://llm"
        ctx.cfg.tool.max_tool_turns = 5
        ctx.cfg.llm.http_timeout = 30.0
        ctx.cfg.llm.context_char_limit = 8000
        ctx.cfg.llm.context_compress_turns = 4
        ctx.cfg.tool.tool_cache_ttl = 300.0
        ctx.cfg.llm.llm_retry_base_delay = 1.0
        ctx.cfg.llm.llm_temperature = 0.2
        ctx.cfg.llm.llm_max_tokens = 1024
        ctx.cfg.llm.sse_heartbeat_timeout = 30.0
        ctx.cfg.llm.sse_malformed_retry = 2
        ctx.cfg.llm.sse_reconnect_max = 1
        ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = True
        ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = False
        ctx.cfg.tool.serial_tool_calls = False
        ctx.cfg.approval.approval_risk_rules = {}
        ctx.cfg.approval.approval_protected_paths = []
        ctx.cfg.approval.approval_high_risk_branches = []
        ctx.cfg.approval.approval_dry_run_tools = ["write_file"]
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.tool.plan_blocked_tools = []
        ctx.cfg.memory.use_memory_layer = False
        ctx.cfg.memory.memory_embed_enabled = False
        ctx.cfg.memory.memory_jsonl_dir = "/opt/llm/memory"
        ctx.cfg.memory.memory_max_inject_semantic = 5
        ctx.cfg.memory.memory_max_inject_episodic = 3
        ctx.cfg.memory.memory_min_importance = 0.3
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

    def test_dry_run_tools_not_printed(self, capsys: Any) -> None:
        """Agentcfg003 REQ-005: dry-run capability is declared per tool; the
        config display no longer prints a dry-run tool list."""
        ctx = self._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "dry_run_tools" not in out

    def test_risk_rules_not_printed(self, capsys: Any) -> None:
        """REQ-005: the removed approval_risk_rules line is gone from the display."""
        ctx = self._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "risk_rules" not in out

    def test_llm_url_prints_without_credentials(self, capsys: Any) -> None:
        """Display boundary: a credential-bearing URL renders without userinfo, query, or fragment."""
        ctx = self._make_cfg_ctx()
        ctx.cfg.llm.llm_url = (
            "https://admin:s3cr3tpw@llm.example.com:8443/v1?key=abc#frag"
        )
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "https://llm.example.com:8443/v1" in out
        assert "s3cr3tpw" not in out
        assert "key=abc" not in out
        # The config model itself is not modified.
        assert (
            ctx.cfg.llm.llm_url
            == "https://admin:s3cr3tpw@llm.example.com:8443/v1?key=abc#frag"
        )

    def test_protected_paths_print_as_logical_identifiers(self, capsys: Any) -> None:
        """Display boundary: configured absolute paths render as logical identifiers, not as paths."""
        ctx = self._make_cfg_ctx()
        root = os.path.join(tempfile.gettempdir(), "mcp_server_logs")
        ctx.cfg.approval.approval_protected_paths = [
            os.path.join(root, "srv", "srv.stderr.log"),
            "/etc/hosts",
        ]
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "srv/srv.stderr.log, hosts" in out
        assert root not in out
        assert "/etc/hosts" not in out


# ── _apply_config_params ──────────────────────────────────────────────────────


class TestApplyConfigDict:
    def test_sse_heartbeat_timeout_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict({"sse_heartbeat_timeout": 60.0})
        assert ctx.cfg.llm.sse_heartbeat_timeout == 60.0

    def test_sse_malformed_retry_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict({"sse_malformed_retry": 5})
        assert ctx.cfg.llm.sse_malformed_retry == 5

    def test_sse_reconnect_max_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict({"sse_reconnect_max": 3})
        assert ctx.cfg.llm.sse_reconnect_max == 3

    def test_llm_stream_retry_flags_reloaded(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        ConfigReloadService(ctx).apply_config_dict(
            {
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
        ctx.services_required.llm = llm
        ctx.cfg.llm.sse_heartbeat_timeout = 45.0
        ctx.cfg.llm.sse_malformed_retry = 3
        ctx.cfg.llm.sse_reconnect_max = 2
        ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = False
        ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = True
        ConfigReloadService(ctx).apply_config_dict(
            {
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

    @pytest.mark.parametrize(
        "removed_key",
        ["approval_resource_keys", "approval_dry_run_tools"],
    )
    def test_removed_approval_maps_rejected_on_reload(self, removed_key: str) -> None:
        """Agentcfg003 REQ-011: a reload payload naming a removed map is rejected by
        the candidate build; the live config never gains the field."""
        from agent.services.exceptions import ConfigReloadValidationError

        ctx = _make_ctx()
        ctx.conv.history = []
        with pytest.raises(ConfigReloadValidationError) as excinfo:
            ConfigReloadService(ctx).apply_config_dict(
                {removed_key: {"github_push": "high"}}
            )
        assert removed_key in str(excinfo.value)
        assert not hasattr(ctx.cfg.approval, removed_key)

    def test_startup_only_history_limits_are_not_synced(self) -> None:
        """context_token_limit and tokenize_url are startup-only: reload never syncs them to hist_mgr."""
        ctx = _make_ctx()
        ctx.conv.history = []
        hist_mgr = MagicMock()
        ctx.services_required.hist_mgr = hist_mgr
        ctx.cfg.llm.context_token_limit = 4000
        ctx.cfg.llm.tokenize_url = "http://llm/tok"
        outcome = ConfigReloadService(ctx).apply_config_dict({})
        hist_mgr.apply_config.assert_not_called()
        assert "hist_mgr" not in outcome.applied


# ── _print_rag_config error path ──────────────────────────────────────────────


class TestPrintRagConfig:
    def test_db_config_error_shows_message(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        with patch("db.config.build_db_config", side_effect=ValueError("bad config")):
            cmd._print_rag_config()
        out = capsys.readouterr().out
        assert "config error" in out
        assert "bad config" in out

    def test_db_paths_print_as_logical_identifiers(self, capsys: Any) -> None:
        """Display boundary: configured DB paths render as logical identifiers, not absolute paths."""
        from unittest.mock import patch

        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        mapping = {
            "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so",
            "rag_db_path": "/opt/llm/rag.sqlite",
            "session_db_path": "/opt/llm/session.sqlite",
        }
        with patch("shared.config_loader.ConfigLoader.load", return_value=mapping):
            cmd._print_rag_config()
        out = capsys.readouterr().out
        assert "rag.sqlite" in out
        assert "session.sqlite" in out
        assert "/opt/llm" not in out


# ── _cmd_reload error paths ───────────────────────────────────────────────────


class TestCmdReload:
    def test_reload_oserror_shows_message(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        with patch(
            "shared.config_loader.ConfigLoader.load_all",
            side_effect=OSError("file not found"),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Reload failed" in out
        assert "I/O error" in out

    def test_reload_valueerror_shows_message(self, capsys: Any) -> None:
        from unittest.mock import patch

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        with patch(
            "shared.config_loader.ConfigLoader.load_all",
            side_effect=ValueError("parse error"),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Reload failed" in out
        assert "parse error" in out

    def test_reload_wrong_typed_value_prints_field_error_without_raw_value(
        self, capsys: Any
    ) -> None:
        """AC-5/REQ-011: a wrong-typed value prints a field-level error and does not raise."""
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        with patch(
            "shared.config_loader.ConfigLoader.load_all",
            return_value={"context_char_limit": "12000"},
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Reload failed" in out
        assert "context_char_limit" in out
        assert "must be" in out
        assert "12000" not in out  # the rule names the type, never the value

    def test_reload_shows_source_files(self, capsys: Any) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(applied=["llm"], needs_restart=[])
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Config reloaded — all changes applied" in out

    def test_reload_shows_applied_items(self, capsys: Any) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(applied=["llm", "hist_mgr"], needs_restart=[])
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Applied (runtime): [2 items]" in out
        assert "  [OK] - llm" in out
        assert "  [OK] - hist_mgr" in out

    def test_reload_shows_needs_restart(self, capsys: Any) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(applied=[], needs_restart=["server1"])
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "WARNING: Some settings require restart to take effect." in out
        assert "Restart required: [1 items]" in out
        assert "  [RESTART] - server1" in out

    def test_reload_mcp_auth_token_change_prints_restart_not_defer(
        self, capsys: Any
    ) -> None:
        from unittest.mock import patch

        ctx = _make_ctx(
            mcp_servers={
                "svc": {
                    "transport": "http",
                    "url": "http://localhost:8080",
                    "cmd": ["python", "s.py"],
                    "auth_token": "old",
                }
            }
        )
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)

        new_cfg = {
            "mcp_servers": {
                "svc": {
                    "transport": "http",
                    "url": "http://localhost:8080",
                    "cmd": ["python", "s.py"],
                    "auth_token": "new",
                }
            }
        }
        with patch("shared.config_loader.ConfigLoader.load_all", return_value=new_cfg):
            cmd._cmd_reload()

        out = capsys.readouterr().out
        assert "[RESTART] - mcp_servers/svc.auth_token" in out
        assert "[DEFER]" not in out

    def test_reload_shows_skipped_items(self, capsys: Any) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(
            applied=["llm"], needs_restart=[], skipped=["debug"]
        )
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Skipped: [1 items]" in out
        assert "  [SKIP] - debug" in out

    def test_reload_shows_startup_only_items(self, capsys: Any) -> None:
        """The startup-only change is reported as pending, not as an ignored list.

        Row 19 replaced the outcome's own `Startup-only (ignored)` list with the
        container's pending list, so the same field is reported once and the report
        says where it stands (REQ-009, AC-5).
        """
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_pending_ctx()
        cmd = _FakeCmd(ctx)
        ctx.services.pending_config.set_startup_only(["use_memory_layer"])
        outcome = ConfigReloadOutcome(
            applied=[], needs_restart=[], startup_only=["use_memory_layer"]
        )
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert (
            "Config reloaded — startup-only settings cannot apply without restart"
            in out
        )
        assert "Pending restart (not applied to the running process):" in out
        assert "  [STARTUP-ONLY] - use_memory_layer" in out
        assert "Startup-only (ignored)" not in out

    def test_reload_no_changes_shows_message(self, capsys: Any) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(applied=[], needs_restart=[])
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "No changes detected." in out

    def test_reload_shows_always_live_items(self, capsys: Any) -> None:
        """Characterization test for the always_live item-listing branch."""
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(
            applied=[], needs_restart=[], always_live=["diagnostics.retention_days"]
        )
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "LIVE (always effective): [1 items]" in out
        assert "  [LIVE] - diagnostics.retention_days" in out

    def test_reload_no_changes_with_empty_always_live_shows_message(
        self, capsys: Any
    ) -> None:
        """Confirm 'No changes detected.' when always_live=[] and nothing else changed."""
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome

        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        outcome = ConfigReloadOutcome(applied=[], needs_restart=[], always_live=[])
        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
            ),
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "No changes detected." in out


# ── _cmd_reload stage reporting (row 38, R5 run) ──────────────────────────────


class TestCmdReloadStageReporting:
    """REQ-005, AC-5: the printed stage matches the state the reload left behind."""

    @staticmethod
    def _run(
        cmd: Any, *, outcome: Any = None, error: BaseException | None = None
    ) -> None:
        from unittest.mock import patch

        with (
            patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
            patch(
                "agent.services.config_reload.ConfigReloadService.apply_config_dict",
                return_value=outcome,
                side_effect=error,
            ),
        ):
            cmd._cmd_reload()

    def test_prepared_stage_is_printed(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        self._run(cmd, outcome=ConfigReloadOutcome(applied=[], needs_restart=[]))
        out = capsys.readouterr().out
        assert "Reload stage: prepared" in out

    def test_committed_stage_is_printed_with_the_applied_list(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        self._run(
            cmd,
            outcome=ConfigReloadOutcome(
                applied=["llm"],
                needs_restart=[],
                stage=ReloadStage.COMMITTED,
            ),
        )
        out = capsys.readouterr().out
        assert "Reload stage: committed" in out
        assert "Applied (runtime): [1 items]" in out

    def test_rolled_back_stage_is_printed_on_a_commit_failure(
        self, capsys: Any
    ) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        self._run(
            cmd,
            error=ConfigReloadCommitError(
                "config reload commit failed at llm (RuntimeError); "
                "applied steps were rolled back",
                field_path="llm_max_tokens",
                stage=ReloadStage.ROLLED_BACK.value,
            ),
        )
        out = capsys.readouterr().out
        assert "Reload stage: rolled_back" in out
        assert "Reload failed: llm_max_tokens" in out
        assert "Applied (runtime)" not in out

    def test_degraded_stage_is_printed_on_a_rollback_failure(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        self._run(
            cmd,
            error=ConfigReloadRollbackError(
                "config reload rollback failed for llm; restart required",
                service="llm",
                stage=ReloadStage.DEGRADED.value,
            ),
        )
        out = capsys.readouterr().out
        assert "Reload stage: degraded" in out
        assert "restart required" in out
        assert "Applied (runtime)" not in out

    def test_a_failed_reload_does_not_raise(self, capsys: Any) -> None:
        """AC-5: the command reports the failure; it never propagates it."""
        ctx = _make_ctx()
        ctx.conv.history = []
        cmd = _FakeCmd(ctx)
        self._run(
            cmd,
            error=ConfigReloadRollbackError(
                "config reload refused: a previous reload left llm inconsistent; "
                "restart required",
                service="llm",
                stage=ReloadStage.DEGRADED.value,
            ),
        )
        assert "Reload stage: degraded" in capsys.readouterr().out


class TestCmdReloadPendingList:
    """REQ-009, AC-5: a startup-only change is printed as pending, never as applied."""

    def test_a_startup_only_change_prints_the_pending_list(self, capsys: Any) -> None:
        ctx = _make_pending_ctx()
        cmd = _FakeCmd(ctx)
        with patch(
            "shared.config_loader.ConfigLoader.load_all",
            return_value={"context_char_limit": 1234},
        ):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "Reload stage: prepared" in out
        assert "Pending restart (not applied to the running process):" in out
        assert "  [STARTUP-ONLY] - context_char_limit" in out
        assert "Applied (runtime)" not in out
        assert "1234" not in out  # the pending list names fields, not values

    def test_nothing_pending_prints_no_pending_section(self, capsys: Any) -> None:
        ctx = _make_pending_ctx()
        cmd = _FakeCmd(ctx)
        with patch("shared.config_loader.ConfigLoader.load_all", return_value={}):
            cmd._cmd_reload()
        out = capsys.readouterr().out
        assert "No changes detected." in out
        assert "Pending restart" not in out

    def test_the_pending_list_survives_to_the_next_reload_command(
        self, capsys: Any
    ) -> None:
        """The second `/reload` still shows what the first one left pending (REQ-009)."""
        ctx = _make_pending_ctx()
        payload = {"context_char_limit": 1234}
        with patch(
            "shared.config_loader.ConfigLoader.load_all",
            return_value=payload,
        ):
            _FakeCmd(ctx)._cmd_reload()
        capsys.readouterr()

        with patch("shared.config_loader.ConfigLoader.load_all", return_value=payload):
            _FakeCmd(ctx)._cmd_reload()
        out = capsys.readouterr().out
        assert "  [STARTUP-ONLY] - context_char_limit" in out


# ── /config show pending-restart section (row 20) ─────────────────────────────


class TestConfigShowPendingSection:
    """REQ-009, AC-5: `/config show` separates pending values from live values."""

    def test_a_pending_field_is_shown_as_pending(self, capsys: Any) -> None:
        ctx = _make_pending_ctx()
        ctx.services.pending_config.set_startup_only(["context_char_limit"])
        cmd = _FakeCmd(ctx)
        cmd._print_pending_config(ctx)
        out = capsys.readouterr().out
        assert "Pending restart (not applied to the running process): [1 items]" in out
        assert "  [STARTUP-ONLY] - context_char_limit" in out

    def test_no_pending_section_when_nothing_is_pending(self, capsys: Any) -> None:
        """The live-value display is unchanged when no restart is pending."""
        ctx = _make_pending_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        cmd._print_pending_config(ctx)
        out = capsys.readouterr().out
        assert "Pending restart" not in out
        assert "context_char_limit" in out  # the live value is still shown

    def test_the_pending_section_is_printed_after_the_live_values(
        self, capsys: Any
    ) -> None:
        ctx = _make_pending_ctx()
        ctx.services.pending_config.set_startup_only(["use_memory_layer"])
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        cmd._print_pending_config(ctx)
        out = capsys.readouterr().out
        assert out.index("use_memory_layer") < out.index("Pending restart")

    def test_cmd_config_prints_the_pending_section_last(self, capsys: Any) -> None:
        """`/config` shows the pending field after the live values, not among them."""
        ctx = _make_pending_ctx()
        ctx.services.pending_config.set_startup_only(["context_char_limit"])
        cmd = _FakeCmd(ctx)
        cmd._cmd_config()
        out = capsys.readouterr().out
        assert "  [STARTUP-ONLY] - context_char_limit" in out
        assert out.rstrip().endswith("  [STARTUP-ONLY] - context_char_limit")


# ── _print_memory_settings ──────────────────────────────────────────────────────


class TestPrintMemorySettings:
    def test_memory_settings_shown_in_config(self, capsys: Any) -> None:
        """_print_config_values() must include a memory layer section."""
        ctx = TestPrintConfigValues()._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "use_memory_layer" in out
        assert "memory_embed_enabled" in out

    def test_memory_disabled_shows_correct_value(self, capsys: Any) -> None:
        """When use_memory_layer=False, output says False."""
        ctx = TestPrintConfigValues()._make_cfg_ctx()
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "use_memory_layer    : False" in out

    def test_memory_enabled_shows_correct_value(self, capsys: Any) -> None:
        """When use_memory_layer=True, output says True."""
        ctx = TestPrintConfigValues()._make_cfg_ctx()
        ctx.cfg.memory.use_memory_layer = True
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "use_memory_layer    : True" in out

    def test_memory_jsonl_dir_prints_as_logical_identifier(self, capsys: Any) -> None:
        """Display boundary: the configured directory renders as a logical identifier."""
        ctx = TestPrintConfigValues()._make_cfg_ctx()
        ctx.cfg.memory.memory_jsonl_dir = "/opt/llm/memory"
        cmd = _FakeCmd(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "memory_jsonl_dir    : memory" in out
        assert "/opt/llm/memory" not in out
        # The empty value still renders the placeholder.
        ctx.cfg.memory.memory_jsonl_dir = ""
        cmd._print_config_values()
        assert "(not set)" in capsys.readouterr().out
