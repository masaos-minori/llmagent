# Resolve ack_event_for_consumer return contract mismatch between code and tests

## Priority
High

## Summary
`ack_event_for_consumer()` returns a 3-element tuple in the current source, while several eventbus tests unpack a 4-element tuple. Decide which return contract is intended, then align the code, callers, tests, and documentation to that single contract so the test suite passes again.

## Background
- A commit titled "4-tuple ack contract" changed `ack_event_for_consumer()` to return `(found, newly_acked, seq, dlq)`. The fourth element signaled that the event is already in the DLQ, so the caller could answer HTTP 409. The tests were updated to unpack four values.
- Two later commits ("per-consumer ACK/NACK state management with NACK idempotency" and "per-consumer delivery state — bug fixes, doc updates, and implementation procedures") rewrote the delivery repository. The function now returns `(found, newly_acked, seq)`; the DLQ case returns `(True, False, None)`. The tests were not updated.
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` describes the ACK result as a 3-value tuple. No document found describes the 4-tuple.
- Pending implementation procedures dated 20261011 exist under `implementations/` for the same EVENTBUS-012 fix plan. Whether they address this mismatch is not confirmed.

## Problem
The following tests fail with `ValueError: not enough values to unpack (expected 4, got 3)`:
- `tests/eventbus/test_eventbus_offsets.py::test_ack_writes_offset`
- `tests/eventbus/test_eventbus_offsets.py::TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward`
- `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_ack_event_for_consumer_advances_offset`
- `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`
- `tests/eventbus/test_eventbus_restart_resume.py::TestOutOfOrderAckNoSkipOnReconnect::test_out_of_order_ack_no_skip_on_reconnect`
- `tests/eventbus/test_eventbus_restart_resume.py::TestOutOfOrderAckNoSkipOnReconnect::test_ordered_ack_baseline`

Evidence (`Explicit in code`): the function signature and docstring in the delivery repository declare 3 values, and the ACK route unpacks 3 values. Evidence (`Verified by test`): the six tests above fail on current `master`.

A second concern follows from the 3-tuple form: the DLQ case `(True, False, None)` is distinguishable from "already acked" `(True, False, seq)` only by `seq is None`. Whether the ACK route still returns 409 for DLQ events under the 3-tuple contract is `Needs confirmation`.

## Reason for Change
- The test suite is red on `master`, which hides further regressions in the eventbus.
- The ACK contract is a boundary between the delivery repository, the ACK route, and the tests. An unresolved mismatch risks silently losing the DLQ-409 behavior.

## Implementation Intent
- First decide the intended contract; do not change code or tests before that decision is recorded in this issue's resolution.
- Option 1: keep the 3-tuple. Update the six tests to unpack three values. Confirm the DLQ-409 behavior is still covered by another mechanism and by a test.
- Option 2: restore the 4-tuple with the DLQ flag. Update the delivery repository, its docstring, the re-export module, the ACK route, and the documentation.
- Change tests and implementation in separate commits, never both in one commit.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py` (`ack_event_for_consumer`)
- `scripts/eventbus/ack_route.py` (ACK handler caller)
- `tests/eventbus/test_eventbus_offsets.py`
- `tests/eventbus/test_eventbus_restart_resume.py`
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
- `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` (only if the contract statement there changes)

## Required Changes
- Record the decision (3-tuple or 4-tuple) with its rationale.
- Align the implementation, the ACK route, and the six failing tests to the chosen contract.
- Verify the DLQ-event ACK path returns the behavior the documentation specifies (HTTP 409), and add or keep a test for it.
- Update the documentation so exactly one contract is described.

## Constraints
- Do not change the per-consumer delivery-state schema (`consumer_last_nack_attempt`, `consumer_delivery_failure_count`).
- Preserve the atomicity of the delivery-state UPSERT and offset advancement in a single transaction (ADR-006 INV-16).
- Production data must not be touched.

## Acceptance Criteria
- The six tests listed under Problem pass.
- `uv run pytest tests/eventbus tests/db` reports no failures.
- The ACK route's behavior for an event already in the DLQ is covered by a passing test and matches `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`.
- The function docstring, the ACK route, the tests, and the documentation describe the same return contract.
- `uv run ruff check`, `uv run mypy`, and `uv run lint-imports` pass.

## Testing Expectations
- Regression: the six failing tests plus the existing ACK/NACK, DLQ, and offset test modules under `tests/eventbus/`.
- If the DLQ-409 behavior has no existing test, add one.
- Run the documentation checkers from `routing.md` Tools "When to run which tool" for the edited docs.

## Documentation Impact
Update `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (return contract and failure behavior). Update the ADR-006 contract statement only if the chosen contract differs from what it states. Record the decision rationale as design intent, not as a signature table.

## Out of Scope
- Changes to NACK idempotency or the `consumer_last_nack_attempt` column.
- Changes to the schema or migrations.
- Unrelated eventbus refactoring.
- The pending `implementations/20261011-071538_*.md` procedures, except to check for overlap.

## Dependencies
- Related to the EVENTBUS-012 fix plan whose implementation procedures are pending under `implementations/`. Check for overlap before implementing, to avoid double work.

## Unresolved Questions
- Which contract is intended: 3-tuple (current code and documentation) or 4-tuple with the DLQ flag (earlier commit and current tests)? `Needs confirmation`.
- Was removal of the DLQ flag intentional in the later repository rewrite, or an oversight? `Needs confirmation`.
- Does the ACK route still return 409 for DLQ events? `Needs confirmation`.
- Do the pending 20261011 implementation procedures already cover this mismatch? `Needs confirmation`.

## AI Implementation Instruction
- Resolve the Unresolved Questions with the user before editing code or tests.
- Change the minimum set of files required for the chosen contract; do not refactor unrelated eventbus code.
- Do not change tests and implementation in the same commit.
- Do not suppress failures with `xfail` or by loosening assertions.
- Run the acceptance commands before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261011-075321
- **Related target files**: `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
