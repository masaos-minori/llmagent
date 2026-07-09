# Implementation: repl_health.py — Add production fail-fast check for `allowed_repos_mode="fail_open"`

## Goal

Add a production-mode `RuntimeError` (warning in local mode) when `allowed_repos_mode="fail_open"` is detected in `audit_security_defaults()`.

## Scope

- `scripts/agent/repl_health.py` only.
- One new check block inserted after the existing `fail_closed_empty.append("github.allowed_repos")` block.

## Assumptions

1. `github_cfg` is already loaded at the insertion point (line ~804, reused from the `allowed_repos`-empty check).
2. The existing `shell_sandbox_backend == "none"` pattern (raise in production, warn in local) is the correct template.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

Insert the following block immediately after the existing `if fail_closed_empty or fail_open_empty:` block:

```python
    if github_cfg is not None and github_cfg.allowed_repos_mode == "fail_open":
        msg = (
            "github.allowed_repos_mode='fail_open' is not permitted in production mode. "
            "Set allowed_repos_mode='fail_closed' in github_mcp_server.toml."
        )
        if production_mode:
            raise RuntimeError(msg)
        logger.warning("Security: %s", msg)
        warnings.append(f"Security: {msg}")
```

### Method

Single in-place edit. No new functions.

### Details

The check mirrors the existing `shell_sandbox_backend == "none"` pattern (lines ~732-737) which raises in production mode and warns in local mode.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py` | no new errors |
