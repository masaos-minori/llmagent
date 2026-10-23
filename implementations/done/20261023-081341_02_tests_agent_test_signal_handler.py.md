## Goal

Make `tests/agent/test_signal_handler.py` the sole home of signal coverage: add real-loop registration (both `SIGTERM` and `SIGINT`), a real `os.kill` delivery case awaited through a real `asyncio.Event`, and a `shutdown_event=None` case; add teardown that removes installed handlers and restores captured dispositions; delete the permanently-skipped Windows-success test; restate the Windows contract in the module docstring.

## Scope

Only `tests/agent/test_signal_handler.py`. Deletion target `tests/agent/test_signal_handler_race.py` is covered by its own procedure (row 3). No production file under `scripts/` changes.

## Assumptions

- `pyproject.toml` sets `asyncio_mode = "auto"`, so new async cases run on a real loop; `loop.add_signal_handler` is available on Linux (`ubuntu-latest`), where the `NotImplementedError` fallback (`signal_handler.py:64`) does not occur.
- `register()` installs via `loop.add_signal_handler` (not `signal.signal`), so it does not change the process's `signal.getsignal` disposition — that is what makes AC-6's before/after assertion hold.
- The surviving `test_complete_failure_logs_error` (`:36-49`) exercises production code and stays unchanged.

## Design decisions

- **Coverage moves to the mirror-named file using the real transport**, not a re-written mock. The deleted `test_signal_handler_race.py` asserted on `MagicMock(spec=AgentREPL)` state the body assigned; its real equivalent (`services may be None`, the `NotImplementedError` fallback) already lives against production code in `test_repl.py:1191-1232` and `:36-49`.
- **Teardown restores process state** so a test that touches the real loop does not leak into the other 3400+ tests: each case removes its installed handlers with `loop.remove_signal_handler(sig)` in a `finally`, and captures `signal.getsignal` before restoring after.

## Alternatives considered

- Keeping the skip-only `test_registered_without_pywin32` — rejected: it can never run on `ubuntu-latest` CI (`.github/workflows/ci.yml:11,:46`), so a permanent `skipif(True)` is dishonest; its contract stays written in the docstring (REQ-007).
- Asserting installation by patching `add_signal_handler` and not installing — weaker; the plan wants the real transport exercised, so install then remove.

## Implementation

### Target file

`tests/agent/test_signal_handler.py`

### Procedure

1. Add imports: `import asyncio`, `import os`, `import signal` (alongside the existing `import ctypes`).
2. Restate the module docstring (`:1-12`): keep the completeness-failure contract, and explicitly record that the Windows success path (`ctypes.WINFUNCTYPE`/`windll`, gated on `os.name=='nt'`) is a documented, never-executed path on this `ubuntu-latest` CI matrix — not a skipped test — and that `test_signal_handler_race.py` (its former home for the cross-platform case) was deleted.
3. Delete `test_registered_without_pywin32` (`:51-78`, the `@pytest.mark.skipif(True)` case).
4. Add `class TestRealSignalTransport` with three `@pytest.mark.asyncio` cases (see Method).

### Method

```python
import asyncio
import os
import signal
from unittest.mock import MagicMock


class TestRealSignalTransport:
    """REQ-006: SignalHandler.register() on the real running loop.

    Both signal numbers are installed (signal_handler.py:61); a real
    os.kill(os.getpid(), SIGTERM) is observed through a real asyncio.Event;
    and the shutdown_event=None path (HEAD's __init__ wiring, repl.py:92)
    still sets shutdown_requested without raising (signal_handler.py:57).
    Handlers are removed in each finally; signal.getsignal dispositions
    are captured before and asserted identical after (AC-6).
    """

    @staticmethod
    def _capture_getsignal():
        return (
            signal.getsignal(signal.SIGTERM),
            signal.getsignal(signal.SIGINT),
        )

    @pytest.mark.asyncio
    async def test_register_installs_both_signals(self) -> None:
        handler = SignalHandler(MagicMock(), asyncio.Event())
        loop = asyncio.get_running_loop()
        seen: list[int] = []
        real_add = loop.add_signal_handler

        def capture(sig, cb):
            seen.append(sig)
            return real_add(sig, cb)  # install the real handler

        prev = self._capture_getsignal()
        try:
            with patch.object(loop, "add_signal_handler", side_effect=capture):
                handler.register(loop)
            assert signal.SIGTERM in seen
            assert signal.SIGINT in seen
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            loop.remove_signal_handler(signal.SIGINT)
        assert self._capture_getsignal() == prev

    @pytest.mark.asyncio
    async def test_delivered_sigterm_sets_shutdown_on_real_objects(self) -> None:
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        event = asyncio.Event()
        handler = SignalHandler(ctx, event)
        loop = asyncio.get_running_loop()
        prev = self._capture_getsignal()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)  # real delivery to this process
            await asyncio.wait_for(event.wait(), timeout=5.0)  # awaited, no sleep
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            loop.remove_signal_handler(signal.SIGINT)
        assert ctx.conv.shutdown_requested is True
        assert event.is_set()
        assert self._capture_getsignal() == prev

    @pytest.mark.asyncio
    async def test_none_event_still_sets_shutdown_without_raising(self) -> None:
        # HEAD's __init__ passes None (repl.py:92); the handler guards on it
        # (signal_handler.py:57) and must not raise.
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        handler = SignalHandler(ctx, None)
        loop = asyncio.get_running_loop()
        prev = self._capture_getsignal()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)
            await asyncio.sleep(0.1)  # yield to let the delivered handler run
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            loop.remove_signal_handler(signal.SIGINT)
        assert ctx.conv.shutdown_requested is True
        assert self._capture_getsignal() == prev
```

**UNK-03**: real `os.kill` delivery inside a pytest-asyncio test is observed via the loop's self-pipe wakeup; awaiting `event.wait()` under `asyncio.wait_for` is deterministic (no fixed sleep drives the assertion). The single `asyncio.sleep(0.1)` in the None case is a loop-yield (there is no event to await by design), not a timing fix — resolve/confirm at implementation and replace with a polling task if flaky.

## Compatibility considerations
Corrections found while implementing: the AC-6 claim that `signal.getsignal` is identical after `loop.remove_signal_handler()` is false inside an asyncio `Runner` for SIGINT (the Runner's own handler is replaced and removal resets to the default), so teardown restores the captured dispositions with `signal.signal`. The `set_shutdown_event` reference is obsolete (method removed); the `None` event case remains valid because the handler still guards on it.


N/A: test-only. Real handlers are removed in teardown; AC-6 asserts `signal.getsignal(SIGTERM)`/`SIGINT` are identical before and after the file runs.

## Security considerations

N/A: delivers a signal to the test process only, scoped to the test via `remove_signal_handler` teardown; no privilege, credential, or external process touched.

## Rollback considerations

N/A: revert the commit; the temporary mutation check uses single-target `git checkout` per `AGENTS.md` Execution policy.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `TestRealSignalTransport` | real loop + real delivered `SIGTERM` | `uv run pytest tests/agent/test_signal_handler.py -q` | Green |
| file-level signal dispositions | `signal.getsignal` before vs after | run whole file, then `uv run pytest tests/ -q -rs` | No `skipif(True)` remains; dispositions unchanged |
| deletion | proof by execution | `uv run pytest tests/agent -q`; `grep -rn "test_signal_handler_race" .` | Green; grep empty |

Static gates: `uv run ruff format`, `uv run ruff check`.

## Completion criteria

- `test_registered_without_pywin32` gone; `test_complete_failure_logs_error` intact (`:36-49`); module docstring restates the Windows contract as never-executed (AC-7).
- `uv run pytest tests/agent/test_signal_handler.py -q` green, including the delivered-`SIGTERM` case setting `conv.shutdown_requested` on a real object (AC-6).
- `grep -rn "test_signal_handler_race" .` empty (AC-7).

## Out of Scope

`tests/agent/test_signal_handler_race.py` (row 3); the `NotImplementedError` fallback path beyond `test_complete_failure_logs_error`; any `scripts/` change; the Windows runtime itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add real-loop registration, delivered-`SIGTERM`, and `None`-event cases; add restoring teardown; delete the skip-only test; restate the module docstring | Completed | 20261023-142356 | 20261023-142356 | Order-independent; safe at HEAD implemented; full suite 9829 passed; procedures corrected (guard renamed, mid-turn test made discriminating, signal disposition restore) |
| 2 | Add/update tests per Validation plan | Completed | 20261023-142356 | 20261023-142356 |  |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-142356 | 20261023-142356 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-142356 | 20261023-142356 | module docstring restatement (REQ-007) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | Step 1 / UNK-03 | Measurement | Open | implementer | confirm real `os.kill` delivery timing form |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-007
- **Source issue**: `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043008_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-081341
- **Related target files**: `tests/agent/test_signal_handler.py`