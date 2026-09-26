# NackResult no longer supports tuple equality in nack tests

## Priority
Medium

## Summary
`tests/eventbus/test_eventbus_ack_nack.py` compares the `NackResult` return value against a plain tuple (e.g. `== (1, 1)`), which now fails because `NackResult` no longer supports tuple-equality (likely converted from a `NamedTuple` to a plain `dataclass`, whose default `__eq__` only compares same-type instances).

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`assert NackResult(delivery_failure_count=1, cycle_failure_count=1) == (1, 1)` fails (similarly for `(-1, -1)`), in at least 3 assertions within `tests/eventbus/test_eventbus_ack_nack.py`.

## Reason for Change
This is a type-contract change (likely `NamedTuple` → `dataclass`) that broke test assertions relying on tuple comparability. Low behavioral risk, but the tests currently do not verify `NackResult`'s actual field values at all (since they error before the assertion completes meaningfully in the failing form).

## Implementation Intent
Confirm `NackResult`'s current type definition. Update the tests to compare against `NackResult(delivery_failure_count=..., cycle_failure_count=...)` instances (or explicit field access) instead of bare tuples, matching the current type.

## Target Files or Areas
- `scripts/eventbus/` module defining `NackResult` (confirm exact path)
- `tests/eventbus/test_eventbus_ack_nack.py`

## Required Changes
- Update the 3 (or more, confirm exact count) tuple-equality assertions in `test_eventbus_ack_nack.py` to compare against `NackResult` instances or explicit fields.

## Constraints
Do not revert `NackResult` to a `NamedTuple` unless investigation shows the dataclass conversion was itself unintentional — prefer fixing the tests to match the current type.

## Acceptance Criteria
- All previously-tuple-equality-failing assertions in `test_eventbus_ack_nack.py` pass using `NackResult`-typed comparisons.

## Testing Expectations
Run `tests/eventbus/test_eventbus_ack_nack.py`; run full suite once after the fix.

## Documentation Impact
N/A: internal type change, no user-facing documentation impact expected.

## Out of Scope
`eb001` (status-code regressions in the same test file) — tracked separately.

## Dependencies
Related to `eb001` (same test file, different root cause).

## Unresolved Questions
Needs confirmation: exact current definition of `NackResult` and how many assertions in the file use bare-tuple comparison.

## AI Implementation Instruction
Confirm `NackResult`'s current type before editing. Update only the tuple-comparison assertions to use the correct current type; do not change `NackResult`'s definition itself unless directed.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
