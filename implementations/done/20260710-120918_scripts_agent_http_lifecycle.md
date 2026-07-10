# Implementation: Replace thread-based subprocess wait with async polling in http_lifecycle.py

Source plan: `plans/20260710-110325_plan.md` (Phase 1)

## Goal

Eliminate the non-daemon background thread that `_terminate_with_timeout` currently leaks via `asyncio.to_thread(proc.wait)` when the target subprocess doesn't exit within the timeout, so that a stuck (e.g. D-state) MCP subprocess can never cause the agent's own process shutdown to hang on `concurrent.futures.thread`'s `atexit`-registered thread join.

## Scope

- `scripts/agent/http_lifecycle.py` only.
- Replace the two `await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)` call sites inside `_terminate_with_timeout` with a new non-blocking polling helper.
- The externally observable behavior of `_terminate_with_timeout` (SIGTERM → wait → SIGKILL-on-timeout → wait → warn-on-still-alive) must not change — this is an internal implementation swap, not a behavior change.
- Does not change the default `timeout` value (3.0s / 5.0s at call sites) — that is a separate, deliberately out-of-scope decision (see source plan section 2, UNK-02 in the prior plan).

## Assumptions

1. `proc.poll()` is non-blocking (wraps `os.waitpid(pid, os.WNOHANG)`) and returns `None` immediately for a still-running process regardless of process state (including D-state) — verified against CPython's `subprocess` module semantics, not something that needs empirical re-verification here.
2. No other code path relies on `_terminate_with_timeout` raising `TimeoutError` — it currently only ever catches its own `TimeoutError` internally and never lets it propagate, so removing `asyncio.wait_for` entirely (and therefore the possibility of a `TimeoutError`) does not change the method's external contract (`-> None`, never raises for a timeout condition).

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Add a new private helper method `_wait_exited(proc, timeout) -> bool` to `HttpServerLifecycleManager`, placed directly above `_terminate_with_timeout` (i.e. after `_read_stderr_tail`, before `_terminate_with_timeout`, keeping related methods adjacent).
2. Add a class-level constant `_TERMINATE_POLL_INTERVAL_SEC: float = 0.05` near the existing `_STDERR_TAIL_BYTES` class constant (line 56).
3. Rewrite `_terminate_with_timeout` (lines 86-124) to call `self._wait_exited(...)` instead of `asyncio.wait_for(asyncio.to_thread(proc.wait), ...)`, replacing the `try/except TimeoutError` structure with a plain `if`/`else`.
4. No change to imports: `asyncio` remains used (for `asyncio.sleep`); `time` remains used (already imported, used elsewhere in `start()`).

### Method

In-place edit of one method plus one new small helper method on the same class. No new module, no new file.

### Details

#### Change 1: add `_TERMINATE_POLL_INTERVAL_SEC` class constant

Before (`scripts/agent/http_lifecycle.py:56`):

```python
    _STDERR_TAIL_BYTES = 64 * 1024
```

After:

```python
    _STDERR_TAIL_BYTES = 64 * 1024
    _TERMINATE_POLL_INTERVAL_SEC: float = 0.05
```

#### Change 2: add `_wait_exited` helper

Insert directly before `_terminate_with_timeout` (currently starting at line 86):

```python
    async def _wait_exited(self, proc: subprocess.Popen[bytes], timeout: float) -> bool:
        """Poll proc.poll() (non-blocking) until it exits or timeout elapses.

        Deliberately avoids asyncio.to_thread: wrapping a blocking proc.wait() in a
        thread cannot be cancelled once asyncio.wait_for's timeout fires, so a
        process stuck in an uninterruptible (D) state leaves a live, non-daemon
        ThreadPoolExecutor worker that CPython's interpreter-shutdown atexit hook
        (concurrent.futures.thread._python_exit) then blocks on indefinitely.
        """
        deadline = time.monotonic() + timeout
        while proc.poll() is None:
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(self._TERMINATE_POLL_INTERVAL_SEC)
        return True
```

#### Change 3: rewrite `_terminate_with_timeout`

Before (`scripts/agent/http_lifecycle.py:86-124`):

```python
    async def _terminate_with_timeout(
        self,
        proc: subprocess.Popen[bytes],
        server_key: str,
        timeout: float = 3.0,
    ) -> None:
        """Terminate proc; escalate to kill if terminate times out."""
        if proc.poll() is not None:
            return
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.terminate()
        else:
            proc.terminate()
        try:
            await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)
        except TimeoutError:
            logger.warning(
                "Lifecycle: force-killing %r (terminate timed out)",
                server_key,
            )
            pgid = self._http_pgids.get(server_key)
            if pgid is not None:
                try:
                    os.killpg(pgid, signal.SIGKILL)  # nosec B603
                except (ProcessLookupError, OSError):
                    proc.kill()
            else:
                proc.kill()
            try:
                await asyncio.wait_for(asyncio.to_thread(proc.wait), timeout=timeout)
            except TimeoutError:
                logger.warning(
                    "Lifecycle: %r still not terminated after kill",
                    server_key,
                )
```

After:

```python
    async def _terminate_with_timeout(
        self,
        proc: subprocess.Popen[bytes],
        server_key: str,
        timeout: float = 3.0,
    ) -> None:
        """Terminate proc; escalate to kill if terminate times out."""
        if proc.poll() is not None:
            return
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.terminate()
        else:
            proc.terminate()
        if await self._wait_exited(proc, timeout):
            return
        logger.warning(
            "Lifecycle: force-killing %r (terminate timed out)",
            server_key,
        )
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.kill()
        else:
            proc.kill()
        if not await self._wait_exited(proc, timeout):
            logger.warning(
                "Lifecycle: %r still not terminated after kill",
                server_key,
            )
```

#### Non-goal reminder

Do not change the `timeout: float = 3.0` default, or the `timeout=5.0` passed in `shutdown_all()` — those are out of scope (see source plan section 2 and the prior plan's UNK-02).

## Validation plan

| Check | Tool / Command | Target | Result |
|---|---|---|---|
| Unit tests (this method) | `uv run pytest tests/test_lifecycle.py -k "TestProcessGroupShutdown" -v` | All pass | PASS — 6 passed in 1.61s (after the paired rewrite in `implementations/20260710-120951_tests_test_lifecycle.md` landed) |
| Full file regression | `uv run pytest tests/test_lifecycle.py -v` | No new failures | **Not run.** After the above targeted run completed and returned results successfully, the user twice reported that the Claude Code CLI session itself crashed (required restart) during/after broader pytest invocations in this session — the second time even after switching to real `os.killpg` avoidance in a different file. Root cause not conclusively identified; out of caution, broad/full-file pytest runs are avoided in this session per explicit user direction. Static analysis substitutes: `grep`-confirmed that every other test class in `tests/test_lifecycle.py` (`TestShutdownAll`, `TestShutdownAllCleanup`, `TestHttpManagerRestart`, `TestHttpLifecycleStderrLog`) replaces `_terminate_with_timeout` with an `AsyncMock`/fake function entirely and never exercises the real `_wait_exited` polling logic, so they cannot be affected by this change. |
| Callers regression | `uv run pytest tests/test_agent_factory.py tests/test_startup.py -v` | No new failures | **Not run** (same reason as above). Static analysis: `tests/test_agent_factory.py`'s `TestShutdownGuard` uses `_make_router()` which sets `router._http_mgr = AsyncMock()` — the whole `HttpServerLifecycleManager` is replaced, never touching real code. `tests/test_startup.py`'s shutdown-related tests operate on a `mock_lifecycle` mock object, same result. Neither file's tests can be affected by this change. |
| Lint | `uv run ruff check scripts/agent/http_lifecycle.py` | 0 errors | PASS |
| Type check | `uv run mypy scripts/` | No new errors | PASS (no hits for `http_lifecycle` in the error output) |
| Complexity | `uv run radon cc scripts/agent/http_lifecycle.py -s -n C` | `_terminate_with_timeout` and `_wait_exited` stay at grade B or better (baseline before this change: `_terminate_with_timeout` = B(8)) | PASS — neither method appears in the `-n C` (grade C or worse) output; only the pre-existing, unrelated `start()` method (C(12)) is flagged |
| No-thread proof | `rg "asyncio.to_thread\|asyncio.wait_for" scripts/agent/http_lifecycle.py` | 0 hits (confirms the thread-leaking pattern is fully removed from this file) | PASS — the only matches are inside the `_wait_exited` docstring prose explaining why the pattern is avoided, not actual calls |
| Security | `uv run bandit -r scripts/agent/http_lifecycle.py -c pyproject.toml` | No new medium/high findings | PASS — only pre-existing informational `nosec` warnings, no new findings |
