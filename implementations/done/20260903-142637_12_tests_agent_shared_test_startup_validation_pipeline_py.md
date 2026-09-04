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
  - `test_warnings_only_no_raise` → stays (integration test, uses startup_instance fixture)
  - `test_routing_drift_strict_true_raises_fatal` → stays (integration test, uses startup_instance fixture)
  - `test_routing_drift_strict_false_warns_only` → stays (integration test, uses startup_instance fixture)
  - `test_skipped_live_routing_no_raise` → stays (integration test, uses startup_instance fixture)
  - `test_validation_pipeline_reports_fatal_when_config_missing` → stays (REQ-001 integration test)
  - `test_build_agent_config_requires_agent_toml` → stays (REQ-002 integration test)
  - `test_check_routing_safety_tiers_context` → stays (routing safety tiers test)
  - `TestSafetyTiers` class → stays (safety tiers test class)
- Note: 4 tests (`test_all_checks_pass_no_raise`, `test_single_fatal_readiness_raises`, `test_security_audit_fatal_remaining_checks_still_run`, `test_multiple_fatals_all_in_error_message`) were removed in a prior commit and no longer exist in the codebase.
- The procedure's Phase 4 step 1 and step 3 are contradictory: step 1 says to remove integration tests, step 3 says to keep them. Current state resolves this: integration tests stay because they depend on `startup_instance` fixture and test the pipeline aggregation behavior.

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

Current state (as of HEAD):
- 4 tests already removed in prior commit (no longer exist)
- 4 integration tests remain with rewritten signatures (use mock pipeline instead of real service calls)
- StartupValidationResult unit tests + fixtures + REQ-001/REQ-002 tests + Safety Tiers tests remain

Action: No changes required. The procedure's Phase 4 step 1 is outdated — those tests were already removed. Step 3 correctly states that integration tests belong in `test_startup_validation_pipeline.py`.

Verification:
1. Run `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` — expect 15 passed
2. Run `ruff check tests/agent/shared/test_startup_validation_pipeline.py` — expect clean

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Complete | — | — | No changes needed; procedure was outdated |
| 2 | Add or update tests per Validation plan | Pending | — | — | Verify existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | Procedure was outdated — tests it references were already removed or rewritten | Yes | — |

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
