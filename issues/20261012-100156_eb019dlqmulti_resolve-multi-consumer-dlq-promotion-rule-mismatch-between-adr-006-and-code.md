# Resolve multi-consumer DLQ promotion rule mismatch between ADR-006 and code

## Priority
High

## Summary
ADR-006 INV-13 and `eventbus_05_dlq_offsets_and_delivery_semantics.md` state that an event is promoted to the DLQ only when every consumer that attempted delivery has exhausted its retry budget and none has ACKed. The code promotes an event when a single consumer's failure count reaches `max_retry`, without checking other consumers or ACKs. Decide which rule is authoritative and bring the code or the documents into agreement.

## Background
- Under the per-consumer model, `consumer_delivery.consumer_delivery_failure_count` is the promotion gate, while `events.dlq_at` stays event-level, so one promotion affects every consumer of the event.
- INV-13 states the intent in its own words: "one consumer's NACKs never promote an Event shared by others".
- This mismatch was found while filing `issues/20261012-095413_eb018dlqprom_*` (promotion conditions in `eventbus_03_dlq_operations.md`), which deliberately avoids asserting the multi-consumer rule.

## Problem
- Evidence (`Explicit in documentation`): ADR-006 INV-13 says an Event promotes only when every attempting consumer has exceeded `max_retry` and none has ACKed; `eventbus_05` repeats this for inline promotion, background-loop promotion, the Failed state definition and the state transitions.
- Evidence (`Explicit in code`): the background sweep selects events joined to `consumer_delivery` where any row has `consumer_delivery_failure_count >= max_retry` and `dlq_at IS NULL`, with no check of other consumers' counts or ACK state; the inline path in the NACK route promotes when the nacking consumer's own count reaches `max_retry`, and the promotion routine checks only that `dlq_at IS NULL`.
- Evidence (`Explicit in code`): NACK rejects a consumer that has itself already ACKed the event, but another consumer's ACK is not consulted.
- Effect (`Derived from confirmed evidence`): with two or more consumers of one event, one consumer exhausting its budget moves the event to the DLQ even if another consumer is still processing it or has ACKed it; a later requeue can then redeliver it to a consumer that already acknowledged it.
- Test coverage (`Explicit in code`): the tests that ADR-006 cites for INV-13, and the other promotion tests found, exercise a single consumer; no test pins the multi-consumer case in either direction.

## Reason for Change
- Correctness risk and documentation/code mismatch on a delivery guarantee: premature DLQ promotion in multi-consumer setups, or a documented guarantee that does not hold.
- The decision has to be made once and applied consistently to ADR, documents, code and tests.

## Implementation Intent
- First obtain the owner's decision on the intended rule; do not change code or documents before it is recorded.
- If the ADR rule is intended, make the sweep and the inline path enforce it (all attempting consumers exhausted, none ACKed) in one shared place, and add multi-consumer tests.
- If the code behavior is intended, amend ADR-006 INV-13 and `eventbus_05` to describe it, following the ADR amendment process and recording the approval.
- Keep `events.dlq_at` event-level and keep the single-consumer behavior unchanged either way.

## Target Files or Areas
- `scripts/eventbus/dlq.py` (promotion query and inline promotion routine)
- `scripts/eventbus/ack_route.py` (inline promotion call in the NACK route)
- `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_dlq.py` (multi-consumer cases)
- `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` (INV-13, only if the code behavior is chosen)
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (promotion paths, Failed state, transitions)

## Required Changes
- Record the owner's decision on the intended multi-consumer rule.
- Apply the decision: either enforce the ADR rule in code with tests, or amend ADR-006 and `eventbus_05` to match the code.
- If the ADR rule is enforced, define how a consumer that never attempted delivery is treated (INV-13 speaks of "attempting" consumers) and document it.
- Register the item in `governance_03` Part 1 as a Known Issue until resolved, if it is not fixed in the same change.

## Constraints
- Do not change the schema; `events.dlq_at` remains event-level.
- Preserve single-consumer behavior and the existing inline-then-sweep structure.
- ADR changes follow the ADR amendment process; docs follow the docs content policy.
- No force of a decision: stop and report if the owner's decision is not available.

## Acceptance Criteria
- A dated owner decision on the multi-consumer rule is recorded.
- The sweep, the inline path, ADR-006 INV-13 and `eventbus_05` all describe and implement the same rule.
- At least one test covers two consumers of one event, showing that one consumer exhausting its budget behaves as the decided rule requires, including the case where the other consumer has ACKed.
- The ADR invariant matrix cites tests that exercise the rule; `tests/eventbus`, `ruff`, `mypy` pass; the documentation and ADR checkers named in `routing.md` report no findings.

## Testing Expectations
- Add multi-consumer tests for the sweep and for the inline path (one consumer exhausted while another is pending, one consumer exhausted while another has ACKed, all consumers exhausted).
- Run `tests/eventbus`, `ruff`, `mypy`, and the documentation and ADR checkers.

## Documentation Impact
Update `eventbus_05` and, if the code behavior is chosen, ADR-006 INV-13 and its Verification entry; record the item in `governance_03` if left open. `eventbus_03_dlq_operations.md` is handled by the separate eb018 issue and must point to `eventbus_05` for the rule.

## Out of Scope
- Changing the per-consumer failure counting, the retry budget, requeue semantics, or the DLQ listing.
- Dropping events-level counters.
- The wording fix in `eventbus_03_dlq_operations.md` (eb018).

## Dependencies
- Related to `issues/20261012-095413_eb018dlqprom_*` (documents the per-consumer condition without the multi-consumer rule).
- Needs the eventbus owner's decision before implementation.

## Unresolved Questions
- Which rule is intended: promote when every attempting consumer has exhausted its budget and none has ACKed (ADR-006), or promote when any single consumer exhausts its budget (current code)? `Needs confirmation`; the git history was not reviewed for the intent.
- How should a consumer with no `consumer_delivery` row for the event count under the ADR rule? `Needs confirmation`; `eventbus_05` says an event with no `consumer_delivery` rows is never promoted, which does not cover a mix of present and absent rows.
- Is the risk observed in practice (events shared by several consumers)? `Unknown`; the number of consumers per topic in deployments is not recorded in the evidence reviewed.

## AI Implementation Instruction
- Resolve the first Unresolved Question with the owner before editing; stop and report if no decision exists.
- Change only the files listed for the chosen option; keep single-consumer behavior unchanged.
- Add the multi-consumer tests before or with the code change and run the checks listed in Testing Expectations.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-100156
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_dlq.py`, `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
