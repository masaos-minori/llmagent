## Goal

Implement `REQ-003` and `REQ-004`: make `BgTaskMonitor.on_task_done` total over a task's terminal
states by checking `task.cancelled()` before reading `task.exception()` (so a cancelled task never
raises `CancelledError` out of the callback), treat a clean cancellation as a counter reset, and move
the unchanged failure ladder into three private helpers.

## Scope

Only `scripts/agent/bg_task_monitor.py`. The tracked set the monitor discards from is supplied by
`REQ-001` (`ctx.turn.background_tasks`). The test migration that lets these assertions run against a
real task lives in rows 05 (`test_orchestrator_bg_failure_threshold.py`) and 06
(`test_orchestrator.py`); this row changes only the monitor.

## Assumptions

- `asyncio.CancelledError` derives from `BaseException`, not `Exception` (measured
  `issubclass(CancelledError, Exception) is False`), so a clean cancellation must be detected via
  `task.cancelled()`, not via `task.exception()`.
- The failure-ladder behavior below/above `BG_FAILURE_THRESHOLD` (10) is intentionally unchanged
  (`REQ-004`); only the cancellation ordering is new.
- `asyncio_mode = "auto"` (in `pyproject.toml`) lets the migrated tests use `async def` without a
  marker.

## Design decisions

- Order the terminal-state check the way asyncio requires: `task.cancelled()` first (reset), then
  `task.exception()` only on the non-cancelled path. The task is discarded from the registry in
  every branch.
- Split the moved ladder into three `A`-grade private helpers — `_count_failure()` (counter
  arithmetic + the two exception-type guards), `_report_first_failure()` (first-failure warning +
  `on_error`), and `_report_threshold_failure()` (threshold/burst log + threshold notification) —
  leaving `on_task_done` at `A (2)`.

## Alternatives considered

- A two-way split (ladder into one helper): rejected — it leaves the counting helper at `C (11)` and
  does not meet the measured complexity target.
- Typing the helper parameters `BaseException`: rejected — mypy fails against the
  `on_error: Callable[[Exception], None]` annotation at the call site; the parameters are typed
  `Exception` because the call site gates on `isinstance(exc, Exception)`.

## Implementation

### Target file

`scripts/agent/bg_task_monitor.py`

### Procedure

1. Rewrite `on_task_done` (`:73-120`) so it checks `task.cancelled()` before `task.exception()`,
   resets the counter on a clean cancellation, routes a real `Exception` through the three helpers,
   and discards the task from `self._tasks` in every branch.
2. Add `_count_failure()`, `_report_first_failure()`, and `_report_threshold_failure()` holding the
   ladder moved out of `on_task_done`, unchanged in behavior.
3. Leave `__init__` (`:40-56`), `_notify_threshold_breach` (`:129-150`), `notify_bg_failure_threshold`
   (`:122-127`), `bg_pause_state`, and `get_consecutive_failures` (`:160-162`) untouched.

### Method

`on_task_done` currently reads `task.exception()` (`:76`) first; for a real cancelled task that call
*raises* `CancelledError`, so the bookkeeping at `:119-120` is never reached and asyncio logs
`Exception in callback BgTaskMonitor.on_task_done()`. The `isinstance(exc, asyncio.CancelledError)`
branch (`:79-81`) is therefore dead for real tasks (reachable only through a mock). The fix is
ordering, not new logic: cancel-check first, then `exception()`. The counting/reporting ladder moves
verbatim into the three helpers.

### Details

Reference shape (preserve every existing counter/notification assertion — `T-3` pins it):

```python
def on_task_done(self, task: asyncio.Task[Any]) -> None:
    """Handle a completed background task across all terminal states.

    A cancelled task is neither a failure nor a success: its counter resets to 0
    (DR-002) and it is discarded from the registry. A failed task runs the
    unchanged failure ladder. ``task.exception()`` is never called on a cancelled
    task (``CancelledError`` derives from ``BaseException`` and would raise).
    """
    task_name = task.get_name()
    count = self._consecutive_failures.get(task_name, 0)

    if task.cancelled():
        count = 0
    else:
        exc = task.exception()
        if exc is not None:
            count = self._count_failure(task_name, exc, count)
            if count == 1:
                self._report_first_failure(task_name, exc)
            elif count >= BG_FAILURE_THRESHOLD:
                self._report_threshold_failure(task_name, exc, count)

    self._consecutive_failures[task_name] = count
    self._tasks.discard(task)
```

`_count_failure()` — counter arithmetic with the two exception-type guards as the first checks:

```python
def _count_failure(self, task_name: str, exc: Exception, count: int) -> int:
    if isinstance(exc, asyncio.CancelledError):   # coroutine surfaced CancelledError without the task being cancelled
        return 0
    if not isinstance(exc, Exception):            # a non-Exception BaseException leaves the streak intact
        return count
    return count + 1
```

`_report_first_failure()` — the original `count == 1` branch (warning + single `on_error` call with
the catch-all around `on_error`).

`_report_threshold_failure()` — the original `count >= BG_FAILURE_THRESHOLD` branch: log ERROR and
call `_notify_threshold_breach` when `count == BG_FAILURE_THRESHOLD` or `(count - BG_FAILURE_THRESHOLD) % 5 == 0`, otherwise log WARNING.

Complexity after the split (measured in the Plan): `on_task_done` `C (11)` → `A (2)`; `_count_failure`
`A (4)`; `_report_first_failure` `A (3)`; `_report_threshold_failure` `A (4)`. The file stays at
6537 B, far below the 20480 B module-size gate.

## Compatibility considerations

No public surface changes: `notify_bg_failure_threshold` remains a backward-compatible alias for
`_notify_threshold_breach`, and `get_consecutive_failures` / `bg_pause_state` are unchanged. The
Orchestrator still attaches `on_task_done` as the done callback (`orchestrator.py:_on_discard`).

## Security considerations

N/A: no authentication, authorization, or data-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_orchestrator_bg_failure_threshold.py` and
  `tests/agent/test_orchestrator.py::TestDiscardAndLogConsecutiveFailures` once migrated to real
  tasks (`T-2`, `T-3`). The failure-ladder tests must pass against **both** the current and the
  changed code — they pin "no behavior change", not the fix.
- Mutation control: reading `task.exception()` before `task.cancelled()` reproduces the old
  `CancelledError` raise and fails the cancelled-task test (`AC-4`).
- Static gates in `T-5` (`ruff`, `mypy`, `vulture`, `bandit`, `check_module_size`).

## Completion criteria

- `on_task_done` checks `task.cancelled()` before `task.exception()` and discards the task in every
  branch.
- A real cancelled task with a seeded counter ends with the counter at 0 and no asyncio callback
  error (`AC-4`).
- The failure ladder is unchanged for a failed task (`AC-5`).
- Complexity does not worsen; the module-size gate passes.

## Out of Scope

- The test migration to real tasks (`test_orchestrator_bg_failure_threshold.py`,
  `test_orchestrator.py`) — rows 05-06.
- `REQ-001`'s registry wiring (`orchestrator.py`) — row 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | cancel-check ordering + three private helpers |
| 2 | Add or update tests per Validation plan | Pending | — | — | tests already exist; migrate to real tasks in rows 05-06 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/vulture/bandit/check_module_size |
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
- **Requirement ID**: `REQ-003` (cancellation is a terminal state → reset + discard) and `REQ-004` (failure ladder unchanged, moved to private helpers)
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `scripts/agent/bg_task_monitor.py`
