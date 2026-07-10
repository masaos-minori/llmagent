# Implementation: Remove `allowed_repos_mode="fail_open"` from GitHubConfig and its validators (Phase A-1)

## Goal

Remove the `allowed_repos_mode` field and its `fail_open` branch entirely from the GitHub MCP security model, making fail-closed (empty `allowed_repos` = deny all) the only behavior — no configurable mode remains.

## Scope

**In:**
- `scripts/mcp/github/models_config.py`: remove `allowed_repos_mode: str = "fail_closed"` field from `GitHubConfig` and its line in `from_dict()`
- `scripts/mcp/github/service_security.py`: simplify `_assert_allowed_repo()` — remove the `mode` variable and its branch; the function becomes `if not allowed: raise GitHubAuthorizationError(...)` unconditionally
- `scripts/agent/security_audit_config.py`: remove `allowed_repos_mode: str` field from `GitHubAuditConfig` and the corresponding line in `load_github_audit_config()`
- `scripts/agent/repl_health.py`: remove the `allowed_repos_mode` extraction (`allowed_repos_mode: str | None = None`, `if github_cfg is not None: allowed_repos_mode = github_cfg.allowed_repos_mode`) and its pass-through as a keyword argument to `ProductionConfigValidator().validate(...)`
- `scripts/shared/production_config_validator.py`: remove the `allowed_repos_mode` parameter from `validate()`, remove the "GitHub allowed_repos_mode check" block inside it, and remove the standalone `validate_github_fail_open()` method entirely
- `config/github_mcp_server.toml`: remove the `allowed_repos_mode = "fail_closed"` line and its comment block; rewrite the `allowed_repos` comment to describe fail-closed-only behavior (empty list = deny all, no mode to configure)

**Out:**
- `allowed_repos` itself (the allowlist) — unchanged, still governs which repos are permitted
- Any other MCP server's allowlist pattern (cicd-mcp's `repo_allowlist`, git-mcp's `allowed_repo_paths`) — these do not have a `mode` concept and are unaffected

## Assumptions

1. `config/github_mcp_server.toml` already sets `allowed_repos_mode = "fail_closed"` explicitly — this repository's own deployment is unaffected by removing the "fail_open" option.
2. No other module besides the five listed above references `GitHubConfig.allowed_repos_mode`, `GitHubAuditConfig.allowed_repos_mode`, or `ProductionConfigValidator.validate_github_fail_open` — confirmed via `grep -rn "allowed_repos_mode" scripts/`.
3. `_assert_allowed_repo()`'s `mode` branch only affects behavior when `allowed_repos` is empty; when non-empty, the branch is already unreachable in practice — removing it introduces no behavior change for any config with a non-empty `allowed_repos` list.

## Implementation

### Target file

1. `scripts/mcp/github/models_config.py`
2. `scripts/mcp/github/service_security.py`
3. `scripts/agent/security_audit_config.py`
4. `scripts/agent/repl_health.py`
5. `scripts/shared/production_config_validator.py`
6. `config/github_mcp_server.toml`

### Procedure

1. In `models_config.py`, delete `allowed_repos_mode: str = "fail_closed"` from the `GitHubConfig` dataclass body and `allowed_repos_mode=_get_str(d, "allowed_repos_mode", "fail_closed"),` from `from_dict()`.
2. In `service_security.py`, rewrite `_assert_allowed_repo()`:
   ```python
   def _assert_allowed_repo(self, owner: str, repo: str) -> None:
       """Raise GitHubAuthorizationError if owner/repo is not permitted.

       Empty allowed_repos denies all repositories (fail-closed).
       """
       from mcp.github.models_config import (  # noqa: PLC0415
           GitHubAuthorizationError,
       )

       allowed = self._cfg.allowed_repos
       slug = f"{owner}/{repo}"
       if not allowed:
           raise GitHubAuthorizationError(
               f"Repository '{slug}' is denied: allowed_repos is empty"
           )
       if slug not in allowed:
           raise GitHubAuthorizationError(f"Repository not in allowed_repos: {slug}")
   ```
3. In `security_audit_config.py`, delete `allowed_repos_mode: str` from `GitHubAuditConfig` and `allowed_repos_mode=cfg.allowed_repos_mode,` from `load_github_audit_config()`.
4. In `repl_health.py`, delete the `allowed_repos_mode` local variable, its conditional assignment, and the `allowed_repos_mode=allowed_repos_mode,` keyword argument passed to `ProductionConfigValidator().validate(...)`.
5. In `production_config_validator.py`:
   - Remove `allowed_repos_mode: str | None = None` from `validate()`'s signature.
   - Remove the `# GitHub allowed_repos_mode check` block (the `if allowed_repos_mode == "fail_open": ...` section).
   - Remove the entire `validate_github_fail_open()` method.
6. In `config/github_mcp_server.toml`, delete the `allowed_repos_mode` key and its comment; rewrite the `allowed_repos` comment to remove references to `allowed_repos_mode`.
7. Run `grep -rn "allowed_repos_mode" scripts/ config/` — expect 0 matches.

### Method

Direct field/branch removal, following the same "fail-closed unconditional" pattern already used as the default. No new abstractions introduced.

### Details

- `_assert_allowed_repo()`'s new unconditional form is a strict subset of the old `fail_closed` branch — deleting the `mode` check removes the only path (`fail_open`) that could allow an empty `allowed_repos` list to pass.
- `ProductionConfigValidator.validate()` callers (only `repl_health.py`) must drop the `allowed_repos_mode=` keyword in the same commit as the signature change, since Python does not tolerate unknown keyword arguments.

## Validation plan

```bash
uv run ruff check scripts/mcp/github/models_config.py scripts/mcp/github/service_security.py \
  scripts/agent/security_audit_config.py scripts/agent/repl_health.py scripts/shared/production_config_validator.py
uv run mypy scripts/mcp/github/ scripts/agent/security_audit_config.py scripts/agent/repl_health.py scripts/shared/production_config_validator.py
PYTHONPATH=scripts uv run lint-imports
grep -rn "allowed_repos_mode" scripts/ config/   # expect no output
```

Expected outcome: no lint/type/import-layer regressions; zero remaining references to `allowed_repos_mode` in `scripts/` and `config/`. (Test-file updates are handled in the companion implementation documents for Phase A-2 and A-3, since this document's changes alone would break several tests that construct `GitHubConfig`/`GitHubAuditConfig` with the removed field.)
