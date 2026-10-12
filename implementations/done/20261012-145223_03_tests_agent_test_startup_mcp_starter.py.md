## Goal
- Add function-level tests that an unexpected failure propagates out of check_routing_drift in strict and non-strict mode (`REQ-004`).

## Scope
- Only `tests/agent/test_startup_mcp_starter.py`: new tests placed after the existing strict-mode drift tests, and one extra import if missing.

## Assumptions
- The helper _make_ctx and the registry reset in setup_function are reused as they are.
- check_routing_drift imports the validation function from the shared routing validation module at call time, so patching that module attribute reaches it.

## Design decisions
- Patch the validation function to raise ValueError and assert the same exception comes out, which proves nothing is swallowed.
- Cover both strict and non-strict, because strict-mode behavior must still reserve RuntimeError for detected drift.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_startup_mcp_starter.py`

### Procedure
1. Add the patch name to the existing import from unittest.mock if it is not imported yet.
2. Add test_routing_drift_unexpected_error_propagates_when_non_strict: patch shared.tool_routing_validation.validate_routing_against_config with a side effect of ValueError("boom"); call check_routing_drift with a ctx from _make_ctx and strict False; expect pytest.raises(ValueError, match="boom").
3. Add test_routing_drift_unexpected_error_propagates_when_strict: same patch, strict True; expect ValueError, not RuntimeError.
4. Leave the three existing tests untouched.
5. Run the two new tests against the unmodified production code and confirm they fail (the old handler returns an empty list instead of raising).

### Method
- Use unittest.mock.patch as a context manager inside each test; keep the registry reset call at the start like the neighbouring tests.

### Details
- Place the new tests under the existing section comment for strict mode, after test_routing_drift_no_drift_returns_empty, before the Bearer-token section.
- Use only plain names for the new tests; no helper is needed.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_starter.py -v`; before procedure 01 the two new tests fail, after it they pass and the three existing tests still pass.
- `uv run ruff format --check tests/agent/test_startup_mcp_starter.py`, `uv run ruff check tests/agent/test_startup_mcp_starter.py`.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05, 06 and 07 (docs); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- Two new tests exist; they fail on the old code and pass after procedure 01; existing tests are unchanged and pass.

## Out of scope
- Pipeline-level behavior (procedure 04) and any production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two function-level tests and confirm they fail on the unmodified code | Completed | 20261012-145609 | 20261012-145624 | stale_detector clean; applied first (mutation precondition) changed: tests/agent/test_startup_mcp_starter.py (+2 tests, +patch import); both fail on the unmodified code (mutation precondition met) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-145743 | 20261012-145743 | ruff format/check pass; 7 tests pass after procedure 01 (2 new ones failed before) |

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
- **Requirement ID**: `REQ-004` (function-level tests)
- **Source issue**: issues/20261012-124829_start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-144923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-145223
- **Related target files**: tests/agent/test_startup_mcp_starter.py