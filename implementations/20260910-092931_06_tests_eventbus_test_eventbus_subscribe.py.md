## Goal
Add an HTTP-level test asserting a second concurrent `/subscribe?consumer_id=X`
connection receives HTTP 409 while the first remains open (REQ-002, REQ-006; AC3).

## Scope
In scope: one new test function in this file. Out of scope: `test_health_ok` — the
one existing test in this file, confirmed mislabeled (it exercises the health
endpoint, not subscribe behavior) and left unmodified per this Plan's scope (renaming
or relocating a mislabeled pre-existing test is not this Requirement's concern).

## Assumptions
- The test client (`TestClient`) can hold a streaming `/subscribe` connection open
  (e.g. via a context manager or by reading the first chunk without closing) long
  enough to issue a second `/subscribe` request with the same `consumer_id` before the
  first closes.

## Design decisions
Add a test that opens one `/subscribe?consumer_id=dup1` connection, keeps it open, then
issues a second `/subscribe?consumer_id=dup1` request and asserts it receives HTTP
409, while confirming the first connection is unaffected (still open/receiving).

## Alternatives considered
Testing duplicate rejection only at the `EventBroker` unit level (row 05) without an
HTTP-level test was considered and rejected: REQ-006 explicitly calls for an
HTTP-level 409 assertion, since the translation from `ConsumerAlreadyConnectedError`
to the actual HTTP status code happens in `subscribe_route.py` (row 02), not
`broker.py` — a unit-level-only test would not catch a mistranslation at the route
layer.

## Implementation
### Target file
`tests/eventbus/test_eventbus_subscribe.py`

### Procedure
1. Add `test_duplicate_consumer_id_rejected_with_409` alongside the existing
   `test_health_ok` function.
2. Use `TestClient`'s streaming-response support (e.g. `client.stream("GET",
   "/subscribe", params={"consumer_id": "dup1"})` as a context manager) to hold the
   first connection open while issuing the second request.

### Method
`pytest` test function, following this file's existing plain-function style (matching
`test_health_ok`).

### Details
```python
def test_duplicate_consumer_id_rejected_with_409(client: TestClient) -> None:
    with client.stream(
        "GET", "/subscribe", params={"consumer_id": "dup1"}
    ) as first_response:
        assert first_response.status_code == 200
        second_response = client.get("/subscribe", params={"consumer_id": "dup1"})
        assert second_response.status_code == 409
```
Adapt to whatever streaming-connection idiom this project's other SSE tests already
use (confirm against `tests/eventbus/test_eventbus_slow_consumer.py`'s or
`tests/eventbus/test_eventbus_replay_subscribe.py`'s existing pattern for holding an
SSE connection open in a test, since `httpx.TestClient`'s exact streaming API may
differ from the sketch above).

## Compatibility considerations
No existing test in this file is modified.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_subscribe.py -v` — both tests (one
existing + one new) pass.

## Completion criteria
The new test passes, confirming a second concurrent connection with the same
non-empty `consumer_id` receives HTTP 409 while the first remains open (AC3).

## Out of scope
`test_health_ok` — unmodified (mislabeling is pre-existing and unrelated to this
Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_duplicate_consumer_id_rejected_with_409` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py
