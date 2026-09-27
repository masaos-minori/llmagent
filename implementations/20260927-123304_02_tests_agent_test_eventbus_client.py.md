## Goal

Create `tests/agent/test_eventbus_client.py`: unit tests for the new `scripts/agent/eventbus_client.py` module (REQ-003).

## Scope

In scope: tests for request construction, auth header, success path, and failure path. Out of scope: integration tests against a real running Event Bus instance (covered separately by this Plan's Validation plan, not a unit-test concern).

## Assumptions

- `scripts/agent/eventbus_client.py` (this Plan's row 1) is implemented before this test file is finalized — write against its actual public interface, not a guessed one.

## Design decisions

- Mock `httpx.AsyncClient` (following existing test patterns for `embedding_client.py`, if any exist under `tests/agent/`) rather than hitting a real network endpoint.

## Alternatives considered

- Spinning up a real Event Bus test instance for these unit tests: rejected — unit tests should be fast and isolated; the Validation plan's integration check covers the real-endpoint case.

## Implementation

### Target file

`tests/agent/test_eventbus_client.py`

### Procedure

1. Check `tests/agent/` for an existing test file testing `embedding_client.py` and follow its mocking convention if one exists, for consistency.
2. Write a test confirming the publish request is sent with the correct URL, auth header, and JSON body.
3. Write a test confirming a 2xx response yields a typed success result.
4. Write a test confirming a network error and a non-2xx response each yield a typed error result, not a raised exception.

### Method

Standard `pytest` unit tests with mocked HTTP client, matching this repository's existing Agent-side client test conventions.

### Details

- Reference `scripts/agent/eventbus_client.py`'s actual public class/method names and result types once implemented (row 1 of this Plan) — do not guess them here.

## Compatibility considerations

N/A: new test file, no existing behavior affected.

## Security considerations

N/A: test-only file, no production code path.

## Rollback considerations

New file; revert via `git revert` or deletion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_eventbus_client.py` | Unit | `uv run pytest tests/agent/test_eventbus_client.py -q` | All tests pass, at least 1 collected |

## Completion criteria

- Tests cover request construction, auth header, success, and failure paths (AC-3).

## Out of scope

- Integration testing against a real Event Bus instance.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on row 1 (`scripts/agent/eventbus_client.py`) being implemented first |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260927-115602_eventbus005_implement-agent-to-eventbus-publish-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120356_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123304
- **Related target files**: tests/agent/test_eventbus_client.py
