"""
tests/test_tool_approval_repos.py
Unit tests for GitHub repo allowlist pre-flight and gitops guards.

Covers check_approval() GitHub write tool gating via allowed_repos and gitops_push_blocked.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_approval import check_approval

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
            "mcp_servers": {
                "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
            },
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
    ctx.workflow.workflow_id = None
    ctx.session.session_id = None
    ctx.services.audit_logger = None
    ctx.services.tools = AsyncMock()
    return ctx


class TestMakeCtxDefaults:
    def test_ctx_turn_id_default(self) -> None:
        ctx = _make_ctx()
        assert ctx.turn.current_turn_id == "test-turn-id"

    def test_ctx_workflow_id_default_none(self) -> None:
        ctx = _make_ctx()
        assert ctx.workflow.workflow_id is None

    def test_ctx_audit_logger_default_none(self) -> None:
        ctx = _make_ctx()
        assert ctx.services.audit_logger is None


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


# ── gitops / allowed_repos guards ────────────────────────────────────────────


class TestGitopsGuards:
    @pytest.mark.asyncio
    async def test_github_push_blocked_when_flag_set(self) -> None:
        """gitops_push_blocked=True denies GitHub write tools immediately."""
        cfg = _make_cfg(gitops_push_blocked=True)
        ctx = _make_ctx(cfg)
        result = await check_approval(ctx, "github_push_files", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_github_push_blocked_false_does_not_block_by_flag(self) -> None:
        """gitops_push_blocked=False: the flag itself does not deny the call."""
        cfg = _make_cfg(
            gitops_push_blocked=False,
            approval_github_allowed_repos=["myorg/allowed-repo"],
        )
        ctx = _make_ctx(cfg)
        with patch(
            "agent.tool_approval._prompt_user_approval", AsyncMock(return_value=True)
        ):
            result = await check_approval(
                ctx, "github_push_files", {"owner": "myorg", "repo": "allowed-repo"}
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_non_github_tool_not_blocked_by_gitops(self) -> None:
        """gitops_push_blocked only affects GitHub write tools."""
        cfg = _make_cfg(gitops_push_blocked=True)
        ctx = _make_ctx(cfg)
        result = await check_approval(ctx, "read_text_file", {"path": "/tmp/f"})
        assert result is True

    @pytest.mark.asyncio
    async def test_allowed_repos_rejects_unlisted_repo(self) -> None:
        """approval_github_allowed_repos non-empty: unlisted owner/repo is denied."""
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        ctx = _make_ctx(cfg)
        result = await check_approval(
            ctx, "github_push_files", {"owner": "myorg", "repo": "other-repo"}
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_allowed_repos_permits_listed_repo(self) -> None:
        """Repo matching allowed_repos entry is not denied by the repo check."""
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        ctx = _make_ctx(cfg)
        with patch(
            "agent.tool_approval._prompt_user_approval", AsyncMock(return_value=True)
        ):
            result = await check_approval(
                ctx, "github_push_files", {"owner": "myorg", "repo": "allowed-repo"}
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_allowed_repos_empty_denies_all_github_write(self) -> None:
        """Empty allowed_repos list is fail-closed: all GitHub write tools are denied."""
        cfg = _make_cfg(approval_github_allowed_repos=[])
        ctx = _make_ctx(cfg)
        result = await check_approval(
            ctx, "github_push_files", {"owner": "any", "repo": "repo"}
        )
        assert result is False
