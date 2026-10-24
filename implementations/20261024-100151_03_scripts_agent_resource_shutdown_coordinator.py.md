## Goal

Implement `REQ-002` and `REQ-006`: make the coordinator read `ctx.turn.background_tasks` as a
guaranteed field (remove the `hasattr` guard) by extracting the cancel-and-join block into one named
private method `_cancel_tracked_tasks()`, and correct the four LIFO/ordering claims the code's own text
makes about a `set`-backed registry (`REQ-006`).

## Scope

Only `scripts/agent/resource_shutdown_coordinator.py`. The WAL checkpoint/backup steps (`:70-111`) and
the error-summary presentation (`:161-164`) are owned by the landed `plans/done/20261022-043330_plan.md`
(shutdown001); the lifecycle/http step (`:139-159`) by `plans/done/20261022-082349_plan.md` (shutdown003).
The test rewrite lives in row 07 (`test_resource_shutdown_coordinator.py`).

## Assumptions

- `AgentContext.turn` is assigned once at `context.py:320`, so `self._ctx.turn.background_tasks` is a
  guaranteed field for the two production callers (`repl.py:88`, the startup-failure path); the
  `hasattr` guard protects a shape no production code produces.
- The registry is a `set` of `asyncio.Task` objects with no creation order, so any iteration order is
  arbitrary.
- `asyncio_mode = "auto"` lets the migrated test use `async def`.

## Design decisions

- Extract `:121-137` into `async def _cancel_tracked_tasks() -> list[tuple[str, str]]` and call it as
  `errors.extend(await self._cancel_tracked_tasks())` at the same position in `close_resources`, so
  `errors`' content and ordering are unchanged.
- Delete the `hasattr` double guard; the field is typed in via `AgentContext`.
- Delete the LIFO rationale and the "history-write task" example rather than documenting around them
  (`DR-005`): no producer creates two tasks, and the measured order never held.

## Alternatives considered

- Make the registry insertion-ordered to render "LIFO" real (`DR-005`): rejected — no producer creates
  two tasks and no task depends on another; inventing ordering serves a dependency that does not exist.
- Keep the guard: rejected — its only test (`test_no_turn_attribute_no_crash`) is replaced, and the
  guard's contract is unreachable in production.

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

1. Add `async def _cancel_tracked_tasks(self) -> list[tuple[str, str]]` holding the snapshot-then-clear,
   cancel, and `asyncio.gather` join moved from `close_resources` (`:121-137`).
2. In `close_resources`, replace the guarded block (`:113-137`) with
   `errors.extend(await self._cancel_tracked_tasks())` at the same position (after the WAL fallback
   backup, before the service-shutdown step).
3. Rewrite the module docstring line (`:7`), the class-docstring passages (`:41`, `:43-44`), and the
   inline comments (`:113-118`, `:128`) per `REQ-006`.

### Method

`close_resources` currently inlines the cancel-and-join behind a `hasattr` guard. Extract that block
into `_cancel_tracked_tasks`, which reads the registry directly (no guard), snapshots then clears it
(so the done callback's `discard` is a no-op and no task is cancelled twice), cancels the snapshot,
and joins via `asyncio.gather(return_exceptions=True)`, collecting only non-`Exception`-free results —
a clean cancellation yields a `CancelledError` instance, which is not an `Exception`, so it adds no
error record (`REQ-005`, `UNK-01`).

### Details

Reference shape:

```python
async def _cancel_tracked_tasks(self) -> list[tuple[str, str]]:
    """Cancel and join the tracked background tasks.

    The registry is a ``set`` of ``asyncio.Task`` objects with no creation order,
    so cancellation order is arbitrary; ``reversed()`` over the snapshot is an
    arbitrary-order reversal, not LIFO. A clean cancellation is not recorded as a
    shutdown error (``CancelledError`` is not an ``Exception``).
    """
    pending_tasks = list(self._ctx.turn.background_tasks)
    self._ctx.turn.background_tasks.clear()
    errors: list[tuple[str, str]] = []
    if pending_tasks:
        logger.info(
            "Cancelling %d tracked background tasks during shutdown",
            len(pending_tasks),
        )
        for t in reversed(pending_tasks):
            t.cancel()
        results = await asyncio.gather(*pending_tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                errors.append(("task_cancellation", f"{type(res).__name__}: {res}"))
    return errors
```

`close_resources` at the former guard position (`:113-137`):

```python
errors.extend(await self._cancel_tracked_tasks())
```

Docstring/comment corrections (`REQ-006`):

- Module docstring line `:7`: drop "in LIFO order (last-created-first-cancelled)"; state the step
  cancels the tracked background tasks and that their order is arbitrary.
- Class docstring (`:41`, `:43-44`): drop "including a history-write task" (no producer creates one —
  `write_history()` runs synchronously at `:67`) and the "LIFO (last-created-first-cancelled)" sentence;
  keep the checkpoint-before-cancellation fact (the WAL checkpoint does run first) and state that the
  remaining tasks have no defined order.
- Inline comment at `:113-118`: replace the "deterministic shutdown / most-recently-created first /
  avoids cancelling critical operations" rationale with a statement that the registry is an unordered
  set and only registered background tasks are cancelled.
- Inline comment at `:128`: replace "Cancel in reverse order (LIFO) for deterministic shutdown" with a
  note that `reversed()` over the snapshot is an arbitrary-order reversal.

`_SHUTDOWN_TIMEOUT_S` (`:30`), the WAL steps, the lifecycle/http step, and the summary are not edited.
`UNK-06` records that the `asyncio.gather` join stays unbounded.

Complexity (measured): `close_resources` `D (21)` → `C (15)`; `ResourceShutdownCoordinator` `C (12)` →
`B (8)`; new `_cancel_tracked_tasks` `A (5)`. The file is 7185 B; `check_module_size` reports no
violation. The residual `C (15)` on `close_resources` is the WAL branch another Plan's landed code
owns (`UNK-07`).

## Compatibility considerations

`close_resources` still returns `None` and still appends the same `list[tuple[str, str]]` to `errors`
in the same order, so the landed reporting code (`:161-164`) is unaffected. `test_repl.py`'s 80 tests
(including `test_checkpoint_completes_before_pending_task_cancelled` at `:1226`) pass unchanged and are
the witness that `AC-3` (checkpoint-before-cancellation order) holds.

## Security considerations

N/A: no authentication, authorization, or data-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_resource_shutdown_coordinator.py` and `tests/agent/test_repl.py` (`T-1`,
  `T-5`). The rewritten `TestSelectiveTaskCancellation` asserts `cancelled()`/`done()`, the empty
  registry, the absence of a `task_cancellation` record and a `Resource close errors` line, and the
  checkpoint-before-cancellation order.
- Mutation control: re-adding the `hasattr` guard, or dropping the `await asyncio.gather`, must fail
  this test (`T-1`).
- Static gates in `T-5` (`ruff`, `mypy`, `vulture`, `bandit`, `check_module_size`, `radon`).

## Completion criteria

- `close_resources` calls `errors.extend(await self._cancel_tracked_tasks())` between the WAL fallback
  backup and the service-shutdown step.
- The `hasattr` guard is gone; the four LIFO/history-write claims are removed (`AC-7`).
- A clean cancellation records no error (`AC-6`); the suite passes; complexity does not worsen.

## Out of Scope

- The test rewrite (`test_resource_shutdown_coordinator.py::TestSelectiveTaskCancellation`) — row 07.
- The WAL steps, the error summary, and the lifecycle/http step (other Plans' landed code).
- `UNK-01` (whether the `task_cancellation` branch can ever fire) — attempted here, recorded either
  way.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | extract _cancel_tracked_tasks, remove guard, fix docstrings |
| 2 | Add or update tests per Validation plan | Pending | — | — | test rewrite in row 07 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/vulture/bandit/check_module_size/radon |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-002` (read registry as guaranteed field; extract `_cancel_tracked_tasks`) and `REQ-006` (correct the four ordering claims)
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `scripts/agent/resource_shutdown_coordinator.py`
