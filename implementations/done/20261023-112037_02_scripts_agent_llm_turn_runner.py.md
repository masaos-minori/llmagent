## Goal

Pass `LLMTurnRunner`'s own guard instance to `execute_all_tool_calls` at its only production
call site, replacing the implicit dependency the plan removes from `tool_runner.py`
(`REQ-001`, `AC-1`, `AC-4`).

## Scope

Only `scripts/agent/llm_turn_runner.py`. One edit: add `guard=self._guard` to the
`execute_all_tool_calls` call at `:115-120`. Reference reads only: `check_all` (`:98`),
`check_empty_result_repeat` (`:125`), `check_error_limit` (`:129`), the `_guard` field
(`:57`), and the `execute_all_tool_calls` import (`:20`).

## Assumptions

- `self._guard` is the per-turn `ToolLoopGuard` assigned in `__init__` (`:57`) and already
  consumed by `check_all`/`check_empty_result_repeat`; passing it by keyword adds no new
  lifetime.
- No other production caller of `execute_all_tool_calls` exists (the plan's only production
  caller claim, verified by grep).

## Design decisions

- **Pass `guard=self._guard` positionally-safe as a keyword argument** so the new required
  keyword-only parameter (`tool_runner.py`, row 1) is satisfied without disturbing the
  existing `out_failed_keys=state.failed_calls` keyword at `:119`.

## Alternatives considered

- Reading the guard from `ctx` — rejected by `REQ-001`: that is the dead `getattr` path
  being removed; the runner already holds the live instance.

## Implementation

### Target file

`scripts/agent/llm_turn_runner.py`

### Procedure

At the `execute_all_tool_calls(...)` call spanning `:115-120`, add `guard=self._guard` as a
keyword argument alongside `out_failed_keys=state.failed_calls`. Nothing else in the file
changes.

### Method

The call currently reads (paraphrasing `:115-119`):
`await execute_all_tool_calls(ctx, <tool_calls>, turn=<turn>, out_failed_keys=state.failed_calls)`.
Insert `, guard=self._guard` before the closing paren.

### Details

- `self._guard` is typed `ToolLoopGuard`; the parameter type in
  `scripts/agent/tool_runner.py` is the same non-optional `ToolLoopGuard` (`REQ-002`), so
  mypy accepts the assignment.
- Do not touch `check_all` (`:98`) or `check_empty_result_repeat` (`:125`); they already use
  `self._guard`.

## Compatibility considerations

### Corrections found while implementing

- Implemented as written (`guard=self._guard` at the single production call site). A grep of `scripts/` confirms there is no other caller.


- This is the sole production caller of the changed signature; the 28 test callers migrate in
  rows 4-6. `check_mock_patch_targets.py` stays green because the patch targets are unchanged.

## Security considerations

- N/A: no new data or permission path; the guard carries tool-result counts only.

## Rollback considerations

- N/A: revert the commit; one-line addition.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/` is clean (only caller now supplies `guard`).
- `uv run pytest tests/agent/test_llm_turn_runner.py tests/agent/test_orchestrator.py -q`
  keeps the mocked-entry-point suite passing unchanged.

## Completion criteria

The `execute_all_tool_calls` call at `:115` passes `guard=self._guard`; mypy is clean; the
mocked turn/orchestrator tests pass unchanged.

## Out of Scope

- The parameter definition and recording in `scripts/agent/tool_runner.py` (row 1).
- The docstring correction (row 3), test migrations (rows 4-7), reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `guard=self._guard` to the `execute_all_tool_calls` call at :115 | Completed | 20261023-163750 | 20261023-163750 | REQ-001; only production caller implemented; full suite 9909 passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-163750 | 20261023-163750 | mypy clean; mocked suite green |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `scripts/agent/llm_turn_runner.py`