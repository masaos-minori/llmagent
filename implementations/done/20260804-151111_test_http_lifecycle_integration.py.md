# Implementation Procedure: tests/agent/test_http_lifecycle_integration.py

## Goal
Add a test proving `HttpServerLifecycleManager.start()`'s health-poll loop, when raced against a
`shutdown_event` that fires shortly after polling begins, raises `HttpStartupError` (reason
"shutdown requested") well before `cfg.startup_timeout_sec` elapses — rather than waiting out
the full per-server timeout.

## Scope
- In scope: one new test added to `TestSubprocessLifecycle` (current lines 279-467, adjacent to
  `test_start_starts_new_process`, current lines 296-322) covering the poll-loop
  shutdown-interruption path added to `start()` by the companion
  `implementations/20260804-151108_http_lifecycle.py.md` procedure.
- Out of scope: all other existing tests in this file (`TestSignalHandling`,
  `TestShutdownSequence`, `TestErrorRecovery`, and the rest of `TestSubprocessLifecycle`) — no
  edits needed.

## Assumptions
- This procedure assumes `implementations/20260804-151108_http_lifecycle.py.md` (this same
  batch) is applied to `scripts/agent/http_lifecycle.py` first, so `start()` accepts
  `shutdown_event` and raises `HttpStartupError` with `reason="shutdown requested"` when the
  poll-loop race detects a shutdown. The test below cannot pass against the pre-change source.
- The existing `test_start_starts_new_process` test (current lines 296-322) already establishes
  the mocking pattern for this method: `patch.object(subprocess, "Popen", ...)`,
  `patch.object(os, "getpgid", ...)`, `patch.object(time, "monotonic", side_effect=...)`,
  `patch.object(asyncio, "sleep", return_value=None)` to fast-forward past real delays, plus a
  `proc_mock` with `poll=Mock(return_value=None)` (never exits) and a health check that never
  returns 200 (simulating a hung server) — the new test reuses this same shape, replacing the
  `asyncio.sleep` patch with a `shutdown_event.set()` trigger instead of a monotonic-clock
  fast-forward.

## Design decisions
- Use a real `asyncio.Event`, pre-set via `event.set()` before calling `start()` (simplest form
  of "shutdown fires shortly after polling begins": firing it before the first poll iteration
  already exercises the interruption branch, since the production code's per-iteration race
  checks the event on every loop pass) — avoids needing a timed background task, keeping the
  test deterministic and fast.
- Mock the health-check HTTP client (`httpx.AsyncClient`) to always return a non-200 status (or
  raise `httpx.HTTPError`), so the loop would otherwise continue polling indefinitely absent the
  shutdown race — isolates the assertion to "shutdown wins the race," not "health check
  eventually succeeds."
- Assert on wall-clock elapsed time using a small, generous upper bound (e.g. assert elapsed <
  2.0s, well under any realistic `startup_timeout_sec` such as the 30s default) rather than
  patching `time.monotonic()`, since the shutdown-fire path does not depend on the deadline
  clock at all — this keeps the test closer to a real end-to-end timing characteristic while
  still being fast and non-flaky.

## Alternatives considered
- Set `shutdown_event` asynchronously via a short `asyncio.sleep(0.1)` background task instead
  of pre-setting it before the call: rejected as the primary test — adds timing nondeterminism
  without adding coverage, since the production race-check happens on every loop iteration
  (pre-setting exercises the same code path deterministically). A secondary variant could be
  added later if "mid-poll, not pre-poll" needs separate coverage, but is not required to
  satisfy this plan's Implementation step 9.
- Fast-forward via `patch.object(time, "monotonic", ...)` like `test_start_starts_new_process`
  does for the timeout path: rejected for this test — conflates two different exit conditions
  (deadline-timeout vs. shutdown-interruption) in one test; keeping the shutdown test
  clock-independent makes the two paths' tests easier to tell apart from failure output alone.

## Implementation

### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
1. Add `import asyncio` and `pytest` are already imported (confirmed, current lines 10, 18) —
   no new top-level imports required.
2. Add a new test method inside `TestSubprocessLifecycle` (current lines 279-467), e.g.:
   ```python
   @pytest.mark.asyncio
   async def test_start_shutdown_event_interrupts_poll_loop(
       self, mgr: HttpServerLifecycleManager
   ) -> None:
       cfg = _make_cfg(cmd=["node", "/fake/server.js"])
       proc_mock = Mock(pid=9999, poll=Mock(return_value=None))
       shutdown_event = asyncio.Event()
       shutdown_event.set()

       mock_client = AsyncMock()
       mock_client.get = AsyncMock(side_effect=httpx.HTTPError("connection refused"))
       mock_client.__aenter__ = AsyncMock(return_value=mock_client)
       mock_client.__aexit__ = AsyncMock(return_value=None)

       start_time = time.monotonic()
       with (
           patch.object(subprocess, "Popen", return_value=proc_mock),
           patch.object(os, "getpgid", return_value=9999),
           patch("httpx.AsyncClient", return_value=mock_client),
       ):
           with pytest.raises(HttpStartupError) as exc_info:
               await mgr.start("test", cfg, shutdown_event=shutdown_event)
       elapsed = time.monotonic() - start_time

       assert exc_info.value.failure.reason == "shutdown requested"
       assert elapsed < 2.0
       assert mgr._http_procs.get("test") is None
   ```
   (Adapt the exact `HttpStartupError`/`StartupFailure` attribute access to this file's existing
   convention — see `test_startup_failure_contains_stderr`, current line ~898, for the accessor
   pattern already used in this file.)

### Method
- Located the target class and an adaptable existing test via `grep -n "class
  TestSubprocessLifecycle\|def test_start_starts_new_process\|def _make_cfg\|class Test" tests/
  agent/test_http_lifecycle_integration.py`, then read lines 1-60 (fixtures/imports/`_make_cfg`)
  and lines 279-357 (`test_start_starts_new_process`, `test_start_env_includes_os_environ`)
  directly to confirm the mocking idiom before drafting the new test in the same style.
- Confirmed `HttpStartupError`/`StartupFailure`'s shape via reading
  `scripts/agent/http_lifecycle.py:36-52` (already read in this session for the companion
  `http_lifecycle.py` procedure).

### Details
- No new fixtures required — reuses the existing `mgr` fixture (referenced throughout this
  class) and `_make_cfg()` helper (current line 27).
- If this file's existing `httpx.AsyncClient` patching convention differs from the sketch above
  (e.g. patched via `"agent.http_lifecycle.httpx.AsyncClient"` rather than bare `"httpx.
  AsyncClient"`), the implementer should match whichever form the adjacent tests in this class
  already use, for consistency — this was not fully disambiguated from the line ranges read in
  this session and should be confirmed at implementation time.

## Compatibility considerations
- Purely additive test; no existing test in this file is modified.

## Security considerations
- N/A — test-only change, no new credential or external I/O (health check is mocked).

## Rollback considerations
- Additive test-only change; revertable via `git revert` with no production impact.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | All existing tests pass unmodified; new shutdown-interruption test passes |
| Format/lint | `uv run ruff format tests/agent/test_http_lifecycle_integration.py && uv run ruff check tests/agent/test_http_lifecycle_integration.py` | 0 errors |
| Type check | `uv run mypy tests/agent/test_http_lifecycle_integration.py` | No new errors vs. baseline |
| Full suite | `uv run pytest` | No new failures |
| Coverage gate | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines in `http_lifecycle.py` |
| Final gate | `uv run pre-commit run --all-files` | Passes |

## Out of scope
- `TestSignalHandling`, `TestShutdownSequence`, `TestErrorRecovery` — unchanged.
- `deploy/deploy.sh` — test files are not part of the deploy copy list.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-142044_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-151111
- Related target files: tests/agent/test_http_lifecycle_integration.py
