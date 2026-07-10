# Implementation: Remove fail_open-specific tests in production-validator and audit-config test files (Phase A-3)

## Goal

Delete tests that exist solely to exercise the removed `allowed_repos_mode`/`fail_open` validation paths, and strip the now-nonexistent `allowed_repos_mode` keyword from `GitHubAuditConfig` constructions elsewhere, so `tests/test_production_config_validator.py`, `tests/test_repl_health.py`, `tests/test_audit_security_failures.py`, and `tests/test_security_audit_config_isolation.py` keep passing after Phase A-1's field removal.

## Scope

**In:**
- `tests/test_production_config_validator.py`: delete `class TestProductionConfigValidatorGitHubFailOpen` (lines 189-218, 4 tests) and `class TestProductionConfigValidatorValidateGithubFailOpen` (lines 239-258, 3 tests) in full
- `tests/test_repl_health.py`: delete `test_github_fail_open_raises_in_production` and `test_github_fail_open_warns_in_local` (both construct `GitHubAuditConfig(allowed_repos_mode="fail_open", ...)`, which becomes a `TypeError` once the field is removed)
- `tests/test_audit_security_failures.py`: remove `allowed_repos_mode="fail_closed",` from the module-level `_GITHUB_OK = GitHubAuditConfig(...)` constant
- `tests/test_security_audit_config_isolation.py`: remove `mock_cfg.allowed_repos_mode = "fail_closed"` and `allowed_repos_mode="fail_closed",` from `test_load_github_audit_config_success`

**Out:**
- Any other test in these four files unrelated to `allowed_repos_mode` — untouched
- `TestProductionConfigValidatorSecurityProfileEnum` (lines 221-236) — sits between the two classes being deleted but is unrelated; must survive the edit intact

## Assumptions

1. `TestProductionConfigValidatorGitHubFailOpen` and `TestProductionConfigValidatorValidateGithubFailOpen` contain no test that also covers still-valid behavior (e.g., non-fail_open assertions) — confirmed by reading all 7 test bodies: every one of them either asserts on `"fail_open" in err/warn` or calls `validate_github_fail_open(...)` directly, both of which cease to exist after Phase A-1.
2. `_GITHUB_OK` in `test_audit_security_failures.py` is used only via `return_value=_GITHUB_OK` mocking (2 call sites) — no test asserts on `_GITHUB_OK.allowed_repos_mode` directly, so removing the constructor kwarg is safe.
3. `test_load_github_audit_config_success` in `test_security_audit_config_isolation.py` asserts `result == GitHubAuditConfig(...)` via dataclass equality — removing `allowed_repos_mode` from both the `mock_cfg` stub and the expected `GitHubAuditConfig(...)` call keeps the equality check meaningful (both sides drop the field together).

## Implementation

### Target file

1. `tests/test_production_config_validator.py`
2. `tests/test_repl_health.py`
3. `tests/test_audit_security_failures.py`
4. `tests/test_security_audit_config_isolation.py`

### Procedure

1. In `test_production_config_validator.py`, delete the two classes verbatim:
   ```python
   class TestProductionConfigValidatorGitHubFailOpen:
       """Tests for GitHub allowed_repos_mode='fail_open' check."""
       # ... 4 tests ...
   ```
   and
   ```python
   class TestProductionConfigValidatorValidateGithubFailOpen:
       """Tests for standalone validate_github_fail_open method."""
       # ... 3 tests ...
   ```
   Leave `TestProductionConfigValidatorSecurityProfileEnum` (positioned between them) untouched.
2. In `test_repl_health.py`, delete `test_github_fail_open_raises_in_production` and `test_github_fail_open_warns_in_local` in full (each constructs a `GitHubAuditConfig` with the removed field and asserts on `"fail_open"` in the resulting error/warning).
3. In `test_audit_security_failures.py`, change:
   ```python
   _GITHUB_OK = GitHubAuditConfig(
       allowed_repos=["owner/repo"],
       allowed_repos_mode="fail_closed",
       allow_force_push=False,
       require_pr_review=True,
   )
   ```
   to:
   ```python
   _GITHUB_OK = GitHubAuditConfig(
       allowed_repos=["owner/repo"],
       allow_force_push=False,
       require_pr_review=True,
   )
   ```
4. In `test_security_audit_config_isolation.py`'s `test_load_github_audit_config_success`, remove `mock_cfg.allowed_repos_mode = "fail_closed"` and the corresponding `allowed_repos_mode="fail_closed",` line in the expected `GitHubAuditConfig(...)` on the assertion's right-hand side.
5. Run `grep -rn "allowed_repos_mode\|fail_open\|validate_github_fail_open" tests/test_production_config_validator.py tests/test_repl_health.py tests/test_audit_security_failures.py tests/test_security_audit_config_isolation.py` — expect 0 matches.

### Method

Direct deletion of self-contained test classes/functions, plus keyword-argument removal at 2 call sites where the field is only used as fixture noise, not as a test assertion target.

### Details

- `TestProductionConfigValidatorGitHubFailOpen`'s `test_fail_closed_no_issue` and `test_no_fail_open_param_no_issue` do not need to be "salvaged" into new fail-closed-only tests — the underlying validator no longer has any GitHub-related branch at all after Phase A-1, so there is nothing left in `ProductionConfigValidator.validate()` for a GitHub-specific test to cover; general non-GitHub validator behavior remains covered by the surviving classes (`TestProductionConfigValidatorStrictKeys`, etc.).
- `test_audit_security_failures.py` and `test_security_audit_config_isolation.py` needed inclusion in this document even though the original work plan listed them as "vestigial cleanup (optional)" — they are not optional: `GitHubAuditConfig` is a real dataclass, and passing an unknown keyword argument (`allowed_repos_mode=`) after the field is removed raises `TypeError` at collection/call time, so these two files must be fixed for the test suite to even import correctly.

## Validation plan

```bash
uv run ruff check tests/test_production_config_validator.py tests/test_repl_health.py \
  tests/test_audit_security_failures.py tests/test_security_audit_config_isolation.py
uv run mypy tests/test_production_config_validator.py tests/test_repl_health.py \
  tests/test_audit_security_failures.py tests/test_security_audit_config_isolation.py
uv run pytest tests/test_production_config_validator.py tests/test_repl_health.py \
  tests/test_audit_security_failures.py tests/test_security_audit_config_isolation.py -v
grep -rn "allowed_repos_mode\|validate_github_fail_open" tests/   # expect no output
```

Expected outcome: all four files pass with no collection errors; zero remaining references to the removed field or method anywhere under `tests/`.
