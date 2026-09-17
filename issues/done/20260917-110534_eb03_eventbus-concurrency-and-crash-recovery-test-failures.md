# eventbus concurrency and crash-recovery test failures

## Priority
High

## Summary
Three eventbus tests fail: `test_partial_ack_replay` (crash-recovery),
`test_concurrent_dlq_requeue`, and `test_concurrent_ack_same_event`
(concurrency). One has a confirmed root cause (a `/nack` call in the test
body is missing the now-mandatory `consumer_id` parameter); the other two
need further investigation but plausibly share a cause with the Principal/
consumer-identity refactor already tracked in a sibling issue.

## Background
`scripts/eventbus/auth.py` requires `consumer_id` on `/nack` and validates
consumer identity ownership via `require_consumer_identity` (confirmed by
the existing, passing test `test_nack_event_mandatory_consumer_id`, which
asserts `/nack` without `consumer_id` returns 422). These three tests were
apparently written against, or not updated for, the current contract.

## Problem
Evidence gathered by running each test individually
(`uv run pytest ... -v -p no:randomly`):

1. **`test_concurrent_dlq_requeue`** — `assert 422 == 200` at
   `tests/eventbus/test_eventbus_concurrent.py:149`. The test's setup loop
   calls `client.post("/nack", params={"event_id": event_id})` three times
   with no `consumer_id`, which the current `/nack` contract requires
   (422 Unprocessable Entity). Root cause: confirmed — missing
   `consumer_id` param in the test body's nack calls.

2. **`test_concurrent_ack_same_event`** — `AssertionError: Expected all 10
   acks to return 200, got 0` at `tests/eventbus/test_eventbus_concurrent.py:87`.
   The test does pass `consumer_id="consumer-1"` on each
   `/events/{event_id}/ack` call, so this is not the same missing-param
   issue. Not yet root-caused; the `client` fixture in this file uses a
   single shared/admin-style token rather than a Principal scoped to
   `consumer-1`, so this may be the same consumer-identity-ownership
   enforcement change tracked in the sibling issue for
   `test_eventbus_auth.py` (see Dependencies) — unconfirmed.

3. **`test_partial_ack_replay`** — `assert 0 == 1` at
   `tests/eventbus/test_eventbus_crash_ack.py:152`: after acking
   `body1`'s event for `consumer_id="consumer-B"`, `get_consumer_offset(db,
   "consumer-B")` returns `0` instead of the expected published `seq`. The
   test does not assert the ack call's status code before checking the
   offset, so a silently-failing ack (same consumer-identity-ownership
   theory as #2, unconfirmed) would produce exactly this symptom.

All three runs also log `WARNING eventbus.db:db.py:604 offsets_dir does not
exist: <tmp path>/offsets` from `migrate_legacy_offsets()` — this appears to
be a pre-existing, harmless warning (it only skips legacy-offset-file
migration when the directory is absent) rather than the failure cause, but
it was not fully ruled out and is noted here for whoever investigates #2/#3.

## Reason for Change
Uncovered via a full `uv run pytest tests/` run while syncing to
`origin/master` via the `git-commit-and-sync` skill. `test_partial_ack_replay`
and both concurrency tests were confirmed to already fail before that sync
(reproduced against the pre-sync commit too), so they are pre-existing, not
newly introduced. They cover crash-recovery replay correctness and
concurrent-request idempotency — both correctness-sensitive behaviors that
are currently unverified.

## Implementation Intent
- Fix `test_concurrent_dlq_requeue` directly: add the required `consumer_id`
  param to each `/nack` call in its setup loop, matching the pattern already
  used correctly elsewhere (e.g. `test_nack_event_mandatory_consumer_id`).
- For `test_concurrent_ack_same_event` and `test_partial_ack_replay`: first
  add a status-code assertion on the currently-unchecked ack call(s) to turn
  the silent failure into a clear, immediate error, then investigate why the
  ack is rejected/fails for the `client`/shared-token fixture used in these
  files. If the cause matches the Principal/consumer-identity-ownership
  question raised in the sibling `test_eventbus_auth.py` issue, coordinate
  the fix approach with that issue rather than diverging.
- Do not weaken `require_consumer_identity` or the `/nack` mandatory-
  `consumer_id` contract to make these tests pass — fix the tests (or, if
  investigation shows a genuine production bug in consumer-identity
  enforcement for these call patterns, file that as its own issue instead of
  silently loosening a test).

## Target Files or Areas
- `tests/eventbus/test_eventbus_concurrent.py` (`TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`, `TestConcurrentAck::test_concurrent_ack_same_event`)
- `tests/eventbus/test_eventbus_crash_ack.py` (`TestCrashBeforeAck::test_partial_ack_replay`)
- `scripts/eventbus/auth.py` (`require_consumer_identity`, read-only reference)
- `scripts/eventbus/ack_route.py` (ack/nack handlers, read-only reference)

## Required Changes
- Add `consumer_id` to the three `/nack` calls in
  `test_concurrent_dlq_requeue`'s setup loop.
- Add status-code assertions on the ack call(s) in `test_partial_ack_replay`
  and confirm/deny the consumer-identity-ownership theory for both
  `test_concurrent_ack_same_event` and `test_partial_ack_replay`.
- Apply whichever fix the investigation indicates (test fixture/token scope
  fix, most likely) and confirm all three tests pass.

## Constraints
N/A: none identified

## Acceptance Criteria
- [ ] `uv run pytest tests/eventbus/test_eventbus_concurrent.py -v` — both
  `test_concurrent_dlq_requeue` and `test_concurrent_ack_same_event` pass
- [ ] `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_partial_ack_replay -v` passes
- [ ] No other test in either file regresses

## Testing Expectations
`uv run pytest tests/eventbus/test_eventbus_concurrent.py -v` and
`uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` (targeted), plus
`uv run pytest tests/eventbus/ -q` for a regression check across the rest of
the eventbus suite.

## Documentation Impact
N/A: test-only fix; no production behavior is expected to change unless
investigation of #2/#3 finds a genuine production bug, in which case file
that separately and note the doc impact there.

## Out of Scope
- Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s (filed separately).
- Do not fix the 14 `test_eventbus_auth.py` failures beyond coordinating on
  a shared root cause if one is confirmed (filed separately).
- Do not fix `test_eventbus_dlq_pagination.py` (filed separately).

## Dependencies
Related to (not blocking) the `test_eventbus_auth.py` issue
(`issues/20260917-110320_eb02_test_eventbus_auth.py-has-14-failing-tests-after-principal-refactor.md`)
— both may share a Principal/consumer-identity-ownership root cause;
coordinate the fix approach if confirmed, but this issue does not require
that one to land first.

## Unresolved Questions
- Is the `client` fixture's shared/admin token in
  `test_eventbus_concurrent.py` and `test_eventbus_crash_ack.py` expected to
  bypass per-consumer identity ownership checks, or must it be scoped per
  consumer_id like `principal_client`? Needs confirmation against the
  intended Principal-refactor design before fixing #2/#3.
- Is the `offsets_dir does not exist` warning genuinely benign in all three
  cases, or does `migrate_legacy_offsets` skipping silently mask a real
  setup issue for these specific tests? Worth a quick check before assuming
  it is unrelated.

## AI Implementation Instruction
Fix `test_concurrent_dlq_requeue`'s missing `consumer_id` param first (confirmed,
low-risk). For the other two, add the missing status-code assertions before
attempting any other change — do not modify assertions or production
authorization logic to force a pass without first understanding why the ack
calls are failing. If the investigation reveals a production bug rather than
a test bug, stop and file that separately instead of expanding this issue's
scope.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-110534
- **Related target files**: tests/eventbus/test_eventbus_concurrent.py, tests/eventbus/test_eventbus_crash_ack.py, scripts/eventbus/auth.py, scripts/eventbus/ack_route.py
