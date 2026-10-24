## Goal

Remove the adapter's now-duplicate turn-end ownership so the Orchestrator bracket is the only
emitter of `turn_end` (`REQ-005`, `REQ-006`), while keeping the engine's required `verify` stage
intact (`REQ-011`).

## Scope

- **In-Scope**: deleting `_handle_turn_end` (`:369-385`), `_format_session_id` (`:206-208`),
  `_build_turn_end_event` (`:210-228`), `_build_turn_end_metadata` (`:230-239`),
  `_build_turn_end_llm_stats` (`:241-...`); making `verify_fn` (`:178-183`) a documented no-op;
  removing the `_deactivate_workflow` call at `:199`; stripping the `ctx.workflow.*` assignments
  from `_handle_workflow_halt` (`:311-321`) while keeping its logging and `self._on_error(exc)`.
- **Out-of-Scope**: `execute_turn`'s signature (`:131-137`), the return tuple (`:204`),
  `_init_workflow_task` (`:252-292`), `_activate_workflow` (`:298-303`), the public aliases
  (`:109-118`), the status block at `:190-198` (turn003's shape), and this file's callers in
  `orchestrator.py` (sibling document).

## Assumptions

- The Orchestrator sibling emits `turn_end`, so the adapter's copy is unreachable after both land.
- `workflow_loader.py:49` requires the `verify` stage to remain in the engine signature even though
  it performs no work.
- No other file in `scripts/` or `tests/` references the five deleted symbols (verified by `rg`).

## Design decisions

- Delete the dead turn-end builders wholesale rather than leaving no-op stubs: they are only
  reached through `verify_fn`, which becomes a no-op, so their bodies are unreachable (`REQ-006`).
- Keep `_handle_workflow_halt`'s `logger.error` (`:316`) and `self._on_error(exc)` (`:320-321`)
  because the Orchestrator still relies on the error hook; only the workflow-state mutation moves
  to the caller's bracket.

## Alternatives considered

`N/A: replacing the builders with no-ops would keep dead code and keep `vulture` /
`check_module_size.py` noisy (`REQ-006`); deletion is the Plan's chosen correction.`

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. Delete `_handle_turn_end` (`:369-385`) in full.
2. Delete the three builders `_build_turn_end_event` (`:210-228`),
   `_build_turn_end_metadata` (`:230-239`), `_build_turn_end_llm_stats` (`:241-...`) in full.
3. Delete `_format_session_id` (`:206-208`).
4. Rewrite `verify_fn` (`:178-183`) to a documented no-op:
   ```python
   async def verify_fn() -> str | None:
       # The verify stage is required by workflow_loader.py:49; turn-end work
       # moved to the Orchestrator's _execute_turn bracket (see its plan). No-op.
       return None
   ```
5. In `execute_turn`'s `finally`, remove the `self._workflow_adapter.deactivate_workflow(self._ctx)`
   call at `:199` (the Orchestrator now owns teardown). Leave the task-status update block
   (`:190-198`) untouched — it is turn003's shape.
6. In `_handle_workflow_halt` (`:311-321`), delete the `ctx.workflow.active = False`,
   `ctx.workflow.current_task_id = None`, `ctx.workflow.workflow_id = None` assignments, but keep
   `logger.error(...)` (`:316`) and `self._on_error(exc)` (`:320-321`).
7. Confirm no remaining reference to any deleted symbol remains in `scripts/` or `tests/`.

### Method

Inline deletions and one small rewrite; no new symbols. The file shrinks from 14798 B, gaining
headroom under the 16384 B gate for turn003's additions.

### Details

- `verify_fn` currently calls `self._handle_turn_end(...)` at `:180-182`; that call is what makes
  the builders reachable today. Removing both the call (by no-opifying `verify_fn`) and the
  builders together keeps the file consistent.
- Do not touch `execute_turn`'s public behavior: it still returns `(answer, error_kind, is_partial)`
  at `:204` and still runs `engine.run(task, plan_fn, execute_fn, verify_fn)`.

## Compatibility considerations

`execute_turn`'s signature and return value are unchanged, so `orchestrator.py`'s call site
(sibling document) is unaffected except that teardown moved out. The public aliases (`:109-118`)
are untouched.

## Security considerations

`N/A: no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- `tests/agent/test_orchestrator.py` still exercises all five exit paths via the mock engine
  fixture (`:142-…`); the integration suite (`tests/integration/test_orchestrator_integration.py`,
  out of scope) must still pass.
- `vulture` reports no dead-code warnings for the deleted symbols (they are gone).
- `check_module_size.py` confirms the file is under the size gate.
- Full agent test suite passes (`rules/toolchain.md`).

## Completion criteria

All five turn-end symbols (`_handle_turn_end`, `_build_turn_end_event`,
`_build_turn_end_metadata`, `_build_turn_end_llm_stats`, `_format_session_id`) are removed,
`verify_fn` is a documented no-op returning `None`, the `finally` no longer calls
`deactivate_workflow`, and `_handle_workflow_halt` keeps its log + error hook without mutating
`ctx.workflow.*`. No `rg` reference to any deleted symbol remains.

## Out of Scope

The Orchestrator bracket (`orchestrator.py`), the emitter's `task_id` parameter
(`audit_event_emitter.py`), the `TurnState` dead fields (`context.py`), the tests, and the doc
passages are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete turn-end symbols, no-op `verify_fn`, move teardown out (`Implementation > Procedure`) | Pending | — | — | depends on orchestrator bracket landing in same commit |
| 2 | Add or update tests per Validation plan | N/A: covered by test_orchestrator.py sibling | | | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `vulture`, `check_module_size.py`, full suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 2 | turn002 (`plans/20261023-102728_plan.md`) and turn003 (`plans/20261023-125756_plan.md`) rewrite this file's regions first; either they land first or the anchors are re-located before editing | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (remove adapter turn-end ownership), `REQ-006` (delete dead
  builders), `REQ-007` (move teardown + halt state clearing to the caller), `REQ-011` (keep the
  `verify` stage, do not change units)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
