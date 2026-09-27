## Goal

Create `tests/eventbus/test_admin_topics_authorization.py`: tests for the new admin endpoint (auth gating, validation, update-takes-effect) (REQ-005).

## Scope

In scope: tests for rows 1-3's combined behavior. Out of scope: tests for the Agent-side client (row 6, separate file).

## Assumptions

- Rows 1-3 are implemented (row 3's Blocked question resolved) before this test file is finalized.

## Design decisions

- Use FastAPI's `TestClient` (or this repository's existing Event Bus test fixture pattern, if `tests/eventbus/` already has one — check for an existing conftest/fixture before writing a new one).

## Alternatives considered

N/A: standard FastAPI endpoint testing approach, no significant alternative considered.

## Implementation

### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

1. Check `tests/eventbus/` for an existing test fixture/conftest pattern for exercising Event Bus routes and reuse it.
2. Write a test confirming a valid ADMIN-token request updates authorization and a subsequent subscribe/publish request reflects it (AC-1) — the exact assertion depends on row 3's resolved enforcement model (per-token `Principal` vs. per-request check).
3. Write a test confirming a non-ADMIN-token request is rejected (AC-2).
4. Write a test confirming an invalid request body is rejected with a 4xx response and does not corrupt state (AC-3) — e.g. send a subsequent valid request and confirm it is unaffected by the earlier invalid one.

### Method

Standard FastAPI endpoint integration tests, following this repository's existing Event Bus test conventions.

### Details

- This test file's step 2 assertion is contingent on row 3's Blocked resolution — do not finalize it until that row specifies the actual enforcement model.

## Compatibility considerations

N/A: new test file, no existing behavior affected.

## Security considerations

N/A: test-only file.

## Rollback considerations

New file; revert via `git revert` or deletion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_admin_topics_authorization.py` | Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q` | All tests pass, at least 1 collected |

## Completion criteria

- Tests cover REQ-001-003 (AC-1, AC-2, AC-3).

## Out of scope

- Agent-side client tests (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Depends on rows 1-3, specifically row 3's Blocked resolution |
| 2 | Add or update tests per Validation plan | Blocked | — | — | This document IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `scripts/eventbus/auth.py`'s (row 3) Blocked resolution | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: tests/eventbus/test_admin_topics_authorization.py
