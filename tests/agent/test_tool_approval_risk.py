"""
tests/test_tool_approval_risk.py
Unit tests for risk classification, operation type classification, and preview building.

Covers _classify_risk(), _build_preview(), and _classify_operation_type().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_policy import classify_risk as _classify_risk
from agent.tool_result_formatter import build_preview as _build_preview

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    PERMISSIVE_ALLOWED_ROOT,
    PERMISSIVE_SQLITE_VEC_SO,
    SHIPPED_APPROVAL_PROTECTED_PATHS,
    SHIPPED_DB_PATH_KEYS,
)
from tests.agent._producer_registry import make_producer_registry

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults.

    agentcfg003: the removed per-tool maps (tool_safety_tiers,
    approval_risk_rules) are no longer config keys; tier and risk come from the
    producer declarations read through the live RuntimeToolRegistry.
    """
    base = build_agent_config(
        {
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
            # memory_embed_enabled now defaults to True; memory_embed_url must be non-empty
            # to satisfy MemoryConfig.__post_init__'s cross-field validation.
            "memory_embed_url": "http://127.0.0.1:9999",
            # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
            **SHIPPED_DB_PATH_KEYS,
            "mcp_servers": {
                "dummy": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            "allowed_root": PERMISSIVE_ALLOWED_ROOT,
            "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
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
    ctx.services_required.audit_logger = None
    ctx.services_required.tools = AsyncMock()
    ctx.services_required.runtime_tools = None
    return ctx


class TestMakeCfgDefaults:
    """REQ-005: the removed per-tool maps are gone from the config surface."""

    def test_approval_config_has_no_risk_rules_field(self) -> None:
        cfg = _make_cfg()
        assert not hasattr(cfg.approval, "approval_risk_rules")

    def test_approval_config_has_no_safety_tiers_field(self) -> None:
        cfg = _make_cfg()
        assert not hasattr(cfg.approval, "tool_safety_tiers")

    def test_removed_maps_are_unknown_keys_for_the_validator(self) -> None:
        """A stale config still naming a removed map is rejected as an unknown
        key (agentcfg003 REQ-005), not silently ignored."""
        from agent.production_config_validator import ProductionConfigValidator

        errors = (
            ProductionConfigValidator()
            .validate({"tool_safety_tiers": {"write_file": "WRITE_SAFE"}})
            .errors
        )
        assert any("tool_safety_tiers" in e for e in errors)


# ── _classify_risk() ──────────────────────────────────────────────────────────


class TestClassifyRisk:
    """REQ-004: the declared tier mapped through _TIER_TO_RISK is the single
    risk source; the removed approval_risk_rules map no longer contributes."""

    def test_write_file_returns_none_from_declared_tier(self) -> None:
        """write_file declares WRITE_SAFE → none (the removed medium rule is gone)."""
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "write_file",
                {"path": "/home/user/file.txt"},
                make_producer_registry(),
            )
            == "none"
        )

    def test_delete_file_returns_medium_from_declared_tier(self) -> None:
        """delete_file declares WRITE_DANGEROUS → medium (was high via the removed rule)."""
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "delete_file",
                {"path": "/home/user/file.txt"},
                make_producer_registry(),
            )
            == "medium"
        )

    def test_read_only_tier_tool_returns_none(self) -> None:
        # list_directory declares READ_ONLY → "none" (auto-approved)
        cfg = _make_cfg()
        assert (
            _classify_risk(cfg, "list_directory", {}, make_producer_registry())
            == "none"
        )

    def test_truly_unknown_tool_returns_high_risk_fail_safe(self) -> None:
        # Tool absent from the runtime registry and no registry supplied
        # -> RiskLevel.HIGH (fail-safe: nothing to consult).
        cfg = _make_cfg()
        assert _classify_risk(cfg, "some_unregistered_tool", {}) == "high"

    def test_unregistered_tool_in_registry_high_risk_survives_no_special_case(
        self,
    ) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg, "totally_unregistered_tool_xyz", {}, make_producer_registry()
            )
            == "high"
        )

    def test_write_to_protected_path_escalates_to_high(self) -> None:
        # tier-MEDIUM delete_file with a protected path escalates to HIGH;
        # tier-NONE write_file is never escalated by approval_protected_paths.
        cfg = _make_cfg()
        reg = make_producer_registry()
        assert (
            _classify_risk(cfg, "delete_file", {"path": "/opt/llm/config.json"}, reg)
            == "high"
        )
        assert (
            _classify_risk(cfg, "write_file", {"path": "/opt/llm/config.json"}, reg)
            == "none"
        )

    def test_medium_tool_outside_protected_path_stays_medium(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "delete_file",
                {"path": "/home/user/file.txt"},
                make_producer_registry(),
            )
            == "medium"
        )

    def test_shell_run_returns_high_by_default(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "shell_run",
                {"command": "rm -rf /tmp/test"},
                make_producer_registry(),
            )
            == "high"
        )

    def test_shell_run_safe_prefix_returns_none(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg, "shell_run", {"command": "ls -la /tmp"}, make_producer_registry()
            )
            == "none"
        )

    def test_shell_run_git_log_returns_none(self) -> None:
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg,
                "shell_run",
                {"command": "git log --oneline -5"},
                make_producer_registry(),
            )
            == "none"
        )

    def test_declared_branch_keys_are_the_escalation_source(self) -> None:
        """REQ-008: the checked keys are the declared branch-kind keys. Plan
        20261126-073010 (REQ-001) declares `branch` on the three github file write
        tools, so approval_high_risk_branches escalates them to HIGH; a tool that
        declares no branch key is not branch-escalated."""
        cfg = _make_cfg()
        reg = make_producer_registry()
        declaring = sorted(
            tool.name
            for tool in reg.all_tools()
            if tool.name.startswith("github_")
            and any(kind == "branch" for kind in tool.resource_scope_keys.values())
        )
        assert declaring == [
            "github_create_or_update_file",
            "github_delete_file",
            "github_push_files",
        ], declaring
        # github_create_pull_request declares no branch key: the target branch changes no risk.
        for base in ("main", "feature/x"):
            assert (
                _classify_risk(
                    cfg,
                    "github_create_pull_request",
                    {"owner": "foo", "repo": "bar", "base": base},
                    reg,
                )
                == "medium"
            )
        # A declared branch key escalates only when its value is a high-risk branch.
        assert (
            _classify_risk(
                cfg,
                "github_push_files",
                {"owner": "foo", "repo": "bar", "branch": "main"},
                reg,
            )
            == "high"
        )
        assert (
            _classify_risk(
                cfg,
                "github_push_files",
                {"owner": "foo", "repo": "bar", "branch": "feature/x"},
                reg,
            )
            == "medium"
        )

    def test_delete_file_on_etc_still_high(self) -> None:
        # delete_file is tier-MEDIUM; the protected /etc/ path escalates it to HIGH.
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg, "delete_file", {"path": "/etc/hosts"}, make_producer_registry()
            )
            == "high"
        )

    def test_declared_tier_is_the_only_risk_source(self) -> None:
        """agentcfg003 REQ-004/REQ-011: with the rules map gone the resolved level
        is exactly the tier mapping — write_file (WRITE_SAFE) resolves to none,
        delete_file (WRITE_DANGEROUS) to medium, shell_run (ADMIN) to HIGH."""
        cfg = _make_cfg()
        reg = make_producer_registry()
        assert _classify_risk(cfg, "write_file", {}, reg) == "none"
        assert _classify_risk(cfg, "delete_file", {}, reg) == "medium"
        assert _classify_risk(cfg, "shell_run", {"command": "ls"}, reg) == "none"
        assert _classify_risk(cfg, "shell_run", {"command": "ls; rm"}, reg) == "high"

    def test_file_path_arg_key_also_escalates(self) -> None:
        # delete_file declares its path-kind key; a protected value escalates.
        cfg = _make_cfg()
        assert (
            _classify_risk(
                cfg, "delete_file", {"path": "/opt/llm/x.py"}, make_producer_registry()
            )
            == "high"
        )

    def test_write_safe_github_tools_resolve_to_none(self) -> None:
        """REQ-003 pin (Plan row 15 lineage): github_create_branch and
        github_create_issue declare WRITE_SAFE; with no rules branch left the tier
        branch alone decides — they resolve to none."""
        cfg = _make_cfg(approval_protected_paths=SHIPPED_APPROVAL_PROTECTED_PATHS)
        reg = make_producer_registry()
        for tool in ("github_create_branch", "github_create_issue"):
            assert _classify_risk(cfg, tool, {}, reg) == "none"

    @pytest.mark.parametrize("tool", ["git_add", "git_commit"])
    def test_tier_none_git_tools_ignore_protected_path(self, tool: str) -> None:
        """REQ-003 gap pin (Plan row 15): WRITE_SAFE tier maps to NONE and the
        NONE short-circuit returns before _escalate_for_path(), so a protected
        path argument cannot raise git_add/git_commit (measured: none)."""
        cfg = _make_cfg(approval_protected_paths=SHIPPED_APPROVAL_PROTECTED_PATHS)
        assert (
            _classify_risk(
                cfg, tool, {"path": "/opt/llm/repo/file.txt"}, make_producer_registry()
            )
            == "none"
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

    def test_preview_is_never_masked(self) -> None:
        preview = _build_preview(
            "write_file", {"path": "/f", "content": "sensitive-body-value"}
        )
        # The approving user must see the raw argument; masking the preview would
        # remove the approval signal while protecting nothing (REQ-001).
        assert "sensitive-body-value" in preview
        assert "***" not in preview


# ── _classify_operation_type() ───────────────────────────────────────────────


class TestClassifyOperationType:
    """REQ-007: the registered tool's declared side_effect_class is the
    authority; without a declaration the result is UNKNOWN."""

    def test_write_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        reg = make_producer_registry()
        for name in ("write_file", "edit_file", "create_directory", "move_file"):
            assert _classify_operation_type(name, reg) == "write"

    def test_mdq_rag_cicd_git_write_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        # Previously-unclassified per-server write-tool sets (MDQ/RAG/CICD/Git)
        # fell through to the default "read" before this fix; the shipped
        # declarations now resolve each of them.
        reg = make_producer_registry()
        for name in (
            "index_paths",
            "refresh_index",
            "rag_delete_document",
            "trigger_workflow",
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        ):
            assert _classify_operation_type(name, reg) == "write"

    def test_delete_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        reg = make_producer_registry()
        assert _classify_operation_type("delete_file", reg) == "delete"
        assert _classify_operation_type("delete_directory", reg) == "delete"

    def test_execute_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert (
            _classify_operation_type("shell_run", make_producer_registry()) == "execute"
        )

    def test_api_write_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        reg = make_producer_registry()
        assert _classify_operation_type("github_push_files", reg) == "api_write"
        assert (
            _classify_operation_type("github_create_pull_request", reg) == "api_write"
        )
        assert _classify_operation_type("github_merge_pull_request", reg) == "api_write"

    def test_read_tools(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        reg = make_producer_registry()
        assert _classify_operation_type("list_directory", reg) == "read"
        assert _classify_operation_type("read_text_file", reg) == "read"

    def test_unregistered_tool_returns_unknown(self) -> None:
        from agent.tool_policy import (
            classify_operation_type as _classify_operation_type,
        )

        assert _classify_operation_type("totally_unregistered_tool_xyz") == "unknown"
        assert _classify_operation_type("search_web") == "unknown"
