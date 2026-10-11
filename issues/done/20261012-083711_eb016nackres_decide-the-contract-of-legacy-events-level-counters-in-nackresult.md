# Decide the contract of legacy events-level counters in NackResult

## Priority
Low

## Summary
`NackResult` still carries `delivery_failure_count` and `cycle_failure_count`, but the per-consumer model no longer writes the events-level counters behind them. Decide whether these fields remain a supported part of the result (as legacy values) or are removed or repurposed, and record that decision so the docstring, tests and route agree.

## Background
- `plans/done/20261011-220109_plan.md` corrected the `nack_event` docstring to say the events-level counters are legacy values that are returned as stored and not modified. Its UNK-01 left open whether any caller still depends on them.
- DLQ promotion is gated on the per-consumer failure count; the events-level columns remain in the schema and are copied into DLQ records and requeued events.
- Repository search for readers of the `NackResult` fields found the following (`Explicit in code`): the only non-test caller is the NACK route; it reads `delivery_failure_count` as the `-1` (event not found) and `-2` (invalid state) sentinels and as a fallback value when no per-consumer count is returned; no code outside tests reads `cycle_failure_count`.
- `tests/eventbus/test_eventbus_ack_nack.py` compares whole `NackResult` values, so the `0`/`0` legacy values and the `-1`/`-2` sentinels are pinned by tests.

## Problem
- The `delivery_failure_count` field of `NackResult` has two unrelated roles: a sentinel channel for not-found and invalid-state outcomes, and a stored legacy value that is always `0` under the per-consumer model. `cycle_failure_count` has the sentinel role only.
- Evidence (`Explicit in code`): the NACK route's response field named `delivery_failure_count` carries the per-consumer count when one exists, not the events-level value, so the same name means different things in the result type and in the HTTP response.
- Whether external consumers of the HTTP response or of `eventbus.db.NackResult` depend on the events-level meaning is not known (`Needs confirmation`).

## Reason for Change
- Maintainability and clarity: a result type whose fields are partly dead and partly sentinels is easy to misread, as the stale docstring showed.
- Low urgency: behavior is correct and covered by tests.

## Implementation Intent
- First settle the contract, then align code, tests and documentation with it; do not change behavior before the decision is recorded.
- Options to evaluate: keep the fields as documented legacy values; or introduce an explicit outcome indicator for not-found and invalid-state and stop overloading the counters. Prefer the smallest change that removes the dual role.
- Preserve the HTTP response shape unless the owner approves a change, because external consumers are unknown.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py` (`NackResult`, `nack_event`)
- `scripts/eventbus/ack_route.py` (NACK route use of the result)
- `tests/eventbus/test_eventbus_ack_nack.py` (assertions on whole `NackResult` values)
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (NACK response field description; edit only if the decision changes it)

## Required Changes
- Record the owner's decision on the legacy counters in the plan produced from this issue.
- If the decision is "keep as legacy", state it once in the `NackResult` docstring and confirm the docs agree; no code change.
- If the decision is to separate outcome from counters, implement it with matching test updates and keep the HTTP response unchanged unless approved.

## Constraints
- Do not change the schema or drop the events-level columns; they are still copied into DLQ records and requeued events.
- Keep DLQ promotion behavior unchanged.
- Documentation follows the docs content policy (no line numbers, concrete config values or implementation counts).

## Acceptance Criteria
- The contract of `delivery_failure_count` and `cycle_failure_count` in `NackResult` is recorded in one place and the docstring, route, tests and documents agree with it.
- No field of `NackResult` carries both a sentinel meaning and a stored-value meaning, or the dual role is explicitly documented as intended.
- `tests/eventbus`, `ruff` and `mypy` pass; the documentation checkers named in `routing.md` report no findings for edited documents.

## Testing Expectations
- If code changes: update the NACK tests that compare whole `NackResult` values and add a case for each outcome (success, not found, invalid state, already acked).
- Run `tests/eventbus`, `ruff`, `mypy`, and the documentation checkers; docstring-only outcomes need no new tests.

## Documentation Impact
Update `eventbus_12_ack_nack_endpoints.md` and regenerate the reference API block only if the decision changes the described response or the function summary. Record intent and boundaries, not implementation counts.

## Out of Scope
- Dropping or migrating the events-level columns.
- Changing DLQ promotion, ACK behavior, or the inline and background promotion paths.
- Renaming the HTTP response field without owner approval.

## Dependencies
- Follows `plans/done/20261011-220109_plan.md` (UNK-01). No blocking dependency.

## Unresolved Questions
- Do external consumers of the NACK HTTP response or of `eventbus.db.NackResult` rely on the events-level meaning? `Needs confirmation`; no in-repository reader was found, external use is unknown.
- Should the response field `delivery_failure_count` keep its name now that it carries the per-consumer count? `Needs confirmation`; default is to keep it.

## AI Implementation Instruction
- Resolve the Unresolved Questions with the owner before changing code; if no decision is available, apply only the "keep as legacy" outcome (docstring and docs consistency).
- Do not change executable behavior, the HTTP response shape, or the schema without an explicit decision.
- Keep changes minimal and run the checks listed in Testing Expectations before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261011-220109_plan.md` (Unknown UNK-01)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-083711
- **Related target files**: `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_ack_nack.py`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
