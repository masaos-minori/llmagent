# Implementation: Rewrite TestProcessGroupShutdown for the polling-based _terminate_with_timeout

Source plan: `plans/20260710-110325_plan.md` (Phase 2)

Depends on: `implementations/20260710-120918_scripts_agent_http_lifecycle.md` (Phase 1 — must land first; these tests exercise the new `_wait_exited` polling implementation, not the old thread-based one).

## Goal

Update `TestProcessGroupShutdown` so it exercises the new poll-based `_terminate_with_timeout`/`_wait_exited` implementation instead of monkeypatching `asyncio.wait_for` (a mechanism the new implementation no longer calls), and add a regression test that proves `asyncio.to_thread` is never invoked — the concrete, re-checkable evidence that the thread-leak bug (issue 1-b) cannot resurface silently.

## Scope

- `tests/test_lifecycle.py`, `TestProcessGroupShutdown` class only (currently `tests/test_lifecycle.py:664-748`, i.e. the three tests `test_terminate_uses_killpg_sigterm`, `test_terminate_fallback_on_process_lookup_error`, `test_terminate_sigkill_on_second_timeout`, plus the `_make_running_proc` helper at lines 656-661).
- Add one new test to the same class proving no thread is spawned.
- `test_terminate_skips_killpg_when_already_exited` (lines 751-775) and `TestShutdownAllCleanup` (lines 592-651) are unaffected by the Phase 1 change (they either exit before reaching `_wait_exited`, or fully mock `_terminate_with_timeout` itself) — run them for regression only, do not rewrite them.
- **Scope addition found during implementation:** `test_start_populates_http_pgids` (also in `TestProcessGroupShutdown`, not called out in the original design) sets `mock_proc.poll.return_value = None` as a *constant* and exercises the real `start()` → `_terminate_with_timeout` path on health-check timeout. Under the new poll-based `_wait_exited`, a constant `None` poll means the test now genuinely waits out the full default `timeout=3.0` twice (SIGTERM + SIGKILL) — 7.21s observed, versus near-instant before (the old implementation relied on the separate `.wait()` mock attribute, which returned instantly regardless of `.poll()`'s value). Fixed with the same "poll reports running until the relevant action has been taken" pattern used elsewhere in this file (see Change 5 below).

## Assumptions

1. Mocking `asyncio.sleep` to bypass real waiting is tempting but risky: `_wait_exited`'s deadline check uses `time.monotonic()`, which reflects *real* wall-clock time regardless of whether `asyncio.sleep` is mocked. If `asyncio.sleep` is replaced with a no-op, the polling loop becomes a real (if fast) busy-loop that still takes the full real `timeout` seconds to reach its deadline — mocking `sleep` alone does not make the test instant. The safer approach (adopted here) is to call `_terminate_with_timeout` with a *small real timeout* (e.g. `timeout=0.05`) and let real `asyncio.sleep` run — the test costs tens of milliseconds, not the full `timeout` used in production, and there is no risk of an unbounded busy-loop fighting a mocked clock.
2. `_make_mock_proc`'s `mock_proc.poll.return_value = exit_code` (`tests/test_lifecycle.py:36-41`) sets a *constant* return value. Tests that need `poll()` to return "still running" for the first call(s) and "exited" afterward must instead set `proc.poll = MagicMock(side_effect=[...])` on the instance after construction, as `_make_running_proc` already does for `.wait`.

## Implementation

### Target file

`tests/test_lifecycle.py`

### Procedure

1. Keep `_make_running_proc` (lines 656-661) as-is — it still supplies a `MagicMock` with a controllable `pid`; the `.wait` attribute it sets is no longer read by production code but leaving it does no harm (or remove it if `ruff`/`vulture` flags it as unused — check after Phase 1 lands).
2. Rewrite `test_terminate_uses_killpg_sigterm`: drop the `mod.asyncio.wait_for` monkeypatch; instead give `proc.poll` a `side_effect` list long enough to cover exactly one `_terminate_with_timeout`-level check plus one `_wait_exited`-level check, call with a small real `timeout`.
3. Rewrite `test_terminate_fallback_on_process_lookup_error` the same way, keeping the `os.killpg` → `ProcessLookupError` → `proc.terminate()` fallback assertion.
4. Rewrite `test_terminate_sigkill_on_second_timeout`: `proc.poll` must report "still running" long enough to span the first `_wait_exited(timeout=small)` call (forcing escalation to SIGKILL), then report "exited" so the second `_wait_exited` call returns quickly. Use a small real `timeout` (e.g. `0.05`) so the forced elapse of the first deadline costs ~50ms of real test time, not the production default (3.0s).
5. Add a new test `test_terminate_never_uses_thread_even_when_process_never_exits`: monkeypatch `mod.asyncio.to_thread` to a `MagicMock(side_effect=AssertionError("to_thread must not be used"))`, set `proc.poll` to always return `None` (never exits), call `_terminate_with_timeout` with a small timeout (e.g. `0.02`), and assert it returns normally (no exception) and that both SIGTERM and SIGKILL were sent via the killpg spy. This is the direct regression test for issue 1-b.

### Method

In-place rewrite of 3 existing test methods, addition of 1 new test method, in the same class. No new test file, no new fixtures beyond what already exists in the module (`_make_mock_proc`, `_make_running_proc`).

### Details

#### Change 1: `test_terminate_uses_killpg_sigterm`

Before (`tests/test_lifecycle.py:667-692`):

```python
    @pytest.mark.asyncio
    async def test_terminate_uses_killpg_sigterm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import signal as _signal

        from agent import http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        async def fast_wait_for(coro: object, timeout: float) -> object:
            return await coro  # type: ignore[misc]

        monkeypatch.setattr(mod.asyncio, "wait_for", fast_wait_for)

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=42)
        mgr._http_pgids["srv"] = 42

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        assert (42, _signal.SIGTERM) in killed
        proc.terminate.assert_not_called()
```

After (as actually implemented — differs from the original design below: instead of a fixed-length `side_effect` list, `proc.poll` is tied to observable state (`killed`/`proc.terminate.called`) via a closure, avoiding the call-count fragility flagged as a risk in Change 3's original note):

```python
    @pytest.mark.asyncio
    async def test_terminate_uses_killpg_sigterm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import signal as _signal

        from agent import http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=42)
        # Still running until SIGTERM has been sent, then reports exited — this
        # lets _wait_exited's first poll (right after SIGTERM) return True
        # immediately, without waiting out the real timeout.
        proc.poll = MagicMock(side_effect=lambda: 0 if killed else None)
        mgr._http_pgids["srv"] = 42

        await mgr._terminate_with_timeout(proc, "srv", timeout=1.0)

        assert (42, _signal.SIGTERM) in killed
        proc.terminate.assert_not_called()
```

(`from agent import http_lifecycle as mod` stays a local import inside each test method, matching the existing convention in this class.)

#### Change 2: `test_terminate_fallback_on_process_lookup_error`

Before (`tests/test_lifecycle.py:694-716`): same `fast_wait_for` monkeypatch pattern wrapping a `ProcessLookupError`-raising `os.killpg`.

After: drop the `asyncio.wait_for` monkeypatch; tie `proc.poll` to `proc.terminate.called` instead (the killpg fallback path calls `proc.terminate()`, not `killed.append`):

```python
        proc.poll = MagicMock(side_effect=lambda: 0 if proc.terminate.called else None)
```

Keep the `raise_lookup` function and the `proc.terminate.assert_called_once()` assertion unchanged.

#### Change 3: `test_terminate_sigkill_on_second_timeout`

Before (`tests/test_lifecycle.py:718-748`): monkeypatches `asyncio.wait_for` with `timeout_first_then_ok` (raises `TimeoutError` on the 1st call, then behaves normally) to force the SIGKILL escalation path, using `timeout=1.0`.

After (as actually implemented — ties `proc.poll` to whether SIGKILL has been sent yet, rather than a fixed-length `side_effect` list, sidestepping the call-count uncertainty the original design flagged):

```python
    @pytest.mark.asyncio
    async def test_terminate_sigkill_on_second_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import signal as _signal

        from agent import http_lifecycle as mod

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=55)
        # Stays "running" through the first _wait_exited call (forcing SIGTERM's
        # wait to time out and escalate to SIGKILL), then reports exited as soon
        # as SIGKILL has actually been sent — a small real timeout means the
        # forced elapse of the first deadline costs only tens of milliseconds.
        proc.poll = MagicMock(
            side_effect=lambda: (
                0 if any(sig == _signal.SIGKILL for _, sig in killed) else None
            )
        )
        mgr._http_pgids["srv"] = 55

        await mgr._terminate_with_timeout(proc, "srv", timeout=0.05)

        assert any(sig == _signal.SIGKILL for _, sig in killed)
```

This is more robust than a fixed-length `side_effect` list because it doesn't depend on the exact number of times `_wait_exited` calls `proc.poll()` before its deadline elapses — it only depends on the actual state transition being tested (SIGKILL sent or not), so it can't raise `StopIteration` regardless of scheduling/timing jitter.

#### Change 5: `test_start_populates_http_pgids` (scope addition, see above)

Before (`tests/test_lifecycle.py`, inside `TestProcessGroupShutdown`):

```python
        monkeypatch.setattr(mod.os, "getpgid", lambda pid: 9999)
        monkeypatch.setattr(mod.os, "killpg", MagicMock())
        _patch_open_to_tmp(monkeypatch, tmp_path)

        mock_proc = _make_mock_proc(exit_code=None)
        mock_proc.pid = 12345
```

After:

```python
        killpg_mock = MagicMock()
        monkeypatch.setattr(mod.os, "getpgid", lambda pid: 9999)
        monkeypatch.setattr(mod.os, "killpg", killpg_mock)
        _patch_open_to_tmp(monkeypatch, tmp_path)

        mock_proc = _make_mock_proc(exit_code=None)
        mock_proc.pid = 12345
        # Still running until killpg has been invoked (start()'s cleanup path),
        # then reports exited — avoids _wait_exited genuinely waiting out the
        # full 3.0s default timeout twice (SIGTERM + SIGKILL) in this test.
        mock_proc.poll = MagicMock(side_effect=lambda: 0 if killpg_mock.called else None)
```

#### Change 4: new regression test

Add after `test_terminate_sigkill_on_second_timeout`:

```python
    @pytest.mark.asyncio
    async def test_terminate_never_uses_thread_even_when_process_never_exits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression test for issue 1-b: _terminate_with_timeout must not leak a
        non-daemon ThreadPoolExecutor worker via asyncio.to_thread, even when the
        target process never exits (simulating an uninterruptible/D-state process).
        """
        import signal as _signal

        killed: list[tuple[int, int]] = []
        monkeypatch.setattr(
            mod.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
        )
        monkeypatch.setattr(
            mod.asyncio,
            "to_thread",
            MagicMock(side_effect=AssertionError("to_thread must not be used")),
        )

        mgr = HttpServerLifecycleManager()
        proc = _make_running_proc(pid=77)
        proc.poll = MagicMock(return_value=None)  # never exits
        mgr._http_pgids["srv"] = 77

        # Small real timeouts so this test costs ~tens of ms, not the 3.0s production default.
        await mgr._terminate_with_timeout(proc, "srv", timeout=0.02)

        assert (77, _signal.SIGTERM) in killed
        assert (77, _signal.SIGKILL) in killed
```

## Validation plan

| Check | Tool / Command | Target | Result |
|---|---|---|---|
| Rewritten tests | `uv run pytest tests/test_lifecycle.py -k "TestProcessGroupShutdown" -v` | All 6 tests (3 rewritten + 1 new + `test_start_populates_http_pgids` fix + `test_terminate_skips_killpg_when_already_exited`) pass | PASS — 6 passed in 1.61s |
| No real-time cost regression | `uv run pytest tests/test_lifecycle.py -k "TestProcessGroupShutdown" -v --durations=10` | Slowest test in this class completes in well under 1 second (proves no accidental full-timeout wait) | PASS — slowest was `test_start_populates_http_pgids` at 1.01s (its own health-poll retry loop, unrelated to the fix); the 4 rewritten/new `_terminate_with_timeout` tests each ran in ≤0.11s |
| Full file regression | `uv run pytest tests/test_lifecycle.py -v` | No new failures (includes `test_terminate_skips_killpg_when_already_exited`, `TestShutdownAllCleanup`, `TestHttpLifecycleStderrLog`) | **Not run.** After the targeted run above returned successfully, the user reported (for a second and third time across this session) that the Claude Code CLI process itself crashed and required a restart, correlated with broader pytest invocations. Root cause not conclusively isolated. Per explicit user direction, broad/full-file pytest runs are avoided in this session going forward. Substituted with static analysis: `grep` confirms `TestShutdownAll`, `TestShutdownAllCleanup`, `TestHttpManagerRestart`, and `TestHttpLifecycleStderrLog` all replace `_terminate_with_timeout` with `AsyncMock()`/a fake function, so none of them exercise the changed `_wait_exited` code path and cannot regress from this change. |
| Lint | `uv run ruff check tests/test_lifecycle.py` | 0 errors | PASS |
| Type check | `uv run mypy scripts/` | No new errors (test file is covered by mypy per `rules/coding.md`) | PASS (no `test_lifecycle` hits in the error output) |
