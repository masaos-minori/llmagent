# Implementation Procedure: test_repl_error_handling.py — regression test for non-`RuntimeError` turn exception

## Goal

Add a regression test asserting that when a turn raises a non-`RuntimeError` exception, the REPL loop contains it, reports it through the view, and stays responsive for the next input instead of propagating out of the loop. Implements `REQ-002` (short purpose: verify the loop remains responsive after a turn-escaping exception).

## Scope

- **In scope**: Add one regression test to `tests/agent/test_repl_error_handling.py` that drives a non-`RuntimeError` exception through `handle_turn` and asserts the loop does not propagate it and remains ready for the next input.
- **Out of scope**: Modifying `scripts/agent/repl_input_loop.py` (covered by the sibling procedure for that target file); changing the existing diagnostic-save-error test; testing startup `session.start()` translation or shutdown-race paths.

## Assumptions

- The loop's preferred containment location is `_repl_loop` (see the sibling procedure for `scripts/agent/repl_input_loop.py`); the test exercises `_repl_loop` directly so it validates the actual containment behavior.
- The CLI view exposes `write_fatal`/`write_warning` (confirmed present and mocked in the existing test in this file).
- With `shutdown_event=None`, `_repl_loop` awaits the dispatch task without spawning a shutdown watcher, giving a deterministic single-turn path for the test.

## Design decisions

- **Exercise the real loop, not a unit stub**: drive `ReplInputLoop._repl_loop` end-to-end with mocked collaborators rather than mocking `_repl_loop` itself, so the test fails if containment regresses.
- **Isolate the failure point**: mock `Orchestrator.handle_turn` to raise the non-`RuntimeError` exception, matching the Plan's T1 (use `ValueError`).
- **Control input deterministically**: feed exactly one line, then EOF, so the loop dispatches once and then exits cleanly on EOF rather than hanging.
- **Reuse the file's existing mocking style** (`MagicMock(spec=...)` for `AgentContext`/`CLIView`, explicit attribute wiring) so the new test matches its neighbors.

## Alternatives considered

- **Mocking `_orchestrator.handle_turn` and calling `_dispatch_line` directly**: simpler but does not exercise the containment branch in `_repl_loop`, so it would not catch a regression in the actual fix. Rejected in favor of driving `_repl_loop`.
- **Feeding input via a thread/queue against real `input()`**: more realistic but nondeterministic and slower. Rejected in favor of monkeypatching `builtins.input`.

## Implementation

### Target file

`tests/agent/test_repl_error_handling.py`

### Procedure

1. Confirm the current test file drives only persister/diagnostic errors and contains no test that pushes a non-`RuntimeError` exception through `handle_turn` (repository evidence from the Plan).
2. Add an async test (mirroring the existing `@pytest.mark.asyncio` decoration) named to reflect intent, for example `test_repl_contains_non_runtime_error_turn_exception`.
3. Build a `MagicMock(spec=AgentContext)` wired with the attributes `_repl_loop` reads before dispatch: `conv.shutdown_requested=False`, `conv.is_processing`, `conv.memory_disabled`, `conv.memory_warning_shown`, and `stats.stat_partial_completions` (used inside `_dispatch_line`).
4. Construct `ReplInputLoop(ctx, view, shutdown_event=None)` where `view = MagicMock(spec=CLIView)`.
5. Initialize the private components `_repl_loop` requires: set `loop._cmds` to a `MagicMock(spec=CommandRegistry)` and `loop._orchestrator` to a `MagicMock(spec=Orchestrator)` whose `handle_turn` is an `AsyncMock(side_effect=ValueError("boom"))`.
6. Monkeypatch `builtins.input` to return one line on the first call and raise `EOFError` thereafter, so the loop dispatches once and then breaks on EOF.
7. Assert, after running `await loop._repl_loop()`:
   - the `ValueError` did not escape (the coroutine returned normally);
   - the view received an operator-facing write (`write_fatal` or `write_warning`) referencing the surfaced error;
   - the loop reached EOF and exited cleanly (no hang, no propagation).
8. Keep the new test isolated: do not modify the existing `test_repl_handles_diagnostic_save_error` test.

### Method

- Use `unittest.mock` helpers already imported in the file (`MagicMock`, `AsyncMock`); add `monkeypatch` fixture usage via pytest's built-in `monkeypatch` for the `builtins.input` patch.
- Do not introduce real I/O, threads, or sleeps; keep the test fast and deterministic.
- Do not assert on internal bookkeeping beyond what proves containment and responsiveness.

### Details

- Propagation path under test: `_dispatch_line` → `Orchestrator.handle_turn` → `_execute_turn` → `WorkflowEngineAdapter.execute_turn`; raising `ValueError` at `handle_turn` reproduces an exception type that currently escapes the loop.
- `shutdown_event=None` selects the no-shutdown-watcher branch of `_repl_loop`, avoiding shutdown-race complexity and isolating the turn-exception containment behavior.
- The assertion that the view was written confirms AC-1's "reported through the view"; clean return on EOF confirms AC-1's "waits for the next input" (responsiveness).

## Compatibility considerations

- The new test must coexist with the existing diagnostic-save-error test without altering its assertions.
- Test must pass once the sibling procedure's fix lands; it should fail against the pre-fix code (negative control), proving it exercises the containment branch.

## Security considerations

- The surfaced error text asserted in the test should use a benign message (`"boom"`); never assert on or leak real secrets, credentials, or sensitive session data.

## Rollback considerations

- Removing the added test reverts coverage; the change is additive and confined to the test file, so reverting the commit restores the prior test suite.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl_error_handling.py` | Format + lint | `uv run ruff format tests/agent/test_repl_error_handling.py` then `uv run ruff check tests/agent/test_repl_error_handling.py` | Clean (no diffs, no errors) |
| `tests/agent/test_repl*.py` | Regression: non-`RuntimeError` turn exception keeps loop responsive | `uv run pytest tests/agent/test_repl*.py -v` | All pass; new regression test present |
| Whole affected lifecycle suite | Full regression | `uv run pytest` on affected lifecycle suites | Pass; diff-cover >= 90% on changed lines |

## Completion criteria

- The new regression test passes and fails against the pre-fix loop (proving it exercises the containment branch) (AC-3).
- The existing REPL tests still pass (AC-3).
- ruff format/check are clean on the modified test file.

## Out of scope

- Any change to `scripts/agent/repl_input_loop.py` (handled by the sibling procedure for that target file).
- Startup `session.start()` exception translation, shutdown-race paths, or input-coroutine cancellation (tracked separately as `repl002`).
- Modifying the existing diagnostic-save-error test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add regression test for non-`RuntimeError` turn exception to `test_repl_error_handling.py` | Completed | 20261001-193738 | 20261001-193738 | REQ-002 Regression test added; negative control confirmed (fails vs pre-fix loop) |
| 2 | Run validation sequence (`rules/toolchain.md`): ruff/mypy/bandit/pytest/diff-cover | Completed | 20261001-193738 | 20261001-193738 | REQ-002 ruff clean; new test passes; existing diagnostic-save-error test still passes |

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
- **Requirement ID**: `REQ-002` — verify the loop stays responsive after a turn-escaping exception
- **Source issue**: issues/20260930-231242_repl001_repl-turn-exception-not-contained-by-runtimeerror-only-handler-crashes-interactive-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-234119_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-173643
- **Related target files**: tests/agent/test_repl_error_handling.py