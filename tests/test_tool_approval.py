"""
tests/test_tool_approval.py
Unit tests for the risk-based tool approval model.

Covers _classify_risk(), _build_preview(), and check_approval().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent_config import AgentConfig, build_agent_config
from agent_repl_tool_exec import (
    _audit_approval,
    _build_preview,
    _classify_risk,
    check_approval,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
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
            "semantic_cache_max_size": 100,
            "tool_definitions_strict": False,
            "mcp_watchdog_interval": 0.0,
            "mcp_watchdog_max_restarts": 3,
            "masked_fields": [],
            "plan_blocked_tools": [],
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "use_refiner": False,
            "refiner_max_tokens": 512,
            "refiner_timeout": 30.0,
            "refiner_max_chars_per_chunk": 300,
            "tool_dedup_max_repeats": 3,
            "tool_cycle_detect_window": 2,
            "tool_error_max_consecutive": 3,
            "web_search_url": "http://127.0.0.1:8004",
            "github_server_url": "http://127.0.0.1:8006",
            **overrides,
        }
    )
    return base


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg = cfg or _make_cfg()
    ctx.current_turn_id = "test-turn-id"
    ctx.services.audit_logger = None
    return ctx


# ── _classify_risk() ──────────────────────────────────────────────────────────


class TestClassifyRisk:
    def test_write_file_returns_medium(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "write_file", {"path": "/home/user/file.txt"})
            == "medium"
        )

    def test_delete_file_returns_high(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "delete_file", {"path": "/home/user/file.txt"})
            == "high"
        )

    def test_unknown_tool_returns_none(self) -> None:
        cfg = _make_cfg()
        assert _classify_risk(cfg, "list_directory", {}) == "none"

    def test_write_to_protected_path_escalates_to_high(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "write_file", {"path": "/opt/llm/config.json"})
            == "high"
        )

    def test_medium_tool_outside_protected_path_stays_medium(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "write_file", {"path": "/home/user/file.txt"})
            == "medium"
        )

    def test_shell_run_returns_high_by_default(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "shell_run", {"command": "rm -rf /tmp/test"}) == "high"
        )

    def test_shell_run_safe_prefix_returns_none(self) -> None:
        cfg = _make_cfg()
        assert _classify_risk(cfg, "shell_run", {"command": "ls -la /tmp"}) == "none"

    def test_shell_run_git_log_returns_none(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "shell_run", {"command": "git log --oneline -5"})
            == "none"
        )

    def test_github_push_to_main_escalates_to_high(self) -> None:
        cfg = _make_cfg()
        # github_create_pull_request is medium by default, but base=main → high
        assert (
            _classify_risk(
                cfg,
                "github_create_pull_request",
                {"owner": "foo", "repo": "bar", "base": "main"},
            )
            == "high"
        )

    def test_github_create_pr_to_feature_remains_medium(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "github_create_pull_request",
                {"owner": "foo", "repo": "bar", "base": "feature/x"},
            )
            == "medium"
        )

    def test_github_push_files_always_high(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "github_push_files",
                {"owner": "foo", "repo": "bar", "branch": "feature/x"},
            )
            == "high"
        )

    def test_delete_file_on_etc_still_high(self) -> None:
        # delete_file is already 'high'; protected path shouldn't lower it
        cfg = _make_cfg()
        assert _classify_risk(cfg, "delete_file", {"path": "/etc/hosts"}) == "high"

    def test_custom_risk_rules_override_default(self) -> None:
        cfg = _make_cfg(approval_risk_rules={"my_tool": "medium"})
        assert _classify_risk(cfg, "my_tool", {}) == "medium"

    def test_empty_risk_rules_all_none(self) -> None:
        cfg = _make_cfg(approval_risk_rules={})
        assert _classify_risk(cfg, "delete_file", {}) == "none"

    def test_file_path_arg_key_also_escalates(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "edit_file", {"file_path": "/opt/llm/x.py"}) == "high"
        )


# ── _build_preview() ──────────────────────────────────────────────────────────


class TestBuildPreview:
    def test_write_file_shows_path_and_content(self) -> None:
        preview = _build_preview(
            "write_file", {"path": "/tmp/a.txt", "content": "hello"}
        )
        assert "/tmp/a.txt" in preview
        assert "hello" in preview

    def test_delete_file_shows_path(self) -> None:
        preview = _build_preview("delete_file", {"path": "/tmp/a.txt"})
        assert "/tmp/a.txt" in preview

    def test_delete_directory_shows_directory_path(self) -> None:
        preview = _build_preview("delete_directory", {"directory_path": "/tmp/dir"})
        assert "/tmp/dir" in preview

    def test_move_file_shows_source_and_destination(self) -> None:
        preview = _build_preview("move_file", {"source": "/a", "destination": "/b"})
        assert "/a" in preview
        assert "/b" in preview
        assert "→" in preview

    def test_shell_run_shows_command(self) -> None:
        preview = _build_preview("shell_run", {"command": "ls -la"})
        assert "ls -la" in preview

    def test_github_shows_owner_repo(self) -> None:
        preview = _build_preview(
            "github_create_issue",
            {"owner": "myorg", "repo": "myrepo", "title": "Bug"},
        )
        assert "myorg/myrepo" in preview

    def test_unknown_tool_shows_json(self) -> None:
        preview = _build_preview("read_text_file", {"path": "/tmp/x"})
        assert "path" in preview

    def test_content_truncated_at_200_chars(self) -> None:
        long_content = "x" * 500
        preview = _build_preview(
            "write_file", {"path": "/tmp/f", "content": long_content}
        )
        # Content preview should not include all 500 chars
        assert long_content not in preview


# ── check_approval() ─────────────────────────────────────────────────────────


class TestCheckApproval:
    @pytest.mark.asyncio
    async def test_none_risk_auto_approved_without_input(self) -> None:
        ctx = _make_ctx()
        with patch("builtins.input") as mock_input:
            result = await check_approval(ctx, "list_directory", {"path": "/tmp"})
        assert result is True
        mock_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_medium_risk_y_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_medium_risk_n_denied(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="n")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_high_risk_yes_approved(self) -> None:
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is True

    @pytest.mark.asyncio
    async def test_high_risk_y_is_insufficient(self) -> None:
        # 'y' alone must NOT approve a high-risk operation
        ctx = _make_ctx()
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "delete_file", {"path": "/tmp/f.txt"})
        assert result is False

    @pytest.mark.asyncio
    async def test_audit_log_written_on_medium_approval(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        audit.info.assert_called_once()
        logged = audit.info.call_args[0][0]
        assert "tool_approval" in logged
        assert "approved" in logged

    @pytest.mark.asyncio
    async def test_audit_log_written_on_denial(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("asyncio.to_thread", new=AsyncMock(return_value="n")):
            await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        logged = audit.info.call_args[0][0]
        assert "denied" in logged

    @pytest.mark.asyncio
    async def test_audit_log_auto_for_none_risk(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        with patch("builtins.input"):
            await check_approval(ctx, "list_directory", {})
        logged = audit.info.call_args[0][0]
        assert "auto" in logged

    @pytest.mark.asyncio
    async def test_audit_log_skipped_when_no_logger(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # Should not raise even with no audit logger
        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": "/tmp/f.txt"})
        assert result is True


# ── _audit_approval() ─────────────────────────────────────────────────────────


class TestAuditApproval:
    def test_no_op_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # Must not raise
        _audit_approval(ctx, "delete_file", "high", {"path": "/tmp/x"}, "approved")

    def test_writes_json_lines_event(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(ctx, "shell_run", "high", {"command": "rm /tmp/x"}, "denied")
        audit.info.assert_called_once()
        payload: str = audit.info.call_args[0][0]
        import orjson

        event = orjson.loads(payload)
        assert event["event"] == "tool_approval"
        assert event["tool"] == "shell_run"
        assert event["risk"] == "high"
        assert event["decision"] == "denied"
        assert "ts" in event

    def test_masked_fields_applied_to_args(self) -> None:
        cfg = _make_cfg(masked_fields=["secret"])
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "write_file",
            "medium",
            {"path": "/tmp/f", "secret": "s3cr3t"},
            "approved",
        )
        payload: str = audit.info.call_args[0][0]
        assert "s3cr3t" not in payload
