# Consolidate DLQ promotion paths and remove obsolete code

## Priority
Medium

## Summary
`scripts/eventbus/dlq.py` defines three promotion functions — `promote_to_dlq()`,
`sweep_orphans()`, and `promote_single()`. Confirmed by repository-wide `grep`: `promote_to_dlq()`
has zero callers anywhere under `scripts/` (only `scripts/eventbus/dlq.py`'s own definition
matches) — `app.py` calls only `sweep_orphans()` (as the periodic `_dlq_loop` sweep) and
`ack_route.py`'s `nack()` calls only `promote_single()` (as the inline on-NACK-threshold
promotion). `promote_to_dlq()` is referenced only from test files
(`tests/eventbus/test_eventbus_dlq.py`, `test_eventbus_dlq_promotion.py`,
`test_eventbus_requeue_edge_cases.py`), confirming memo4.md's claim that it "has no caller in
the attached runtime files."

## Background
Confirmed by direct read of `scripts/eventbus/dlq.py`: `promote_to_dlq()` (lines 47-77) and
`sweep_orphans()` (lines 80-111) are near-duplicates — both select
`WHERE delivery_failure_count >= ? AND dlq_at IS NULL` and both call `_atomic_write()` then
update `dlq_at`; the only functional difference is that `sweep_orphans()`'s `UPDATE` includes an
extra `AND dlq_at IS NULL` guard (line 104) making it safely re-runnable, while
`promote_to_dlq()`'s `UPDATE` (line 66) has no such guard. `promote_single()` (lines 114-147) is
the third, distinct inline-promotion path actually wired into `ack_route.py`'s `nack()` (line
92, via a local `from eventbus.dlq import promote_single` import).

## Problem
Runtime code uses `promote_single()` for inline promotion and `sweep_orphans()` as a safety
sweep, while `promote_to_dlq()` duplicates batch-promotion behavior with no runtime caller.
Retaining three overlapping implementations increases the chance that a future fix to the
promotion/write logic is applied to one path but not the others — `promote_to_dlq()`'s
already-weaker `UPDATE` guard (missing the `dlq_at IS NULL` re-run safety that `sweep_orphans()`
has) is itself an example of this drift.

## Reason for Change
Keep one authoritative implementation for each DLQ use case. Inline promotion and recovery
sweep may remain separate entry points, but they must share the same state-transition and
persistence logic. Unsupported duplicate code should be removed.

## Implementation Intent
Confirm (already done for this issue, but re-verify at implementation time) that
`promote_to_dlq()` has no supported runtime caller, and remove it if so — updating or removing
the tests that currently exercise it directly (`test_eventbus_dlq.py`,
`test_eventbus_dlq_promotion.py`, `test_eventbus_requeue_edge_cases.py`) rather than leaving them
referencing a deleted function. Extract the shared row-select/atomic-write/DB-update logic
common to `sweep_orphans()` and `promote_single()` into one internal helper both call, so a
future fix to that shared logic cannot land in one path without the other.

## Target Files or Areas
- `scripts/eventbus/dlq.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/app.py`
- `tests/eventbus/test_eventbus_dlq.py`
- `tests/eventbus/test_eventbus_dlq_promotion.py`
- `tests/eventbus/test_eventbus_requeue_edge_cases.py`

## Required Changes
- Search the entire repository for imports, callers, tests, and documentation references to
  `promote_to_dlq()` (already done for this issue: zero runtime callers found, three test files
  reference it directly).
- Remove `promote_to_dlq()` if it has no supported caller after re-verification at
  implementation time.
- Extract shared promotion logic used by the inline (`promote_single`) and sweep
  (`sweep_orphans`) paths where appropriate — at minimum, align `sweep_orphans()`'s safer
  `dlq_at IS NULL` re-run guard into whatever shared helper is extracted.
- Preserve atomic file creation (`_atomic_write()`) and conditional database update behavior.
- Update the three test files currently calling `promote_to_dlq()` directly, and current-
  specification documentation.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] No stale reference to `promote_to_dlq()` remains after removal, or the function has a
      documented unique supported responsibility distinct from `sweep_orphans()`/
      `promote_single()` if retained instead.
- [ ] Inline promotion (`promote_single`) and sweep (`sweep_orphans`) use consistent
      persistence rules (shared re-run-safety guard, shared atomic-write/DB-update sequence).
- [ ] DLQ behavior and tests remain correct after consolidation — every currently-passing DLQ
      test continues to pass, either unchanged or updated to target the surviving function(s).

## Testing Expectations
Update `tests/eventbus/test_eventbus_dlq.py`, `test_eventbus_dlq_promotion.py`, and
`test_eventbus_requeue_edge_cases.py` to stop referencing `promote_to_dlq()` directly if it is
removed (retarget their assertions to `sweep_orphans()`/`promote_single()` as appropriate,
without weakening what each test actually verifies). Run the complete EventBus test suite and
the repository's linting, type checking, and documentation consistency checks.

## Documentation Impact
If any EventBus documentation describes `promote_to_dlq()` as a supported entry point, correct
it to reflect the consolidated inline/sweep model.

## Out of Scope
- DLQ requeue real-redelivery redesign (tracked separately in this batch as EB-H03) — do not
  fold that larger redesign into this cleanup issue.
- Changing the DLQ file format or `_atomic_write()`'s mechanism itself.

## Dependencies
Coordinate with this batch's DLQ requeue redesign (EB-H03) if both land close together, since
EB-H03 also touches `promote_single()`/`sweep_orphans()`'s consistency with the redesigned
retry-state model — sequence the two so schema/behavior changes are not applied twice.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Re-run the repository-wide search for `promote_to_dlq` at implementation time (not only trust
this issue's already-recorded result) before deleting it, in case a caller was added since this
issue was filed. Do not delete the three test files that reference it — retarget their
assertions to the surviving function(s) instead, preserving what behavior each test actually
verifies.
