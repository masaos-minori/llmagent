# Implementation Procedure: test_startup.py

**Plan:** plans/20260924-181019_plan.md
**Target File:** tests/agent/test_startup.py
**Change Responsibility:** Read-only
**Severity Classification:** Medium
**Estimated Effort:** Small
**Dependencies:** None

---

## Goal

This file is marked as Read-only in the plan. No modifications are required. Use only for verification — confirm existing behavior-lock tests still pass after changes to `mcp_tool_discovery.py` and `runtime_tool_registry.py`.

---

## Current State

File: `tests/agent/test_startup.py`

Contains behavior-lock tests for StartupOrchestrator. These tests verify:
- Startup sequence correctness
- MCP server initialization order
- Tool registration flow
- Error propagation during startup

---

## Implementation Steps

### Phase 1: Verification Only

No code changes. Run tests after completing phases in other implementation procedures:

```bash
uv run pytest tests/agent/test_startup.py -v
```

If any tests fail due to the new `all_tools()` API or refactored `discover_all()`, update assertions accordingly.

---

## Allowed Operations

- Read file content for verification
- Run tests against this file
- Update test assertions if API changes require it

## Prohibited Operations

- Do NOT add new test cases (out of scope for this implementation procedure)
- Do NOT modify test infrastructure or fixtures
- Do NOT change test naming conventions
- Do NOT modify unrelated test files

## Unknowns to Resolve During Implementation

- UNK-01: Whether existing mock setup needs updating if `registry._tools` was mocked directly

## Risks

- **Risk 1:** Behavior-lock tests may catch subtle regressions not caught by unit tests
- **Risk 2:** Integration-level tests may reveal issues at the boundary between components

## Acceptance Criteria

1. All existing tests pass after changes to source files
2. No new test failures introduced
3. Test assertions remain valid
