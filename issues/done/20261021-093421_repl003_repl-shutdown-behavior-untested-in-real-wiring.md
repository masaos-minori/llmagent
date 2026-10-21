# REPL shutdown behavior is untested through the real wiring; the guard tests assert mock state

## Priority
Medium

## Summary
Make the REPL shutdown/signal test suite exercise `AgentREPL.__init__` + `run()` wiring and real
signal handling, so a wiring gap like `repl001` cannot stay invisible behind green tests.

## Background
`tests/agent/test_repl.py` reaches 3467 passed / 7 skipped for `tests/agent` while the
shutdown-event wiring defect exists, i.e. the suite is green and silent about it.

## Problem
- The fixture `_make_bare_repl()` replaces the production-wired input loop with a repaired one:
  `repl._shutdown_event = asyncio.Event()` at `tests/agent/test_repl.py:60` and
  `repl._input_loop = ReplInputLoop(ctx, view, repl._shutdown_event)` at `:78`. Every
  shutdown-race test therefore runs on wiring the production code never produces. Some tests set the
  event on both objects explicitly (`:384-385`, `:438-440`). No test constructs `AgentREPL()` and
  inspects the wiring `__init__` produced.
- `tests/agent/test_repl.py:367` contains `assert dispatch_hang.is_set() or True` — an assertion that
  can never fail.
- `tests/agent/test_signal_handler_race.py` operates on `MagicMock(spec=AgentREPL)` and asserts on the
  mock's own attributes (`:14-45`); it simulates the guard with a literal `if handler._turn_active:`
  (`:39-41`) and calls `handler._on_first_turn(...)`, an attribute that does not exist on `AgentREPL`
  (it exists on `Orchestrator`/`ConversationStateManager`). `:79` uses `repl.ctx` while production uses
  `_ctx`. These tests cannot fail regardless of production code, yet their names suggest coverage.
- `TestCrossPlatformSignalHandlerConsistency` is permanently disabled by
  `@pytest.mark.skipif(True, ...)` (`:48-70`), and the Windows fallback class is skipped (`:106`); the
  skipped class patches `signal.signal` while production uses `loop.add_signal_handler`
  (`scripts/agent/signal_handler.py:61-63`), so it would not test the production path even if enabled.
- `tests/agent/test_signal_handler.py` covers only the `NotImplementedError` fallback; nothing asserts
  real SIGINT/SIGTERM behavior on the REPL path.

### Verification (re-read at HEAD `dc26b0015`, 2026-10-22)

Every claim above is confirmed, with the exact mechanism identified and three corrections added.

Confirmed:

- `tests/agent/test_repl.py:28-88` is the fixture the issue describes: `AgentREPL.__new__(AgentREPL)` at
  `:30` (bypasses `__init__`), `repl._shutdown_event = asyncio.Event()` at `:60`,
  `repl._input_loop = ReplInputLoop(ctx, view, repl._shutdown_event)` at `:78`, and hand-binding of
  `_input_loop._cmds` / `_input_loop._orchestrator` at `:79-80`. `grep -rn "AgentREPL(" tests/` returns
  no match, so no test ever runs `AgentREPL.__init__`.
- The production side of the same claim, stated precisely: `repl.py:82` assigns
  `self._shutdown_event: asyncio.Event | None = None`, `:85` passes that `None` to `ReplInputLoop`, and
  `:92` passes it to `SignalHandler`. `run()` (`:110-114`) later creates the event and rebinds **only**
  `SignalHandler` through `set_shutdown_event()` (`signal_handler.py:136-138`) and hands the new event to
  `StartupOrchestrator` (`repl.py:120-122` → `startup.py:53`, `:61`, which forwards it to
  `McpServerStarter` at `:62`). `ReplInputLoop.bind()` (`repl_input_loop.py:72-75`) binds only `_cmds`
  and `_orchestrator`. So in production `ReplInputLoop._shutdown_event` stays `None` for the whole
  session and `_read_input`'s fallback branch (`repl_input_loop.py:189-194`) is the only branch ever
  taken. The fixture repairs exactly this, which is why the suite is green while `repl001`'s defect
  exists.
- `test_repl.py:367` is `assert dispatch_hang.is_set() or True  # may or may not have been cancelled`,
  inside `TestReplLoop.test_signal_mid_turn_exits_within_graceful_timeout` (`:334-368`). Two more
  never-failing structures sit in the same test: `except TimeoutError: pass  # Should not happen`
  (`:359-361`) swallows the guard the test exists to measure, and `:364-365` asserts
  `elapsed = time.time() - start; elapsed < 2.0`, which contradicts this issue's own Constraint.
- `:384-385` (`test_signal_before_turn_starts_still_exits`) sets `repl._shutdown_event` **and**
  `repl._input_loop._shutdown_event`; `:438-440` (`test_shutdown_during_input_cancels_input_coro`)
  replaces the event on both objects. Confirmed. A second fixture performs the same repair:
  `_make_repl_for_shutdown()` (`:618-637`) — `AgentREPL.__new__` at `:620`, a fresh
  `asyncio.Event()` at `:632-633`, `ReplInputLoop(ctx, view, shutdown_event)` at `:636`. Its docstring
  (`:619`) says the event is there "for `_read_input` tests" but not that it bypasses `__init__` or that
  production passes `None`, which is the disclosure this issue asks for.
- `tests/agent/test_signal_handler_race.py` (140 lines, 8 tests) matches the issue line for line:
  `MagicMock(spec=AgentREPL)` at `:17`, `:25`, `:34`; the simulated guard `if handler._turn_active:` at
  `:39-41`; `handler._on_first_turn` (`:36`, `:43`) — that attribute exists on `Orchestrator`
  (`orchestrator.py:83`), `ConversationStateManager` (`conversation_state_manager.py:68`) and
  `AuditEventEmitter` (`audit_event_emitter.py:64`), not on `AgentREPL`; `repl.ctx` at `:75-92` where
  production spells `_ctx` (`repl.py:78`); `@pytest.mark.skipif(True, ...)` at `:48` (class, 2 tests)
  and `:106` (1 test); the skipped class patches `signal.signal` while
  `SignalHandler.register()` uses `loop.add_signal_handler` (`signal_handler.py:51-63`).
- `tests/agent/test_signal_handler.py` (78 lines, 2 tests) covers only the Windows fallback:
  `test_complete_failure_logs_error` (`:36-49`) drives the `NotImplementedError` branch with a
  `MagicMock` loop, and `:51-78` is permanently skipped.

Corrections to the issue's claims:

- "nothing asserts real SIGINT/SIGTERM behavior on the REPL path" is too strong.
  `TestSigtermHandlerShutdownCoordination` (`test_repl.py:1249-1312`) already drives the real
  `AgentREPL.run()`, captures the closure that the real `SignalHandler.register()` handed to the loop
  (only the `add_signal_handler` *call* is patched, `:1268-1277`), invokes it, and asserts on real
  state: `repl._ctx.conv.shutdown_requested is True` and `repl._shutdown_event.is_set()`
  (`:1297-1298`, `:1311-1312`). What is genuinely missing is (a) a real signal delivered to the
  process, and (b) any assertion about the `ReplInputLoop` and `SignalHandler` objects `__init__`
  produced. A new test must not duplicate (a) of `:1249-1312` as if it did not exist.
- The loop-side shutdown machinery is also already exercised on a real event loop with real
  `asyncio.Event` objects, on the fixture-repaired wiring:
  `test_signal_mid_turn_exits_within_graceful_timeout` (`:334`),
  `test_signal_before_turn_starts_still_exits` (`:370`),
  `test_shutdown_during_input_cancels_input_coro` (`:427`). The gap is the wiring, not the machinery.
- `TestRunBindsStartupResultsToInputLoop` (`:712-730`) is green at HEAD and is the wiring-guard pattern
  this issue asks to extend (`assert repl._input_loop._cmds is cmds`, `:729-730`). It is cited
  accurately.
- Numbers in `Background` are stale at this HEAD: `uv run pytest tests/agent -q --collect-only` collects
  3487 tests, and `uv run pytest tests/agent tests/test_cli_view.py -q` reports **3536 passed,
  7 skipped in 121.00 s**. The issue's `3467 passed / 7 skipped` is not reproducible. The qualitative
  claim (green while the defect exists) holds.
- The permanently-`skipif(True)` sites are 3 (4 tests): `test_signal_handler_race.py:48` (2),
  `:106` (1), `test_signal_handler.py:51` (1). The other 3 of the 7 skips are condition-gated
  (`test_context.py:41`, `memory/test_memory_vec_session.py:25`, `memory/test_memory_retriever.py:610`).
  No workflow runs on Windows: every job in `.github/workflows/` is `runs-on: ubuntu-latest`, so those
  Windows-gated tests can never execute in this repository's CI.
- `Documentation Impact` names a document that does not exist: there is no `docs/` test-guidance file
  (`docs/` contains `00_governance`, `01_overview`, `10_adr`, `21_rag`, `22_mcp`, `23_agent`,
  `24_eventbus`, `40_shared`, `41_db`, `90_deployment`, `91_security`; no `docs/01_general/`). The
  test-structure rules live in `skills/python-test-and-fix/workflow.md` `Test structure` (`:24-54`) and
  the enforced rules in `skills/python-test-and-fix/SKILL.md` `Core Testing Rules` (`:18-23`), which is
  where `routing.md:14-15` sends test work. That is the correct target for the new rule.
- `test_signal_handler_race.py` also violates `workflow.md:53-54` (`tests/` mirrors `scripts/`): there is
  no `scripts/agent/signal_handler_race.py`, and the mirror-named `test_signal_handler.py` already
  exists. Nothing references the file: `grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/
  rules/` returns no match.
- Constructing the real `AgentREPL()` in a test is feasible without touching `/opt/llm`: every
  collaborator `__init__` only stores references (`wal_checkpoint_manager.py:43-45`,
  `session_persister.py:39-48`, `resource_shutdown_coordinator.py:53-62`, `diagnostic_store.py:39-41`),
  and `WalCheckpointManager` opens its `SQLiteHelper` inside `checkpoint_sync()`, not in `__init__`. Only
  the three heavy names imported into `agent.repl` — `AgentContext` (`repl.py:78`), `CLIView` (`:79`,
  which builds a real `prompt_toolkit.PromptSession`), and `DiagnosticStore` (`:80`) — need to be replaced
  at the use-site module, which is the form `tools/check_mock_patch_targets.py` requires.

## Reason for Change
The tests that appear to cover shutdown are the reason the defect in `repl001` was not detected: the
fixture repairs the wiring before asserting the behavior the wiring provides.

## Implementation Intent
Add a wiring-level guard in the style of the existing `TestRunBindsStartupResultsToInputLoop`
(`tests/agent/test_repl.py:712-730`), which already proves the project wants this class of defect
caught by a test. Replace mock-self-asserting tests with tests that call production code.

## Target Files or Areas
- `tests/agent/test_repl.py` (modify)
- `tests/agent/test_signal_handler.py` (modify: real-loop registration and a real delivered signal)
- `tests/agent/test_signal_handler_race.py` (delete; see Verification and Required Changes)
- `skills/python-test-and-fix/SKILL.md`, `skills/python-test-and-fix/workflow.md` (the test-guidance home
  the Documentation Impact intends; no `docs/` test-guidance file exists)

Not targeted: `scripts/agent/repl.py`, `scripts/agent/signal_handler.py`,
`scripts/agent/repl_input_loop.py` (this issue changes no production code; the wiring it wants asserted
is `repl001`'s fix), `tests/agent/test_context.py:41` and the `tests/agent/memory/` skips (platform- or
extension-gated, listed in Out of Scope).

## Required Changes
- Add a test that builds the real `AgentREPL()` with only `agent.repl.AgentContext`, `agent.repl.CLIView`
  and `agent.repl.DiagnosticStore` replaced at the use-site module, and asserts that one
  `asyncio.Event` object is identical in `AgentREPL._shutdown_event`,
  `ReplInputLoop._shutdown_event` and `SignalHandler._shutdown_event` after `__init__`, and stays
  identical after `run()` with startup stubbed. `run()`'s chain holds the event in four places
  (`repl.py:113-114`, `:120-122` → `startup.py:53`, `:61-62`), so the post-`run()` assertion covers the
  `StartupOrchestrator`/`McpServerStarter` holders the issue names; `ReplInputLoop` is the one holder that
  today receives `None` (`repl.py:82`, `:85`).
- Remove the tautological assertion at `test_repl.py:367` **and** the two adjacent never-failing
  structures in the same test: let the `asyncio.wait_for(…, timeout=5.0)` result decide the outcome
  instead of `except TimeoutError: pass` (`:359-361`), and drop the `time.time()` arithmetic at
  `:364-365` in favour of that bound. This is what the issue's own Constraint already requires.
- Delete `tests/agent/test_signal_handler_race.py` rather than rewriting it: after the mock-self-asserting
  bodies (`:13-45`, `:72-102`) and the permanently skipped `signal.signal` class (`:48-70`) are removed,
  the only remaining test (`TestWindowsCtypesFallback`, `:104-140`) duplicates
  `test_signal_handler.py::TestWindowsCtypesFallback` (`:33-78`) through a different mechanism, and the
  file has no `scripts/` mirror (`workflow.md:53-54`).
- Add the coverage the deletion leaves uncovered, in `test_signal_handler.py`: `SignalHandler.register()`
  called on the real running loop asserts handlers are installed for both `SIGTERM` and `SIGINT`
  (`signal_handler.py:51-63` — nothing asserts the SIGINT half today), and a real
  `os.kill(os.getpid(), signal.SIGTERM)` sets `ctx.conv.shutdown_requested` on a real `AgentContext` and
  sets the event. A companion case with `shutdown_event=None` asserts `shutdown_requested` is still set
  and nothing raises, which is HEAD's actual `__init__` wiring (`repl.py:89`). Restore the process's
  prior handlers in teardown (`signal.getsignal` capture plus `loop.add_signal_handler(sig)` removal).
- Delete the permanently skipped Windows-success tests (`test_signal_handler_race.py:106`,
  `test_signal_handler.py:51-78`): no workflow in `.github/workflows/` runs on Windows, so a skip entry
  records coverage the repository can never run. Keep the contract as an explicit statement in the
  module docstring (`test_signal_handler.py:3-11` already does this) rather than as a test that is always
  skipped. `test_complete_failure_logs_error` (`:36-49`) is kept: it does exercise production code.
- Make fixture wiring differences explicit: `_make_bare_repl`'s docstring must state that it bypasses
  `__init__` and repairs the shutdown-event wiring production does not provide at HEAD (`:60`, `:78-80`),
  and every class that depends on the repaired wiring must say so. A fixture repair is only acceptable
  together with a wiring-level test; `TestRunBindsStartupResultsToInputLoop` (`:712-730`) is the pattern
  to extend.

## Constraints
- Tests must not touch `/opt/llm` or production paths (`tests/conftest.py` isolation). Constructing the
  real `AgentREPL()` must keep `AgentContext`, `CLIView` and `DiagnosticStore` replaced at the
  `agent.repl` use-site so no config file, database or terminal is opened.
- Do not add new dev dependencies. `os.kill`, `signal.getsignal`, `loop.add_signal_handler` and
  `pytest-asyncio` (already configured, `pyproject.toml:131-136`) are enough for real signal delivery.
- Keep assertions independent of the wall clock and of absolute timing (no `time.sleep`-boundary asserts).
  `TestReplLoop.test_signal_mid_turn_exits_within_graceful_timeout` already violates this at
  `tests/agent/test_repl.py:364-365` (`elapsed = time.time() - start`, `elapsed < 2.0`); bringing it in
  line is part of this issue, not a separate cleanup.
- Real signal handlers installed on the running loop must be removed in teardown and the process's prior
  dispositions restored (`signal.getsignal` capture + `loop.add_signal_handler(sig)` with no callback), so
  later tests in the same process are unaffected (`skills/python-test-and-fix/SKILL.md:22`).

## Acceptance Criteria
- At least one test fails when the shutdown event is not passed to `ReplInputLoop` (verify by
  temporarily reverting the wiring): with `repl001` implemented, edit the construction so
  `ReplInputLoop` receives `None`, run `uv run pytest tests/agent/test_repl.py -q`, expect the wiring
  guard to fail, then restore with `git checkout -- scripts/agent/repl.py`. At HEAD the guard already
  fails for the same reason (`repl.py:82`, `:85`), which is the reason the ordering below is a hard
  constraint.
- A `SIGTERM` delivered with `os.kill(os.getpid(), signal.SIGTERM)` sets `conv.shutdown_requested` on a
  real `AgentContext` and sets the event, and `signal.getsignal(signal.SIGTERM)` /
  `signal.getsignal(signal.SIGINT)` are identical before and after the file runs.
- No test in the target files asserts only on state that the test itself assigned to a mock, contains an
  assertion that can never be false, or performs `time.time()` arithmetic. Checkable with:
  `grep -n "or True" tests/agent/test_repl.py`,
  `grep -n "MagicMock(spec=AgentREPL)" tests/agent/`,
  `grep -n "time.time()" tests/agent/test_repl.py`.
- `uv run pytest tests/agent -q` is green and no permanently-`skipif(True)` test remains anywhere under
  `tests/` (HEAD: 3 such sites, 4 tests — `test_signal_handler_race.py:48`, `:106`,
  `test_signal_handler.py:51`). The remaining skips are the condition-gated
  `test_context.py:41`, `memory/test_memory_vec_session.py:25`, `memory/test_memory_retriever.py:610`.
- `tests/agent/test_signal_handler_race.py` no longer exists and no reference to it remains:
  `grep -rn "test_signal_handler_race" .` is empty.

## Testing Expectations
This issue is a test-only change; the mutation it must survive is removing the event wiring in
`scripts/agent/repl.py`. Baselines at HEAD `dc26b0015` to compare against:
`uv run pytest tests/agent -q --collect-only` → 3487 collected;
`uv run pytest tests/agent tests/test_cli_view.py -q` → 3536 passed, 7 skipped in 121.00 s.
Deleting `test_signal_handler_race.py` removes 8 collected tests (4 of them always skipped) and
`test_signal_handler.py:51-78` removes 1 more; record the new collected count in the implementation
record so the delta is attributable. Run
`uv run pytest tests/agent/test_repl.py tests/agent/test_signal_handler.py -q`, then the full
`uv run pytest tests/agent -q`, then the mutation above, then `uv run python tools/check_mock_patch_targets.py`
(new `patch("agent.repl.…")` targets are added) and `uv run ruff format` / `uv run ruff check`. Coverage:
`uv run coverage run -m pytest tests/` then `uv run coverage xml` and
`uv run diff-cover coverage.xml --compare-branch=master` (90% changed-line threshold).

## Documentation Impact
Register the rule in the two places `routing.md:14-15` sends test work, because no `docs/` test-guidance
file exists: `skills/python-test-and-fix/SKILL.md` `Core Testing Rules` (`:18-23`, one rule stating that
components constructed in `__init__` and rebound after startup require a wiring-level guard test, and that
a test MUST NOT assert on state the test itself assigned to a mock) and `skills/python-test-and-fix/workflow.md`
`Test structure` (`:24-54`, a paragraph on pairing a fixture that repairs wiring with a wiring-level test,
with `_make_bare_repl` as the worked example). No `docs/23_agent/*` change: no documented behavior of
`AgentREPL`, `SignalHandler` or `ReplInputLoop` changes here.

## Out of Scope
- The production fixes themselves (`repl001`, `repl002`).
- Unrelated skipped tests: `tests/agent/test_context.py:47`,
  `tests/agent/test_startup_memory_failures.py:106,119`, `tests/agent/test_signal_handler.py:51`
  (platform-gated) — tracked elsewhere, not here.

## Dependencies
- Follows `repl001` (`plans/20261022-030840_plan.md`) as a hard ordering constraint, not a preference:
  the wiring guard asserts something production does not do until that Plan is implemented, so implementing
  this issue first would leave either a failing suite or a guarded `xfail`. Follows `repl002`
  (`plans/20261022-040200_plan.md`) for `tests/agent/test_repl.py`: that Plan adds cases to the same file
  and changes none, and `repl002` changes the read `_read_input` races against, so the wiring this issue
  asserts should be the post-`repl002` one.
- `TestReplLoop.test_signal_mid_turn_exits_within_graceful_timeout`'s 5.0 s `asyncio.wait_for` bound is
  tighter than production's `_GRACEFUL_TIMEOUT_S = 10.0` (`repl_input_loop.py:55`). It stays correct only
  while the hung dispatch in that test is cancellable; if `repl001`'s bounded cancel path makes an
  uncancellable dispatch reachable, the bound must be revisited. Needs confirmation at implementation.

## Unresolved Questions
- Whether `test_signal_handler_race.py` should be merged into `test_signal_handler.py` or kept as a
  distinct file. **Resolved: delete it.** After the mock-self-asserting bodies and the permanently skipped
  `signal.signal` class are removed, nothing left in the file tests a production API, its one remaining
  test duplicates `test_signal_handler.py::TestWindowsCtypesFallback` (`:33-78`), and the file has no
  `scripts/` mirror (`skills/python-test-and-fix/workflow.md:53-54`). `test_signal_handler.py` becomes the
  single home of signal coverage.
- Whether the permanently skipped Windows-success tests should be deleted or kept as skips. **Resolved:
  delete**, on the measured fact that every job in `.github/workflows/` is `runs-on: ubuntu-latest`, so a
  skip in this repository can never become a pass. The contract stays documented in
  `test_signal_handler.py`'s module docstring (`:3-11`), which already explains the platform gate.

## AI Implementation Instruction
Write tests that fail when the production wiring is wrong. Do not simulate production logic inside a
test body, and do not assert on attributes the test itself set on a mock.

## Traceability
- **Workflow phase**: `python-code-review` (REPL core-loop and test review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `tests/agent/test_repl.py`, `tests/agent/test_signal_handler.py`,
  `tests/agent/test_signal_handler_race.py` (to be deleted),
  `skills/python-test-and-fix/SKILL.md`, `skills/python-test-and-fix/workflow.md`
