#!/usr/bin/env python3
"""mcp_servers/github/models_config.py
Typed config loading and domain exceptions for github-mcp server.

Dependency direction: mcp_servers.github.models_config → (no local deps)
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_PER_PAGE: int = 10


def _get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


@dataclasses.dataclass
class GitHubConfig:
    """Typed configuration for the GitHub MCP server."""

    allowed_repos: list[str] = dataclasses.field(default_factory=list)
    path_denylist: list[str] = dataclasses.field(default_factory=list)
    protected_branches: list[str] = dataclasses.field(default_factory=list)
    max_file_size_kb: int = 0
    audit_log_path: str = ""
    allow_force_push: bool = False
    require_pr_review: bool = True
    default_per_page: int = DEFAULT_PER_PAGE
    max_per_page: int = 100
    llm_url: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GitHubConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            allowed_repos=list(d.get("allowed_repos", [])),
            path_denylist=list(d.get("path_denylist", [])),
            protected_branches=list(d.get("protected_branches", [])),
            max_file_size_kb=int(d.get("max_file_size_kb", 0)),
            audit_log_path=_get_str(d, "audit_log_path"),
            allow_force_push=bool(d.get("allow_force_push", False)),
            require_pr_review=bool(d.get("require_pr_review", True)),
            default_per_page=int(d.get("default_per_page", DEFAULT_PER_PAGE)),
            max_per_page=int(d.get("max_per_page", 100)),
            llm_url=_get_str(d, "llm_url"),
        )

    @classmethod
    def load(cls) -> GitHubConfig:
        """Load from github_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("github_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class GitHubAuthorizationError(RuntimeError):
    """Raised when a repo/path/branch policy check fails (HTTP 403)."""


class GitHubNotFoundError(RuntimeError):
    """Raised when a GitHub resource is not found (HTTP 404)."""


class GitHubValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


class GitHubConflictError(RuntimeError):
    """Raised on a GitHub conflict (HTTP 409)."""


class GitHubUpstreamError(RuntimeError):
    """Raised on GitHub API 5xx or unexpected upstream failures."""


class GitHubAuditError(RuntimeError):
    """Raised when audit log writing fails and audit_log_path is configured."""
