# `Orchestrator._llm_turn_executor` rename to `_llm_executor` not propagated to tests

## Priority
High

## Summary
`tests/agent/test_orchestrator.py` fails 78 of its tests (the largest single
contributor to the full suite's pre-existing failure count) with
`AttributeError: 'Orchestrator' object has no attribute '_llm_turn_executor'. Did you
mean: '_llm_executor'?`. The attribute was renamed on `Orchestrator` in a prior
refactor; the shared test-construction helper still references the old name, cascading
the failure across nearly every test class in the file. A second file,
`tests/integration/test_orchestrator_integration.py`, also references the old name.

## Background
Commit `35a1e1969` ("refactor: extract orchestrator into dedicated component modules")
renamed the attribute assigned in `Orchestrator.__init__`
(`scripts/agent/orchestrator.py`) from `self._llm_turn_executor = LlmTurnExecutor(...)`
to `self._llm_executor = LlmTurnExecutor(...)`, and updated the one internal call site
(`self._llm_executor.handle_llm_turn(...)`) accordingly — same class, same constructor
arguments, a pure rename with no type or shape change. `LlmTurnExecutor`'s constructor
already receives `diagnostic_store` directly, so `orch._diagnostic_store` no longer
needs to be reassigned onto the executor after construction.

## Problem
`rg -n "_llm_turn_executor" tests/ scripts/` finds 7 remaining references, all in
tests, none in production code:
- `tests/agent/test_orchestrator.py`: 4 occurrences, including one inside the shared
  `_make_orchestrator()` helper used to construct the `Orchestrator` under test by
  nearly every test class in the file — this single line is why one rename produces 78
  failures.
- `tests/integration/test_orchestrator_integration.py`: 3 occurrences, following the
  same pattern (`orch._llm_turn_executor._diagnostic_store = orch._diagnostic_store`).

## Reason for Change
78 failing tests in `tests/agent/test_orchestrator.py` block confident verification of
`Orchestrator` behavior — a core Agent component — and mask any genuine regression a
future change might introduce in this area, since the current failure list already
looks total. `test_orchestrator_integration.py`'s failures are undercounted here (see
Out of Scope) and may include additional, unrelated causes worth a separate look once
this rename is fixed.

## Implementation Intent
Rename all 7 remaining `_llm_turn_executor` references to `_llm_executor` across both
test files. For the `orch._llm_turn_executor._diagnostic_store = orch._diagnostic_store`
line specifically (in whichever file it appears), remove the reassignment entirely
rather than renaming it in place — it is redundant now that `LlmTurnExecutor`'s
constructor already receives `diagnostic_store` directly. Do not change any production
file; `scripts/agent/orchestrator.py`'s current `_llm_executor` naming and construction
are confirmed correct.

## Target Files or Areas
- `tests/agent/test_orchestrator.py` (4 occurrences, including the shared
  `_make_orchestrator()` helper)
- `tests/integration/test_orchestrator_integration.py` (3 occurrences)
- `scripts/agent/orchestrator.py` (reference only — confirms current `_llm_executor`
  naming and constructor signature; not a modification target)

## Required Changes
- Replace each of the 4 `_llm_turn_executor` references in
  `tests/agent/test_orchestrator.py` with `_llm_executor`.
- Replace each of the 3 `_llm_turn_executor` references in
  `tests/integration/test_orchestrator_integration.py` with `_llm_executor`, removing
  the now-redundant `._diagnostic_store = orch._diagnostic_store` reassignment rather
  than just renaming its left-hand side.
- No change to `scripts/agent/orchestrator.py`.

## Constraints
Do not modify `scripts/agent/orchestrator.py` or `LlmTurnExecutor`'s constructor — the
current production naming and constructor-injection design are confirmed correct; this
is a test-only rename-propagation fix.

## Acceptance Criteria
- [ ] No occurrence of `_llm_turn_executor` remains in `tests/` or `scripts/`
  (`rg -n "_llm_turn_executor" tests/ scripts/` returns no matches)
- [ ] `uv run pytest tests/agent/test_orchestrator.py -q` no longer reports the
  `_llm_turn_executor` `AttributeError` (78 fewer failures than the current baseline)
- [ ] `uv run pytest tests/integration/test_orchestrator_integration.py -q` no longer
  reports the `_llm_turn_executor` `AttributeError` (32 fewer failures — see Testing
  Expectations; this file's one remaining failure after this fix is a distinct,
  separately-tracked defect, not this issue's concern)

## Testing Expectations
- `uv run pytest tests/agent/test_orchestrator.py -q` — all 78
  `_llm_turn_executor`-attributable failures must be resolved
- `uv run pytest tests/integration/test_orchestrator_integration.py -q` — **Resolved
  2026-09-09**: a follow-up investigation confirmed 32 of this file's 33 failures
  (not just the 3 occurrences originally found) share this exact cause — every failing
  test that goes through the shared `_make_orchestrator()`-equivalent construction path
  hits the same `_llm_turn_executor` `AttributeError`, the same cascading-from-one-line
  mechanism as `test_orchestrator.py`'s 78. The file's one remaining failure
  (`TestCompleteTurnExecution::test_handle_turn_history_compression_persists_when_needed`,
  which constructs `Orchestrator(ctx)` directly and is unaffected by this rename) is a
  distinct, genuine production defect, filed separately as
  `issues/20260909-130135_orch003_history-compression-no-longer-persists-to-session-store.md`
  — do not attempt to fix it as part of this issue.

## Documentation Impact
N/A: test-only rename propagation; no documented behavior changes.

## Out of Scope
- Any change to `scripts/agent/orchestrator.py` or `LlmTurnExecutor`.
- `test_orchestrator_integration.py`'s one remaining, distinct failure
  (`test_handle_turn_history_compression_persists_when_needed`) — tracked separately,
  see Testing Expectations.
- `tests/agent/test_orchestrator_bg_failure_threshold.py`'s 6 failures — `rg` found no
  `_llm_turn_executor` reference in this file, so its failures are a separate,
  uninvestigated cause, not part of this issue.

## Dependencies
N/A: none. Related to (but does not duplicate) the now-deleted triage record
`issues/20260908-203803_regr001_full-suite-491-pre-existing-failures.md`, which first
sampled this failure.

## Unresolved Questions
N/A: none — resolved 2026-09-09 (see Testing Expectations); `test_orchestrator_integration.py`'s
full failure count is now fully accounted for (32 by this issue, 1 by `orch003`).

## AI Implementation Instruction
Apply the rename mechanically to all 7 occurrences; do not guess at a fix for
`test_orchestrator_integration.py`'s failure count beyond its 3 confirmed occurrences —
if failures remain after the rename, report them as a new, separate finding rather than
extending this issue's scope to cover them. Do not modify
`scripts/agent/orchestrator.py`.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-105759
- **Related target files**: see Target Files or Areas above
