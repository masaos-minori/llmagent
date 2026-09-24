# Implementation Procedure: test_mcp_tool_discovery.py

**Plan:** plans/20260924-181019_plan.md
**Target File:** tests/agent/services/test_mcp_tool_discovery.py
**Change Responsibility:** Read-only
**Severity Classification:** Medium
**Estimated Effort:** Small
**Dependencies:** None

---

## Goal

This file is marked as Read-only in the plan. No modifications are required. Use only for verification — confirm existing tests still pass after changes to `mcp_tool_discovery.py` and `runtime_tool_registry.py`.

---

## Current State

File: `tests/agent/services/test_mcp_tool_discovery.py`

Contains unit tests for McpToolDiscoveryService with httpx.AsyncClient mocking. Tests cover:
- Basic tool discovery
- Error handling for failed connections
- Server filtering
- Tool validation

---

## Implementation Steps

### Phase 1: Verification Only

No code changes. Run tests after completing phases in other implementation procedures:

```bash
uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v
```

If any tests fail due to the new `all_tools()` API or refactored `discover_all()`, update assertions accordingly.

---

## Allowed Operations

- Read file content for verification
- Run tests against this file
- Update test assertions if API changes require it (rare, only if `all_tools()` breaks existing mocks)

## Prohibited Operations

- Do NOT add new test cases (out of scope for this implementation procedure)
- Do NOT modify test infrastructure or fixtures
- Do NOT change test naming conventions
- Do NOT modify unrelated test files

## Unknowns to Resolve During Implementation

- UNK-01: Whether existing mock setup needs updating if `registry._tools` was mocked directly and now requires `registry.all_tools()`

## Risks

- **Risk 1:** Existing tests may mock `registry._tools` directly — if so, mocks need updating to use `all_tools()` instead
- **Risk 2:** Test coverage gaps may be exposed by refactoring — existing passing tests don't guarantee full coverage

## Traceability
- **Workflow phase**: code-implementation
- **Requirement ID**: REQ-003 (refactor discover_all to under 40 lines)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-181019_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: $(date +%Y%m%d-%H%M%S)
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | — | — | |
| 2 | Read the current implementation procedure file | Completed | — | — | Read-only verification only |
| 3 | Implement the feature and pass code validation | Completed | — | — | N/A: no code changes required |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | See targeted run below |
| 5 | Update documentation per docs/00_index.md task-scope mapping | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for changed file |
| 6 | Validate documentation updates | Completed | — | — | N/A: no documentation changes to validate |
| 7 | Move the implementation procedure file to implementations/done/ | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
