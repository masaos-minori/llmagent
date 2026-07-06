# Implementation: agent/security_audit_config.py — Narrow audit API for MCP server config access

## Goal

Create a new module `scripts/agent/security_audit_config.py` that is the single authorised point in the agent layer for importing MCP server config models. All security audit checks must go through this module; no other agent file may import from `mcp.shell.models`, `mcp.git.models`, `mcp.github.models_config`, or `mcp.cicd.models` directly.

## Scope

**In**: Create `security_audit_config.py` with 4 narrow audit DTOs and 4 loader functions wrapping MCP server config models.

**Out**: Changes to `repl_health.py`, tests, or `.importlinter`. Those are separate phases.

## Assumptions

1. `mcp.shell.models.ShellConfig`, `mcp.git.models.GitConfig`, `mcp.github.models_config.GitHubConfig`, `mcp.cicd.models.CicdConfig` all expose a `load()` classmethod.
2. `ShellConfig.shell_sandbox_backend` (str) and `ShellConfig.command_allowlist` (list[str]) are accessible fields.
3. `GitConfig.allowed_repo_paths` (list[str]) is accessible.
4. `GitHubConfig.allowed_repos` (list[str]), `GitHubConfig.allow_force_push` (bool), `GitHubConfig.require_pr_review` (bool) are accessible.
5. `CicdConfig.workflow_allowlist` (list[str]) is accessible.
6. `mcp.github` and `mcp.cicd` are optional dependencies; `ImportError` must be silently skipped.
7. The module lives under `scripts/agent/` and may import from `mcp.*` without violating `.importlinter` (an exception will be added for this specific module in a later phase if needed).

## Implementation

### Target file

`scripts/agent/security_audit_config.py`

### Procedure

1. Create the file with module docstring.
2. Define 4 frozen dataclasses: `ShellAuditConfig`, `GitAuditConfig`, `GitHubAuditConfig`, `CicdAuditConfig`.
3. Implement `load_shell_audit_config() -> ShellAuditConfig | None`.
4. Implement `load_git_audit_config() -> GitAuditConfig | None`.
5. Implement `load_github_audit_config() -> GitHubAuditConfig | None`.
6. Implement `load_cicd_audit_config() -> CicdAuditConfig | None`.
7. Each loader wraps its import in `try/except ImportError` (returns `None`); wraps config load in `try/except Exception` and re-raises as `RuntimeError`.

### Method

```python
"""agent/security_audit_config.py
Narrow API for security audit access to MCP server config models.

This is the ONLY agent module permitted to import from MCP server config models.
All security audit checks must go through this module.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShellAuditConfig:
    sandbox_backend: str
    command_allowlist: list[str]


@dataclass(frozen=True)
class GitAuditConfig:
    allowed_repo_paths: list[str]


@dataclass(frozen=True)
class GitHubAuditConfig:
    allowed_repos: list[str]
    allow_force_push: bool
    require_pr_review: bool


@dataclass(frozen=True)
class CicdAuditConfig:
    workflow_allowlist: list[str]


def load_shell_audit_config() -> ShellAuditConfig | None:
    """Load shell config for audit. Returns None if not installed."""
    try:
        from mcp.shell.models import ShellConfig
    except ImportError:
        return None
    try:
        cfg = ShellConfig.load()
        return ShellAuditConfig(
            sandbox_backend=cfg.shell_sandbox_backend,
            command_allowlist=list(cfg.command_allowlist),
        )
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load shell config: {exc}") from exc


def load_git_audit_config() -> GitAuditConfig | None:
    """Load git config for audit. Returns None if not installed."""
    try:
        from mcp.git.models import GitConfig
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
        from mcp.github.models_config import GitHubConfig
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
        raise RuntimeError(f"Security audit: failed to load GitHub config: {exc}") from exc


def load_cicd_audit_config() -> CicdAuditConfig | None:
    """Load CI/CD config for audit. Returns None if not installed."""
    try:
        from mcp.cicd.models import CicdConfig
    except ImportError:
        return None
    try:
        cfg = CicdConfig.load()
        return CicdAuditConfig(workflow_allowlist=list(cfg.workflow_allowlist))
    except Exception as exc:
        raise RuntimeError(f"Security audit: failed to load CI/CD config: {exc}") from exc
```

### Details

- All 4 DTOs use `frozen=True` for immutability.
- `ImportError` is caught at the import statement, not the load call — ensures optional dependencies are handled cleanly.
- `RuntimeError` is raised for config load failures; callers (e.g. `audit_security_defaults()`) must catch it.
- No logging in this module; callers are responsible for logging.

## Validation plan

- `mypy scripts/agent/security_audit_config.py` — no errors.
- `ruff check scripts/agent/security_audit_config.py` — 0 errors.
- Unit test: mock `ShellConfig.load()` → returns correct `ShellAuditConfig`.
- Unit test: `ImportError` on `mcp.shell.models` → returns `None`.
- Unit test: `ShellConfig.load()` raises `ValueError` → `RuntimeError` raised.
