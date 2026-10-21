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

## Reason for Change
The tests that appear to cover shutdown are the reason the defect in `repl001` was not detected: the
fixture repairs the wiring before asserting the behavior the wiring provides.

## Implementation Intent
Add a wiring-level guard in the style of the existing `TestRunBindsStartupResultsToInputLoop`
(`tests/agent/test_repl.py:712-730`), which already proves the project wants this class of defect
caught by a test. Replace mock-self-asserting tests with tests that call production code.

## Target Files or Areas
- `tests/agent/test_repl.py`
- `tests/agent/test_signal_handler.py`
- `tests/agent/test_signal_handler_race.py`

## Required Changes
- Add a test that builds `AgentREPL()` (startup stubbed) and asserts the shutdown event identity
  between `SignalHandler`, `ReplInputLoop`, and `StartupOrchestrator`.
- Remove or rewrite the tautological assertion at `test_repl.py:367`.
- Rewrite `test_signal_handler_race.py` to call `SignalHandler.register()` on a real event loop and
  deliver a real signal (or invoke the handler the loop registered), asserting
  `ctx.conv.shutdown_requested` and the event on a real `AgentContext`, not a `MagicMock`.
- Delete or implement the permanently skipped classes; do not keep tests that would test a
  non-production API (`signal.signal`) if un-skipped.
- Make fixture wiring differences explicit: if a fixture re-wires a component, state why in the
  docstring and pair it with a wiring-level test.

## Constraints
- Tests must not touch `/opt/llm` or production paths (`tests/conftest.py` isolation).
- Do not add new dev dependencies.
- Keep assertions independent of the wall clock and of absolute timing (no `time.sleep`-boundary
  asserts).

## Acceptance Criteria
- At least one test fails when the shutdown event is not passed to `ReplInputLoop` (verify by
  temporarily reverting the wiring).
- No test in the three files asserts only on state that the test itself assigned to a mock.
- `uv run pytest tests/agent -q` is green with zero permanently-`skipif(True)` tests in these files.

## Testing Expectations
This issue is a test-only change; the mutation it must survive is removing the event wiring in
`scripts/agent/repl.py`. Run `uv run pytest tests/agent/test_repl.py
tests/agent/test_signal_handler.py tests/agent/test_signal_handler_race.py -q` and the full
`uv run pytest tests/agent -q`.

## Documentation Impact
Note in `docs/` test guidance (the testing section referenced by `routing.md`) that
wiring-level assertions are the required pattern for components constructed in `__init__` and rebound
after startup.

## Out of Scope
- The production fixes themselves (`repl001`, `repl002`).
- Unrelated skipped tests: `tests/agent/test_context.py:47`,
  `tests/agent/test_startup_memory_failures.py:106,119`, `tests/agent/test_signal_handler.py:51`
  (platform-gated) — tracked elsewhere, not here.

## Dependencies
- Follows `repl001`/`repl002`: the regression tests are written against the fixed behavior.

## Unresolved Questions
- Whether `test_signal_handler_race.py` should be merged into `test_signal_handler.py` or kept as a
  distinct file. Needs confirmation.

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
  `tests/agent/test_signal_handler_race.py`
