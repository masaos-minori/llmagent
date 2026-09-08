# Implementation Procedure: Add INV-07 integration test

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: tests/agent/shared/test_startup_validation_pipeline.py

## Goal
Add integration test mapping to ADR-004 INV-07 in `tests/agent/shared/test_startup_validation_pipeline.py`.

## Priority
Medium

## Scope
- **In-Scope**: Add integration test mapping to ADR-004 INV-07
- **Out-of-Scope**: Any other test_startup_validation_pipeline.py behavior change

## Background
No existing integration test for INV-07 (REQ-006; Acceptance criterion 4). The new test must map to ADR-004's INV-07 scenario.

## Problem
No integration test exists to verify INV-07 compliance.

## Reason for change
This is a test coverage addition — INV-07 must be tested to prevent regression.

## Implementation Steps

### Step 1: Understand the current test structure
Read `tests/agent/shared/test_startup_validation_pipeline.py` to understand the existing test patterns and fixtures.
Expected outcome: Identify how to add a new test following the existing conventions.

### Step 2: Locate INV-07 definition in ADR-004
Read `docs/adr/ADR-004-environment-failure-handling-policy.md` to find the INV-07 row and understand what it requires.
Expected outcome: Document the INV-07 requirements.

### Step 3: Create the INV-07 integration test
Add a test like:
```python
def test_inv07_environment_failure_handling():
    """Integration test mapping to ADR-004 INV-07."""
    # Implement based on INV-07 requirements
    ...
```
Expected outcome: Test maps to INV-07 requirements.

### Step 4: Run targeted pytest run
Run: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py::test_inv07_environment_failure_handling -q`
Expected outcome: New test passes.

### Step 5: Run full test suite for the file
Run: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -q`
Expected outcome: All tests pass.

## Acceptance criteria
- [ ] INV-07 integration test added
- [ ] Test maps to INV-07 requirements
- [ ] Targeted pytest run passes
- [ ] Full test suite passes
- [ ] REQ-006 satisfied

## Tests
New integration test for INV-07 in `tests/agent/shared/test_startup_validation_pipeline.py`.

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-006: INV-07 status updated
- Related target file: docs/adr/ADR-004-environment-failure-handling-policy.md (INV-07 definition)

## Assumptions
- The test follows the existing pytest conventions in the file
- The INV-07 requirements can be implemented as an integration test

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the INV-07 requirements can be adequately tested as an integration test | Need to review INV-07 definition | Read ADR-004 | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (test coverage addition).

## Design
This is a Path A task (single file, test coverage addition). The approach is simple: add a new test following the existing conventions, mapping to INV-07 requirements.

## Alternatives considered
- Adding the test as a unit test — rejected because INV-07 is an integration-level concern
- Using parametrize to test multiple scenarios — rejected because the single INV-07 case is sufficient

## Compatibility considerations
- The test should work with existing pytest fixtures
- The test should not require external dependencies (e.g., actual MCP servers)

## Rollback considerations
- If the test fails due to missing INV-07 implementation, revert the test and investigate further

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Understand current test structure | Pending | — | — | |
| 2 | Locate INV-07 definition | Pending | — | — | |
| 3 | Create INV-07 integration test | Pending | — | — | |
| 4 | Run targeted pytest run | Pending | — | — | |
| 5 | Run full test suite | Pending | — | — | |

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
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: tests/agent/shared/test_startup_validation_pipeline.py

(End of file - total 100 lines)
