## Goal

Separate SIGINT from SIGTERM, make Ctrl-C act by controller state, fix the Windows ctypes fallback, and define an off-by-default double-Ctrl-C force exit (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/signal_handler.py` and `tests/agent/test_signal_handler.py`. Job cancellation wiring belongs to the maintenance-job Plan; only the seam is used here.

## Assumptions

- Verified: the ctypes handler uses `win32con.CTRL_CLOSE_EVENT` (`scripts/agent/signal_handler.py:101`) although `win32con` is imported only in the branch whose `import win32api` just failed, so the callback raises `NameError`.
- Needs confirmation (non-blocking, UNK-01): the force-exit window and method; this procedure makes it off by default and injectable.
- Windows behavior is tested only through the control-event function (UNK-03).

## Design decisions

- Constructor gains keyword-only `controller`, `force_exit_on_second_sigint`(new) (default False), and `force_exit`(new) (callable, default exits the process with status 130); `register` binds SIGTERM to the shutdown handler and SIGINT to a new interrupt handler.
- The interrupt handler calls `ReplInputController.handle_interrupt`; for the shutdown-in-progress action it calls `force_exit`(new) only when the flag is set.
- A pure method `_dispatch_control_event`(new) maps Windows event numbers (Ctrl-C 0, Ctrl-Break 1, close 2, logoff 5, shutdown 6) to the interrupt or shutdown handler; both the pywin32 and ctypes callbacks call it, and no code references `win32con` outside the pywin32 branch.

## Alternatives considered

Rejected: reusing one handler for both signals (the Issue's defect); rejected: reading policy from config now (no owner decision yet, UNK-01).

## Implementation
### Target file
`scripts/agent/signal_handler.py`

### Procedure
1. Split the single handler into a shutdown handler (current behavior) and an interrupt handler; register them per signal in `register`.
2. Add `_dispatch_control_event`(new) and route both Windows callbacks through it using numeric constants.
3. Add the constructor arguments with defaults so `SignalHandler(ctx, shutdown_event)` keeps working; resolve the controller lazily from `get_input_controller` when none is given.
4. Update the module and class docstrings (they say SIGTERM/SIGINT share shutdown).

### Method
Keep `register`'s NotImplementedError fallback structure but remove the nested duplication by calling `_dispatch_control_event`(new); do not add new registration paths.

### Details
- Log each interrupt action at info level without any input text.
- The shutdown handler still sets `ctx.conv.shutdown_requested` and the shutdown event.

### Companion test files
- `tests/agent/test_signal_handler.py`
  - Procedure: Add tests: SIGINT per state (prompt, turn, job, shutdown), SIGTERM graceful shutdown, `_dispatch_control_event`(new) for each event number, the ctypes path no longer raising `NameError`, force exit off by default and on when enabled; keep the existing registration tests.
  - Validation: `uv run pytest tests/agent/test_signal_handler.py -q`

## Compatibility considerations

`SignalHandler(ctx, shutdown_event)` still constructs; SIGINT no longer triggers shutdown on its own (documented).

## Security considerations

Force exit skips graceful cleanup, so it is opt-in only; no input text is logged.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_signal_handler.py tests/agent/test_repl.py -q`
- `uv run ruff check scripts/agent/signal_handler.py && uv run mypy scripts/agent/signal_handler.py`

## Completion criteria

- Ctrl-C behaves by state as the Plan specifies; SIGTERM and close events start graceful shutdown; the ctypes callback has no unbound name; force exit is tested both ways.

## Out of Scope

Real Windows console behavior, job cancellation implementation, shutdown deadline machine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test files included) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` (state-dependent Ctrl-C, SIGTERM/console close, Windows ctypes fix, force exit)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/signal_handler.py`, `tests/agent/test_signal_handler.py`
