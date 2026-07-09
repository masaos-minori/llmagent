# Implementation: security_audit_config.py — Add `allowed_repos_mode` to GitHubAuditConfig

## Goal

Add `allowed_repos_mode: str` field to `GitHubAuditConfig` dataclass and populate it from `GitHubConfig.load().allowed_repos_mode` in `load_github_audit_config()`.

## Scope

- `scripts/agent/security_audit_config.py` only.
- One field addition to `GitHubAuditConfig` and one line in `load_github_audit_config()`.

## Assumptions

1. `GitHubConfig.allowed_repos_mode` exists on the source model (`scripts/mcp/github/models_config.py:40`) with default `"fail_closed"`.
2. `GitHubAuditConfig` is a `frozen=True` dataclass; adding a new required field changes its constructor signature — all direct callers must be updated in a coordinated change.

## Implementation

### Target file

`scripts/agent/security_audit_config.py`

### Procedure

1. Add `allowed_repos_mode: str` field to `GitHubAuditConfig` dataclass.
2. Add `allowed_repos_mode=cfg.allowed_repos_mode` to the return statement of `load_github_audit_config()`.

### Method

In-place edits. No new functions or classes.

### Details

#### Change 1: `GitHubAuditConfig` dataclass

Before:

```python
@dataclass(frozen=True)
class GitHubAuditConfig:
    allowed_repos: list[str]
    allow_force_push: bool
    require_pr_review: bool
```

After:

```python
@dataclass(frozen=True)
class GitHubAuditConfig:
    allowed_repos: list[str]
    allowed_repos_mode: str
    allow_force_push: bool
    require_pr_review: bool
```

#### Change 2: `load_github_audit_config()` return

Before:

```python
    return GitHubAuditConfig(
        allowed_repos=list(cfg.allowed_repos),
        allow_force_push=cfg.allow_force_push,
        require_pr_review=cfg.require_pr_review,
    )
```

After:

```python
    return GitHubAuditConfig(
        allowed_repos=list(cfg.allowed_repos),
        allowed_repos_mode=cfg.allowed_repos_mode,
        allow_force_push=cfg.allow_force_push,
        require_pr_review=cfg.require_pr_review,
    )
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/security_audit_config.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/security_audit_config.py` | no new errors |
