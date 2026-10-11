# Align duplicate ACK response field name between route, tests and documentation

## Priority
Medium

## Summary
The ACK endpoint reports a duplicate ACK with the response field `already_acked: true`, but the ACK/NACK endpoint reference documents the field as `newly_acked: false`. Decide which field name is the public contract, then make the route, tests, and documentation describe that one name.

## Background
- The route answers a duplicate ACK with HTTP 200 and `{event_id, acked: true, seq, already_acked: true}`. The first ACK response omits the flag.
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` documents the duplicate-ACK response schema, its field table, and its state-transition row with `newly_acked: false`.
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` documents the same duplicate ACK as returning `already_acked: true`. The two documents therefore also disagree with each other.
- The tests assert `already_acked` (`tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_concurrent.py`).
- The internal repository function returns a `newly_acked` boolean in its tuple. The documented HTTP field name appears to have been confused with that internal name.
- This was recorded as UNK-03 (non-blocking, out of scope) in `plans/done/20261011-153619_plan.md`, which fixed the ACK return contract and the DLQ-event 409 but deliberately left the response field name alone because it is a public response shape.
- No in-repository consumer of the field was found under `scripts/` besides the route that produces it. Consumers outside the repository are not known.

## Problem
- A client following `eventbus_12_ack_nack_endpoints.md` checks `newly_acked` and never sees it, so it cannot detect a duplicate ACK. A client following `eventbus_05_dlq_offsets_and_delivery_semantics.md` checks `already_acked`.
- Evidence (`Explicit in code`): the route sets `already_acked` only. Evidence (`Verified by test`): three test modules assert `already_acked`. Evidence (`Explicit in documentation`): `eventbus_12` says `newly_acked`, `eventbus_05` says `already_acked`.

## Reason for Change
- Documentation/code mismatch on a public API response: a client written from the reference documentation silently misses duplicate-ACK detection.
- Two documents contradict each other, so the intended contract cannot be read from the documentation alone.

## Implementation Intent
- First decide the public field name; do not change code or documents before that decision is recorded in this issue's resolution.
- Default direction, subject to the decision: keep `already_acked` (it matches the route, three test modules, and `eventbus_05`) and correct `eventbus_12` to describe it. Changing the route to `newly_acked` would be a public response-shape change and needs an explicit decision.
- Describe the response behavior (when the field is present, its value), not a signature table.

## Target Files or Areas
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (duplicate-ACK response schema, field table, state-transition row)
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (only to confirm it matches the chosen name)
- `scripts/eventbus/ack_route.py` (only if the decision is to rename the field)
- `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_concurrent.py` (only if the decision is to rename the field)

## Required Changes
- Record the decision (field name and rationale).
- Make the ACK/NACK endpoint reference and the delivery-semantics document use the same field name and the same presence rule.
- If the route field is renamed, update the route and the three test modules in separate commits, and note the response-shape change in the documentation.

## Constraints
- Do not change the ACK return contract of `ack_event_for_consumer()` or the DLQ-event 409 behavior.
- Preserve the first-ACK, unknown-event (404), forbidden (403), and bad-request (400) responses.
- Do not weaken test assertions or mark tests `xfail`.

## Acceptance Criteria
- Exactly one duplicate-ACK field name appears across the route, the tests, `eventbus_12_ack_nack_endpoints.md`, and `eventbus_05_dlq_offsets_and_delivery_semantics.md`.
- The documented presence rule (absent on the first ACK, present on a duplicate ACK) matches the route behavior and is covered by a passing test.
- `uv run pytest tests/eventbus` reports no failures.
- The documentation checkers named in `routing.md` "When to run which tool" report no findings for each edited document.
- `uv run ruff check` and `uv run lint-imports` pass if code changed.

## Testing Expectations
- Documentation-only direction: run the documentation checkers; the existing three test modules already pin the route behavior.
- If the route field is renamed: update the three test modules, run `uv run pytest tests/eventbus`, and add a case for the first-ACK response to confirm the flag is absent.

## Documentation Impact
Update `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (response schema, field table, state-transition row) so it matches the chosen field name and presence rule. Confirm `eventbus_05_dlq_offsets_and_delivery_semantics.md` agrees. Record the decision as design intent and behavior, not as a signature table.

## Out of Scope
- The ACK return contract, the DLQ-event 409, NACK behavior, schema, and migrations.
- Other documentation clean-up in the eventbus documents.

## Dependencies
- Follows `plans/done/20261011-153619_plan.md` (UNK-03). No blocking dependency.

## Unresolved Questions
- Which field name is the intended public contract: `already_acked` (route, tests, `eventbus_05`) or `newly_acked` (`eventbus_12`)? `Needs confirmation`.
- Does any consumer outside this repository read the duplicate-ACK field? `Needs confirmation`.

## AI Implementation Instruction
- Resolve the Unresolved Questions with the user before editing code, tests, or documentation.
- Change the minimum set of files for the chosen name; do not refactor unrelated eventbus code.
- Do not change tests and implementation in the same commit.
- Do not suppress failures with `xfail` or by loosening assertions.
- Run the acceptance commands before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261011-153619_plan.md` (Unknown UNK-03)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261011-201147
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `scripts/eventbus/ack_route.py`
