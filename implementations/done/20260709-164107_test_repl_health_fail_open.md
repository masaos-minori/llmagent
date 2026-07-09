# Implementation: tests/test_repl_health.py — Add 3 fail_open audit tests

## Goal

Add 3 tests to `TestAuditSecurityDefaults` in `test_repl_health.py` covering the new `allowed_repos_mode="fail_open"` production fail-fast check.

## Scope

- `tests/test_repl_health.py` only.
- Three new test methods in `TestAuditSecurityDefaults`:
  1. `test_github_fail_open_raises_in_production`
  2. `test_github_fail_open_warns_in_local`
  3. `test_github_fail_closed_no_error_in_production`

## Assumptions

1. `_make_ctx(servers=..., security_profile=...)` helper exists in the test class.
2. `GitHubAuditConfig(...)` constructor now includes `allowed_repos_mode` field.
3. The existing `patch` patterns for `load_github_audit_config` are the correct template.

## Implementation

### Target file

`tests/test_repl_health.py`

### Procedure

Add 3 test methods to `TestAuditSecurityDefaults`.

### Details

#### Test 1: `test_github_fail_open_raises_in_production`

```python
def test_github_fail_open_raises_in_production(self) -> None:
    ctx = self._make_ctx(
        servers={"svc": {"auth_token": "tok"}}, security_profile="production"
    )
    gh_cfg = GitHubAuditConfig(
        allowed_repos=[], allowed_repos_mode="fail_open",
        allow_force_push=False, require_pr_review=True,
    )
    with (
        patch("agent.repl_health.load_shell_audit_config", return_value=None),
        patch("agent.repl_health.load_git_audit_config", return_value=None),
        patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
        patch("agent.repl_health.load_cicd_audit_config", return_value=None),
    ):
        with pytest.raises(RuntimeError, match="fail_open"):
            audit_security_defaults(ctx, production_mode=True)
```

#### Test 2: `test_github_fail_open_warns_in_local`

```python
def test_github_fail_open_warns_in_local(self) -> None:
    ctx = self._make_ctx(servers={"svc": {"auth_token": "tok"}})
    gh_cfg = GitHubAuditConfig(
        allowed_repos=[], allowed_repos_mode="fail_open",
        allow_force_push=False, require_pr_review=True,
    )
    with (
        patch("agent.repl_health.load_shell_audit_config", return_value=None),
        patch("agent.repl_health.load_git_audit_config", return_value=None),
        patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
        patch("agent.repl_health.load_cicd_audit_config", return_value=None),
    ):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("fail_open" in w for w in warnings)
```

#### Test 3: `test_github_fail_closed_no_error_in_production`

```python
def test_github_fail_closed_no_error_in_production(self) -> None:
    ctx = self._make_ctx(
        servers={"svc": {"auth_token": "tok"}}, security_profile="production"
    )
    gh_cfg = GitHubAuditConfig(
        allowed_repos=["owner/repo"], allowed_repos_mode="fail_closed",
        allow_force_push=False, require_pr_review=True,
    )
    with (
        patch("agent.repl_health.load_shell_audit_config", return_value=None),
        patch("agent.repl_health.load_git_audit_config", return_value=None),
        patch("agent.repl_health.load_github_audit_config", return_value=gh_cfg),
        patch("agent.repl_health.load_cicd_audit_config", return_value=None),
    ):
        audit_security_defaults(ctx, production_mode=True)  # must not raise
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New tests | `uv run pytest tests/test_repl_health.py -k fail_open -v` | all 3 pass |
| Lint | `uv run ruff check tests/test_repl_health.py` | 0 errors |
