## Goal

Implement `REQ-007` (migration) and support `REQ-003`/`REQ-004`: replace every
`MagicMock(spec=asyncio.Task)` task in `tests/agent/test_orchestrator_bg_failure_threshold.py` with a
real `asyncio.Task` created on the running loop, so the monitor's terminal-state handling is exercised
against the shape asyncio actually produces — including a task cancelled through `task.cancel()` then
awaited, which the mocks could never express.

## Scope

Only `tests/agent/test_orchestrator_bg_failure_threshold.py`. All 13 mock-task sites (`:50`, `:65`,
`:79`, `:85`, `:115`, `:135`, `:162`, `:189`, `:210`, `:227`, `:233`, `:247`, `:253`) are migrated.
The monitor itself changes in row 02; the registry wiring in row 01.

## Assumptions

- `asyncio_mode = "auto"` (in `pyproject.toml`) runs `async def` tests on a running loop without a
  marker; the existing `@pytest.mark.asyncio` decorators remain harmless.
- Python 3.11+ `asyncio.Task.get_name()` exists (the suite targets 3.13), so real tasks expose the
  `get_name()` the monitor reads.
- A task that raises captures its exception for later `task.exception()`; a cleanly cancelled task
  reports `cancelled() is True` after being awaited, and `task.exception()` would raise — so the test
  must await the cancellation before calling `on_task_done`.

## Design decisions

- Add three module-level helper coroutines — `_raising_task(message)`, `_successful_task()`, and
  `_cancellable_task()` — and build each real task with `asyncio.create_task(...)`, awaiting it before
  `on_task_done` so its terminal state is settled.
- Keep every existing assertion's *intent* (counter values at each step, first-failure notification
  once, threshold reached exactly at 10, no notification after); change only how the task is produced.

## Alternatives considered

- Keeping the mocks: rejected — a `MagicMock`'s `.cancelled()` is truthy, so a mock is always
  classified as cancelled and the fixed contract cannot be expressed (`turn005c_failures.txt`, 17
  failures).

## Implementation

### Target file

`tests/agent/test_orchestrator_bg_failure_threshold.py`

### Procedure

1. Add the three helper coroutines near the top (after `_make_ctx`).
2. In each test, replace the `MagicMock(spec=asyncio.Task)` construction with a real task obtained
   from the helpers, awaiting the task so its terminal state is settled before `on_task_done`.
3. In the cancelled-task tests, cancel the task and await it inside `pytest.raises(asyncio.CancelledError)`
   before calling `on_task_done`, then assert the counter reset and that no asyncio callback error was
   logged.
4. Preserve the logging-capture fixtures (`CapturingHandler` / `LevelCapturingHandler`) — real tasks
   drive the real `agent.bg_task_monitor` logger, so the captured records are genuine.

### Method

A real raising task returns its exception via `task.exception()` (does not raise); a real cancelled
task reports `cancelled() is True` after being awaited and would raise `CancelledError` from
`exception()`, so it must be awaited first. The helper coroutines encode these three shapes; each test
awaits the task it creates before handing it to `on_task_done`.

### Details

Add after `_make_ctx`:

```python
async def _raising_task(message: str) -> None:
    """A task whose body raises ``RuntimeError(message)``; ``task.exception()`` returns it."""
    raise RuntimeError(message)


async def _successful_task() -> int:
    """A task that returns normally; ``task.exception()`` is ``None``."""
    return 42


async def _cancellable_task() -> None:
    """A task that waits forever until cancelled."""
    await asyncio.Event().wait()


def _run_raising(message: str) -> asyncio.Task[object]:
    task = asyncio.create_task(_raising_task(message))
    return task  # caller awaits to settle the exception


async def _await_raising(message: str) -> asyncio.Task[object]:
    task = asyncio.create_task(_raising_task(message))
    await task  # retrieves the exception so no "never retrieved" warning fires
    return task


async def _make_cancelled(name: str) -> asyncio.Task[object]:
    task = asyncio.create_task(_cancellable_task(), name=name)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    return task
```

Migration patterns per class (apply to all 13 sites):

- Single/multiple failure (`TestConsecutiveFailuresIncrement`, `TestThresholdReachedBehavior`,
  `TestOnErrorCallbackExceptionHandling`):

  ```python
  task = await _await_raising(f"error {i}")
  monitor.on_task_done(task)
  ```

- Success reset (`test_success_after_failures...` analog):

  ```python
  task = await _await_raising("boom")   # preceding failures
  success = await _successful_task()
  monitor.on_task_done(success)
  ```

- Cancellation reset (`TestCancelledTaskCounterReset`, and the cancelled branch of
  `TestConsecutiveFailuresIncrement.test_reset_on_cancelled_task`):

  ```python
  cancelled = await _make_cancelled("cancelled_task")
  monitor.on_task_done(cancelled)
  ```

Two facts the mocks could not express — add assertions:

- Counter reset by a real cancellation: after `_make_cancelled`, `get_consecutive_failures` for the
  cancelled task is 0 while the streaking task keeps its count.
- No asyncio callback error: capture the `asyncio` logger around the cancelled-task call and assert no
  `Exception in callback BgTaskMonitor.on_task_done()` record appears (`AC-4`).

Mutation control (`AC-4`): re-ordering the monitor so `task.exception()` is read before
`task.cancelled()` makes this test raise `CancelledError` and leaves the counter at its seeded value —
the measured current behavior.

## Compatibility considerations

File-scoped: test-only. The other active Plans do not touch this file. Every migrated test keeps its
original counter and notification-count assertions, so it passes against both the current and the
changed monitor (`T-3` pins "no behavior change").

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py -q` — all tests pass; the
  cancelled-task tests assert counter 0 and no asyncio callback error.
- Mutation control above fails against the exception-first ordering.
- Static gates in `T-5` (`ruff`, `check_mock_patch_targets.py` confirms no
  `MagicMock(spec=asyncio.Task)` remains: `grep -rn "MagicMock(spec=asyncio.Task)" tests/agent/` is
  empty, `AC-8`).

## Completion criteria

- All 13 mock-task sites replaced with real tasks from `asyncio.create_task` / the helpers.
- The cancelled-task tests assert counter 0 and no asyncio callback error (`AC-4`, `AC-8`).
- The suite passes; no `MagicMock(spec=asyncio.Task)` remains.

## Out of Scope

- The monitor source change (row 02).
- The orchestrator test migration (row 06) and the coordinator test rewrite (row 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | migrate 13 mock-task sites to real tasks |
| 2 | Add or update tests per Validation plan | Pending | — | — | add counter-reset + no-callback-error assertions |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/check_mock_patch_targets/pytest |
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
- **Requirement ID**: `REQ-007` (migrate mock tasks to real tasks) supporting `REQ-003`/`REQ-004`
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `tests/agent/test_orchestrator_bg_failure_threshold.py`
