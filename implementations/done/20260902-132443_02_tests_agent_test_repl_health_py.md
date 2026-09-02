## Goal

Update `test_shell_sandbox_none_warns` and `test_shell_sandbox_none_raises_in_production` so both assert `RuntimeError` is raised for `shell_sandbox_backend == "none"` regardless of `production_mode` value. Replace the current warning-only assertion for the non-production case with a `pytest.raises(RuntimeError)` assertion. (REQ-002; AC-2)

## Scope

- Modify exactly two test methods in `tests/agent/test_repl_health.py`:
  - `test_shell_sandbox_none_warns` — change from asserting warning-only to asserting `RuntimeError`
  - `test_shell_sandbox_none_raises_in_production` — keep as-is (already asserts `RuntimeError`)
- Consider consolidating into a single parametrized test covering both `production_mode` values

## Assumptions

- The test infrastructure (mocking, fixtures) remains unchanged — only the assertions need updating
- `ShellAuditConfig(sandbox_backend="none", command_allowlist=["ls"])` is still valid for constructing the test fixture
- The error message regex `"Production mode requires shell sandbox"` may need updating if the message text changes in the source code (REQ-001)

## Design decisions

- Option A (preferred): consolidate into a single parametrized test using `pytest.mark.parametrize("production_mode", [True, False])` — eliminates duplication and makes the equivalence explicit
- Option B: keep two separate tests, updating `test_shell_sandbox_none_warns` to use `pytest.raises(RuntimeError, match=...)` instead of the warning assertion
- Choice: Option A — cleaner and more maintainable

## Alternatives considered

- Keeping two separate tests with identical assertions — rejected as unnecessary duplication when a parametrized approach covers both cases identically
- Using different `match` patterns for each `production_mode` value — rejected because the message text should be consistent across environments once REQ-001 lands

## Compatibility considerations

- Test behavior changes: the previously-passing `test_shell_sandbox_none_warns` will now fail until updated — this is intentional and expected
- If REQ-001's message text change is applied first, the `match=` pattern in the test must be updated accordingly

## Security considerations

- No security impact — this is a test update reflecting the corrected behavior

## Rollback considerations

- To roll back: revert the test assertions to their previous state (warning-only for `production_mode=False`, RuntimeError for `production_mode=True`)

## Validation plan

### Unit test validation
- Run `uv run pytest tests/agent/test_repl_health.py -v` — all tests pass, including the updated `shell_sandbox_backend == "none"` assertions for both `production_mode` values
- Specifically verify: `test_shell_sandbox_none_warns` and `test_shell_sandbox_none_raises_in_production` both assert `RuntimeError`

### Coverage
- `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — >= 90% diff coverage on changed lines

## Completion criteria

- [ ] `test_shell_sandbox_none_warns` asserts `RuntimeError` is raised (not just a warning) when `production_mode=False`
- [ ] `test_shell_sandbox_none_raises_in_production` continues to assert `RuntimeError` when `production_mode=True`
- [ ] Both tests cover `shell_sandbox_backend == "none"` identically regardless of `production_mode`
- [ ] `uv run pytest tests/agent/test_repl_health.py -v` passes with no failures
- [ ] diff coverage >= 90% on changed lines

## Out of scope

- Modifying any other test methods in this file
- Adding new test cases beyond the two existing ones
- Changes to test infrastructure or fixtures

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `test_shell_sandbox_none_warns` and `test_shell_sandbox_none_raises_in_production` to assert `RuntimeError` for both `production_mode` values | Done | 2026-09-02 | 2026-09-02 | Updated both tests; also patched `shutil.which` for firejail PATH check |
| 2 | Run `uv run pytest tests/agent/test_repl_health.py -v` and confirm all tests pass | Done | 2026-09-02 | 2026-09-02 | All 24 TestAuditSecurityDefaults tests pass |
| 3 | Run diff coverage check on changed lines | Done | 2026-09-02 | 2026-09-02 | Covered |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002; AC-2
- **Source issue**: issues/20260831-192510_adr004_07_shell_mcp_sandbox_production_only_enforcement.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-104253_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-132443
- **Related target files**: tests/agent/test_repl_health.py
