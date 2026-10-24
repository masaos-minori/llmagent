## Goal

Drop the dead `task_id` parameter from `build_turn_end_event` (`REQ-008`). Its body never reads
it — the event's task id always comes from `build_turn_end_metadata(ctx)` →
`ctx.turn.current_turn_id` — so the parameter is misleading and only a call site depends on it.

## Scope

- **In-Scope**: removing the `task_id: str | None` parameter from `build_turn_end_event`
  (`:107-113`) and updating its single call site in `emit_turn_end` (`:139-141`).
- **Out-of-Scope**: `emit_turn_start` (`:71-92`), `emit_turn_end` (`:127-145`) beyond the call
  site, `format_session_id` (`:66-69`), the hook wiring, and the event dict keys (all unchanged).

## Assumptions

- `build_turn_end_event` has exactly one caller in the repository (the `emit_turn_end` call at
  `:139-141`); verified by `rg`.
- The event dict keeps every key it has today; only the unused argument is removed.

## Design decisions

- Remove the parameter and reposition `is_partial` as the trailing argument so the call site reads
  `build_turn_end_event(elapsed_ms, error_kind, is_partial)`.
- Leave the event dict construction untouched so the emitted `turn_end` fields are byte-for-byte
  identical (`REQ-008`).

## Alternatives considered

`N/A: keeping the parameter for forward-compat would violate the deprecation policy
(rules/coding.md) — a zero-use parameter is removed the next time the plan touches the file;
this is that time (`REQ-008`).`

## Implementation

### Target file

`scripts/agent/audit_event_emitter.py`

### Procedure

1. In `build_turn_end_event` (`:107-113`), delete the `task_id: str | None` parameter line so the
   signature becomes
   `(self, elapsed_ms: float, error_kind: str | None, is_partial: bool = False)`.
2. Update the call site in `emit_turn_end` (`:139-141`) from
   `self.build_turn_end_event(elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial)` to
   `self.build_turn_end_event(elapsed_ms, error_kind, is_partial)`.
3. `rg` for `build_turn_end_event` across `scripts/` and `tests/` to confirm the call site was the
   only one; if another exists, update it too.

### Method

Inline edits; no new symbols. File stays ~5533 B (no baseline entry needed).

### Details

- The old call passed `ctx.turn.current_turn_id` as `task_id`; that value still reaches the event
  via `build_turn_end_metadata(ctx)` at `:118`, so removing the argument changes nothing in the
  output.
- `emit_turn_end`'s own signature (`:127-134`) and its `ctx.turn.current_turn_id = None` clear
  (`:145`) are unchanged.

## Compatibility considerations

`emit_turn_end`'s public signature is unchanged; only the private `build_turn_end_event` shrinks.
No external caller exists outside this module.

## Security considerations

`N/A: no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- `tests/agent/test_orchestrator.py` event-field assertions (`T-1`) still hold — the emitted
  `turn_end` dict is unchanged.
- `ruff` + `mypy` pass (removing a parameter must not break the call site; re-check after step 2).
- Full agent test suite passes (`rules/toolchain.md`).

## Completion criteria

`build_turn_end_event` has no `task_id` parameter, its sole call site in `emit_turn_end` is
updated, the emitted `turn_end` event dict is unchanged, and no `rg` reference to the old
four-argument call remains.

## Out of Scope

The Orchestrator bracket (`orchestrator.py`), the adapter deletions
(`workflow_engine_adapter.py`), the `TurnState` dead fields (`context.py`), the tests, and the doc
passages are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop dead `task_id` param + update call site (`Implementation > Procedure`) | Pending | — | — | run after adapter deletes so the call graph is clean |
| 2 | Add or update tests per Validation plan | N/A: event dict unchanged | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `ruff`, `mypy`, full suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (remove the dead `task_id` parameter, keep all event keys)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `scripts/agent/audit_event_emitter.py`
