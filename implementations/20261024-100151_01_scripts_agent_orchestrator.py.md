## Goal

Implement `REQ-001`: make `ctx.turn.background_tasks` the single authoritative registry for
background tasks by deleting the Orchestrator's private `self._background_tasks` set and re-pointing
both constructor injections (`BgTaskMonitor`, `ConversationStateManager`) at
`ctx.turn.background_tasks`. Remove the now-unused `import asyncio`.

## Scope

Only `scripts/agent/orchestrator.py`. The set is populated by
`conversation_state_manager.py` (pre-existing, commit `35a1e1969`); that file needs no edit
(plan traceability, `REQ-001`). `BgTaskMonitor`'s internal counter/threshold/pause logic is out of
scope here (row 02).

## Assumptions

- `ctx.turn` is a `TurnState` constructed once with `AgentContext` (`context.py:320`), so
  `ctx.turn.background_tasks` exists for the process lifetime and is written only by the producer.
- Both `BgTaskMonitor` and `ConversationStateManager` already accept an injected `tasks` set; their
  constructor signatures are unchanged, so re-pointing the argument is signature-neutral.
- The producer (`conversation_state_manager.py:112-118`) adds spawned tasks to whatever set it was
  given, so pointing both consumers at `ctx.turn.background_tasks` makes add/discard hit one set.

## Design decisions

- Delete the Orchestrator's private set entirely; the registry lives in `ctx.turn.background_tasks`
  (the object the shutdown coordinator already reads). One set, three readers (`DR-001`).
- Point both injections at `ctx.turn.background_tasks` by reference — no copy — so the producer's
  `.add()` and the monitor's `.discard()` operate on the same set object (`T-4`).

## Alternatives considered

- Keep the Orchestrator's set as the registry and inject it into the coordinator (`DR-004`):
  rejected — the coordinator is built before the Orchestrator in construction order
  (`repl.py:88` vs `startup_component_init.py:77`), requiring a new binding in files this Plan does
  not own.
- Copy the set into `ctx.turn.background_tasks`: rejected — a copy breaks the shared-reference
  contract; `add`/`discard` must hit one set.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Delete the private-set declaration `self._background_tasks: set[asyncio.Task[object]] = set()`
   (line 89).
2. In the `BgTaskMonitor(...)` call, replace `tasks=self._background_tasks` with
   `tasks=ctx.turn.background_tasks` (line 96).
3. In the `ConversationStateManager(...)` call, replace `tasks=self._background_tasks` with
   `tasks=ctx.turn.background_tasks` (line 113).
4. Remove `import asyncio` (line 24): after step 1 it is unused (`ruff` reports `F401` — measured).

### Method

`__init__` currently owns a second set (`:89`) that no reader of `ctx.turn.background_tasks` ever
sees — the coordinator reads `ctx.turn.background_tasks` while this set is the one the producer
populates, so cancellation never reaches the title task. Replace that declaration with a reference to
the context-owned set at both injection sites, then drop the now-dead import. `_on_discard`
(`:198-199`) is unchanged and still delegates to `BgTaskMonitor.on_task_done`. `handle_turn`,
`_execute_turn`, and the pause-notice path (`_on_pause_blocked`, `:185-196`) are not edited.

### Details

- Deletion — remove line 89 entirely:

  ```python
  self._background_tasks: set[asyncio.Task[object]] = set()
  ```

- `BgTaskMonitor` construction (lines 94-100) — re-point the `tasks=` argument:

  ```python
  self._bg_task_monitor = BgTaskMonitor(
      ctx,
      tasks=ctx.turn.background_tasks,
      on_discard=self._on_discard,
      on_error=self._on_error,
      pause_on_critical_failure=pause_on_critical_failure,
  )
  ```

- `ConversationStateManager` construction (lines 110-118) — re-point the `tasks=` argument:

  ```python
  self._conversation_manager = ConversationStateManager(
      ctx,
      diagnostic_store=self._diagnostic_store,
      tasks=ctx.turn.background_tasks,
      on_discard=self._on_discard,
      tracer=tracer,
      on_first_turn=on_first_turn,
      on_error=on_error,
  )
  ```

- Import removal — delete line 24 (`import asyncio`). Verified: `asyncio` appears nowhere else in
  the file (only at the deleted annotation at `:89`), so this is safe and removes the `F401` the
  deletion exposes.

## Compatibility considerations

No signature changes. `ctx.turn.background_tasks` already exists with type
`set[asyncio.Task[Any]]` (`context.py:200`); the consumers' `tasks` parameter expects exactly that.
No new public surface. `test_import_smoke.py` (AC-9) proves no cross-module import is added or
reordered.

## Security considerations

N/A: no authentication, authorization, or data-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_orchestrator.py`,
  `tests/agent/test_orchestrator_bg_failure_threshold.py`,
  `tests/agent/test_resource_shutdown_coordinator.py`, and `tests/agent/test_import_smoke.py`
  (`T-1`, `T-4`, `T-5`).
- `grep -rn "_background_tasks" scripts/agent/orchestrator.py` is empty;
  `grep -n "tasks=ctx.turn.background_tasks" scripts/agent/orchestrator.py` returns two matches;
  `grep -n "^import asyncio" scripts/agent/orchestrator.py` is empty (`AC-1`).
- Run the lint/type/import gates in `rules/toolchain.md` (`T-5`).

## Completion criteria

- `Orchestrator.__init__` no longer declares `self._background_tasks`; both injections pass
  `ctx.turn.background_tasks`.
- `import asyncio` removed from the file.
- `AC-1` grep checks pass; the suites pass; `test_import_smoke.py` passes.

## Out of Scope

- `conversation_state_manager.py` spawn/add site (pre-existing dependency).
- `BgTaskMonitor` counter/threshold/pause internals (row 02).
- `scripts/agent/bg_task_monitor.py`, `scripts/agent/resource_shutdown_coordinator.py`,
  `scripts/agent/context.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | delete private set, re-point two injections, drop unused import |
| 2 | Add or update tests per Validation plan | Pending | — | — | tests already exist (T-1, T-4); verify they pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/lint-imports/check_module_size |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs-only rows are elsewhere in the plan. |

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
- **Requirement ID**: `REQ-001` — make `ctx.turn.background_tasks` the single tracked-task registry; delete the Orchestrator's private set and re-point both injections
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `scripts/agent/orchestrator.py`
