# EventBus out-of-order ACK skips lower-seq events on resume

## Priority
High

## Summary
A consumer's committed offset is the highest acknowledged `seq` (a high-water mark), and a reconnect resumes from `seq > offset`. If ACKs arrive out of `seq` order, a lower-`seq` event that has not been acknowledged is skipped on resume. Decide whether the EventBus should keep this behavior as the specification or change how the resume position is computed.

## Background
Known Issue EVENTBUS-001 originally stated that offset monotonicity is not guaranteed. Investigation showed that statement is inaccurate: the offset never moves backward, because the per-consumer offset upsert only applies when the new value is greater than the stored one, and tests cover lower-or-equal values being skipped. The accurate residual behavior is the high-water-mark semantics described above. The documentation had described it as "non-monotonic", which is wrong, and the ADR's Known Deviations section carried a stale legacy entry for the same ID. Those documentation inaccuracies are corrected separately; this issue covers the remaining design question.

## Problem
- Resume position is derived only from the stored offset; the per-consumer delivery-state records are not consulted when a consumer reconnects.
- With out-of-order ACKs, the offset can jump past an unacknowledged lower-`seq` event, and that event is not re-delivered after reconnect.
- ADR-006 states the delivery baseline is at-least-once (duplicates tolerated, losses not). The skip behavior is in tension with that baseline unless consumers are required to ACK strictly in `seq` order.

## Reason for Change
Event loss on resume is a correctness and reliability concern. The current behavior is documented only as a caveat, and there is no recorded decision on whether strictly ordered ACKs are a consumer obligation or a server guarantee.

## Implementation Intent
First record a design decision, then implement only if the decision changes behavior:
- Option A: keep the high-water-mark offset as the specification and make ordered ACK a documented consumer obligation (no code change; adjust ADR-006 wording about losses).
- Option B: compute the resume position so that no unacknowledged lower-`seq` event is skipped (for example from the lowest unacknowledged event, or by re-delivering unacknowledged events), keeping the stored offset non-decreasing.
Preserve the existing atomic ACK and offset update and the non-decreasing guarantee in either option.

## Target Files or Areas
- EventBus delivery and offset repository (ACK transaction and offset upsert)
- EventBus subscribe route (resume position selection)
- ADR-006 and the EventBus DLQ/offsets/delivery-semantics document
- EventBus offset tests

## Required Changes
- Decide between Option A and Option B and record the decision in ADR-006.
- If Option B is chosen: change the resume position computation, and add regression tests for out-of-order ACK followed by reconnect.
- Update the EventBus delivery-semantics document to match the decision.

## Constraints
- The offset must remain non-decreasing, and ACK plus offset update must remain one atomic transaction.
- Duplicate delivery is tolerated by the at-least-once baseline; loss is not.
- Existing consumers that already ACK in order must see no behavior change.

## Acceptance Criteria
- ADR-006 records the chosen option and its rationale.
- Under the chosen behavior, a test demonstrates what happens to a lower-`seq` unacknowledged event after an out-of-order ACK and a reconnect.
- For Option B, no unacknowledged event is skipped on resume in that test.
- The EventBus documentation and ADR-006 describe the same behavior with no contradiction.

## Testing Expectations
- Regression test: ACK a higher `seq` before a lower `seq` is acknowledged, reconnect with the same consumer ID, and assert the resumed stream.
- Existing offset monotonicity tests continue to pass.
- Documentation consistency checks for `docs/` changes.

## Documentation Impact
Yes. Record the delivery-semantics decision (intent, consumer obligations, failure behavior) in ADR-006 and the EventBus delivery-semantics document. Update the Known Issues entry EVENTBUS-001 to reflect the decision, and remove it once the decision is implemented or accepted.

## Out of Scope
- Changing offset monotonicity enforcement itself.
- Removing the legacy file-based offset path.
- DLQ behavior and NACK handling.

## Dependencies
N/A: none

## Unresolved Questions
- Is strictly ordered ACK an acceptable consumer obligation (Option A), or must the server prevent skipping (Option B)?
- Does any current consumer ACK out of order in practice? (not checked)

## AI Implementation Instruction
Do not change code until the design decision is recorded. Keep changes minimal and limited to the EventBus delivery and subscribe paths and their tests. Preserve the atomic ACK-and-offset transaction and the non-decreasing offset guarantee. Stop and report if the decision is unclear.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-095313
- **Related target files**: scripts/eventbus/delivery_repo.py, scripts/eventbus/subscribe_route.py, docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md
