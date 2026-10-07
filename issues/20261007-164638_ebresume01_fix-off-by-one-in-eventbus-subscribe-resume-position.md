# Fix off-by-one in eventbus subscribe resume position

## Priority
High

## Summary
`/subscribe` replays events with `seq > start_seq`, but `start_seq` is set to the
position the consumer should resume FROM (an inclusive position). The event at the
resume position is therefore never replayed. Resolve the mismatch so that no event is
skipped on reconnect, and align tests and docs.

## Background
Eventbus delivery is specified as At-Least-Once (duplicates allowed, loss not allowed;
see ADR-006 INV-07). The resume position for a reconnecting consumer is computed by
`get_resume_position()` as either the lowest unacked `seq` at or below the stored
offset, or `stored_offset + 1`. The `Last-Event-ID` fallback is documented as
`Last-Event-ID + 1`. In all three cases the value is an inclusive "first seq to
deliver".

This was found while fixing documentation for review items H07/M21 (see the
investigation notes); the docs were deliberately not changed to describe the
suspected behavior as specification.

## Problem
Evidence (Explicit in code):
- `start_seq` is assigned from `since_seq`, `get_resume_position()`, or
  `last_event_id + 1` in the subscribe route.
- The replay queries use `WHERE seq > ?` bound to `start_seq`.
- Consequence for each source:
  - Consumer with offset N, all events up to N acked: resume position is N+1, query is
    `seq > N+1`, so event N+1 is skipped.
  - Consumer with lowest unacked event U at or below the offset: resume position is U,
    query is `seq > U`, so U itself (the very event that must be redelivered) is
    skipped. This defeats the purpose of the out-of-order ACK protection.
  - `Last-Event-ID: L` yields `start_seq = L+1`, query is `seq > L+1`, so event L+1 is
    skipped. The standard SSE contract expects replay to start at L+1.
- `since_seq=N` alone is consistent with "seq > N" semantics (documented as such), so
  it is not affected.
- Existing test `test_last_event_id_fallback_when_since_seq_and_offset_are_zero`
  (T-5, `tests/eventbus/test_eventbus_subscribe.py`) publishes three events, sends
  `Last-Event-ID: 1`, and asserts the first replayed event has `seq=3`. That asserts
  the skip of seq 2 and locks in the suspected defect.
- The tests for the offset-based resume paths (T-6, T-7 in the same file) are
  placeholders (`pass`). `test_resume_from_sqlite_offset` uses `since_seq=<offset>`
  directly rather than `get_resume_position()`, and the `get_resume_position()` tests
  assert the returned value only, not the replayed events.
- A code comment in the subscribe route describes the resume position as
  `max(lowest_unacked_seq, stored_offset)`, which does not match
  `get_resume_position()` (it returns the lowest unacked seq when one exists, else
  `stored_offset + 1`).

Confidence: High that the code path skips the event (direct reading of the assignments
and queries). Not yet confirmed by an end-to-end reproduction; see Unresolved
Questions.

## Reason for Change
- Correctness and data-loss risk: events can be silently dropped on reconnect,
  contradicting the At-Least-Once invariant. A consumer reconnecting after an
  out-of-order ACK is the exact case the resume-position design protects, and it is
  the case that fails.
- A test currently asserts the defective behavior, so a fix without test changes will
  fail CI and a naive "make tests green" change could re-introduce the defect.

## Implementation Intent
- Decide one meaning for `start_seq` in the subscribe route and apply it consistently.
  Two acceptable directions: (a) keep `start_seq` as an exclusive lower bound and
  convert inclusive resume positions to exclusive ones at assignment (subtract one for
  the resume-position and `Last-Event-ID` sources); or (b) make the replay predicate
  inclusive for those sources while keeping `since_seq` semantics documented as
  "seq > N". Prefer the smallest change that keeps the public `since_seq` contract
  unchanged.
- Preserve: `since_seq` > resume position > `Last-Event-ID` precedence, the 412
  behavior for `Last-Event-ID` above max seq, the batching and live-phase handoff
  (`replay_ceil` logic), and `GET /replay` semantics.
- Make the replay-ceiling and batch-advance logic consistent with the chosen meaning
  (the loop updates `start_seq` from the lowest emitted seq; verify it does not
  introduce a second off-by-one when the predicate changes).
- Do not change `get_resume_position()` return semantics unless direction (a)/(b)
  analysis shows it is the better single point of change.

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py`
- `scripts/eventbus/delivery_repo.py` (only if its contract is adjusted)
- `tests/eventbus/test_eventbus_subscribe.py` (T-5 expectation; T-6 and T-7
  placeholders)
- `tests/eventbus/test_eventbus_restart_resume.py`
- `docs/24_eventbus/eventbus_03_dlq_operations.md`
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

## Required Changes
- Reproduce the defect with an end-to-end test through `/subscribe` for each of the
  three sources: in-order ACK offset, out-of-order ACK (lowest unacked event), and
  `Last-Event-ID`.
- Fix the subscribe route so the event at the resume position is replayed in all three
  cases, without changing `since_seq=N` behavior.
- Correct the T-5 expectation to the first event after `Last-Event-ID` (the next seq,
  not the one after it).
- Replace the T-6 and T-7 placeholders with real tests (consumer-offset resume, and
  `since_seq` precedence over the consumer offset).
- Correct the misleading `max(...)` comment in the subscribe route.
- Update the eventbus docs so the replay predicate and resume position are described
  consistently (see Documentation Impact).

## Constraints
- At-Least-Once must hold: duplicates are acceptable, loss is not. When in doubt, an
  extra redelivery is preferred over a skipped event.
- The public `since_seq` meaning (events with `seq > since_seq`) must not change.
- No change to the ACK, NACK, or offset-write paths.

## Acceptance Criteria
- Reconnect with in-order ACKs up to N replays event N+1 first.
- Reconnect after out-of-order ACKs replays the lowest unacked event first (that event
  included).
- `Last-Event-ID: L` replays event L+1 first; `Last-Event-ID` equal to the current max
  seq still yields no events; above max still returns 412.
- `since_seq=N` still replays events with `seq > N`.
- No event is emitted twice within one connection by the replay-to-live handoff.
- T-5 is corrected, T-6 and T-7 are real tests, and all eventbus tests pass.
- Eventbus docs describe one consistent predicate.

## Testing Expectations
- Integration tests through the `/subscribe` endpoint (TestClient) asserting the
  exact ordered `seq` values of the first replayed events for each resume source.
- Regression test for the replay-to-live handoff around the boundary (event published
  while replay is in progress).
- Run the eventbus test directory, then the full validation sequence in
  `rules/toolchain.md`.

## Documentation Impact
Documentation must be updated: intent and boundaries of the replay predicate and resume
position (inclusive vs. exclusive) in `eventbus_03` and `eventbus_05`, so they state
one rule. No Known Issue entry is needed if the fix lands together with the docs; if
the fix is deferred, register this defect in the Known Issue ledger and cross-reference
this file from both eventbus docs.

## Out of Scope
- Changing ACK/NACK semantics, DLQ promotion, or the consumer-offset schema.
- Changing `GET /replay` behavior.
- Other eventbus review items (authorization model, ACK/NACK state management).
- Refactoring unrelated parts of the subscribe route.

## Dependencies
- Related but independent: `issues/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`.
- Docs for the related review items H07/M21/G15 were already corrected; this issue
  only covers the remaining resume-position predicate.

## Unresolved Questions
- Not yet reproduced end to end: the conclusion rests on code reading plus the T-5
  assertion. Confirm with a failing test first (Required Changes, first bullet).
- Is the T-5 expectation (`seq=3` for `Last-Event-ID: 1`) intentional, for example
  because clients are expected to send the last NOT-yet-processed id? Nothing in the
  docs suggests so (eventbus_03 documents `Last-Event-ID + 1` as the start), but the
  owner should confirm before the test is changed.
- Whether any deployed consumer relies on the current skip behavior is unknown.

## AI Implementation Instruction
- Write the failing end-to-end tests first and confirm they fail for the stated
  reason before changing the route.
- Keep the change minimal and local to the subscribe route; do not touch unrelated
  files or the ACK paths.
- If the T-5 intent question cannot be answered from the repository, stop and report
  it instead of choosing silently.
- Do not implement out-of-scope items. Comments and docs follow the repository
  language rules (comments in English, docs under `docs/` in English).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-164638
- **Related target files**: `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/delivery_repo.py`, `tests/eventbus/test_eventbus_subscribe.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
