# Make DLQ promotion and requeue atomic, locked, and documented

## Priority
Medium

## Summary
Immediate DLQ promotion, the background recovery sweep, and requeue locking currently form one lifecycle whose concurrency behavior is not guaranteed atomic; this issue moves the requeue path's redelivery/sequence-lookup/failure-state inspection under the shared database lock and documents the requeue API's response contract, superseding `EVENTBUS-002`'s undocumented-pagination note where applicable.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `EVENTBUS-002` ("`/replay?format=json` Pagination Format Undocumented") and `EVENTBUS-003` ("Dual Path for DLQ Promotion Undocumented", already tracked separately) both concern documentation gaps in the same DLQ/replay area this issue also touches.

## Problem
The DLQ requeue request path does not currently guarantee that redelivery, new-sequence lookup, and failure-state inspection all occur under one shared lock/transaction, so concurrent requeue attempts risk a non-deterministic outcome (e.g. more than one successful redelivery, or an incorrect returned sequence). Separately, the requeue API's request parameters, defaults, bounds, ordering, and response fields are not fully documented, and `EVENTBUS-002`'s pagination-format note may already be stale or partially overlapping with this gap.

## Reason for Change
Immediate promotion, recovery sweep, requeue locking, and concurrency behavior form one DLQ lifecycle.

## Implementation Intent
Guarantee deterministic and auditable DLQ transitions under concurrent execution by moving the relevant reads/writes under the shared database lock, and document the requeue API's contract precisely enough to update or retire `EVENTBUS-002` per the documentation policy.

## Target Files or Areas
- `scripts/eventbus/dlq_route.py`
- `scripts/eventbus/db.py`
- `tests/eventbus/test_eventbus_dlq.py`
- `scripts/eventbus/replay_route.py`
- `docs/eventbus`
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Move redelivery, new-sequence lookup, and failure-state inspection under the shared database lock.
- Prefer one transaction or a database operation that returns the inserted sequence.
- Add concurrent requeue tests.
- Document request parameters, defaults, bounds, ordering, and response fields.
- Document empty-result and invalid-parameter behavior.
- Update or remove `EVENTBUS-002` according to the documentation policy.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- All connection access in the requeue request path uses the shared lock.
- Concurrent requeue attempts produce one successful redelivery.
- The response returns the correct new event ID and sequence.
- The API reference matches the implemented JSON response.
- Pagination ordering and limits are explicit.
- `EVENTBUS-002` no longer contains an obsolete description.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria), including concurrent-requeue tests. Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update `docs/eventbus`'s DLQ/replay operations reference and `EVENTBUS-002`'s governance entry only after implementation evidence (the corrected atomic behavior and documented contract) is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch, though it touches the same `docs/00_governance_03_issue-and-uncertainty-management.md` file as `eventbus05` and `eventbus10`.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to DLQ requeue atomicity and its documentation; do not rewrite unrelated replay or publish logic beyond what the shared-lock fix requires. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Only update or remove `EVENTBUS-002` after the documented behavior is verified against the implemented response, per the governance document's own policy — do not remove it speculatively.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102435
- **Related target files**: scripts/eventbus/dlq_route.py, scripts/eventbus/db.py, tests/eventbus/test_eventbus_dlq.py, scripts/eventbus/replay_route.py, docs/eventbus, docs/00_governance_03_issue-and-uncertainty-management.md
