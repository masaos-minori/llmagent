## Goal

Implement `REQ-007` (migration) supporting `REQ-003`/`REQ-004`: migrate only
`TestDiscardAndLogConsecutiveFailures` (`tests/agent/test_orchestrator.py:1669-1873`, 8 test methods,
18 `_fake_task` call sites) from `MagicMock` tasks to real `asyncio.Task` objects, and delete the
now-unused `_fake_task` helper (whose docstring and the class docstring name `_discard_and_log()`, a
method that no longer exists).

## Scope

Only the `TestDiscardAndLogConsecutiveFailures` class in `tests/agent/test_orchestrator.py`. The file
is 2276 lines and shared with three other active Plans (`turn002`, `turn003`, `turn004`); every other
class — in particular `TestHandleTurnPauseGuard` (`:1876`) — is left untouched. The `_make_ctx` /
`_make_orchestrator` harness (`:35`, `:130-146`) is not changed. The monitor itself changes in row 02;
the registry wiring in row 01.

## Assumptions

- `asyncio_mode = "auto"` runs `async def` tests on a running loop without a marker.
- `from agent.context import ConversationState` is already imported (`:15`); `TurnState` must be added
  to that import so a real registry can be exercised.
- A real raising task returns its exception via `task.exception()`; a cleanly cancelled task reports
  `cancelled() is True` after being awaited (and would raise from `exception()`, so it must be awaited
  first).

## Design decisions

- Delete `_fake_task` (`:1675-1682`) and the class docstring's reference to `_discard_and_log()`
  (`:1670-1672`); add small module-level helpers that build real raising / successful / cancelled
  tasks.
- Convert the eight `def test_…` bodies to `async def`, replacing each `_fake_task(...)` call with a
  real task awaited to its terminal state. Keep every counter/notification-count assertion.
- Set `ctx.turn = TurnState()` in the class so `ctx.turn.background_tasks` is a real registry when the
  monitor discards from it (needed once row 01 points the monitor at `ctx.turn.background_tasks`;
  harmless against the current code).

## Alternatives considered

- Keeping `_fake_task`: rejected — a `MagicMock`'s `.cancelled()` is truthy, so a mock is always
  classified as cancelled and the fixed contract cannot be expressed.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Add `TurnState` to the `from agent.context import` import at the top of the file.
2. Add module-level helper coroutines (near `_make_ctx`): `_await_raising(message)`,
   `_successful()`, and `_make_cancelled(name)` — same shapes as in row 05.
3. In `TestDiscardAndLogConsecutiveFailures`: delete the `_fake_task` static method and rewrite the
   class docstring to drop the `_discard_and_log()` reference.
4. Convert each of the eight `def test_…` methods to `async def` and replace every
   `self._fake_task(...)` argument with a real task from the helpers, awaiting it before
   `orch._bg_task_monitor.on_task_done(...)`.
5. In the cancellation test, cancel the task and await it inside `pytest.raises(asyncio.CancelledError)`
   before calling `on_task_done`, and assert no warning/error was logged.
6. In each method that exercises the registry, set `ctx.turn = TurnState()` (e.g. right after
   `_make_ctx(ctx)`), before `_make_orchestrator(ctx)`.

### Method

The eight methods currently drive `on_task_done` with `_fake_task(RuntimeError(...))` (which returns
its exception rather than raising) and `_fake_task(asyncio.CancelledError())` (which returns a
`CancelledError` instance rather than raising). Real tasks differ: a raising task is awaited to settle
its captured exception; a cancelled task is awaited inside `pytest.raises` so `cancelled()` is true
before `on_task_done`. The helpers encode these shapes; the method bodies change only in how the task
is produced — all assertions are preserved.

### Details

Representative conversions:

- Failure ladder (`test_four_consecutive_failures_each_log_via_warning`,
  `test_fifth_consecutive_failure_logs_via_error`, `test_threshold_reached_notifies_exactly_once_with_task_name`,
  `test_threshold_notification_falls_back_to_critical_log_on_error_raising`,
  `test_threshold_reached_with_pause_enabled_sets_pause_state`):

  ```python
  task = await _await_raising("boom")
  orch._bg_task_monitor.on_task_done(task)
  ```

- Success reset (`test_success_after_failures_resets_counter_to_zero`):

  ```python
  success = await _successful()
  orch._bg_task_monitor.on_task_done(success)
  ```

- Cancellation reset (`test_cancelled_error_after_failures_resets_counter_and_logs_nothing`):

  ```python
  cancelled = await _make_cancelled("test_bg_task")
  with (
      patch("agent.bg_task_monitor.logger.warning") as mock_warning,
      patch("agent.bg_task_monitor.logger.error") as mock_error,
  ):
      orch._bg_task_monitor.on_task_done(cancelled)
  assert orch._bg_task_monitor.get_consecutive_failures("test_bg_task") == 0
  mock_warning.assert_not_called()
  mock_error.assert_not_called()
  ```

`test_threshold_reached_with_pause_disabled_leaves_pause_state_empty` (`:1860-1873`) is migrated like
the others; it passes today for the wrong reason (a mock's `.exception()` returning `None` reads as
"success"), and the real-task version now genuinely exercises the success path.

## Compatibility considerations

File-scoped and class-scoped within the file: only `TestDiscardAndLogConsecutiveFailures` changes.
`check_mock_patch_targets.py` guards the patch targets; the other three Plans' classes are untouched,
so their tests keep passing.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py::TestDiscardAndLogConsecutiveFailures -q` — all eight
  tests pass against both the current and the changed monitor (`T-3`).
- `grep -n "_fake_task" tests/agent/test_orchestrator.py` is empty (`AC-8`).
- Run the full `tests/agent/test_orchestrator.py` suite — no regression in the other classes.
- Static gates in `T-5`.

## Completion criteria

- `_fake_task` deleted; all 18 call sites replaced with real tasks.
- The eight methods are `async def` and pass against both code states.
- No `_fake_task` remains (`AC-8`); the rest of the file is unchanged.

## Out of Scope

- The monitor source change (row 02) and the registry wiring (row 01).
- Every other class in the file, including `TestHandleTurnPauseGuard`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | migrate one class (8 methods) to real tasks |
| 2 | Add or update tests per Validation plan | Pending | — | — | cancellation test asserts no log output |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest/ruff/check_mock_patch_targets |
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
- **Requirement ID**: `REQ-007` (migrate this class's mock tasks to real tasks) supporting `REQ-003`/`REQ-004`
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `tests/agent/test_orchestrator.py`
