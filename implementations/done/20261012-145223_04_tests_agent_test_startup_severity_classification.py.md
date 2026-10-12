## Goal
- Add pipeline-level tests for the new severity rule of an unexpected drift-check failure, and pin the unchanged RuntimeError and safety-tier behavior (`REQ-004`).

## Scope
- Only `tests/agent/test_startup_severity_classification.py`: new tests in the existing routing-drift section of the test class.

## Assumptions
- The helpers _run_check_services and _make_startup_ctx are reused; the context is a mock, so routing_drift_strict must be set explicitly in every new test (an unset mock attribute is truthy).
- A FATAL outcome makes the run return a non-empty exception value, as the neighbouring FATAL tests assert.

## Design decisions
- Drive the real check_services through _run_check_services with check_routing_drift replaced by a mock that raises, and assert on the recorded outcomes for the routing_drift source.
- Include the unreadable-strictness case by giving the tool configuration a mock with no attributes, so reading the setting raises AttributeError.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_startup_severity_classification.py`

### Procedure
1. After the existing drift tests add test_routing_drift_unexpected_failure_is_fatal_when_strict: set routing_drift_strict to True on the context, make check_routing_drift raise ValueError("boom"); assert the returned exception is not None and a FATAL outcome exists for routing_drift.
2. Add test_routing_drift_unexpected_failure_is_warning_when_not_strict: strict False; assert the exception is None and exactly one WARNING outcome exists for routing_drift, none FATAL.
3. Add test_routing_drift_runtime_error_is_fatal_regardless_of_strict: strict False, RuntimeError raised; assert FATAL.
4. Add test_routing_drift_unreadable_strictness_is_fatal: replace the tool configuration with a mock that has no attributes; check_routing_drift raises ValueError; assert FATAL.
5. Add test_routing_safety_tiers_unexpected_failure_is_fatal after the safety-tier tests: check_routing_safety_tiers raises ValueError; assert FATAL for routing_safety_tiers (pins block 5b).
6. Run the new tests against the unmodified production code: the strict and unreadable-strictness cases fail; the non-strict case (the pipeline tests mock the drift check, so the existing outer handler already gives a WARNING), the RuntimeError case, and the safety-tier case pass because they pin existing behavior.

### Method
- Follow the existing pattern: build the context with _make_startup_ctx, run with _run_check_services, filter outcomes by source, assert on the status.

### Details
- Use pytest.mark.asyncio as the neighbouring tests do.
- Status comparisons use the StartupCheckStatus enum already imported in this module.
- Do not touch existing tests or helpers.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_severity_classification.py -v`; before procedures 01 and 02 two of the five new tests fail (strict and unreadable strictness), after them all pass and the existing tests still pass.
- `uv run ruff format --check tests/agent/test_startup_severity_classification.py`, `uv run ruff check tests/agent/test_startup_severity_classification.py`.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05, 06 and 07 (docs); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- Five new tests exist; the two new-policy ones (strict and unreadable strictness) fail on the old code and all five pass after procedures 01 and 02; existing tests are unchanged and pass.

## Out of scope
- Function-level tests (procedure 03), other check blocks, and production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the five pipeline-level tests and confirm the new-policy cases fail on the unmodified code | Completed | 20261012-145624 | 20261012-145654 | stale_detector clean changed: tests/agent/test_startup_severity_classification.py (+5 tests); procedure corrected: 2 of 5 fail on the old code (strict, unreadable); non-strict, RuntimeError, safety-tier pin existing behavior |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-145743 | 20261012-145743 | ruff format/check pass; all 5 new tests pass after procedures 01 and 02 |

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
- **Requirement ID**: `REQ-004` (pipeline-level tests)
- **Source issue**: issues/20261012-124829_start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-144923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-145223
- **Related target files**: tests/agent/test_startup_severity_classification.py