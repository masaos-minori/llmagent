# Implementation: Update GitHubAuditConfig construction sites in 2 test files

## Goal

Add `allowed_repos_mode="fail_closed"` to the 2 remaining `GitHubAuditConfig(...)` direct construction sites that are not covered by the `test_repl_health.py` changes.

## Scope

- `tests/test_security_audit_config_isolation.py` (~line 132-143)
- `tests/test_audit_security_failures.py` (line 25)

## Assumptions

1. Both files construct `GitHubAuditConfig` without the `allowed_repos_mode` keyword, which will cause `TypeError` once the new required field is added.

## Implementation

### Target files

1. `tests/test_security_audit_config_isolation.py`
2. `tests/test_audit_security_failures.py`

### Procedure

#### File 1: `tests/test_security_audit_config_isolation.py`

Add `mock_cfg.allowed_repos_mode = "fail_closed"` alongside the other `mock_cfg.*` assignments, and add `allowed_repos_mode="fail_closed"` to the expected `GitHubAuditConfig(...)` equality check.

#### File 2: `tests/test_audit_security_failures.py`

Add `allowed_repos_mode="fail_closed"` to the `_GITHUB_OK` fixture.

### Details

#### Change 1: `tests/test_security_audit_config_isolation.py` (~line 132-143)

Before:

```python
mock_cfg.allowed_repos = ["owner/repo"]
mock_cfg.allow_force_push = False
mock_cfg.require_pr_review = True
```

After:

```python
mock_cfg.allowed_repos = ["owner/repo"]
mock_cfg.allowed_repos_mode = "fail_closed"
mock_cfg.allow_force_push = False
mock_cfg.require_pr_review = True
```

And add `allowed_repos_mode="fail_closed"` to the expected `GitHubAuditConfig(...)` equality check.

#### Change 2: `tests/test_audit_security_failures.py` (line 25)

Before:

```python
_GITHUB_OK = GitHubAuditConfig(
    allowed_repos=["ok/repo"],
    allow_force_push=False,
    require_pr_review=True,
)
```

After:

```python
_GITHUB_OK = GitHubAuditConfig(
    allowed_repos=["ok/repo"],
    allowed_repos_mode="fail_closed",
    allow_force_push=False,
    require_pr_review=True,
)
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_security_audit_config_isolation.py tests/test_audit_security_failures.py` | 0 errors |
| Regression | `uv run pytest tests/test_security_audit_config_isolation.py tests/test_audit_security_failures.py -v` | all pass |
