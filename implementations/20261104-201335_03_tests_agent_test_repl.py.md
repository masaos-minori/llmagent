## Goal

Add entry-function tests to `tests/agent/test_repl.py` proving that `main()` returns
without raising when startup raises `StartupInterrupted`, that another exception still
propagates, and that `agent.__main__` delegates to `agent.repl.main`. Implements
REQ-004 (AC-1, AC-2, AC-3, AC-4) of the source plan.

## Scope

- Add a new class `TestMainEntry` (new) immediately after `TestRunStartupInterrupted`
  (ends L1107, before `TestCloseResourcesWALCheckpoint` at L1108).
- Add the two imports the new class needs: `runpy` (module-level, next to the other
  stdlib imports at L11-16) and `from agent.repl import main` (next to
  `from agent.repl import AgentREPL` at L22).
- Three tests, all using mocks only (no real services start):

  1. `test_main_returns_when_startup_interrupted` (new) (REQ-001, AC-1): patch
     `agent.repl.AgentREPL` so `run` raises `StartupInterrupted`, call `main()`, assert
     it returns `None` and raises nothing.
     ```python
     def test_main_returns_when_startup_interrupted(self) -> None:
         """REQ-004: main() returns without raising when startup raises StartupInterrupted."""
         from agent.startup import StartupInterrupted
         with patch("agent.repl.AgentREPL") as mock_repl:
             mock_repl.return_value.run = AsyncMock(
                 side_effect=StartupInterrupted("shutdown requested")
             )
             assert main() is None
     ```
  2. `test_main_propagates_non_interrupt_exception` (new) (REQ-003, AC-2): patch
     `agent.repl.AgentREPL` so `run` raises `RuntimeError`, assert `main()` re-raises it
     unchanged.
     ```python
     def test_main_propagates_non_interrupt_exception(self) -> None:
         """REQ-003: main() re-raises a non-interrupt exception unchanged."""
         with patch("agent.repl.AgentREPL") as mock_repl:
             mock_repl.return_value.run = AsyncMock(side_effect=RuntimeError("config invalid"))
             with pytest.raises(RuntimeError, match="config invalid"):
                 main()
     ```
  3. `test_main_module_delegates_to_repl_main` (new) (REQ-002, AC-3): patch `agent.repl.main`,
     run `agent.__main__` via `runpy` with `run_name="__main__"`, assert one call. Pop
     `agent.__main__` from `sys.modules` first so the module imports fresh under the
     patch.
     ```python
     def test_main_module_delegates_to_repl_main(self) -> None:
         """REQ-002: running agent.__main__ delegates to agent.repl.main."""
         import sys
         import runpy
         saved = sys.modules.pop("agent.__main__", None)
         try:
             with patch("agent.repl.main") as mock_main:
                 runpy.run_module("agent.__main__", run_name="__main__")
                 mock_main.assert_called_once()
         finally:
             if saved is not None:
                 sys.modules["agent.__main__"] = saved
     ```

## Assumptions

- `main()` runs `asyncio.run(AgentREPL().run())` internally, so patching
  `agent.repl.AgentREPL` and making `run` an `AsyncMock` with a `side_effect` drives the
  exact path `main()` exercises.
- `from agent.repl import main` inside `__main__.py` reads the current `agent.repl.main`
  attribute at execution time, so patching `agent.repl.main` before `runpy` runs makes
  the delegation observable (test 3).
- The interrupted-startup test (test 1) fails on the pre-change code (no try/except in
  `main()` → `StartupInterrupted` escapes → the test raises instead of returning) and
  passes after the change (REQ-004 / AC-4).

## Design decisions

- One new class `TestMainEntry` (new) keeps the entry-function tests grouped and separate from
  the existing `TestRunStartupInterrupted` (`run()` contract) and from the
  `partialcount001` `_dispatch_line` warning tests that also live in `test_repl.py`.

## Alternatives considered

- Add the three tests as methods inside `TestRunStartupInterrupted`: rejected — that
  class asserts the `run()` contract; the entry-function tests exercise `main()` /
  `__main__`, a different surface.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Add `import runpy` to the stdlib import block (near L11-16) and
   `from agent.repl import main` near L22.
2. Insert the `TestMainEntry` (new) class with the three tests above after L1107.

### Method

Append a new test class; no edits to existing tests or to `repl.py` / `__main__.py`
(those are rows 01, 02).

### Details

- Test 1 pins REQ-004's "fails on pre-change code" requirement: record in the failure log
  that it errors on the current `main()` before row 01 lands (REQ-004 / AC-4).
- Test 3 restores `sys.modules["agent.__main__"]` in `finally` so the test leaves no
  stale cache for later tests.
- No real services start: every test patches `agent.repl.AgentREPL` or `agent.repl.main`.

## Compatibility considerations

- The existing `TestRunStartupInterrupted` tests (which pin the `run()` contract) pass
  unchanged; this class only adds new surface coverage.
- Overlap with `plans/20261104-115736_partialcount001_partial-completion-counter-dead.md`:
  that Plan adds `_dispatch_line` warning tests to `test_repl.py` in a separate class;
  this Plan adds entry-function tests in `TestMainEntry` (new). Compatible, no ordering needed
  (both verified against current source in Step 3a).

## Security considerations

- N/A: behavior-lock tests with mocks only.

## Rollback considerations

- Revert the commit (`git checkout -- tests/agent/test_repl.py`).

## Validation plan

- New tests: `uv run pytest tests/agent/test_repl.py -v` — test 1 fails before row 01,
  all three pass after (AC-4); test 2 and the run() contract tests confirm propagation.
- Regression: `uv run pytest tests/agent/test_startup_rollback.py -v` — all pass.
- Static: `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/ tests/eventbus` — clean.
- Full suite + diff-cover ≥90% on the new lines; `generate_reference_table --check` exit 0.

## Completion criteria

- `main()` returns `None` on `StartupInterrupted`; another exception propagates;
  `__main__` calls `agent.repl.main` once (AC-1, AC-2, AC-3).
- Test 1 fails on the pre-change code and passes after (AC-4).
- Existing `run()` contract tests pass unchanged.

## Out of Scope

- `scripts/agent/repl.py` (row 01) and `scripts/agent/__main__.py` (row 02).
- The `partialcount001` `_dispatch_line` warning tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | N/A for this row: rows 01/02 carry the production change |
| 2 | Add or update tests per Validation plan | Pending | — | — | Three `TestMainEntry` (new) tests; test 1 recorded failing on pre-change code |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-103359_interruptexit001_startup-interrupt-exits-traceback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-201335
- **Related target files**: tests/agent/test_repl.py
