# Implementation Procedure: Add cross-server permission test for Config Isolation

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: tests/agent/test_config_permission_cross_server.py

## Goal
Add cross-server permission test for Config Isolation enforcement in `tests/agent/test_config_permission_cross_server.py`.

## Priority
Medium

## Scope
- **In-Scope**: Add cross-server permission test for Config Isolation enforcement
- **Out-of-Scope**: Any other test_config_permission_cross_server.py behavior change

## Background
No existing cross-server test for Config Isolation (REQ-003; Acceptance criterion 1). The new test must verify that Config Isolation is enforced across server boundaries.

## Problem
No cross-server test exists to verify Config Isolation enforcement.

## Reason for change
This is a test coverage addition — Config Isolation must be tested across server boundaries to prevent regression.

## Implementation Steps

### Step 1: Understand the current test structure
Read `tests/agent/test_config_permission_cross_server.py` to understand the existing test patterns and fixtures.
Expected outcome: Identify how to add a new test following the existing conventions.

### Step 2: Determine Config Isolation enforcement requirements
Review `scripts/mcp_servers/server.py` and `scripts/shared/config_loader.py` to understand how Config Isolation is enforced across server boundaries.
Expected outcome: Document the Config Isolation enforcement requirements.

### Step 3: Create the cross-server permission test
Add a test like:
```python
def test_config_isolation_cross_server_enforcement():
    """Cross-server test for Config Isolation enforcement."""
    # Implement based on Config Isolation requirements
    ...
```
Expected outcome: Test verifies Config Isolation enforcement across server boundaries.

### Step 4: Run targeted pytest run
Run: `uv run pytest tests/agent/test_config_permission_cross_server.py::test_config_isolation_cross_server_enforcement -q`
Expected outcome: New test passes.

### Step 5: Run full test suite for the file
Run: `uv run pytest tests/agent/test_config_permission_cross_server.py -q`
Expected outcome: All tests pass.

## Acceptance criteria
- [ ] Cross-server Config Isolation test added
- [ ] Test verifies Config Isolation enforcement across server boundaries
- [ ] Targeted pytest run passes
- [ ] Full test suite passes
- [ ] REQ-003 satisfied

## Tests
New cross-server test for Config Isolation in `tests/agent/test_config_permission_cross_server.py`.

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-003: MCPServer.run_http() fails closed when own_config_file is falsy
- Related target file: scripts/mcp_servers/server.py (fail-closed branch must exist first)

## Assumptions
- The test follows the existing pytest conventions in the file
- The Config Isolation enforcement can be tested across server boundaries

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the Config Isolation enforcement can be adequately tested across server boundaries | Need to review Config Isolation implementation | Read server.py and config_loader.py | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (test coverage addition).

## Design
This is a Path A task (single file, test coverage addition). The approach is simple: add a new test following the existing conventions, verifying Config Isolation enforcement across server boundaries.

## Alternatives considered
- Adding the test as a unit test — rejected because Config Isolation is an integration-level concern
- Using parametrize to test multiple scenarios — rejected because the single Config Isolation case is sufficient

## Compatibility considerations
- The test should work with existing pytest fixtures
- The test should not require external dependencies (e.g., actual MCP servers)

## Rollback considerations
- If the test fails due to missing Config Isolation enforcement, revert the test and investigate further

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Understand current test structure | Pending | — | — | |
| 2 | Determine Config Isolation requirements | Pending | — | — | |
| 3 | Create cross-server permission test | Pending | — | — | |
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
- **Related target files**: tests/agent/test_config_permission_cross_server.py

(End of file - total 100 lines)
