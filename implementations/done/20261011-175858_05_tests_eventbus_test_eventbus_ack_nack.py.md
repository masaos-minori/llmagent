## Goal
- Add one route-level test to `tests/eventbus/test_eventbus_ack_nack.py` that pins the ACK behavior for an event already in the DLQ: HTTP 409 with `event already in dead letter queue` (`REQ-004`).

## Scope
- One new test method in `class TestAckHttpBehavior`.
- No change to existing tests, fixtures, or production code.

## Assumptions
- Verified in the current file: `TestAckHttpBehavior` holds the other ACK route tests, uses the module's `client` fixture and the `_event()` and `_simulate_delivery_http()` helpers, and reaches the database through `eventbus.app.app.state.db`.
- The `events` table has a nullable `dlq_at` column; setting it marks the event as DLQ for the route and the repository.
- The test fails until procedure 04 is applied (the route currently returns 200).

## Design decisions
- Publish an event through `/publish`, mark it DLQ by writing `events.dlq_at` through `app.state.db` and committing, then POST the ACK, mirroring how `_simulate_delivery_http` writes through the same connection.
- Assert the status code, the `detail` text, and that no acked `consumer_delivery` row and no `consumer_offsets` row exists for the consumer, which proves nothing was written.
- Keep the test independent of the `already_acked` field name (Plan `UNK-03`).

## Alternatives considered
- Put the test in `tests/eventbus/test_eventbus_ack_endpoint.py`: rejected, because that file is not a Plan target and `test_eventbus_ack_nack.py` already groups the ACK/NACK route tests.
- Test only through the repository function: rejected, because the behavior under test is the HTTP response.

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure
1. Re-read `TestAckHttpBehavior` and the two helpers.
2. Add `test_ack_dlq_event_returns_409` after `test_ack_unknown_event_returns_404`.
3. Run the new test before and after procedure 04 to confirm it fails first and passes after.

### Method
- Use Edit to insert the method after the existing unknown-event test, with the same type hints (`client: Any`) and docstring style.

### Details
- Steps in the test: build the body with `_event()`; `POST /publish`; mark the event DLQ with an `UPDATE events SET dlq_at = ? WHERE event_id = ?` through `app.state.db` and `commit()`; `POST /events/{id}/ack` with `consumer_id` `consumer-A`.
- Assertions: status 409; `resp.json()["detail"] == "event already in dead letter queue"`; `SELECT acked FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?` returns no row or `acked = 0`; `SELECT offset FROM consumer_offsets WHERE consumer_id = ?` returns no row.
- Use a fixed ISO timestamp string for `dlq_at`.

## Compatibility considerations
- Test-only addition; existing tests are unchanged.
- The pending procedure `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md` also edits this file (two failing tests); apply them in either order, re-reading the file first.

## Security considerations
N/A: test-only; uses a temporary database and a test token.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- tests/eventbus/test_eventbus_ack_nack.py` before it is committed.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -k dlq_event`: fails before procedure 04, passes after.
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py`: no new failures.
- `uv run ruff check` and `uv run mypy` report no findings.

## Completion criteria
- The new test passes after procedure 04 and fails on the pre-change route.
- It asserts 409, the detail text, and that nothing was written.
- No existing test was modified.

## Out of scope
- Production code, other test files, and the `already_acked` field-name question.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_ack_dlq_event_returns_409` to `TestAckHttpBehavior` | Completed | 20261011-195047 | 20261011-195047 | Added test_ack_dlq_event_returns_409 to TestAckHttpBehavior. Changed: tests/eventbus/test_eventbus_ack_nack.py. Stale detector flagged the new symbol as missing (false positive for a symbol this procedure creates) |
| 2 | Confirm the test fails before and passes after procedure 04 | Completed | 20261011-195047 | 20261011-195047 | Failed before the route change (stash check), passes after |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261011-195047 | 20261011-195047 | ack_nack + ack_endpoint: 28 passed; full suite 8200 passed. Pre-existing ruff format diff in this file is unrelated |
| 4 | Update documentation, if in scope | Completed | 20261011-195047 | 20261011-195047 | N/A: no documentation change for this file N/A: no documentation change for this file |

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
- **Requirement ID**: `REQ-004` (route-level DLQ-event ACK test)
- **Source issue**: issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-153619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-175858
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py