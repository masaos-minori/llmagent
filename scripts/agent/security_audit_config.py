"""agent/security_audit_config.py

Narrow API for security audit access to MCP server config models.

This is the ONLY agent module permitted to import from MCP server config models.
All security audit checks must go through this module.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShellAuditConfig:
    """Security audit configuration for shell command execution."""

    sandbox_backend: str
    command_allowlist: list[str]


@dataclass(frozen=True)
class GitAuditConfig:
    """Security audit configuration for git operations."""

    allowed_repo_paths: list[str]


@dataclass(frozen=True)
class GitHubAuditConfig:
    """Security audit configuration for GitHub API operations."""

    allowed_repos: list[str]
    allow_force_push: bool
    require_pr_review: bool


@dataclass(frozen=True)
class CicdAuditConfig:
    """Security audit configuration for CI/CD pipeline operations."""

    workflow_allowlist: list[str]


def load_shell_audit_config() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp_servers.shell.shell_models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load shell config: {exc}"
        ) from exc


def load_git_audit_config() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp_servers.git.git_models import GitConfig
    except ImportError:
        return None
    try:
        cfg = GitConfig.load()
        return GitAuditConfig(allowed_repo_paths=list(cfg.allowed_repo_paths))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load git config: {exc}") from exc


def load_github_audit_config() -> GitHubAuditConfig | None:
    """Load GitHub config for audit. Returns None if not installed."""
    try:
        from mcp_servers.github.models_config import GitHubConfig
    except ImportError:
        return None
    try:
        cfg = GitHubConfig.load()
        return GitHubAuditConfig(
            allowed_repos=list(cfg.allowed_repos),
            allow_force_push=cfg.allow_force_push,
            require_pr_review=cfg.require_pr_review,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load GitHub config: {exc}"
        ) from exc


def load_cicd_audit_config() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp_servers.cicd.cicd_models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(
            f"Security audit: failed to load CI/CD config: {exc}"
        ) from exc
