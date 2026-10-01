# Implementation Procedure: test_repl.py — regression test for shutdown-during-input cancellation

## Goal

Add a regression test asserting that a shutdown fired during an in-progress input read results in `input_coro` being cancelled. Implements `REQ-003` (short purpose: verify `input_coro` is cancelled on shutdown-during-input).

## Scope

- **In scope**: Add one regression test to `TestReplLoop` in `tests/agent/test_repl.py` that drives a shutdown event mid-read and asserts `input_coro.cancelled()` is True and the read returns `None`.
- **Out of scope**: Modifying `scripts/agent/repl_input_loop.py` (covered by the sibling procedure for that target file); changing the existing `test_shutdown_requested_breaks_loop` test; testing startup `session.start()` translation or shutdown-race paths.

## Assumptions

- The existing `TestReplLoop` class already drives `_read_input` with mocked `input` and fires shutdown (e.g. `test_shutdown_requested_breaks_loop`); the new test can follow the same pattern.
- With `shutdown_event=None`, `_read_input` skips the shutdown-watcher branch entirely, so the test must use a real `asyncio.Event` to exercise the shutdown-during-input path.
- The CLI view exposes `write_turn_end` (confirmed present in the existing test setup).

## Design decisions

- **Exercise the real loop, not a unit stub**: drive `ReplInputLoop._read_input` end-to-end with mocked collaborators rather than mocking `_read_input` itself, so the test fails if cancellation regresses.
- **Isolate the failure point**: fire the shutdown event while `input("> ")` is blocked in the executor, matching the Plan's T1.
- **Reuse the file's existing mocking style** (`MagicMock(spec=...)` for `AgentContext`/`CLIView`, explicit attribute wiring) so the new test matches its neighbors.

## Alternatives considered

- **Modifying `test_shutdown_requested_breaks_loop`**: simpler but mixes concerns — that test validates shutdown breaking the loop, not specifically that `input_coro` is cancelled. Rejected in favor of a separate dedicated test.
- **Feeding input via a thread/queue against real `input()`**: more realistic but nondeterministic and slower. Rejected in favor of monkeypatching `builtins.input`.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Confirm the current test file drives only persister/diagnostic errors and contains no test that asserts `input_coro.cancelled()` after a shutdown-during-read (repository evidence from the Plan).
2. Add an async test (mirroring the existing `@pytest.mark.asyncio` decoration) named to reflect intent, for example `test_shutdown_during_input_cancels_input_coro`.
3. Build a `MagicMock(spec=AgentContext)` wired with the attributes `_repl_loop` reads before dispatch: `conv.shutdown_requested=False`, `conv.is_processing`, `conv.memory_disabled`, `conv.memory_warning_shown`, and `stats.stat_partial_completions` (used inside `_dispatch_line`).
4. Construct `ReplInputLoop(ctx, view, shutdown_event=asyncio.Event())` where `view = MagicMock(spec=CLIView)`.
5. Initialize the private components `_repl_loop` requires: set `loop._cmds` to a `MagicMock(spec=CommandRegistry)` and `loop._orchestrator` to a `MagicMock(spec=Orchestrator)`.
6. Monkeypatch `builtins.input` to return one line on the first call and raise `EOFError` thereafter, so the loop dispatches once and then exits cleanly on EOF.
7. Start a task that fires `shutdown_event.set()` after a brief delay (e.g., `asyncio.sleep(0.01)`), simulating a shutdown request during the in-progress input read.
8. Assert, after running `await loop._read_input(loop)`:
   - `input_coro.cancelled()` is True (the pending `input("> ")` was cancelled);
   - the read returns `None` (the shutdown abort path was taken);
   - the loop reached EOF and exited cleanly (no hang, no propagation).
9. Keep the new test isolated: do not modify the existing `test_shutdown_requested_breaks_loop` test.

### Method

- Use `unittest.mock` helpers already imported in the file (`MagicMock`, `AsyncMock`); add `monkeypatch` fixture usage via pytest's built-in `monkeypatch` for the `builtins.input` patch.
- Do not introduce real I/O, threads, or sleeps; keep the test fast and deterministic.
- Do not assert on internal bookkeeping beyond what proves cancellation and responsiveness.

### Details

- Propagation path under test: `_read_input` → `loop.run_in_executor(None, lambda: input("> "))` → executor blocks on user input → shutdown event fires → `input_coro.cancel()` called → `await input_coro` raises `CancelledError` → caught and swallowed.
- The assertion that `input_coro.cancelled()` confirms AC-1's "cancelled, not merely abandoned"; clean return of `None` confirms AC-2's "read returns None".
- The existing `test_shutdown_requested_breaks_loop` does NOT assert `input_coro.cancelled()` — it only checks that `handle_turn` was called once and shutdown breaks the loop. This new test fills that gap.

## Compatibility considerations

- The new test must coexist with the existing `test_shutdown_requested_breaks_loop` without altering its assertions.
- Test must pass once the sibling procedure's fix lands; it should fail against the pre-fix code (negative control), proving it exercises the cancellation branch.

## Security considerations

- N/A: this change involves test-only additions; no secrets, credentials, or sensitive data are introduced.

## Rollback considerations

- Removing the added test reverts coverage; the change is additive and confined to the test file, so reverting the commit restores the prior test suite.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl.py` | Format + lint | `uv run ruff format tests/agent/test_repl.py` then `uv run ruff check tests/agent/test_repl.py` | Clean (no diffs, no errors) |
| `tests/agent/test_repl*.py` | Regression: shutdown-during-input cancels `input_coro`; success-path reads unaffected | `uv run pytest tests/agent/test_repl*.py -v` | All pass; new regression test present |
| Whole affected lifecycle suite | Full regression | `uv run pytest` on affected lifecycle suites | Pass; diff-cover >= 90% on changed lines |

## Completion criteria

- The new regression test passes and fails against the pre-fix loop (proving it exercises the cancellation branch) (AC-3).
- The existing REPL tests still pass (AC-3).
- ruff format/check are clean on the modified test file.

## Out of scope

- Any change to `scripts/agent/repl_input_loop.py` (handled by the sibling procedure for that target file).
- Startup `session.start()` exception translation, shutdown-race paths, or per-turn exception containment (tracked separately as `repl001`).
- Modifying the existing `test_shutdown_requested_breaks_loop` test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add regression test for shutdown-during-input cancellation to `test_repl.py` | Completed | 20261001-182959 | 20261001-212028 | REQ-003 |
| 2 | Run validation sequence (`rules/toolchain.md`): ruff/mypy/bandit/pytest/diff-cover | Completed | — | 20261001-212028 | REQ-003 |

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
- **Requirement ID**: `REQ-003` — verify `input_coro` is cancelled on shutdown-during-input
- **Source issue**: issues/20260930-231626_repl002_replinputloop-does-not-cancel-pending-input-coroutine-on-shutdown-during-input-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-092325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-182746
- **Related target files**: tests/agent/test_repl.py