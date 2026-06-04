"""
tests/test_tool_approval.py
Unit tests for the risk-based tool approval model.

Covers _classify_risk(), _build_preview(), and check_approval().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config import AgentConfig, build_agent_config
from agent.tool_approval import check_approval
from agent.tool_audit import audit_approval as _audit_approval
from agent.tool_audit import audit_tool_exec as _audit_tool_exec
from agent.tool_policy import classify_risk as _classify_risk
from agent.tool_result_formatter import build_preview as _build_preview
from agent.tool_runner import execute_one_tool_call

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
            # Standard tier classification; mirrors config/agent.json defaults
            "tool_safety_tiers": {
                "list_directory": "READ_ONLY",
                "read_text_file": "READ_ONLY",
                "directory_tree": "READ_ONLY",
                "search_files": "READ_ONLY",
                "grep_files": "READ_ONLY",
                "search_web": "READ_ONLY",
                "github_search_repositories": "READ_ONLY",
                "github_get_file_contents": "READ_ONLY",
                "write_file": "WRITE_SAFE",
                "edit_file": "WRITE_SAFE",
                "create_directory": "WRITE_SAFE",
                "move_file": "WRITE_SAFE",
                "github_create_branch": "WRITE_SAFE",
                "github_create_issue": "WRITE_SAFE",
                "github_add_issue_comment": "WRITE_SAFE",
                "delete_file": "WRITE_DANGEROUS",
                "delete_directory": "WRITE_DANGEROUS",
                "github_push_files": "WRITE_DANGEROUS",
                "github_create_or_update_file": "WRITE_DANGEROUS",
                "github_delete_file": "WRITE_DANGEROUS",
                "github_merge_pull_request": "WRITE_DANGEROUS",
                "github_create_pull_request": "WRITE_DANGEROUS",
                "github_update_pull_request": "WRITE_DANGEROUS",
                "shell_run": "ADMIN",
            },
            **overrides,
        }
    )
    return base


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg = cfg or _make_cfg()
    ctx.turn.current_turn_id = "test-turn-id"
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

    def test_read_only_tier_tool_returns_none(self) -> None:
        # list_directory is READ_ONLY tier → "none" (auto-approved)
        cfg = _make_cfg()
        assert _classify_risk(cfg, "list_directory", {}) == "none"

    def test_truly_unknown_tool_returns_medium_fail_safe(self) -> None:
        # Tool absent from both approval_risk_rules and tool_safety_tiers
        # → Fail-Safe: WRITE_DANGEROUS default → "medium"
        cfg = _make_cfg()
        assert _classify_risk(cfg, "some_unregistered_tool", {}) == "medium"

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

    def test_empty_risk_rules_falls_back_to_tier(self) -> None:
        # With empty approval_risk_rules, tier classification kicks in.
        # delete_file tier=WRITE_DANGEROUS → "medium" (Fail-Safe, not "none")
        cfg = _make_cfg(approval_risk_rules={})
        assert _classify_risk(cfg, "delete_file", {}) == "medium"

    def test_empty_risk_rules_read_only_still_none(self) -> None:
        # READ_ONLY tier tools remain "none" even with empty approval_risk_rules
        cfg = _make_cfg(approval_risk_rules={})
        assert _classify_risk(cfg, "list_directory", {}) == "none"

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

    def test_operation_type_in_audit_event(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(ctx, "delete_file", "high", {"path": "/tmp/x"}, "denied")
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert event["operation_type"] == "delete"

    def test_resource_scope_contains_path_keys(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "write_file",
            "medium",
            {"path": "/opt/llm/x.py", "other": "val"},
            "approved",
        )
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert "path" in event["resource_scope"]
        assert "other" not in event["resource_scope"]

    def test_resource_scope_contains_branch_keys(self) -> None:
        ctx = _make_ctx()
        audit = MagicMock()
        ctx.services.audit_logger = audit
        _audit_approval(
            ctx,
            "github_create_pull_request",
            "medium",
            {"owner": "org", "repo": "r", "base": "main"},
            "approved",
        )
        import orjson

        event = orjson.loads(audit.info.call_args[0][0])
        assert "base" in event["resource_scope"]
        assert "owner" not in event["resource_scope"]


# ── _classify_operation_type() ───────────────────────────────────────────────


class TestClassifyOperationType:
    def test_write_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        for name in ("write_file", "edit_file", "create_directory", "move_file"):
            assert _classify_operation_type(name) == "write"

    def test_delete_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert _classify_operation_type("delete_file") == "delete"
        assert _classify_operation_type("delete_directory") == "delete"

    def test_execute_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert _classify_operation_type("shell_run") == "execute"

    def test_api_write_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert _classify_operation_type("github_push_files") == "api_write"
        assert _classify_operation_type("github_create_pull_request") == "api_write"
        assert _classify_operation_type("github_merge_pull_request") == "api_write"

    def test_read_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert _classify_operation_type("list_directory") == "read"
        assert _classify_operation_type("read_text_file") == "read"
        assert _classify_operation_type("search_web") == "read"


# ── check_approval() dry_run flow ─────────────────────────────────────────────


class TestCheckApprovalDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_result_appended_to_preview(self) -> None:
        """dry_run execution output should be included in preview before prompt."""
        cfg = _make_cfg()
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(
            return_value=("Dry-run: /tmp/f (5 bytes) [new file]", False, "")
        )

        printed: list[str] = []
        with (
            patch("builtins.print", side_effect=lambda *a: printed.append(str(a))),
            patch("asyncio.to_thread", new=AsyncMock(return_value="y")),
        ):
            result = await check_approval(
                ctx, "write_file", {"path": "/tmp/f.txt", "content": "hi"}
            )

        assert result is True
        combined = " ".join(printed)
        assert "Dry-run" in combined
        ctx.services.tools.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dry_run_skipped_for_non_dry_run_tool(self) -> None:
        """shell_run is not in approval_dry_run_tools; dry_run must not be called."""
        cfg = _make_cfg(approval_dry_run_tools=[])
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock()

        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            await check_approval(ctx, "shell_run", {"command": "rm /tmp/x"})

        ctx.services.tools.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dry_run_exception_does_not_abort_approval(self) -> None:
        """If dry_run raises, approval flow must continue normally."""
        cfg = _make_cfg()
        ctx = _make_ctx(cfg=cfg)
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(side_effect=RuntimeError("mcp error"))

        with (
            patch("builtins.print"),
            patch("asyncio.to_thread", new=AsyncMock(return_value="y")),
        ):
            result = await check_approval(
                ctx, "write_file", {"path": "/tmp/f.txt", "content": "hi"}
            )

        assert result is True  # approval still proceeds


# ── check_approval(): ALLOWED_ROOT pre-flight ─────────────────────────────────


class TestCheckApprovalAllowedRoot:
    @pytest.mark.asyncio
    async def test_path_outside_root_immediately_denied(self, tmp_path: Any) -> None:
        import tempfile

        root = tempfile.mkdtemp()
        cfg = _make_cfg(allowed_root=root)
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services.audit_logger = audit

        result = await check_approval(ctx, "write_file", {"path": "/etc/passwd"})

        assert result is False
        logged = audit.info.call_args[0][0]
        assert "denied_root_jail" in logged

    @pytest.mark.asyncio
    async def test_path_inside_root_proceeds_to_risk_check(self, tmp_path: Any) -> None:
        import tempfile

        root = tempfile.mkdtemp()
        cfg = _make_cfg(allowed_root=root)
        ctx = _make_ctx(cfg=cfg)

        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(
                ctx, "write_file", {"path": f"{root}/file.txt"}
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_disabled_root_does_not_block(self, tmp_path: Any) -> None:
        # Use tmp_path (not /etc) to avoid triggering approval_protected_paths escalation
        outside = str(tmp_path / "outside.txt")
        cfg = _make_cfg(allowed_root="", approval_protected_paths=[])
        ctx = _make_ctx(cfg=cfg)

        with patch("asyncio.to_thread", new=AsyncMock(return_value="y")):
            result = await check_approval(ctx, "write_file", {"path": outside})

        assert result is True


# ── check_approval(): GitHub repo allowlist pre-flight ───────────────────────


class TestCheckApprovalGitHubAllowlist:
    @pytest.mark.asyncio
    async def test_fail_closed_empty_allowlist_denies_write(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        ctx = _make_ctx(cfg=cfg)
        audit = MagicMock()
        ctx.services.audit_logger = audit

        result = await check_approval(
            ctx, "github_push_files", {"owner": "org", "repo": "repo"}
        )

        assert result is False
        logged = audit.info.call_args[0][0]
        assert "denied_repo_allowlist" in logged

    @pytest.mark.asyncio
    async def test_repo_in_allowlist_proceeds(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["org/repo"])
        ctx = _make_ctx(cfg=cfg)

        with patch("asyncio.to_thread", new=AsyncMock(return_value="yes")):
            result = await check_approval(
                ctx, "github_push_files", {"owner": "org", "repo": "repo"}
            )

        assert result is True


# ── _audit_tool_exec() ────────────────────────────────────────────────────────


class TestAuditToolExec:
    def test_writes_to_audit_logger_when_conditions_met(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-abc"

        _audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")

        ctx.services.audit_logger.info.assert_called_once()
        logged = ctx.services.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert "req-123" in logged

    def test_skips_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = None
        # No error raised even though logger is None
        _audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")

    def test_skips_when_mcp_request_id_is_empty(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        _audit_tool_exec(ctx, "read_text_file", {}, False, "")
        ctx.services.audit_logger.info.assert_not_called()


# ── execute_one_tool_call() ───────────────────────────────────────────────────


class TestExecuteOneToolCall:
    @pytest.mark.asyncio
    async def test_unpacks_three_tuple_from_execute(self) -> None:
        ctx = _make_ctx()
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(return_value=("result text", False, ""))
        ctx.services.audit_logger = None
        ctx.cfg.use_tool_summarize = False
        ctx.cfg.tool_result_max_llm_chars = 4000
        ctx.cfg.masked_fields = []

        tc = {
            "id": "call_1",
            "function": {"name": "read_text_file", "arguments": '{"path": "/tmp/f"}'},
        }
        tc_id, name, args, full_text, is_error, llm_text = await execute_one_tool_call(
            ctx, tc, 0
        )

        assert tc_id == "call_1"
        assert name == "read_text_file"
        assert full_text == "result text"
        assert not is_error
        ctx.services.tools.execute.assert_awaited_once_with(
            "read_text_file", {"path": "/tmp/f"}
        )

    @pytest.mark.asyncio
    async def test_audit_tool_exec_called_with_x_request_id(self) -> None:
        ctx = _make_ctx()
        ctx.services.tools = MagicMock()
        ctx.services.tools.execute = AsyncMock(return_value=("ok", False, "req-999"))
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.use_tool_summarize = False
        ctx.cfg.tool_result_max_llm_chars = 4000
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-x"

        tc = {"id": "call_2", "function": {"name": "read_text_file", "arguments": "{}"}}
        await execute_one_tool_call(ctx, tc, 0)

        ctx.services.audit_logger.info.assert_called_once()
        logged = ctx.services.audit_logger.info.call_args[0][0]
        assert "req-999" in logged
