# History fallback truncation rebuilds the list per dropped message (O(N·M))

## Priority
Low

## Summary
Replace the per-message list rebuild in `HistoryManager._apply_unit_drops` with a single
pass so fallback truncation does not degrade to O(N·M) when many turn units must be
dropped.

## Background
`scripts/agent/history.py::_fallback_truncate` drops whole turn units (never splitting one,
never orphaning a tool row, never emptying the history) to bring context under the char
limit when LLM-based compression fails. It is a fallback path, not the hot compression
path.

## Problem
`_apply_unit_drops` rebuilds `new_history = [x for x in new_history if x is not m]` for
every message in every drop-candidate unit. Dropping U units of k messages each from a
history of N messages is O(U·k·N); when most of the history must be dropped this
approaches O(N²).

## Reason for Change
Correctness is unaffected and the path is a fallback, but a large history that needs heavy
truncation pays a quadratic cost for an otherwise linear operation. Practical risk is
unconfirmed (不明) without profiling or history-size data; the change is a non-blocking
robustness improvement.

## Implementation Intent
Compute the set of protected/drop message ids once, then build the dropped history in a
single pass over `history`, keeping only messages outside the drop set. Preserve the
existing guarantees: whole-unit drops, no orphaned tool row, never-empty history, system
messages and the `protect_turns` tail preserved. Do not change the selection policy,
protected-turn handling, or the `_fallback_truncate` gating/reporting.

## Target Files or Areas
- `scripts/agent/history.py` (`_apply_unit_drops`, `_fallback_truncate`)

## Required Changes
- Replace the nested identity-scan rebuild in `_apply_unit_drops` with a single-pass
  partition over the history.
- Keep the same drop semantics (unit boundaries, never empty, protected ids).
- Add or adjust a unit test exercising heavy truncation and asserting the result equals
  the current output.

## Constraints
- Must preserve the no-orphan-tool-row and never-empty-history invariants (also required by
  `issues/done/20261026-224931_history001_token-overflow-compression-fallback.md`).
- Identity-based membership (`id(m)`) must stay correct even when two messages have equal
  content.
- Do not change `_fallback_truncate` gating, the selection policy, or protected-turn
  handling.

## Acceptance Criteria
- `_apply_unit_drops` produces identical output to the current implementation for the same
  inputs.
- A history where most units are dropped completes in a single linear pass instead of a
  per-message full-list scan.

## Testing Expectations
- Unit test asserting equivalence with the current output across several drop scenarios,
  including heavy truncation.
- `ruff` and `mypy --no-namespace-packages` on `history.py`; existing history tests pass
  unchanged.

## Documentation Impact
Not required unless the docs describe the fallback truncation algorithm's complexity; if
so, note it is a single-pass drop.

## Out of Scope
- Changing when fallback truncation triggers (see history001 for the token-path gating
  issue).
- Improving token estimation or compression selection.

## Dependencies
N/A: none. `issues/done/20261026-224931_history001_token-overflow-compression-fallback.md`
constrains the invariant this must preserve but is independent.

## Unresolved Questions
- Whether history size ever makes this measurable (不明); profile before merging if
  uncertain.

## AI Implementation Instruction
Rewrite `_apply_unit_drops` in `scripts/agent/history.py` to a single-pass drop preserving
unit boundaries, no-orphan-tool-row, and never-empty-history. Do not touch selection
policy, protected-turn handling, or `_fallback_truncate` gating. Add an equivalence unit
test.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-141240
- **Related target files**: scripts/agent/history.py
