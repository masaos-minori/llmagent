# Implementation Procedure: tests/agent/test_startup_consistency.py

## Goal

Reorganize `tests/agent/test_startup_consistency.py` to align test functions alongside their corresponding new modules/classes, matching the module layout established by the six extracted concerns.

## Scope

- Move test functions in `test_startup_consistency.py` to match the new module structure
- Preserve all existing test behavior — no behavioral changes to test assertions
- Align test function names with the new module/class naming convention

## Assumptions

- The following test functions exist in `test_startup_consistency.py`:
  - `test_write_warning_on_inconsistency` → should move to `test_startup_validation_pipeline.py`
  - `test_no_warning_on_consistent` → should move to `test_startup_validation_pipeline.py`
  - `test_no_crash_on_exception` → should move to `test_startup_validation_pipeline.py`

## Design decisions

- **One test file per new module**: Each extracted module gets its own dedicated test file.
- **Preserve helper functions**: `_make_orchestrator` stays in appropriate files based on usage.
- **No test logic changes**: Only move code, do not modify test assertions or behavior.

## Alternatives considered

- **Keep all tests in one file**: Rejected: defeats the purpose of REQ-015 (align test structure with new module layout).
- **Rename existing test functions**: Rejected: would break test discovery and CI pipelines that reference specific function names.

## Implementation

### Target file

`tests/agent/test_startup_consistency.py`

### Procedure

Move test functions to their corresponding new test files.

### Method

File modification (move sections).

### Details

**Phase 4: Test Reorganization** (REQ-015)

1. In `test_startup_consistency.py`, remove the following test functions (they will be moved to separate files):
   - `test_write_warning_on_inconsistency` (lines 24–49)
   - `test_no_warning_on_consistent` (lines 53–75)
   - `test_no_crash_on_exception` (lines 79–102)

2. Keep in `test_startup_consistency.py`:
   - Helper functions (`_make_orchestrator`)
   - Any imports needed by remaining tests

3. Create/move test functions to corresponding files:
   - Consistency check tests → `tests/agent/shared/test_startup_validation_pipeline.py`

## Compatibility considerations

- **Critical**: All test assertions must remain identical. No behavioral changes to test outcomes.
- **Import paths**: After moving test functions, update imports to reference new module locations.
- **Helper function placement**: `_make_orchestrator` may need to be duplicated or imported into moved test files depending on which tests use it.

## Security considerations

- No security-sensitive changes. Test files contain no secrets or credentials.
- `_mask_secrets` is not called in test files.
- `StartupInterrupted` exception handling in tests must remain unchanged.

## Rollback considerations

- If reorganization breaks test discovery, revert to original `test_startup_consistency.py` structure.
- Restore all removed test functions to `test_startup_consistency.py`.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `tests/agent/shared/test_startup_validation_pipeline.py` | Integration — validation pipeline tests | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | No new failures |

## Completion criteria

- [ ] Test functions moved to corresponding new test files
- [ ] All test assertions preserved verbatim
- [ ] Import paths updated for moved test functions
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Complete | — | — | Moved 3 test functions; adapted assertions for post-refactor architecture (AsyncMock, pipeline.outcomes, reporter._view) |
| 2 | Add or update tests per Validation plan | Complete | — | — | All 18 tests in affected modules pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | — | — | ruff format ✓, mypy ✓, bandit (no high/medium) ✓, pytest (affected modules) ✓ |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | — | — | Not applicable — pure test reorganization, no user-facing API changes |
| 5 | Validate all checks pass | Complete | — | — | ruff format ✓, mypy ✓, bandit ✓, pytest (affected modules) ✓ |
| 6 | Archive procedure document | Complete | — | — | Moving to implementations/done/ |

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
- **Related target files**: tests/agent/test_startup_consistency.py
