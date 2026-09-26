# EventBus requeue response missing dlq_imminent and conflicting status

## Priority
Medium

## Summary
3 tests across `test_eventbus_requeue_edge_cases.py` and `test_eventbus_dlq_promotion.py` expect a `dlq_imminent` boolean key in the `/dlq/{event_id}/requeue` response and expect a second requeue of an already-max-retry event to succeed (200); the response is missing the key and the second requeue instead returns 409.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `test_eventbus_requeue_edge_cases.py::test_repeated_requeue_increments_dlq_requeue_count`: second requeue call returns `409` instead of the expected `200`.
- `test_eventbus_requeue_edge_cases.py::test_requeue_event_at_max_retry_then_re_promoted`: `KeyError: 'dlq_imminent'` — response JSON has no such key.
- `test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_delivery_failure_count_gte_max_retry`: same `KeyError: 'dlq_imminent'`.

Both symptoms point to the `/dlq/{event_id}/requeue` endpoint's response contract and re-promotion/conflict logic not matching what the tests (and their docstrings, which describe the intended "dlq_imminent warning" and "repeated requeue" semantics) expect.

## Reason for Change
Either the `dlq_imminent` field was planned but never implemented (a coverage/feature gap, tests written ahead of implementation), or it was implemented and later dropped (a regression). Either way, the requeue endpoint's contract as tested is not what the endpoint currently returns, and repeated-requeue-at-max-retry behavior appears inconsistently enforced (409 on the second call rather than the documented re-promotion flow).

## Implementation Intent
Read the current `/dlq/{event_id}/requeue` handler implementation to determine: (a) whether a `dlq_imminent` field was ever implemented anywhere in the response model, (b) what triggers the 409 on a second requeue call. Decide whether to implement the missing `dlq_imminent` field and adjust the conflict logic to match the tests' documented intent, or correct the tests if the current contract is the intended one (Needs confirmation on which is authoritative — check for a Plan/design doc backing the `dlq_imminent` field before assuming it should be added).

## Target Files or Areas
- EventBus DLQ requeue route handler and its response model (confirm exact path under `scripts/eventbus/`)
- `tests/eventbus/test_eventbus_requeue_edge_cases.py`
- `tests/eventbus/test_eventbus_dlq_promotion.py`

## Required Changes
- Confirm whether `dlq_imminent` exists anywhere in the codebase (production or a spec/doc) to determine if this is a missing feature or a regression.
- Implement or restore the `dlq_imminent` field in the requeue response if confirmed as intended.
- Fix the second-requeue conflict logic so it matches the documented repeated-requeue semantics.

## Constraints
Do not change the requeue endpoint's existing successful-first-requeue behavior.

## Acceptance Criteria
- All 3 listed tests pass.
- The `dlq_imminent` field (if added) is documented and covered by a passing test for both `True` and absent/`False` cases.

## Testing Expectations
Run `tests/eventbus/test_eventbus_requeue_edge_cases.py` and `tests/eventbus/test_eventbus_dlq_promotion.py`; run full suite once after the fix.

## Documentation Impact
Update the DLQ/requeue endpoint documentation (confirm exact path, e.g. `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`'s "Requeue Semantics" section) to describe the `dlq_imminent` field and repeated-requeue behavior once the correct contract is confirmed.

## Out of Scope
Other unrelated eventbus failing tests (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether `dlq_imminent` is a planned-but-unimplemented feature or a regression — check git history/any design doc referencing it before implementing.

## AI Implementation Instruction
Search the repository (source and docs) for any prior reference to `dlq_imminent` before deciding whether to implement it fresh or restore a regression. Do not invent the field's exact semantics without such evidence — if none is found, state that in the fix's notes and propose the simplest interpretation consistent with the failing tests' docstrings.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_dlq_promotion.py
