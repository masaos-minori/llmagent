## Goal

Keep a preview out of applied-operation state (REQ-009): no `tool_call_state` row and no attempt-side-effect flag for a preview-mode call.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- Exclusion is chosen over a new `previewed` state, which would need a persisted-schema change (Plan Out-of-Scope).
- A preview of a non-READ tool still passes the approval and grant checks unchanged; only the recording is skipped.
- The replay-directive procedures edit this module first (Plan UNK-01); re-read `_record_pending_state` before editing.

## Design decisions

- `_record_pending_state` returns `None` for a preview before its fail-closed branch, so `_finalize_state` is already a no-op for it.
- `attempt_side_effect` is set only for a call that is not a preview, so a preview does not block a later retry.

## Alternatives considered

Writing a `previewed` row and excluding it from the applied listings was rejected: it adds a persisted state for an operation with nothing to recover.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
Add a preview guard to `_record_pending_state` and to the side-effect flag in `_execute_prepared_call`.

### Method
- In `_record_pending_state`, at the top, return `None` when `pc.context is not None and pc.context.execution_mode == "preview"`.
- In `_execute_prepared_call`, set `ctx.turn.attempt_side_effect = True` only when the call is not a preview; keep the grant check as it is.
- Update the docstrings of both functions to say a preview is not recorded.

### Details
- Audit (`audit_tool_exec`) still records the preview call; only workflow state is skipped.

### Companion test files
- `tests/agent/test_tool_runner.py`
  - Procedure: Add cases: a preview-mode prepared call leaves the recorder untouched and `attempt_side_effect` unset; an applied call of the same tool is recorded as before; a preview without a recorder does not raise.
  - Validation: `uv run pytest tests/agent/test_tool_runner.py`

## Compatibility considerations

Behavior change only for preview-mode calls, which did not exist as a mode before this Plan.

## Security considerations

A preview does not skip approval or grant checks, so skipping the state row does not widen what can run.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_preparation.py`
- `uv run mypy scripts/agent/tool_runner.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- A preview-mode call writes no `tool_call_state` row and does not set `attempt_side_effect`.
- Applied calls behave exactly as before.

## Out of Scope

- Schema or state vocabulary changes.
- Mode resolution (`tool_preparation.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-174157 | 20261125-174157 | changed; preview guard at the top of _record_pending_state, mode-scoped attempt_side_effect in _execute_prepared_call, both docstrings updated; stale check clean |
| 2 | Add or update tests per Validation plan | Completed | 20261125-174157 | 20261125-174157 | 3 cases added via _execute_with_dag plus a direct _record_pending_state call; _pc fixture gained execution_mode kwarg; 144 passed (141 existing + 3 new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending; generate_reference_table_check reports manifest drift for the new new_execution_context symbol, resolved by plan row procedure 37; Step 5 N/A: docs work is the plan row docs/23_agent/agent_13_reference-api-generated.md end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/agent/tool_runner.py`, `tests/agent/test_tool_runner.py`