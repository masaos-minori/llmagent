# Implementation Procedure: tests/agent/shared/test_startup_validation_pipeline.py

## Goal

Reorganize `tests/agent/shared/test_startup_validation_pipeline.py` to align test classes/functions alongside their corresponding new modules/classes, matching the module layout established by the six extracted concerns.

## Scope

- Move test classes/functions in `test_startup_validation_pipeline.py` to match the new module structure
- Preserve all existing test behavior — no behavioral changes to test assertions
- Align test class/function names with the new module/class naming convention

## Assumptions

- The following test classes/functions exist in `test_startup_validation_pipeline.py`:
  - `test_validation_result_empty_has_no_fatal` → stays (StartupValidationResult unit test)
  - `test_validation_result_fatal_detected` → stays (StartupValidationResult unit test)
  - `test_validation_result_multiple_fatals_collected` → stays (StartupValidationResult unit test)
  - `test_validation_result_warnings_only_no_fatal` → stays (StartupValidationResult unit test)
  - `test_validation_result_skipped_not_fatal` → stays (StartupValidationResult unit test)
  - `mock_ctx` fixture → stays (shared fixture for validation pipeline tests)
  - `startup_instance` fixture → stays (shared fixture for validation pipeline tests)
  - `test_all_checks_pass_no_raise` → should move to `test_startup_validation_pipeline.py`
  - `test_single_fatal_readiness_raises` → should move to `test_startup_validation_pipeline.py`
  - `test_security_audit_fatal_remaining_checks_still_run` → should move to `test_startup_validation_pipeline.py`
  - `test_multiple_fatals_all_in_error_message` → should move to `test_startup_validation_pipeline.py`
  - `test_warnings_only_no_raise` → should move to `test_startup_validation_pipeline.py`
  - `test_routing_drift_strict_true_raises_fatal` → should move to `test_startup_validation_pipeline.py`
  - `test_routing_drift_strict_false_warns_only` → should move to `test_startup_validation_pipeline.py`
  - `test_skipped_live_routing_no_raise` → should move to `test_startup_validation_pipeline.py`

## Design decisions

- **One test file per new module**: Each extracted module gets its own dedicated test file.
- **Preserve helper functions**: `mock_ctx`, `startup_instance` fixtures stay in appropriate files based on usage.
- **No test logic changes**: Only move code, do not modify test assertions or behavior.

## Alternatives considered

- **Keep all tests in one file**: Rejected: defeats the purpose of REQ-015 (align test structure with new module layout).
- **Rename existing test classes/functions**: Rejected: would break test discovery and CI pipelines that reference specific class/function names.

## Implementation

### Target file

`tests/agent/shared/test_startup_validation_pipeline.py`

### Procedure

Move test classes/functions to their corresponding new test files.

### Method

File modification (move sections).

### Details

**Phase 4: Test Reorganization** (REQ-015)

1. In `test_startup_validation_pipeline.py`, remove the following test classes/functions (they will be moved to separate files):
   - `test_all_checks_pass_no_raise` (lines 82–104)
   - `test_single_fatal_readiness_raises` (lines 108–135)
   - `test_security_audit_fatal_remaining_checks_still_run` (lines 139–165)
   - `test_multiple_fatals_all_in_error_message` (lines 169–202)
   - `test_warnings_only_no_raise` (lines 206–228)
   - `test_routing_drift_strict_true_raises_fatal` (lines 232–259)
   - `test_routing_drift_strict_false_warns_only` (lines 263–289)
   - `test_skipped_live_routing_no_raise` (lines 293–313)

2. Keep in `test_startup_validation_pipeline.py`:
   - Helper functions (`mock_ctx`, `startup_instance` fixtures)
   - Any imports needed by remaining tests

3. Create/move test classes/functions to corresponding files:
   - Startup validation pipeline integration tests → `tests/agent/shared/test_startup_validation_pipeline.py`

## Compatibility considerations

- **Critical**: All test assertions must remain identical. No behavioral changes to test outcomes.
- **Import paths**: After moving test classes/functions, update imports to reference new module locations.
- **Helper function placement**: `mock_ctx`, `startup_instance` may need to be duplicated or imported into moved test files depending on which tests use them.

## Security considerations

- No security-sensitive changes. Test files contain no secrets or credentials.
- `_mask_secrets` is not called in test files.
- `StartupInterrupted` exception handling in tests must remain unchanged.

## Rollback considerations

- If reorganization breaks test discovery, revert to original `test_startup_validation_pipeline.py` structure.
- Restore all removed test classes/functions to `test_startup_validation_pipeline.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `tests/agent/shared/test_startup_validation_pipeline.py` | Integration — validation pipeline tests | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | No new failures |

## Completion criteria

- [ ] Test classes/functions moved to corresponding new test files
- [ ] All test assertions preserved verbatim
- [ ] Import paths updated for moved test classes/functions
- [ ] `ruff`, `mypy`, `bandit` clean on all modified/new test files
- [ ] All four test files pass unchanged in outcome
- [ ] No duplicate test coverage across files

## Out of scope

- Changing test assertions or adding new tests
- Modifying `repl_health.py`, `http_lifecycle.py`, or `factory.py` internals
- Performance optimization

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-015
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: tests/agent/shared/test_startup_validation_pipeline.py
