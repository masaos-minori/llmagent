## Goal

Add a constructor-level wiring guard that runs the real `AgentREPL.__init__` and asserts one `asyncio.Event` is held by `ReplInputLoop` and `SignalHandler`; extend it to the `run()` handoff chain; declare both wiring-repairing fixtures; and replace the never-failing assertions in `test_signal_mid_turn_exits_within_graceful_timeout` with assertions that fail when the cancel branch of `_repl_loop` is removed.

## Scope

Only `tests/agent/test_repl.py`. No production file under `scripts/` is touched. The three heavy collaborators substituted at the use site are `agent.repl.AgentContext`, `agent.repl.CLIView`, `agent.repl.DiagnosticStore` (the substitution direction `tools/check_mock_patch_targets.py` enforces); every other double (view, orchestrator, command registry, diagnostic store) stays as written.

## Assumptions

- `pyproject.toml` sets `asyncio_mode = "auto"` and the `integration` marker exists, so new async cases run on a real loop on `ubuntu-latest`.
- The collaborator `__init__`s perform no I/O (`wal_checkpoint_manager.py`, `session_persister.py`, `resource_shutdown_coordinator.py`, `diagnostic_store.py`), so a real `AgentREPL()` construction is safe in a unit test.
- `tests/conftest.py` isolates `sys.path` so nothing opens `/opt/llm`, a real config, or a database.
- Line numbers below are current-HEAD values from `scripts/agent/repl.py` / `repl_input_loop.py`; the frozen Plan cites them +1 (a known line-shift, UNK-03). Prefer the content anchors over the printed numbers.

## Design decisions

- **The guard is a construction test, not an attribute test.** It calls the real `AgentREPL()` with only the three names substituted, then asserts `isinstance(event, asyncio.Event)` *before* any identity comparison. Requiring the object to exist is what makes the guard fail at HEAD (`repl.py:81`/`:84` pass `None`) and pass after `repl001` (`plans/20261022-030840_plan.md`). A pure `a is b` would pass today on two `None`s — the exact failure mode this Plan removes.
- **A second guard follows the proven `TestSigtermHandlerShutdownCoordination._run_and_capture_handler` shape** (`test_repl.py:1261-1284`): real `run()`, `agent.repl.StartupOrchestrator` + `agent.wal_checkpoint_manager.SQLiteHelper` substituted, `close_resources` stubbed, `loop.add_signal_handler` *captured* instead of installed, and `run()` made to exit promptly. The new part is inspecting what the constructed objects hold rather than what a handler does.

## Alternatives considered

- Constructing `AgentREPL()` with no substitution at all — rejected: it builds real `CLIView`/`DiagnosticStore`/`AgentContext`, which pull in config/terminal/LLM dependencies the skill forbids.
- Patching `agent.repl.StartupOrchestrator` and reading `startup._mcp_starter._shutdown_event` for the full holder chain — rejected: a patched class yields a `MagicMock` instance, so the private attribute read is meaningless. Instead assert on the *construction call* (see Method), which receives the real event as a kwarg.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Add `class TestWiringGuard` (module-level, near `TestRunBindsStartupResultsToInputLoop` at `test_repl.py:712`, which stays as the pattern the new guard joins).
   - `test_construction_holds_one_event` (REQ-001): real `AgentREPL()` under three use-site patches; assert `isinstance(repl._shutdown_event, asyncio.Event)`; assert `repl._input_loop._shutdown_event is repl._shutdown_event`; assert `repl._signal._shutdown_event is repl._shutdown_event`.
   - `test_run_handoff_holds_one_event` (REQ-002): mirror `_run_and_capture_handler`; capture `add_signal_handler`; assert the event `run()` created is the one `SignalHandler` received via `set_shutdown_event` (`signal_handler.py:136-138`), the one `ReplInputLoop` holds, and the one passed to `StartupOrchestrator` (assert via the captured construction call); note `McpServerStarter` is a transitive holder (`startup.py:62`).
2. Rewrite `_make_bare_repl` (`test_repl.py:28-83`) and `_make_repl_for_shutdown` (`:618-637`) docstrings to state they bypass `AgentREPL.__init__` (`:30`, `:620`) and hand-supply the event `__init__` does not (`repl.py:81`, `:84`), naming `TestWiringGuard` as the paired guard (REQ-003).
3. Correct `TestReplLoop.test_signal_mid_turn_exits_within_graceful_timeout` (`:333-367`) (REQ-004, REQ-005): delete `start = time.time()`, the `except TimeoutError: pass` block, `elapsed = time.time() - start`, `assert elapsed < 2.0`, and `assert dispatch_hang.is_set() or True`; let `asyncio.wait_for(..., timeout=5.0)` decide; capture the `CancelledError` in the hang stub; assert the dispatch was cancelled and the persist hook awaited once; add the branch-describing docstring.
4. Leave every other class and `TestRunBindsStartupResultsToInputLoop` as written.

### Method

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestWiringGuard:
    """REQ-001/REQ-002: AgentREPL.__init__ and run() wire ONE asyncio.Event.

    Construction guard fails at HEAD because repl.py:81 sets
    self._shutdown_event = None and repl.py:84/:91 forward that None to
    ReplInputLoop and SignalHandler; it passes once repl001
    (plans/20261022-030840_plan.md) makes __init__ the sole owner of the event.
    """

    @pytest.mark.asyncio
    async def test_construction_holds_one_event(self) -> None:
        # Only the three heavy names are substituted; the real __init__ body runs.
        with (
            patch("agent.repl.AgentContext"),
            patch("agent.repl.CLIView"),
            patch("agent.repl.DiagnosticStore"),
        ):
            repl = AgentREPL()

        # Non-None precondition FIRST: a bare identity assertion would pass on
        # two Nones and hide the defect this guard exists to catch.
        assert isinstance(repl._shutdown_event, asyncio.Event)
        assert repl._input_loop._shutdown_event is repl._shutdown_event
        assert repl._signal._shutdown_event is repl._shutdown_event

    @staticmethod
    async def _run_and_inspect_holder_chain() -> None:
        captured_events: list = []

        def fake_add_signal_handler(sig, handler):
            captured_events.append(None)  # signal number is irrelevant here

        loop = asyncio.get_running_loop()
        with (
            patch("agent.repl.StartupOrchestrator") as MockStartup,
            patch("agent.wal_checkpoint_manager.SQLiteHelper"),
            patch.object(loop, "add_signal_handler", side_effect=fake_add_signal_handler),
        ):
            repl = AgentREPL()  # real __init__; event still None until run()
            repl._shutdown.close_resources = AsyncMock()
            MockStartup.return_value.run = AsyncMock(
                side_effect=RuntimeError("stop-after-registration")
            )
            with pytest.raises(RuntimeError, match="stop-after-registration"):
                await repl.run()

        # run() creates the event (repl.py:112) and rebinds SignalHandler
        # (repl.py:113 -> signal_handler.py:136-138).
        event = repl._shutdown_event
        assert isinstance(event, asyncio.Event)
        assert repl._signal._shutdown_event is event
        assert repl._input_loop._shutdown_event is event
        # StartupOrchestrator is constructed at repl.py:119 with this event as a
        # kwarg; asserting on the construction call (not the mocked instance) is
        # what survives patching. McpServerStarter (startup.py:62) inherits it.
        assert MockStartup.call_args.kwargs["shutdown_event"] is event

    @pytest.mark.asyncio
    async def test_run_handoff_holds_one_event(self) -> None:
        await self._run_and_inspect_holder_chain()
```

Resolve **UNK-02** here: the chain stops at `ReplInputLoop` + `SignalHandler` for the runtime attribute reads and uses the `MockStartup.call_args` construction check for `StartupOrchestrator`; `McpServerStarter` is transitive (`startup.py:62`) and documented as such. If the implementer prefers the full object graph, construct a real `StartupOrchestrator` outside `run()` (its `__init__` does no I/O) and read its held event — but that duplicates the constructor guard, so the construction-call check is preferred.

### Details

Corrected `test_signal_mid_turn_exits_within_graceful_timeout` body (replaces `:333-367`):

```python
@pytest.mark.asyncio
async def test_signal_mid_turn_exits_within_graceful_timeout(self) -> None:
    """SIGTERM while _dispatch_line hangs exits via the race branch
    (repl_input_loop.py:_repl_loop 255-284): _make_bare_repl supplies a real
    asyncio.Event, so _shutdown_event is not None and the cancel path runs.
    HEAD's real __init__ passes None, which falls to the :285-305
    await-with-timeout branch; that path is covered by TestWiringGuard, not here."""
    repl = _make_bare_repl()
    dispatch_hang = asyncio.Event()
    dispatch_cancelled = asyncio.Event()

    async def _hang_dispatch(*args, **kwargs):
        try:
            await dispatch_hang.wait()  # left unset so dispatch stays pending
        except asyncio.CancelledError:
            dispatch_cancelled.set()

    repl._orchestrator.handle_turn = AsyncMock(side_effect=_hang_dispatch)

    async def _set_shutdown_after_delay():
        await asyncio.sleep(0.02)
        repl._shutdown_event.set()  # leave dispatch_hang unset -> gets cancelled

    asyncio.ensure_future(_set_shutdown_after_delay())

    mock_banner = MagicMock()
    mock_persister = AsyncMock()
    with patch.object(
        repl._input_loop, "_read_input", new=AsyncMock(return_value="test input")
    ):
        # No try/except: a TimeoutError now fails the test instead of being
        # swallowed (was `except TimeoutError: pass` at :362-363).
        await asyncio.wait_for(
            repl._input_loop.run(mock_banner, mock_persister), timeout=5.0
        )

    assert dispatch_cancelled.is_set(), (
        "race branch must cancel the hung dispatch (repl_input_loop.py:278-283)"
    )
    assert mock_persister.await_count == 1, "post-loop persist hook awaited once"
```

**UNK-01** resolution (implementer, via the mutation in the Validation plan): both assertions discriminate; keep the `CancelledError` capture as primary and the `await_count` as secondary. Remove `dispatch_task.cancel()` at `repl_input_loop.py:279` temporarily → dispatch never cancels, `wait_for(timeout=5.0)` times out, `TimeoutError` propagates → test fails. Restore with `git checkout -- scripts/agent/repl_input_loop.py`.

## Compatibility considerations
Corrections found while implementing (the procedure predates the event-ownership fix that has since landed): `AgentREPL.__init__` now owns the event, `run()` no longer creates it or calls `set_shutdown_event` (removed), so the guard no longer "fails at HEAD". The constructor and `run()` handoff guard already existed as `TestAgentREPLOwnsOneShutdownEvent`; it was renamed `TestWiringGuard` (the name the skills text references) rather than duplicated. The mid-turn test as specified did not discriminate: removing `dispatch_task.cancel()` still passed because the outer `wait_for` cancellation reaches the inner wait and is swallowed; the corrected test also asserts `elapsed < 1.0` and was verified to fail when the cancel is removed.


N/A: test-only change; the guard is order-independent and lands after `repl001` per the hard ordering in the Plan's Notes. At HEAD it fails by design (the non-`None` assertion), which is the expected pre-`repl001` state (AC-1).

## Security considerations

N/A: no production code changes; no credential, permission, or I/O boundary touched.

## Rollback considerations

N/A: revert the commit. The temporary mutation check uses single-target `git checkout` per `AGENTS.md` Execution policy.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `TestWiringGuard` | Fails at HEAD on the non-`None` assertion; passes after `repl001` | `uv run pytest tests/agent/test_repl.py -q -k TestWiringGuard` | Red at HEAD (expected), green post-`repl001` |
| `TestWiringGuard` (mutation) | `repl.py:84` passes `None` again; remove `dispatch_task.cancel()` at `repl_input_loop.py:279` | edit, `uv run pytest tests/agent/test_repl.py -q`, `git checkout -- scripts/agent/repl.py scripts/agent/repl_input_loop.py` | Each produces a named failing test |
| corrected `TestReplLoop` case | unchanged subject, honest assertions | `uv run pytest tests/agent/test_repl.py -q -k test_signal_mid_turn_exits_within_graceful_timeout` | Green at HEAD |
| whole file | no regressions | `uv run pytest tests/agent/test_repl.py -q` | Green |

Static gates: `uv run python tools/check_mock_patch_targets.py` (AC-9), `uv run ruff format`, `uv run ruff check`.

## Completion criteria

- `grep -n "or True" tests/agent/test_repl.py` empty; `grep -n "time.time()" tests/agent/test_repl.py` empty; `except TimeoutError: pass` absent from `test_signal_mid_turn_exits_within_graceful_timeout` (AC-3).
- Both fixture docstrings name the bypassed `__init__` and the paired `TestWiringGuard` (AC-4); guard and corrected test each name the `_repl_loop` branch they exercise (AC-5).
- `TestWiringGuard` red at HEAD, green after `repl001`; mutation checks produce named failures (AC-1).
- `uv run python tools/check_mock_patch_targets.py` passes with the new `patch("agent.repl.…")` targets (AC-9).

## Out of Scope

Every production file under `scripts/`; the value of `_GRACEFUL_TIMEOUT_S` (`repl_input_loop.py:55`); any other timeout; the Windows-success test (owned by `test_signal_handler.py`, REQ-007); the four permanently-skipped tests elsewhere in the suite.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestWiringGuard` (constructor + run-handoff), rewrite both fixture docstrings, correct the graceful-shutdown assertions | Completed | 20261023-142355 | 20261023-142355 | Gated on repl001 for the guard; fixture/docstring/correction rows safe at HEAD implemented; full suite 9829 passed; procedures corrected (guard renamed, mid-turn test made discriminating, signal disposition restore) |
| 2 | Add/update tests per Validation plan (mutation checks) | Completed | 20261023-142355 | 20261023-142355 |  |
| 3 | Run validation sequence (`rules/toolchain.md`) incl. `check_mock_patch_targets.py` | Completed | 20261023-142355 | 20261023-142355 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-142355 | 20261023-142355 | test-only change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Guard asserts the single-event ownership `repl001` introduces; at HEAD `repl.py:81`/`:84` pass `None`, so the guard fails by design | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | Step 1 / UNK-02 | Design decision | Open | implementer | decide the post-`run()` holder-chain depth before writing the guard |
| WI-02 | Step 1 / UNK-01 | Assertion choice | Open | implementer | run the mutation, keep the discriminating assertion |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043008_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-081341
- **Related target files**: `tests/agent/test_repl.py`