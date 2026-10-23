## Goal

Route `scripts/agent/repl_input_loop.py`'s two blocking stdin reads through the instance-owned `StdinReader` (new) so neither uses `loop.run_in_executor(None, …)`, eliminating the pool-worker-holds-exit defect for the primary prompt path (`plans/20261022-040200_plan.md`, REQ-005, REQ-006, REQ-011; AC-2, AC-5, AC-8).

## Scope

Modify only `scripts/agent/repl_input_loop.py`: replace the two `loop.run_in_executor(None, lambda: input("> "))` calls with the instance reader, and add the reader instance to `ReplInputLoop.__init__`. Every other statement in `_read_input` and `_repl_loop` stays as written.

## Assumptions

- `ReplInputLoop` owns one `StdinReader` (new) instance for its lifetime; it is used only from the event loop that runs `_repl_loop`.
- The `"> "` prompt and the `lambda: input("> ")` semantics are preserved exactly.

## Design decisions

- The reader is created in `__init__` and stored as `self._stdin_reader`, matching REQ-005 (each owner holds its own instance). The two call sites become `await self._stdin_reader.read()` instead of `await loop.run_in_executor(None, lambda: input("> "))`.
- No other statement in `_read_input` changes: `_input_task`, `_InputAborted`, `_shutdown_watcher`, `input_coro.cancel()`, `_abort_input()`, `_input_coro` tracking, the `None`-fallback branch, the `(self, loop)` signature, `_repl_loop`'s race structure, and `_GRACEFUL_TIMEOUT_S` (`:55`) all stay byte-identical.

## Alternatives considered

N/A: the Plan's design fixes the mechanism (daemon reader thread); this row only performs the mechanical substitution at the two call sites.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. In `ReplInputLoop.__init__`, create `self._stdin_reader = StdinReader(prompt="> ")` alongside the existing attributes.
2. Replace the shutdown-event branch read at `:144` (`return await loop.run_in_executor(None, lambda: input("> "))`) with `return await self._stdin_reader.read()`.
3. Replace the fallback-branch read at `:191` (`raw = await loop.run_in_executor(None, lambda: input("> "))`) with `raw = await self._stdin_reader.read()`.
4. Import `StdinReader` (new) from `scripts/agent/stdin_reader.py`.

### Method

- The replacement is a one-line substitution at each site; the surrounding `try/except (KeyboardInterrupt, SystemExit)` at `:145-146` (which maps to `_InputAborted`) and the `try/except (EOFError, KeyboardInterrupt)` at `:192-194` are untouched, so EOF/Ctrl-C behavior is preserved (`AC-5`).
- The worker's exceptions arrive as stored future exceptions (REQ-004), so `_input_task`'s existing catch of `KeyboardInterrupt`/`SystemExit` at `:145` still applies.

### Details

- Verify with `grep -n "run_in_executor\|to_thread" scripts/agent/repl_input_loop.py` returning nothing (`AC-2`).
- Do not touch `_should_exit`, `_dispatch_line`, `_abort_input`, or `_GRACEFUL_TIMEOUT_S`.

## Compatibility considerations

`_read_input`'s `(self, loop)` signature and return contract (`str | None`) are unchanged. This file is a shared Frozen target with `plans/20261022-030840_plan.md` (repl001); regions are disjoint — repl001 owns `_repl_loop`'s mid-turn race (`:271-284`) and the shutdown-event handoff, this row owns the two read calls (`:144`, `:191`). Implement repl001 first so the `:144` branch is live before this row rewires it.

## Security considerations

N/A: no new trust boundary or data path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Integration: real `_read_input` driven through `builtins.input` stubs, loop `run_in_executor` spy, `threading.enumerate()` assertion; existing race cases unchanged. | `uv run pytest tests/agent/test_repl.py -q` ; `grep -n "run_in_executor\|to_thread" scripts/agent/repl_input_loop.py` | Existing `:640-706` and `test_no_shutdown_event_fallback` pass unchanged; new cases pass; grep returns nothing (AC-2, AC-5). |

## Completion criteria

- Neither `:144` nor `:191` calls `run_in_executor`; both await the instance reader.
- `TestPromptReadDoesNotUseAnExecutor` (new) passes (loop spy never called; no non-daemon thread).
- `TestReadInputShutdownRace` and `test_no_shutdown_event_fallback` pass unchanged.

## Out of Scope

The multiline continuation read (`cli_view.py`, row 3) and the approval prompt (`tool_approval.py`, row 4). Any change to `_repl_loop`, signal handling, or the shutdown path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewire `scripts/agent/repl_input_loop.py`'s two prompt reads | Completed | 20261023-135516 | 20261023-135516 | REQ-005, REQ-006, REQ-011; AC-2, AC-5, AC-8 implemented; full suite 9831 passed; procedures corrected (reader state machine, call-time input lookup, new-markers, nonexistent doc checkers); rows 11-13 added for three further approval test files; generated reference table regenerated |
| 2 | Add or update tests per Validation plan | Completed | 20261023-135516 | 20261023-135516 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-135516 | 20261023-135516 |  |

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
- **Requirement ID**: REQ-005, REQ-006, REQ-011
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `scripts/agent/repl_input_loop.py`