## Goal

Read every normal and multiline line through the controller, map the five outcomes, and report turn state so Ctrl-C can cancel only the turn (REQ-001, REQ-003, REQ-008).

## Scope
**Release unit**: input-controller-cutover

In scope: `scripts/agent/repl_input_loop.py` and `tests/agent/test_repl.py`. The signal side of Ctrl-C is the signal handler row.

## Assumptions

- Verified by radon: `_read_input` is CC 11 and `_repl_loop` is CC 31 (grade E); changes stay at call sites and new logic lives in the controller or small helpers.
- A cancelled turn is not a shutdown: `ctx.conv.shutdown_requested` stays false and the loop returns to the prompt.

## Design decisions

- Replace the `get_stdin_reader()` attribute with `get_input_controller()`; build a normal request with the `> ` prompt and map outcomes: completed gives the stripped line, eof and shutdown end the loop as today, cancelled prints a notice and returns an empty line so the loop continues.
- A trailing backslash calls `ReplInputController.collect_multiline` instead of `CLIView.read_multiline`; a discarded result continues the loop without dispatch.
- Around each turn call `ReplInputController.begin_turn` with the dispatch task's cancel method and `ReplInputController.end_turn` in the existing `finally`; a task cancelled by Ctrl-C (not by shutdown) prints a short warning and continues.

## Alternatives considered

Rejected: handling Ctrl-C inside the loop with `KeyboardInterrupt` (never delivered on POSIX because the signal is routed through the event loop).

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
1. Update the imports and the constructor attribute; keep the `bind` contract.
2. Rewrite `_read_input` to submit the normal request on both branches (with and without the shutdown event), keeping the shutdown-race logic that cancels the read.
3. Replace the multiline call with the controller helper, passing the view's `write_warning` as the notify callable and `sys.stdin.isatty()` as the interactive flag.
4. Register and clear the turn-cancel callback in `_repl_loop`, and handle `asyncio.CancelledError` from a Ctrl-C turn cancel without breaking the loop.

### Method
Edit `_read_input` and the turn section of `_repl_loop` only; extract two small private helpers (`_map_outcome`(new), `_turn_cancelled`(new)) rather than adding branches to `_repl_loop`.

### Details
- `_abort_input` keeps calling `write_turn_end` and clearing `_input_coro` for the eof/shutdown paths.
- Do not change `_GRACEFUL_TIMEOUT_S` handling or the shutdown wait in `_repl_loop`.

### Companion test files
- `tests/agent/test_repl.py`
  - Procedure: Update `TestSignalDuringPromptEndsLoop` (line 849) for the new SIGTERM and prompt-Ctrl-C meaning; add timeout-then-tool-approval and timeout-then-Memory-confirmation scenarios, a cancelled-turn test, and outcome mapping tests.
  - Validation: `uv run pytest tests/agent/test_repl.py -q`

## Compatibility considerations

Prompt text, `/exit`, EOF, and shutdown behavior are unchanged; Ctrl-C at the prompt no longer ends the REPL (documented in the docs rows).

## Security considerations

Partial multiline input is never submitted on timeout (AC-3).

## Rollback considerations

N/A: revert the commit (release unit `input-controller-cutover`).

## Validation plan

- `uv run pytest tests/agent/test_repl.py tests/test_cli_view.py -q`
- `uv run ruff check scripts/agent/repl_input_loop.py && uv run mypy scripts/agent/repl_input_loop.py && uv run radon cc scripts/agent/repl_input_loop.py -s` (complexity must not rise)

## Completion criteria

- All prompt reads go through the controller; no `read_multiline` caller remains.
- A cancelled turn returns to the prompt; shutdown behavior is unchanged; tests pass with no complexity increase for `_repl_loop`.

## Out of Scope

Signal registration, controller internals, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-212457 | 20261122-213733 | Changed: scripts/agent/repl_input_loop.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-212457 | 20261122-213733 | targeted tests pass (647 in the affected directories) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-212457 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-001` (loop is the normal-prompt caller), `REQ-003` (outcome mapping, multiline), `REQ-008` (turn-state reporting for Ctrl-C)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/repl_input_loop.py`, `tests/agent/test_repl.py`
