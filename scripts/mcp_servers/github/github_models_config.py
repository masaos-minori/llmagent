#!/usr/bin/env python3
"""scripts/mcp_servers/github/github_models_config.py

Typed config loading and domain exceptions for github-mcp server.

Dependency direction: mcp_servers.github.github_models_config → (no local deps)
"""

from __future__ import annotations

import dataclasses
import logging
import math
from typing import Any

from shared.config_loader import ConfigLoader
from shared.config_utils import get_non_negative_number, get_str, get_typed
from shared.repo_identity import is_canonical_repo_key, normalize_repo_key

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_PER_PAGE: int = 10
DEFAULT_CONNECT_TIMEOUT_SEC: float = 5.0
DEFAULT_READ_TIMEOUT_SEC: float = 30.0


def _get_positive_number(d: dict[str, Any], key: str, default: float) -> float:
    """Return ``d[key]`` as a strictly positive finite number.

    Uses the same strict style as the shared non-negative helper (rejects a
    ``bool``, a non-number, a non-finite value), but rejects ``0`` as well: a
    timeout must never be able to disable itself. A TOML integer is accepted as
    a number and returned as ``float``. Raises ``ValueError`` naming the key and
    the received value. Returns ``default`` when the key is absent or its value
    is ``None``.
    """
    value = d.get(key)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"'{key}' must be a number, got {type(value).__name__}: {value!r}"
        )
    if not math.isfinite(value):
        raise ValueError(f"'{key}' must be a number, got non-finite value: {value!r}")
    if value <= 0:
        raise ValueError(f"'{key}' must be a number greater than 0, got {value!r}")
    return float(value)


def _normalize_allowed_repos(entries: list[Any]) -> list[Any]:
    """Canonicalize and deduplicate `owner/repo` allowlist entries.

    Entries that are already canonicalizable (a string with exactly one `/`) are mapped
    through the shared identity helper and deduplicated in a deterministic sorted order.
    Anything else is kept unchanged, in input order, so `load()` can report the offending
    entries instead of `from_dict()` crashing on them.
    """
    canonical: list[str] = []
    seen: set[str] = set()
    malformed: list[Any] = []
    for entry in entries:
        if isinstance(entry, str) and entry.count("/") == 1:
            key = normalize_repo_key(*entry.split("/"))
            if key not in seen:
                seen.add(key)
                canonical.append(key)
        else:
            malformed.append(entry)
    return sorted(canonical) + malformed


@dataclasses.dataclass
class GitHubConfig:
    """Typed configuration for the GitHub MCP server."""

    allowed_repos: list[str] = dataclasses.field(default_factory=list)
    path_denylist: list[str] = dataclasses.field(default_factory=list)
    protected_branches: list[str] = dataclasses.field(default_factory=list)
    max_file_size_kb: int = 0
    max_file_read_size_kb: int = 0
    audit_log_path: str = ""
    allow_force_push: bool = False
    require_pr_review: bool = True
    allow_global_search: bool = False
    default_per_page: int = DEFAULT_PER_PAGE
    max_per_page: int = 100
    connect_timeout_sec: float = DEFAULT_CONNECT_TIMEOUT_SEC
    read_timeout_sec: float = DEFAULT_READ_TIMEOUT_SEC
    llm_url: str = ""

    auth_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GitHubConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            allowed_repos=_normalize_allowed_repos(
                list(get_typed(d, "allowed_repos", list, "a list", default=[]))
            ),
            path_denylist=list(
                get_typed(d, "path_denylist", list, "a list", default=[])
            ),
            protected_branches=list(
                get_typed(d, "protected_branches", list, "a list", default=[])
            ),
            max_file_size_kb=get_non_negative_number(
                d, "max_file_size_kb", int, "an integer", default=0
            ),
            max_file_read_size_kb=get_non_negative_number(
                d, "max_file_read_size_kb", int, "an integer", default=0
            ),
            audit_log_path=get_str(d, "audit_log_path"),
            allow_force_push=get_typed(
                d, "allow_force_push", bool, "a boolean", default=False
            ),
            require_pr_review=get_typed(
                d, "require_pr_review", bool, "a boolean", default=True
            ),
            allow_global_search=get_typed(
                d, "allow_global_search", bool, "a boolean", default=False
            ),
            default_per_page=get_non_negative_number(
                d, "default_per_page", int, "an integer", default=DEFAULT_PER_PAGE
            ),
            max_per_page=get_non_negative_number(
                d, "max_per_page", int, "an integer", default=100
            ),
            connect_timeout_sec=_get_positive_number(
                d, "connect_timeout_sec", DEFAULT_CONNECT_TIMEOUT_SEC
            ),
            read_timeout_sec=_get_positive_number(
                d, "read_timeout_sec", DEFAULT_READ_TIMEOUT_SEC
            ),
            llm_url=get_str(d, "llm_url"),
            auth_token=get_str(d, "auth_token"),
        )

    @classmethod
    def load(cls) -> GitHubConfig:
        """Load from github_mcp_server.toml; raises on failure (fail-fast).

        An empty or absent ``protected_branches`` is a load error: the server
        must not start with the protected-branch guard silently disabled
        (ADR-004 fail-closed). An empty ``path_denylist`` stays valid under the
        registered ADR-004 exception. from_dict() with an empty list remains
        valid for unit tests.

        Startup also refuses a configuration the runtime guards cannot honour:
        ``default_per_page``/``max_per_page`` of 0 or below, a ``default_per_page``
        above ``max_per_page``, and any ``allowed_repos`` entry that is not a
        canonical ``owner/repo`` key. from_dict() normalizes what it can and leaves
        the rest visible; only load() decides whether the server may start.
        """
        cfg = cls.from_dict(ConfigLoader().load("github_mcp_server.toml"))
        if not cfg.protected_branches:
            raise ValueError(
                "github_mcp_server.toml: protected_branches must not be empty"
            )
        if cfg.default_per_page <= 0 or cfg.max_per_page <= 0:
            raise ValueError(
                "github_mcp_server.toml: default_per_page and max_per_page must be "
                f"greater than 0 (got {cfg.default_per_page}, {cfg.max_per_page})"
            )
        if cfg.default_per_page > cfg.max_per_page:
            raise ValueError(
                "github_mcp_server.toml: default_per_page must not exceed max_per_page "
                f"(got {cfg.default_per_page} > {cfg.max_per_page})"
            )
        malformed = [e for e in cfg.allowed_repos if not is_canonical_repo_key(e)]
        if malformed:
            raise ValueError(
                "github_mcp_server.toml: allowed_repos entries must be canonical "
                f"'owner/repo' keys (lower-case, exactly one '/'): {malformed!r}"
            )
        return cfg


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


class GitHubOutcomeUnknownError(RuntimeError):
    """Raised when a write's transport failed ambiguously (timeout, connection loss after send).

    A timeout never implies non-application: the write may already have landed
    remotely, so the outcome is unknown and the call is never retried
    automatically (mcpai006 REQ-003).
    """


class GitHubAppliedAuditError(GitHubAuditError):
    """Raised when the completion audit fails after the write was applied.

    The write landed; only the audit record is missing, so this is reported as
    `applied_audit_failed` rather than a generic audit failure and is never
    retried (mcpai006 REQ-005).
    """
