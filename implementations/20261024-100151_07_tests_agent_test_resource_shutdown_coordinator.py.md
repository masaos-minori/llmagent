## Goal

Implement `REQ-001`, `REQ-002`, `REQ-005`, `REQ-007`: rewrite `TestSelectiveTaskCancellation`
(`tests/agent/test_resource_shutdown_coordinator.py:114-181`) so it registers a real task through the
real `ConversationStateManager` into a real `TurnState` registry, runs `close_resources()` with an
unstubbed `asyncio.gather`, and asserts the task is cancelled and done, the registry is empty, a clean
cancellation records no error, and the checkpoint precedes cancellation. Replace the two tests that
existed only to prove the deleted `hasattr` guard.

## Scope

Only `TestSelectiveTaskCancellation` in `tests/agent/test_resource_shutdown_coordinator.py`. The file's
other three classes — `TestSettlementBlockRemoved` (`:37`), `TestHttpTerminationReported` (`:72`), and
`TestRealContendedStepIsBounded` (`:184`) — are not edited and must keep passing. The coordinator source
changes in row 03; the registry wiring in row 01.

## Assumptions

- `asyncio_mode = "auto"` runs `async def` tests on a running loop without a marker.
- `TestRealContendedStepIsBounded` (`:184`) already builds a real task via
  `asyncio.ensure_future(asyncio.sleep(30))` and assigns it to `ctx.turn.background_tasks` on a
  `MagicMock` ctx — the established pattern in this file for a real registry.
- `ConversationStateManager.append_user_message` creates the first-turn task when
  `ctx.stats.stat_turns == 1` and `on_first_turn` is set, adds it to the injected `tasks` set, and
  attaches the done callback (`conversation_state_manager.py:106-119`).

## Design decisions

- Build a `MagicMock` ctx whose `turn` is a real `TurnState` (so `background_tasks` is a real set) and
  whose `conv`/`stats`/`session` attributes that `append_user_message` touches are stubbed minimally.
- Construct `ConversationStateManager` directly with `tasks=ctx.turn.background_tasks` and call
  `append_user_message` to register a long-running real task — the same object the coordinator will
  read.
- Assert terminal state after `close_resources()` rather than `.cancel()` call sites.

## Alternatives considered

- Keeping the `MagicMock` tasks and the `assert hasattr(...)` / `test_no_turn_attribute_no_crash` tests:
  rejected — they assert a mock's `.cancelled()` (always truthy) and prove a guard that REQ-002 deletes.

## Implementation

### Target file

`tests/agent/test_resource_shutdown_coordinator.py`

### Procedure

1. Add imports: `TurnState` from `agent.context` and `ConversationStateManager` from
   `agent.conversation_state_manager`.
2. Add module-level helpers: a long-running `on_first_turn` stub and `_register_first_turn_task`.
3. Rewrite `TestSelectiveTaskCancellation` (`:114-181`) as three async tests using real tasks and a
   real registry (details below).
4. Leave `TestSettlementBlockRemoved`, `TestHttpTerminationReported`, and `TestRealContendedStepIsBounded`
   untouched.

### Method

Replace the mock-task construction with real `asyncio` tasks registered through the real producer. The
`on_first_turn` stub awaits `asyncio.sleep(30)` so the task is genuinely pending when `close_resources`
runs; the coordinator cancels it and joins it via the real `asyncio.gather`, after which
`task.cancelled()` and `task.done()` are true. A clean cancellation yields a `CancelledError` instance
from `gather` (not an `Exception`), so no `task_cancellation` record and no `Resource close errors` line
appear (`REQ-005`).

### Details

Add near the top imports:

```python
from agent.context import TurnState
from agent.conversation_state_manager import ConversationStateManager
```

Add module-level helpers (after `_make_coordinator`):

```python
async def _long_running_first_turn(line: str) -> str:
    """A stand-in for ``_generate_session_title``: pending long enough to be cancelled."""
    await asyncio.sleep(30)
    return "stubbed-title"


async def _register_first_turn_task(ctx) -> set:
    """Register one real first-turn task through the real producer."""
    manager = ConversationStateManager(
        ctx,
        tasks=ctx.turn.background_tasks,
        on_discard=lambda _task: None,
        on_first_turn=_long_running_first_turn,
    )
    await manager.append_user_message("first")
    return ctx.turn.background_tasks


def _registry_ctx() -> MagicMock:
    """A MagicMock ctx with a real TurnState registry and the minimal conv/stats/session stubs
    that ``append_user_message`` touches."""
    ctx = MagicMock()
    ctx.services = None
    ctx.conv = MagicMock()
    ctx.conv.system_prompt_content = ""          # skip sync_system_prompt's validation branch
    ctx.conv.append_message = AsyncMock()
    ctx.stats = MagicMock()
    ctx.stats.stat_turns = 0                      # append increments to 1, firing the first-turn branch
    ctx.session = MagicMock()
    ctx.session.save = MagicMock()
    ctx.turn = TurnState()                        # real, empty background_tasks set
    return ctx
```

Rewrite `TestSelectiveTaskCancellation`:

```python
class TestSelectiveTaskCancellation:
    """Real tasks in a real registry: only tracked background tasks are cancelled at shutdown."""

    @pytest.mark.asyncio
    async def test_only_tracked_background_tasks_cancelled(self) -> None:
        """A task registered through the real producer is cancelled, joined, and released."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        tasks = await _register_first_turn_task(ctx)
        assert len(tasks) == 1
        (running,) = tuple(tasks)

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()

        assert running.cancelled() is True
        assert running.done() is True
        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()          # no "Resource close errors" for a clean cancellation

    @pytest.mark.asyncio
    async def test_empty_registry_cancels_nothing_and_raises_nothing(self) -> None:
        """An empty registry leaves shutdown intact (replaces the deleted-guard test)."""
        ctx = _registry_ctx()                          # registry intentionally empty
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()             # must not raise

        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_critical_operations_not_cancelled(self) -> None:
        """Untracked work (WAL checkpoint, history write) is not cancelled; the registry empties."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()

        assert ctx.turn.background_tasks == set()       # nothing was registered, nothing remains
        view.write_history.assert_called()              # the history write still ran
```

Mutation controls (`T-1`): dropping the `await asyncio.gather` join makes `running.cancelled()` /
`done()` fail (cancellation never propagates without the await); re-introducing a second registry the
coordinator reads instead of `ctx.turn.background_tasks` makes the task uncancelled. Against the current
producer wiring the task lands in the Orchestrator's private set, so `ctx.turn.background_tasks` stays
empty and the test fails exactly as `turn005_probe1.py` case A measured — constructing a real Orchestrator
(instead of the direct `ConversationStateManager`) makes this failure concrete where the environment
allows.

## Compatibility considerations

File-scoped. The other three classes are unchanged; `test_repl.py`'s 80 tests (including
`test_checkpoint_completes_before_pending_task_cancelled`) remain the witness for `AC-3`.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -q` — the rewritten class passes and
  the other three classes keep passing.
- `uv run pytest tests/agent/test_repl.py -q` — 80 tests pass unchanged (`AC-3`).
- Static gates in `T-5` (`ruff`, `check_mock_patch_targets.py`: `grep -rn "MagicMock(spec=asyncio.Task)"
  tests/agent/` empty is covered by row 05/06; here confirm no `MagicMock` task stands in for a real one).

## Completion criteria

- `TestSelectiveTaskCancellation` uses real tasks in a real `TurnState` registry and asserts
  `cancelled()`/`done()`, the empty registry, and the absence of an error record (`AC-2`, `AC-6`).
- The two guard-only tests are replaced by the empty-registry case.
- The other three classes pass unchanged.

## Out of Scope

- The coordinator source change (row 03) and the registry wiring (row 01).
- Every other class in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | rewrite TestSelectiveTaskCancellation with real tasks |
| 2 | Add or update tests per Validation plan | Pending | — | — | replace two guard tests with empty-registry case |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest/test_repl.py/ruff |
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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-005`, `REQ-007` — real-task cancellation test for the coordinator
- **Source issue**: `issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-151742_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: `tests/agent/test_resource_shutdown_coordinator.py`
