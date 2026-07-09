"""Tests for audit_security_defaults() fail-closed exception handling."""

from unittest.mock import patch

import pytest
from agent.security_audit_config import (
    GitAuditConfig,
    GitHubAuditConfig,
    ShellAuditConfig,
)


def _make_ctx(lockdown=False):
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.cfg.mcp.security_lockdown_enabled = lockdown
    ctx.cfg.tool.allowed_tools = []
    return ctx


_SHELL_OK = ShellAuditConfig(sandbox_backend="firejail", command_allowlist=["ls"])
_GIT_OK = GitAuditConfig(allowed_repo_paths=["/home"])
_GITHUB_OK = GitHubAuditConfig(
    allowed_repos=["owner/repo"], allowed_repos_mode="fail_closed", allow_force_push=False, require_pr_review=True
)


# --- Shell config load failure ---


def test_shell_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch(
        "agent.repl_health.load_shell_audit_config",
        side_effect=RuntimeError(
            "Security audit: failed to load shell config: disk fail"
        ),
    ):
        with pytest.raises(RuntimeError, match="shell config"):
            audit_security_defaults(ctx, production_mode=True)


def test_shell_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch(
        "agent.repl_health.load_shell_audit_config",
        side_effect=RuntimeError(
            "Security audit: failed to load shell config: disk fail"
        ),
    ):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("shell config" in w for w in warnings)


# --- Git config load failure ---


def test_git_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch(
                "agent.repl_health.load_git_audit_config",
                side_effect=RuntimeError(
                    "Security audit: failed to load git config: not found"
                ),
            ):
                with pytest.raises(RuntimeError, match="git config"):
                    audit_security_defaults(ctx, production_mode=True)


def test_git_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch(
                "agent.repl_health.load_git_audit_config",
                side_effect=RuntimeError(
                    "Security audit: failed to load git config: not found"
                ),
            ):
                warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("git config" in w for w in warnings)


# --- GitHub config load failure ---


def test_github_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch("agent.repl_health.load_git_audit_config", return_value=_GIT_OK):
                with patch(
                    "agent.repl_health.load_github_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load GitHub config: bad value"
                    ),
                ):
                    with pytest.raises(RuntimeError, match="GitHub config"):
                        audit_security_defaults(ctx, production_mode=True)


def test_github_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch("agent.repl_health.load_git_audit_config", return_value=_GIT_OK):
                with patch(
                    "agent.repl_health.load_github_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load GitHub config: bad value"
                    ),
                ):
                    warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("GitHub config" in w for w in warnings)


# --- CI/CD config load failure ---


def test_cicd_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch("agent.repl_health.load_git_audit_config", return_value=_GIT_OK):
                with patch(
                    "agent.repl_health.load_github_audit_config",
                    return_value=_GITHUB_OK,
                ):
                    with patch(
                        "agent.repl_health.load_cicd_audit_config",
                        side_effect=RuntimeError(
                            "Security audit: failed to load CI/CD config: io error"
                        ),
                    ):
                        with pytest.raises(RuntimeError, match="CI/CD config"):
                            audit_security_defaults(ctx, production_mode=True)


def test_cicd_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch("agent.repl_health.load_git_audit_config", return_value=_GIT_OK):
                with patch(
                    "agent.repl_health.load_github_audit_config",
                    return_value=_GITHUB_OK,
                ):
                    with patch(
                        "agent.repl_health.load_cicd_audit_config",
                        side_effect=RuntimeError(
                            "Security audit: failed to load CI/CD config: io error"
                        ),
                    ):
                        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("CI/CD config" in w for w in warnings)


# --- lockdown=True does not suppress config load failures ---


def test_lockdown_does_not_suppress_production_failure():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx(lockdown=True)
    with patch(
        "agent.repl_health.load_shell_audit_config",
        side_effect=RuntimeError("Security audit: failed to load shell config: fail"),
    ):
        with pytest.raises(RuntimeError, match="shell config"):
            audit_security_defaults(ctx, production_mode=True)


# --- Optional dependency not installed stays silent ---


def test_import_error_stays_silent():
    from agent.repl_health import audit_security_defaults

    ctx = _make_ctx()
    with patch("agent.repl_health.load_shell_audit_config", return_value=_SHELL_OK):
        with patch("shutil.which", return_value="/usr/bin/firejail"):
            with patch("agent.repl_health.load_git_audit_config", return_value=_GIT_OK):
                with patch(
                    "agent.repl_health.load_github_audit_config", return_value=None
                ):
                    warnings = audit_security_defaults(ctx, production_mode=True)
    assert not any("GitHub config" in w for w in (warnings or []))
