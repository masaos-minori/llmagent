## Goal

Create `tests/agent/test_eventbus_subscriber.py`: unit tests for the new `scripts/agent/eventbus_subscriber.py` module (REQ-004).

## Scope

In scope: tests for event parsing, disconnection/reconnection, and the consumer-id constraint. Out of scope: integration tests against a real running Event Bus instance.

## Assumptions

- `scripts/agent/eventbus_subscriber.py` (this Plan's row 1) is implemented before this test file is finalized.

## Design decisions

- Mock the SSE streaming response (following whatever mocking convention `tests/agent/test_eventbus_client.py`, from the EVENTBUS-005 Plan, establishes for `httpx`-based clients, for consistency across the two sibling test files).

## Alternatives considered

- Spinning up a real Event Bus test instance: rejected — same reasoning as the EVENTBUS-005 test procedure; unit tests should stay fast and isolated.

## Implementation

### Target file

`tests/agent/test_eventbus_subscriber.py`

### Procedure

1. Check `tests/agent/test_eventbus_client.py` (sibling module from the EVENTBUS-005 Plan) for its `httpx` mocking convention and reuse it for consistency.
2. Write a test confirming events are correctly parsed from a mocked SSE stream.
3. Write a test simulating a disconnection followed by a reconnection, confirming a fresh `consumer_id` is used and no `ConsumerAlreadyConnectedError`-equivalent failure occurs.
4. Write a test confirming a stream-level error is surfaced as a typed result, not a raised exception that crashes the test process.

### Method

Standard `pytest` unit tests with a mocked streaming HTTP client.

### Details

- Reference `scripts/agent/eventbus_subscriber.py`'s actual public class/method names once implemented (row 1 of this Plan) — do not guess them here.

## Compatibility considerations

N/A: new test file, no existing behavior affected.

## Security considerations

N/A: test-only file.

## Rollback considerations

New file; revert via `git revert` or deletion.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_eventbus_subscriber.py` | Unit | `uv run pytest tests/agent/test_eventbus_subscriber.py -q` | All tests pass, at least 1 collected |

## Completion criteria

- Tests cover event parsing, reconnection, and the consumer-id constraint (AC-4).

## Out of scope

- Integration testing against a real Event Bus instance.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-141518 | 20260927-141518 | Depends on row 1 being implemented first Test file written and validated as part of the sibling procedure 01's cycle; 5/5 tests pass, covers event parsing, heartbeat handling, auth/consumer_id, reconnection, and max-attempts typed error |
| 2 | Add or update tests per Validation plan | Completed | 20260927-141518 | 20260927-141518 | This document IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-141518 | 20260927-141518 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-141518 | 20260927-141518 | N/A: test-only file |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260927-115629_eventbus006_implement-agent-eventbus-sse-subscribe-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120532_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123444
- **Related target files**: tests/agent/test_eventbus_subscriber.py