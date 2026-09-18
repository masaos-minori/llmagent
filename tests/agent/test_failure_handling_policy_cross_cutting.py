"""tests/agent/test_failure_handling_policy_cross_cutting.py

Cross-cutting tests for ADR-004 environment failure handling policy.
Covers INV-010 and INV-011.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agent.security_audit_config import (
    GitAuditConfig,
    GitHubAuditConfig,
    ShellAuditConfig,
)
from agent.services.security_audit import audit_security_defaults


def _make_ctx(lockdown=False):
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.cfg.mcp.security_lockdown_enabled = lockdown
    ctx.cfg.tool.allowed_tools = None
    # Explicitly set approval to empty dict so getattr returns {} not MagicMock
    ctx.cfg.approval = MagicMock()
    ctx.cfg.approval.tool_safety_tiers = {}
    return ctx


_SHELL_OK = ShellAuditConfig(sandbox_backend="firejail", command_allowlist=["ls"])
_GIT_OK = GitAuditConfig(allowed_repo_paths=["/home"])
_GITHUB_OK = GitHubAuditConfig(
    allowed_repos=["owner/repo"],
    allow_force_push=False,
    require_pr_review=True,
)

_CICD_OK = MagicMock()
_CICD_OK.workflow_allowlist = ["build"]

# Patch the CICD loader at the source location before any tests run
_original_load_cicd = None


@pytest.fixture(autouse=True)
def _patch_cicd():
    global _original_load_cicd
    with patch(
        "agent.services.security_audit.load_cicd_audit_config",
        return_value=_CICD_OK,
    ):
        yield


class TestFailureHandlingPolicy:
    def test_shell_config_failure_production_raises(self) -> None:
        """INV-010: shell config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            side_effect=RuntimeError(
                "Security audit: failed to load shell config: disk fail"
            ),
        ):
            with pytest.raises(RuntimeError, match="shell config"):
                audit_security_defaults(ctx)

    def test_git_config_failure_production_raises(self) -> None:
        """INV-010: git config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load git config: not found"
                    ),
                ):
                    with pytest.raises(RuntimeError, match="git config"):
                        audit_security_defaults(ctx)

    def test_github_config_failure_production_raises(self) -> None:
        """INV-010: GitHub config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        side_effect=RuntimeError(
                            "Security audit: failed to load GitHub config: bad value"
                        ),
                    ):
                        with pytest.raises(RuntimeError, match="GitHub config"):
                            audit_security_defaults(ctx)

    def test_lockdown_does_not_suppress_production_failure(self) -> None:
        """INV-011: lockdown mode does not suppress config load failures."""
        ctx = _make_ctx(lockdown=True)
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            side_effect=RuntimeError(
                "Security audit: failed to load shell config: fail"
            ),
        ):
            with pytest.raises(RuntimeError, match="shell config"):
                audit_security_defaults(ctx)

    def test_all_configs_load_success_returns_no_warnings(self) -> None:
        """INV-010: successful config loads produce no warnings."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        return_value=_GITHUB_OK,
                    ):
                        warnings = audit_security_defaults(ctx)
        assert not warnings

    def test_partial_config_failure_produces_targeted_exception(self) -> None:
        """INV-011: partial failures raise RuntimeError for specific components only."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        side_effect=RuntimeError(
                            "Security audit: failed to load GitHub config: bad value"
                        ),
                    ):
                        with pytest.raises(RuntimeError, match="GitHub config"):
                            audit_security_defaults(ctx)

    def test_lockdown_mode_validates_required_configs(self) -> None:
        """INV-011: lockdown mode enforces stricter validation on required configs."""
        ctx = _make_ctx(lockdown=True)
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load git config: error"
                    ),
                ):
                    with pytest.raises(RuntimeError, match="git config"):
                        audit_security_defaults(ctx)

    def test_non_production_profile_raises_on_config_failures(self) -> None:
        """INV-011: non-production profiles also raise on config load failures (_load_audit_config_or_raise)."""
        ctx = _make_ctx()
        # Simulate non-production profile by setting a flag
        ctx.cfg.env = MagicMock()
        ctx.cfg.env.name = "local"
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            return_value=_SHELL_OK,
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load git config: error"
                    ),
                ):
                    with pytest.raises(RuntimeError, match="git config"):
                        audit_security_defaults(ctx)
