# eventbus DLQ pagination test failure

## Priority
Medium

## Summary
`tests/eventbus/test_eventbus_dlq_pagination.py::test_dlq_pagination` fails
with `assert 0 >= 5` because its setup never successfully moves any event
into the DLQ: every `/nack` call in the test is missing the now-mandatory
`consumer_id` query parameter, so each one is rejected with 422 before any
event accumulates enough nacks to reach the dead-letter queue.

## Background
`scripts/eventbus/auth.py`'s `/nack` endpoint requires `consumer_id` (see
the passing test `test_nack_event_mandatory_consumer_id`, which asserts a
422 without it). This pagination test was written calling `/nack` without
that parameter.

## Problem
Confirmed by running the test directly
(`uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py::test_dlq_pagination -v -p no:randomly`):
captured stdout shows every nack attempt logging
```
nack1: 422 {'detail': [{'type': 'missing', 'loc': ['query', 'consumer_id'], 'msg': 'Field required', 'input': None}]}
nack2: 422 {'detail': [{'type': 'missing', 'loc': ['query', 'consumer_id'], 'msg': 'Field required', 'input': None}]}
```
(the test itself prints these, so it already logs the 422s — it just doesn't
assert on them). Because no event is ever actually nacked into the DLQ, the
later `GET /dlq` call returns `body["total"] == 0`, failing
`assert body["total"] >= 5` at line 79.

## Reason for Change
Uncovered via a full `uv run pytest tests/` run while syncing to
`origin/master` via the `git-commit-and-sync` skill. This is the same root
cause (missing `consumer_id` on a test's `/nack` call) as one of the three
issues filed in the sibling `eventbus-concurrency-and-crash-recovery`
issue's item #1 — a mechanical, confirmed, low-risk test fix.

## Implementation Intent
Add `consumer_id` to every `/nack` call in this test's setup, matching the
pattern already used correctly in `test_nack_event_mandatory_consumer_id`
and other passing tests. Also add an explicit status-code assertion (or at
minimum check the printed 422 bodies) on each nack call so a future contract
change fails loudly here instead of producing a confusing downstream
pagination-count mismatch.

## Target Files or Areas
- `tests/eventbus/test_eventbus_dlq_pagination.py` (`test_dlq_pagination`)

## Required Changes
- Add `consumer_id` (a fixed test value is fine, e.g. `"consumer-A"`) to each
  `/nack` call's `params`.
- Add an assertion that each nack call returns 200 before proceeding, so the
  test fails immediately at the nack step rather than later at the pagination
  assertion if this regresses again.

## Constraints
N/A: none identified

## Acceptance Criteria
- [ ] `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py -v` passes
- [ ] The test now asserts on each `/nack` call's status code

## Testing Expectations
`uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py -v` (targeted),
plus `uv run pytest tests/eventbus/ -q` for a regression check.

## Documentation Impact
N/A: test-only fix, no production behavior change.

## Out of Scope
- Do not change the `/nack` endpoint's mandatory-`consumer_id` contract.
- Do not fix the other eventbus test issues filed separately (`_TOKEN_CONSUMER_MAP`,
  `test_eventbus_auth.py`, concurrency/crash-recovery).

## Dependencies
Same root-cause pattern as item #1 in
`issues/20260917-110534_eb03_eventbus-concurrency-and-crash-recovery-test-failures.md`
(missing `consumer_id` on a test's `/nack` call) — not blocking, can be fixed
independently.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Make only the two changes described in Required Changes. Do not touch the
DLQ pagination implementation itself (`scripts/eventbus/dlq_route.py` or
`scripts/eventbus/dlq.py`) — this is purely a test-setup fix.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-110721
- **Related target files**: tests/eventbus/test_eventbus_dlq_pagination.py
