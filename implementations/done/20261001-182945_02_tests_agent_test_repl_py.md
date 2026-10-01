# Implementation Procedure: test_repl.py — regression test for shutdown-during-input cancellation

## Goal

Add a regression test asserting that a shutdown fired during an in-progress input read results in `input_coro` being cancelled. Implements `REQ-003` (short purpose: verify `input_coro` is cancelled when shutdown fires mid-read).

## Scope

- **In scope**: Add one regression test to `tests/agent/test_repl.py` (`TestReplLoop`) asserting that a shutdown fired during an in-progress input read cancels `input_coro` and that the read returns `None`.
- **Out of scope**: Modifying `scripts/agent/repl_input_loop.py` (covered by the sibling procedure for that target file); testing startup `session.start()` translation or shutdown-race paths beyond the specific shutdown-during-input scenario.

## Assumptions

- The existing `test_shutdown_requested_breaks_loop` test drives `_read_input` with mocked `input` and fires shutdown mid-read, but does not assert `input_coro.cancelled()` after a shutdown-during-read.
- With `shutdown_event=None`, `_read_input` uses the simple `input("> ")` path without the shutdown watcher race, so the test must set up a real `asyncio.Event` to exercise the shutdown-done branch.
- The test should use the same mocking style as the existing `test_shutdown_requested_breaks_loop` test (monkeypatching `builtins.input`, using `MagicMock` for collaborators).

## Design decisions

- **Exercise the real `_read_input` method**, not a unit stub: drive `ReplInputLoop._read_input` end-to-end with mocked collaborators rather than mocking `_read_input` itself, so the test fails if cancellation regresses.
- **Isolate the failure point**: set up a real `asyncio.Event` as `shutdown_event`, fire it while `input("> ")` is blocked, and assert `input_coro.cancelled()` is True.
- **Reuse the file's existing mocking style** (`MagicMock(spec=...)` for `AgentContext`/`CLIView`, explicit attribute wiring) so the new test matches its neighbors.

## Alternatives considered

- **Mocking `_read_input` directly**: simpler but does not exercise the actual cancellation behavior. Rejected in favor of driving `_read_input`.
- **Feeding input via a thread/queue against real `input()`**: more realistic but nondeterministic and slower. Rejected in favor of monkeypatching `builtins.input`.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Confirm the current test file has no test that asserts `input_coro.cancelled()` after a shutdown-during-read (repository evidence from the Plan).
2. Add an async test (mirroring the existing `@pytest.mark.asyncio` decoration) named to reflect intent, for example `test_shutdown_during_input_cancels_input_coro`.
3. Build a `MagicMock(spec=AgentContext)` wired with the attributes needed for `_read_input`: `conv.shutdown_requested=False`, `conv.is_processing`, `conv.memory_disabled`, `conv.memory_warning_shown`, and `stats.stat_partial_completions`.
4. Construct `ReplInputLoop(ctx, view, shutdown_event=asyncio.Event())` where `view = MagicMock(spec=CLIView)`.
5. Initialize the private components `_read_input` requires: set `loop._cmds` to a `MagicMock(spec=CommandRegistry)`.
6. Monkeypatch `builtins.input` to block indefinitely (or raise `EOFError` after a short delay), so the loop dispatches once and then blocks on input.
7. Fire the `shutdown_event` while the input read is in progress (e.g., via a separate thread or `asyncio.create_task`).
8. Assert, after running `await loop._read_input(loop)`:
   - `input_coro.cancelled()` is True (the pending task was cancelled);
   - the read returned `None` (not a string value).
9. Keep the new test isolated: do not modify the existing `test_shutdown_requested_breaks_loop` test.

### Method

- Use `unittest.mock` helpers already imported in the file (`MagicMock`, `AsyncMock`); add `monkeypatch` fixture usage via pytest's built-in `monkeypatch` for the `builtins.input` patch.
- Do not introduce real I/O, threads, or sleeps; keep the test fast and deterministic.
- Do not assert on internal bookkeeping beyond what proves cancellation and responsiveness.

### Details

- The test must set up a real `asyncio.Event` as `shutdown_event` to exercise the shutdown-done branch of `_read_input` (line ~156).
- Firing the event while `input("> ")` is blocked triggers the `if shutdown_done or shutdown_coro in done:` branch, which previously did not cancel `input_coro`.
- The assertion that `input_coro.cancelled()` confirms AC-1's "cancelled, not merely abandoned".
- Clean return of `None` confirms AC-2's "the read returns `None` and the loop proceeds to shutdown as before".

## Compatibility considerations

- The new test must coexist with the existing `test_shutdown_requested_breaks_loop` test without altering its assertions.
- Test must pass once the sibling procedure's fix lands; it should fail against the pre-fix code (negative control), proving it exercises the cancellation branch.

## Security considerations

- N/A: no security-sensitive paths introduced; the change is confined to asyncio task lifecycle management.

## Rollback considerations

- Removing the added test reverts coverage; the change is additive and confined to the test file, so reverting the commit restores the prior test suite.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl.py` | Format + lint | `uv run ruff format tests/agent/test_repl.py` then `uv run ruff check tests/agent/test_repl.py` | Clean (no diffs, no errors) |
| `tests/agent/test_repl*.py` | Regression: shutdown-during-input cancels `input_coro`; success-path reads unaffected | `uv run pytest tests/agent/test_repl*.py -v` | All pass; new regression test present |
| Whole affected lifecycle suite | Full regression | `uv run pytest` on affected lifecycle suites | Pass; diff-cover >= 90% on changed lines |

## Completion criteria

- After a shutdown fires during an in-progress input read, `input_coro.cancelled()` is True and the read returns `None` (AC-3).
- Success-path input reads (line returned, EOF, error, aborted) are unaffected; existing `tests/agent/test_repl*.py` tests still pass (AC-3).
- ruff format/check are clean on the modified test file.

## Out of scope

- Any change to `scripts/agent/repl_input_loop.py` (handled by the sibling procedure for that target file).
- Startup `session.start()` exception translation, shutdown-race paths, or per-turn exception containment (tracked separately as `repl001`).
- Modifying the existing `test_shutdown_requested_breaks_loop` test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read reference files; confirm shutdown-during-input cancellation gap | Completed | 20261001-183414 | 20261001-183610 | REQ-003 Duplicate: already implemented by 20261001-182746_02 |
| 2 | Add regression test asserting `input_coro.cancelled()` after shutdown-during-input | Pending | — | — | REQ-003 |
| 3 | Run validation sequence (`rules/toolchain.md`): ruff/mypy/bandit/pytest/diff-cover | Pending | — | — | REQ-003 |

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
- **Requirement ID**: `REQ-003` — verify `input_coro` is cancelled when shutdown fires mid-read
- **Source issue**: issues/20260930-231626_repl002_replinputloop-does-not-cancel-pending-input-coroutine-on-shutdown-during-input-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-092325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-182945
- **Related target files**: tests/agent/test_repl.py