# Fix ack_event_for_consumer UPSERT that never sets consumer_delivery.acked to 1

## Priority
High

## Summary
`ack_event_for_consumer()` in `scripts/eventbus/delivery_repo.py` runs a UPSERT whose
`acked = COALESCE(consumer_delivery.acked, excluded.acked)` keeps the existing value
instead of writing the new one, so `consumer_delivery.acked` is never updated from `0`
to `1` after an ACK. Every ACK therefore reports `newly_acked=True`, idempotency breaks,
and the per-consumer ACK guard in the NACK path never fires. This is root cause category 2
below.

The eventbus test suite is red on `master` with 16 failures spanning three distinct root
causes. This issue addresses category 2 (this COALESCE defect) only. Category 1 (the
3-tuple vs 4-tuple return-contract mismatch) is tracked by
`issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md`;
category 3 (test seed INSERTs referencing a non-existent `last_nack_attempt` column) is
tracked by `issues/20261012-075903_eb014_fix-eventbus-test-seed-inserts-referencing-non-existent-last_nack_attempt-column.md`.
Fixing all three is required to green the suite.

## Background
- The per-consumer delivery model stores ack state in the `consumer_delivery.acked`
  column (`INTEGER NOT NULL DEFAULT 0`, see `scripts/eventbus/schema.py`). A delivered
  but un-acked row has `acked=0`; a successfully ACKed row must have `acked=1`.
- `ack_event_for_consumer()` computes `newly_acked` by reading the pre-existing
  `acked` value (`existing["acked"] == 0`) and then persists the ACK via an
  `INSERT ... ON CONFLICT DO UPDATE SET acked = ...` UPSERT.
- The NACK path (`ack_route.py::_nack_and_promote`, `delivery_repo.py::nack_event`)
  gates on `SELECT 1 FROM consumer_delivery WHERE acked = 1` to reject a consumer that
  already ACKed an event (HTTP 409). This gate only works if `acked` actually becomes 1.
- A pending implementation procedure
  (`implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`) addresses
  these same four failing tests but misdiagnoses them (see Problem).

## Problem
The suite is red on current source with 16 failures across three distinct root causes.
This issue addresses category 2; the others are tracked separately.

### Category 2 — COALESCE never advances `acked` to 1 (this issue)
Four tests fail on current source from this root cause:

- `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_with_consumer_id`
  — after ACK, `consumer_delivery.acked` reads `0`, not `1` (line 161).
- `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_already_acked`
  — second ACK returns `newly_acked=True`, so the response has no `already_acked` key;
  `data.get("already_acked")` is `None`, not `True` (line 196).
- `tests/eventbus/test_eventbus_concurrent.py::TestConcurrentAck::test_concurrent_ack_same_event`
  — all 10 concurrent ACKs report `newly_acked=True`; `newly_acked_count == 10`, not `1`
  (line 110).
- `tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent::test_nack_http_409_on_per_consumer_acked`
  — a consumer that ACKed then NACKs gets HTTP 200 instead of 409 (line 480), because
  `acked` never became `1` so the per-consumer ACK guard never triggers.

### Category 1 — 3-tuple vs 4-tuple return-contract mismatch
(`issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md`)
Six tests fail with `ValueError: not enough values to unpack (expected 4, got 3)` because
`ack_event_for_consumer()` returns a 3-tuple while the tests unpack 4:

- `tests/eventbus/test_eventbus_offsets.py::test_ack_writes_offset`
- `tests/eventbus/test_eventbus_offsets.py::TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward`
- `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`
- `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_ack_event_for_consumer_advances_offset`
- `tests/eventbus/test_eventbus_restart_resume.py::TestOutOfOrderAckNoSkipOnReconnect::test_out_of_order_ack_no_skip_on_reconnect`
- `tests/eventbus/test_eventbus_restart_resume.py::TestOutOfOrderAckNoSkipOnReconnect::test_ordered_ack_baseline`

### Category 3 — test seed INSERTs reference a non-existent column
(`issues/20261012-075903_eb014_fix-eventbus-test-seed-inserts-referencing-non-existent-last_nack_attempt-column.md`)
Five tests fail with `sqlite3.OperationalError: table consumer_delivery has no column named
last_nack_attempt` because their seed INSERTs use a column name absent from the schema and
set `acked=NULL` instead of `acked=0`:

- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_consumer_delivery_failure_count_gte_max_retry`
- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`
- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count`
- `tests/eventbus/test_eventbus_dlq_pagination.py::test_dlq_pagination`
- `tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`

Evidence (`Confirmed by repository evidence`): direct reproduction against
`ack_event_for_consumer()`:

```
before ack acked = 0
return: True True 1          # found=True, newly_acked=True, seq=1
after  ack acked = 0         # BUG: acked stays 0 despite newly_acked=True
second return: True True 1   # BUG: re-reads acked=0, claims newly_acked again
after 2nd ack acked = 0
```

Root cause (`Confirmed by repository evidence`): the UPSERT at
`scripts/eventbus/delivery_repo.py:207-213`:

```sql
INSERT INTO consumer_delivery (consumer_id, event_id, acked) VALUES (?, ?, 1)
ON CONFLICT(consumer_id, event_id) DO UPDATE SET
    acked = COALESCE(consumer_delivery.acked, excluded.acked)
```

`excluded.acked` is the value being inserted (`1`). `COALESCE(existing, 1)` returns the
existing value, so `acked` is never advanced to `1`. The argument order is reversed; it
should prefer the incoming value. The inline comment "Keep first acked value via
COALESCE — do not overwrite" describes an intent that the code does not actually
implement: idempotency is already handled by the pre-read `newly_acked` computation, and
an ACK must persist `acked=1`.

The pending procedure `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`
states the `delivery_repo.py` change is "correct", that `already_acked` was
"intentionally removed", and that the 409 assertion needs "no change". All three claims
are false: the four failures are a real defect in `delivery_repo.py`, not a test/contract
mismatch. Fixing them by weakening the tests (dropping `already_acked` assertions) would
mask the defect rather than resolve it.

## Reason for Change
- The ACK/NACK contract is core message-delivery semantics. A consumer that ACKs an
  event is not actually recorded as ACKed, so reconnect/replay logic treats every event
  as un-acked, and a consumer that already consumed an event can NACK it and trigger
  spurious retries/DLQ processing instead of receiving the documented 409.
- The test suite is red, which hides further regressions.

## Implementation Intent
- Fix the UPSERT so it writes `acked=1` on ACK. Prefer correcting the COALESCE argument
  order (`COALESCE(excluded.acked, consumer_delivery.acked)`) or replacing it with
  `acked = excluded.acked` / `acked = 1`; both yield `1` since the inserted value is
  constant. Do not introduce a separate return flag or change the tuple shape.
- Update the misleading inline comment at the UPSERT to describe the actual behavior
  (ACK persists `acked=1`; idempotency comes from the pre-read `newly_acked`).
- Do not treat the four category-2 failures as a test/contract mismatch: the production
  UPSERT is wrong, not these tests. Fix the production code for category 2.
- Categories 1 and 3 ARE genuine test defects (a return-shape mismatch and seed data that
  does not match the schema); those tests must be edited. See the referenced issues.
- Do not alter the per-consumer schema, the offset-advancement transaction, or NACK
  idempotency.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py` — `ack_event_for_consumer()` UPSERT (lines ~207-213)
- `scripts/eventbus/ack_route.py` — only if the comment/docstring about `already_acked`
  needs correction to match the restored behavior (verify before editing)
- `tests/eventbus/test_eventbus_ack_endpoint.py`,
  `tests/eventbus/test_eventbus_ack_nack.py` — expected to start passing once category 2 is
  fixed; do not edit (their assertions encode correct behavior).
- `tests/eventbus/test_eventbus_concurrent.py::TestConcurrentAck::test_concurrent_ack_same_event`
  passes once category 2 is fixed. A *different* test in that file
  (`TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`) fails under category 3 and is
  fixed by the eb014 issue, not here.

## Required Changes
- Correct the COALESCE argument order in `ack_event_for_consumer()` so
  `consumer_delivery.acked` becomes `1` after an ACK.
- Fix the inline comment at the UPSERT so it no longer claims the value is preserved.
- Confirm the four category-2 tests now pass and no other test regresses.
- Do not attempt to green the full suite from here alone: categories 1 and 3 require the
  edits tracked by eb012ack and eb014 respectively.

## Constraints
- Preserve the atomic single-transaction guarantee of the delivery-state UPSERT plus
  offset advancement (ADR-006 INV-16).
- Do not change the `ack_event_for_consumer()` return tuple shape or add a DLQ flag.
- Do not modify the per-consumer schema or migration.
- Production data must not be touched.

## Acceptance Criteria
- The four category-2 tests pass: `test_ack_event_with_consumer_id`,
  `test_ack_event_already_acked`, `test_concurrent_ack_same_event`,
  `test_nack_http_409_on_per_consumer_acked`.
- No previously-passing test regresses from the category-2 fix alone.
- `consumer_delivery.acked` reads `1` immediately after a successful
  `ack_event_for_consumer()` call (verified by a direct reproduction or unit test).
- The second ACK for the same consumer returns `newly_acked=False` (idempotent).
- The full `tests/eventbus` suite is green only after categories 1 (eb012ack) and 3
  (eb014) are also addressed; that is out of scope for this issue.

## Testing Expectations
- Regression: the four failing tests plus the full `tests/eventbus/` suite.
- Add a focused regression test asserting `consumer_delivery.acked == 1` after
  `ack_event_for_consumer()` and that a second ACK is idempotent, if none exists.
- Run `uv run ruff check`, `uv run mypy`, `uv run lint-imports` per `rules/toolchain.md`.

## Documentation Impact
If `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` documents the ACK result or the
per-consumer `acked` semantics, confirm it states that an ACK sets
`consumer_delivery.acked=1` and that a repeat ACK is idempotent. Do not add
implementation-detail SQL to docs.

## Out of Scope
- The `eb012ack` 3-tuple vs 4-tuple return-contract issue
  (`issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md`)
  — different root cause (category 1), still open; tracked separately.
- The test seed-column defect (`issues/20261012-075903_eb014_fix-eventbus-test-seed-inserts-referencing-non-existent-last_nack_attempt-column.md`)
  — different root cause (category 3), still open; tracked separately.
- NACK idempotency, `consumer_last_nack_attempt`, or the per-consumer failure counters.
- Schema or migration changes.
- Unrelated eventbus refactoring.

## Dependencies
- Related to the pending `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md`
  procedure, which targets the same four tests but is misdiagnosed. Resolve this issue's
  root cause first; the procedure must be corrected or withdrawn to avoid conflicting
  (test-weakening) fixes.

## Unresolved Questions
- Should the COALESCE be replaced entirely with `acked = excluded.acked`, or kept as
  `COALESCE(excluded.acked, consumer_delivery.acked)`? Both are correct here; the
  former is clearer. `Needs confirmation` only if team prefers preserving the COALESCE
  structure for future-proofing.
- Does any external consumer rely on the (buggy) absence of `already_acked`? Low risk;
  restoring correct behavior re-introduces the key on repeat ACK. `Needs confirmation`
  if there is a downstream contract.

## AI Implementation Instruction
- Do NOT weaken the four category-2 tests or drop their assertions; the production code is
  wrong, not the tests.
- Make the smallest change that makes `acked` become `1`: fix the COALESCE argument order
  (or set `acked = excluded.acked`). Do not change the tuple return shape.
- This issue does NOT authorize editing tests for categories 1 and 3 — those are separate
  issues (eb012ack, eb014). Only the category-2 production fix belongs here.
- Do not touch the schema, migrations, offset transaction, or NACK idempotency.
- Verify the four category-2 tests pass before reporting completion; the full suite turns
  green only after categories 1 and 3 are also fixed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: `implementations/20261011-080000_01_delivery_repo_fix_test_failures.md` (misdiagnosed; superseded by this issue's root cause)
- **Generated at**: 20261011-204621
- **Related target files**: `scripts/eventbus/delivery_repo.py`
