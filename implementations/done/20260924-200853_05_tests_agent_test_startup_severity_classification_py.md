# Implementation Procedure: test_startup_severity_classification.py

**Plan:** plans/20260924-181019_plan.md
**Target File:** tests/agent/test_startup_severity_classification.py
**Change Responsibility:** Read-only
**Severity Classification:** Medium
**Estimated Effort:** Small
**Dependencies:** None

---

## Goal

This file is marked as Read-only in the plan. No modifications are required. Use only for verification — confirm severity classification logic remains correct after changes to `mcp_tool_discovery.py`.

---

## Current State

File: `tests/agent/test_startup_severity_classification.py`

Contains severity classification verification tests for 8 startup checks. These tests verify:
- FATAL severity classification for critical failures
- WARNING severity classification for non-critical failures
- INFO severity classification for informational messages
- Correct mapping of error types to severity levels

---

## Implementation Steps

### Phase 1: Verification Only

No code changes. Run tests after completing phases in other implementation procedures:

```bash
uv run pytest tests/agent/test_startup_severity_classification.py -v
```

If any tests fail due to the duplicate-FATAL exception handling added in Phase 1 of the primary target file, update assertions accordingly.

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

- UNK-01: Whether existing severity classification tests need updating if duplicate-FATAL logic changes error categorization

## Risks

- **Risk 1:** Severity classification tests are sensitive to error message format changes
- **Risk 2:** Duplicate-FATAL handling may alter which errors get classified as FATAL vs WARNING

## Acceptance Criteria

1. All existing tests pass after changes to source files
2. No new test failures introduced
3. Test assertions remain valid
