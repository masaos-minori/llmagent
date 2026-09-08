# Implementation Procedure: Add falsy own_config_file fail-closed test

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: tests/shared/test_config_loader.py

## Goal
Add startup-scenario test asserting falsy `own_config_file` raises in `tests/shared/test_config_loader.py`.

## Priority
High

## Scope
- **In-Scope**: Add test for falsy own_config_file fail-closed path
- **Out-of-Scope**: Any other test_config_loader.py behavior change

## Background
No existing test covers the falsy `own_config_file` fail-closed path (REQ-003; Acceptance criterion 1). The new test must assert that a falsy `own_config_file` value raises an error during startup instead of silently skipping Config Isolation restriction.

## Problem
No test exists to verify the fail-closed behavior when `own_config_file` is falsy.

## Reason for change
This is a test coverage addition — the fail-closed behavior must be tested to prevent regression.

## Implementation Steps

### Step 1: Understand the current test structure
Read `tests/shared/test_config_loader.py` to understand the existing test patterns and fixtures.
Expected outcome: Identify how to add a new test following the existing conventions.

### Step 2: Create the falsy own_config_file test
Add a test like:
```python
def test_falsy_own_config_file_raises():
    """Test that falsy own_config_file raises on startup."""
    server = MCPServer(own_config_file="")  # or None
    with pytest.raises(ValueError):
        server.run_http()
```
Expected outcome: Test asserts ValueError raised when own_config_file is falsy.

### Step 3: Run targeted pytest run
Run: `uv run pytest tests/shared/test_config_loader.py::test_falsy_own_config_file_raises -q`
Expected outcome: New test passes.

### Step 4: Run full test suite for the file
Run: `uv run pytest tests/shared/test_config_loader.py -q`
Expected outcome: All tests pass.

## Acceptance criteria
- [ ] Falsy own_config_file test added
- [ ] Test asserts ValueError raised
- [ ] Targeted pytest run passes
- [ ] Full test suite passes
- [ ] REQ-003 satisfied

## Tests
New unit/integration tests for the falsy-`own_config_file` fail-closed path in `tests/shared/test_config_loader.py`.

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-003: MCPServer.run_http() fails closed when own_config_file is falsy
- Related target file: scripts/mcp_servers/server.py (fail-closed branch must exist first)

## Assumptions
- The test follows the existing pytest conventions in the file
- The MCPServer constructor accepts own_config_file parameter
- The ValueError is raised during run_http(), not during __init__

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the fail-closed branch may cause startup failures in development environments where own_config_file is intentionally falsy | Need to verify all four environments before deploying | Check environment configurations | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (test coverage addition).

## Design
This is a Path A task (single file, test coverage addition). The approach is simple: add a new test following the existing conventions, asserting ValueError raised when own_config_file is falsy.

## Alternatives considered
- Using parametrize to test multiple falsy values — rejected because the single falsy case is sufficient to demonstrate the gap
- Testing via integration scenario — rejected because the unit test is simpler and more focused

## Compatibility considerations
- The test should work with existing pytest fixtures
- The test should not require external dependencies (e.g., actual MCP servers)

## Rollback considerations
- If the test fails due to missing fail-closed branch, revert the test and wait for the implementation fix

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Understand current test structure | Pending | — | — | |
| 2 | Create falsy own_config_file test | Pending | — | — | |
| 3 | Run targeted pytest run | Pending | — | — | |
| 4 | Run full test suite | Pending | — | — | |

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
- **Related target files**: tests/shared/test_config_loader.py

(End of file - total 100 lines)
