# DLQ requeue: in-place vs new-event-id lineage model conflict across tests

## Priority
Medium

## Summary
`scripts/eventbus/dlq_route.py::dlq_requeue()` and `scripts/eventbus/db.py::requeue_event()`
implement DLQ requeue as an in-place operation: the same `event_id` has `dlq_at`
cleared and re-enters the active queue. A newer, still-unwired function,
`scripts/eventbus/db.py::redeliver_event()`, implements a different model: it
leaves the original row's `dlq_at` untouched (permanent DLQ record) and inserts a
brand-new row with a fresh UUID v4 `event_id`, `redelivered_from` pointing back at
the original, and `cycle_failure_count` reset to 0. The `events` table schema
already carries the `redelivered_from`/`cycle_failure_count` columns needed for
the lineage model (see `scripts/eventbus/schema.sql` and `_migrate()` in `db.py`),
but `redelivered_from` is otherwise unused in production code today.

The test suite currently asserts BOTH models as if they were the single intended
behavior of the same `/dlq/{event_id}/requeue` endpoint:

- `tests/eventbus/test_eventbus_dlq.py` (`test_dlq_requeue`,
  `test_requeue_increments_dlq_requeue_count`) and
  `tests/eventbus/test_eventbus_requeue_edge_cases.py`
  (`test_requeue_valid_dmq_event`, `test_repeated_requeue_increments_dlq_requeue_count`,
  `test_requeue_event_at_max_retry_then_re_promoted`) assert the in-place model:
  same `event_id`, `dlq_at` cleared, event reappears in `/dlq` list only before
  requeue.
- `tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`
  asserts the lineage model: a successful requeue response must contain
  `new_event_id` (a valid UUID v4) and `new_seq` (an int greater than the
  original event's seq), and only one of N concurrent requeue attempts on the
  same original event should succeed.

These cannot both be true of the same route at the same time. I confirmed this by
prototyping the lineage-model wiring (switching `dlq_requeue()` to call
`redeliver_event()`, adding a `redelivered_from`-based "already redelivered" guard
to `redeliver_event()` since the original row's `dlq_at` is intentionally left set
under that model, and returning `new_seq` by reading back the inserted row's
`seq`): this made `test_concurrent_dlq_requeue` pass but broke the 5 in-place-model
tests listed above. I reverted the prototype rather than pick a side unilaterally,
since which model is the intended production behavior is a design decision, not a
bug fix.

## Background
`redeliver_event()` and the `redelivered_from`/`cycle_failure_count` schema columns
were added in a separate, earlier commit (concurrent eventbus work landed via
rebase during this session — see `scripts/eventbus/db.py` history), apparently in
anticipation of moving DLQ requeue to the lineage model, but the route
(`dlq_route.py::dlq_requeue()`) was never switched over to call it — it still
calls the older `requeue_event()`. `test_eventbus_concurrent.py` was updated (in
commit `8d915f7c6`) to assert the lineage-model response shape, but the other DLQ
test files were not updated to match, and `redeliver_event()` itself was not yet
wired into the route or given the concurrency guard it needs to satisfy the
"only one redeliver succeeds" requirement.

## Problem
`/dlq/{event_id}/requeue`'s intended semantics are ambiguous in the current
codebase: the route implementation, and 5 out of 6 currently-passing DLQ-requeue
tests, assume in-place requeue; 1 test (added most recently) assumes the lineage
model. Whichever direction is chosen, the losing side's tests need rewriting, not
just the production code.

## Reason for Change
`test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`
currently fails and will keep failing until this is resolved one way or the other.

## Implementation Intent
Decide whether DLQ requeue should be in-place (current route behavior) or
lineage-based (new event_id per redeliver, matching `redeliver_event()` and the
schema support already in place), then:
- If in-place is correct: update `test_concurrent_dlq_requeue` to drop the
  `new_event_id`/`new_seq` assertions and match the in-place response shape, and
  consider removing or repurposing the now-dead `redeliver_event()` function.
- If lineage is correct: wire `dlq_route.py::dlq_requeue()` to
  `redeliver_event()` (adding a `redelivered_from`-based idempotency guard, since
  the original row's `dlq_at` is deliberately left set), and rewrite the 5
  in-place-model tests listed above (in `test_eventbus_dlq.py` and
  `test_eventbus_requeue_edge_cases.py`) to match.

## Target Files or Areas
- `scripts/eventbus/dlq_route.py` (`dlq_requeue()`)
- `scripts/eventbus/db.py` (`requeue_event()`, `redeliver_event()`)
- `tests/eventbus/test_eventbus_dlq.py`
- `tests/eventbus/test_eventbus_requeue_edge_cases.py`
- `tests/eventbus/test_eventbus_concurrent.py`

## Required Changes
- Pick one requeue model as the intended production behavior.
- Align `dlq_route.py` and `db.py` (`requeue_event`/`redeliver_event`) with that
  choice.
- Rewrite whichever test file(s) assert the discarded model.
- If the lineage model is chosen, give `redeliver_event()` a correct
  concurrency guard (the original row's `dlq_at` is intentionally left set, so a
  `redelivered_from`-existence check — or an equivalent — is needed to ensure
  only one redeliver succeeds per original event; a prototype of this exists in
  this issue's investigation history, see this session's rebase-conflict
  resolution around commit `ca11d6417`/`c8cfe8fc3`).

## Constraints
N/A: covered by Implementation Intent — the constraint is entirely "pick one
model consistently," not a technical limitation.

## Acceptance Criteria
- `uv run pytest tests/eventbus/ -q -p no:randomly` passes with 0 unresolved
  failures related to DLQ requeue.
- Exactly one requeue model is implemented and all DLQ-requeue tests assert
  that same model.

## Testing Expectations
Full `tests/eventbus/` regression run after the change; the specific tests
listed under Target Files or Areas must be updated or pass unmodified,
depending on which model is chosen.

## Documentation Impact
If eventbus has any operator-facing docs describing `/dlq/{event_id}/requeue`'s
response shape, update them to match whichever model is chosen (in particular
whether callers should expect the same `event_id` back or a new one).

## Out of Scope
Do not change `/nack`, `/ack`, or the DLQ promotion logic
(`scripts/eventbus/dlq.py`) — those are unaffected by this decision and were
already fixed and verified separately in this session.

## Dependencies
N/A: none

## Unresolved Questions
- Which model (in-place vs lineage) is actually the intended design? Neither the
  commit history nor the test suite states this explicitly — it needs an owner
  decision.

## AI Implementation Instruction
Do not guess and implement one model unilaterally without confirming the
decision first — a prototype of the lineage-model wiring already exists in this
session's history and is known to break 5 other tests; a decision is needed
before more work is invested in either direction.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-142700
- **Related target files**: scripts/eventbus/dlq_route.py, scripts/eventbus/db.py, tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_concurrent.py
