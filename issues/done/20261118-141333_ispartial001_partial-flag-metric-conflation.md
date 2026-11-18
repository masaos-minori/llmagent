# `is_partial` audit metric conflates partial-text with turn compensation

## Priority
Low

## Summary
Split the two distinct conditions joined into the `is_partial` value returned from
`Orchestrator._execute_turn` so the `partial_completion` audit metric is not reported True
for a compensated turn that had no partial text.

## Background
`orchestrator.py::_execute_turn` computes, in the `except BaseException` branch,
`is_partial = bool(getattr(exc, "partial_text", "")) or compensated`, where `compensated`
is the result of `boundary.rollback_partial_turn()`. The value is returned through
`workflow_engine_adapter.execute_turn` and recorded as the `partial_completion` field of
the turn-end audit event (`audit_event_emitter.py`).

## Problem
`is_partial` is True when either the exception carried partial text OR the turn's partial
DB rows were rolled back. These are unrelated conditions joined by `or`. A turn that was
compensated (rows deleted) without any partial LLM text therefore reports
`partial_completion=true`, which mislabels a clean rollback as a partial completion.

## Reason for Change
The metric currently feeds only an audit field, so no downstream behavior depends on it,
but a misleading `partial_completion=true` can corrupt analytics/dashboards built on the
audit stream and hides the distinction between "generation cut off" and "turn rolled
back cleanly." Non-blocking; fixable without a behavior change elsewhere.

## Implementation Intent
Track the two signals separately at the point they are known: `had_partial_text` from
`exc.partial_text` and `was_compensated` from `rollback_partial_turn()`. Pass both through
`workflow_engine_adapter.execute_turn` (extend the returned tuple or carry them on a small
result object) and expose them to `audit_event_emitter` so the audit event can record them
independently, or keep a single `is_partial` only if its documented meaning is widened to
"turn did not complete cleanly." Preserve the existing `ConversationPersistenceError`
branch (`is_partial=False`) and the rest of the turn contract.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`_execute_turn`)
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn` return value)
- `scripts/agent/audit_event_emitter.py` (`partial_completion` field)

## Required Changes
- Compute `had_partial_text` and `was_compensated` as separate booleans in the
  `except BaseException` branch.
- Propagate both to the audit emitter, or widen and re-document `is_partial` if a single
  flag is retained.
- If a single flag is kept, update its docstring/comment to state the widened meaning.

## Constraints
- Do not change the `ConversationPersistenceError` branch (`is_partial` stays False).
- Do not change how `is_partial` is consumed elsewhere beyond the audit metric.
- Preserve the turn contract shape used by the REPL (`stat_partial_completions` warning,
  `/stats`). Note `issues/done/20261031-180511_partialcount001` already fixed a separate
  counter bug in this area.

## Acceptance Criteria
- A compensated turn with no partial text reports `partial_completion=false`.
- A turn whose exception carried partial text reports `partial_completion=true`.
- The audit event still carries the information needed for observability.

## Testing Expectations
- Unit test: orchestrator `except BaseException` branch with a partial-text exception sets
  the partial signal True; with a non-partial exception plus a compensating boundary sets
  the compensation signal True and the partial signal False.
- `ruff` and `mypy --no-namespace-packages` on the touched files; existing orchestrator and
  audit tests pass unchanged.

## Documentation Impact
Not required unless docs describe the `partial_completion` audit field's meaning; if so,
align it with the separated signals.

## Out of Scope
- Changing whether partial completions are recovered/resumed (by design; see
  partialcount001 Out of Scope).
- Changing the persistence/compensation logic itself.

## Dependencies
N/A: none. `issues/done/20261031-180511_partialcount001_partial-completion-counter-dead.md`
addressed a different partial-completion bug (the counter) and constrains this area.

## Unresolved Questions
- Whether anything downstream consumes the `partial_completion` audit field beyond a count
  (不明); if nothing does, the fix is purely metric-accuracy.

## AI Implementation Instruction
Separate the partial-text and compensation signals in `scripts/agent/orchestrator.py`,
propagate both through `workflow_engine_adapter.execute_turn`, and record them
independently in `audit_event_emitter`. Do not alter the `ConversationPersistenceError`
branch or the compensation logic. Stop and report if the `partial_completion` field has a
downstream consumer that would need the combined semantics.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-141333
- **Related target files**: scripts/agent/orchestrator.py, scripts/agent/workflow_engine_adapter.py, scripts/agent/audit_event_emitter.py
