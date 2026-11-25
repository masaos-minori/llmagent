## Goal
Make the persisted `tool_call_state` row carry the canonical argument hash, and add the turn-entry
reconstruction that turns `interrupted` replayable rows into replay directives.

## Scope
**Release unit**: persisted directive store

## Assumptions
- The row is the directive source of truth; no separate directive table is created (Plan Design D1).
- One-time consumption is recorded durably by the row's state transition (`interrupted` →
  `dispatch_starting` on replay), so a restarted process sees no directive for a consumed row.

Validation correction: the transition records consumption only once the row leaves the replayable states.
`classify_stale_pending` re-transitions a stale row at `dispatch_starting` to `interrupted` (mcpdl001 REQ-009),
so a row the replay left there produces a directive again; durable one-time consumption is recorded by the
terminal state the replay reaches. The query docstring states this.

## Design decisions
- This module returns persisted rows only; the directive object itself is declared by sibling
  procedure seq 06 (`agent.tool_preparation`), so no new type is introduced here and no import from
  `agent.tool_preparation` is added — the module keeps its current dependency set.

## Alternatives considered
- Building directive objects inside `tool_call_state_ops` — rejected: it would import an `agent`
  preparation type into the workflow layer and duplicate a type the preparation phase owns.

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`

### Procedure
Extend the write path and the row mapping with `args_hash`, and add the reconstruction query.

### Method
- `record_tool_call` gains an `args_hash` parameter and adds the column to the INSERT column list.
- `ToolCallState` gains `args_hash: str`; `_row_to_state` reads `row["args_hash"]`.
- Add `reconstruct_replay_directives` (new) that returns this task's `interrupted` rows with
  `retry_class = 'retryable'` as `list[ToolCallState]`.

### Details
- The reconstruction query filters `task_id` and `state = 'interrupted'` and `retry_class`, reusing
  `idx_tool_call_state_task_state`; it reads only, never writes, so it cannot race the guarded
  UPDATE in `classify_stale_pending`.
- `classify_stale_pending` remains the only writer of `interrupted`; reconstruction runs after it at
  turn entry, so rows it lists are the same rows the directive is built from.
- INSERT OR IGNORE behavior is unchanged: a re-recorded key is still a no-op, and the stored hash
  stays the one written by the first insert.

## Compatibility considerations
`_row_to_state` reads a column that only exists after sibling procedure seq 01 lands; the two rows
are in the same release unit.

## Security considerations
N/A: the hash is already computed at preparation; no new trust boundary.

## Rollback considerations
Revert the commit as a unit with sibling procedure seq 01; the dataclass field and the DDL column
cannot be rolled back independently.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py` — recorded rows carry the hash;
  reconstruction returns rows only for `interrupted` replayable rows.
- Full sequence per `rules/toolchain.md` (ruff, mypy, lint-imports).

## Completion criteria
A recorded row stores the hash, `_row_to_state` exposes it, and reconstruction lists exactly the
`interrupted` replayable rows for the task.

## Out of Scope
No directive type, no consumption bookkeeping beyond the row state, no change to
`mcp_dedup.sqlite`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `record_tool_call`, `ToolCallState`, `_row_to_state` | Completed | — | 20261125-122656 | stale detection clean; changed: scripts/agent/workflow/tool_call_state_ops.py |
| 2 | Add `reconstruct_replay_directives` (new) | Completed | — | 20261125-122656 | reconstruct_replay_directives added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-122656 | 2026-11-25 | ruff/mypy/bandit/module-size pass; 11 red states: record_tool_call call sites updated by procedure 12 end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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
- **Requirement ID**: `REQ-001` (directive fields and one-time consumption), `REQ-006` (persisted hash)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`