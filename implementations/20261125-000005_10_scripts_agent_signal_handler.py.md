## Goal

Make the first shutdown request start the bounded sequence and the second one interrupt the step in progress: arm the budget on the first signal, route the second SIGINT to the running step, and make the forced exit a configured opt-in (REQ-002: one global deadline; REQ-011: second-signal behavior; AC-4).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the SIGINT and SIGTERM handlers, the budget arming call, and the source of the force-exit decision.
- Out of scope: the budget object (row 1), the input-loop interrupt routing (row 8), and the configuration fields (rows 17-19).

## Assumptions

- `_sigint_handler()` (`scripts/agent/signal_handler.py:105-114`) never starts shutdown today: it delegates to the input controller and only forces an exit when `force_exit_on_second_sigint` is already true, so a Ctrl-C during normal operation cancels a turn but does not begin the sequence.
- `force_exit_on_second_sigint` is a constructor parameter today (`scripts/agent/signal_handler.py:74`), not a configured value; the Plan makes it come from `shutdown_force_exit_on_second_sigint` (new) (rows 17, 19).
- `_exit_process` (`scripts/agent/signal_handler.py:53-55`) calls `os._exit`, which skips every cleanup step, so it must stay an explicit opt-in.

## Design decisions

- Arming happens outside the SIGINT handler: the deadline starts when shutdown is actually requested (SIGTERM, or the REPL exit paths in rows 7 and 8), before any step runs, and `arm()` (row 1) returns `False` for later requests so repeated signals cannot extend the deadline.
- SIGINT keeps not starting shutdown (REQ-011): an accidental Ctrl-C must still not end a session, so the handler only interrupts a step when a shutdown is already in progress.
- The second SIGINT requests an interrupt on the budget (`request_interrupt()` (new)) so the step in progress stops at its next boundary, instead of the handler killing the process.
- `os._exit` is kept only for the configured force-exit path, and the configured value is read once at construction rather than per signal, so a signal handler does no configuration work.
- Compatibility impact: Ctrl-C during normal operation still cancels the current turn; Ctrl-C while a shutdown is in progress now interrupts the running step, and the forced exit only happens when configured.

## Alternatives considered

- keep SIGINT purely as a turn cancel and start shutdown only from `/exit` — rejected: the Plan's Problem section names "SIGINT never starts shutdown" as a defect, and row 47 documents the new behavior.

## Implementation
### Target file
`scripts/agent/signal_handler.py`

### Procedure
1. Take the budget in `__init__` alongside the shutdown event.
2. In `_sigterm_handler()` (`scripts/agent/signal_handler.py:91-103`), arm the budget before setting the shutdown event, so the deadline starts before the sequence does.
3. In `_sigint_handler()` (`scripts/agent/signal_handler.py:105-114`), keep the existing controller delegation when no shutdown is in progress, and call `request_interrupt()` (new) when the budget is already armed. SIGINT never arms the budget.
4. Keep the force-exit branch (`scripts/agent/signal_handler.py:110-113`) but drive it from the configured value (row 17) rather than only the constructor argument, and keep `_FORCE_EXIT_STATUS` (`scripts/agent/signal_handler.py:47`) unchanged.
5. Leave the Windows control-event dispatch (`scripts/agent/signal_handler.py:116` onward) arming the same budget, so every shutdown request shares one deadline.

### Method
- The handler does three things only: arm, request an interrupt, or (when configured) force an exit. It never runs a step and never touches the write gate.

### Details
- The log lines stay at the same levels so existing log expectations keep holding; the new interrupt path logs the step it interrupted by name (REQ-012).

### Companion test files
- `tests/agent/test_signal_handler.py`
  - Procedure: arm the budget on the first signal, route a second signal to the budget's interrupt channel, and keep `os._exit` reachable only when `shutdown_force_exit_on_second_sigint` (new) is true.
  - Validation: `uv run pytest tests/agent/test_signal_handler.py -q` (REQ-002, REQ-011; AC-4).

## Compatibility considerations

- Callers that construct `SignalHandler` with `force_exit_on_second_sigint=True` keep working; the configured value becomes the default path (`tests/agent/test_signal_handler.py`, companion row 31).
- `_exit_process` remains injectable, which is what the existing tests use to avoid a real `os._exit`.

## Security considerations

- N/A: no new output; the interrupt log names a step, not a path.

## Rollback considerations

- Revert this row's commit with row 31: the arming and interrupt expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/signal_handler.py` | Unit | `uv run pytest tests/agent/test_signal_handler.py -q` | first request arms, second request interrupts, force exit only when configured |
| `scripts/agent/signal_handler.py` | Unit | `uv run pytest tests/agent/test_repl_shutdown_machine.py -q` | the interrupt reaches the step in progress |

## Completion criteria

- The first SIGTERM or REPL exit request arms one deadline that later requests cannot move.
- A second SIGINT interrupts the running step, and `os._exit` runs only when the configured opt-in is true.

## Out of Scope

- Budget internals, the step machine, and the configuration plumbing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row 31 |
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
- **Requirement ID**: REQ-002 (one global deadline), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/signal_handler.py`, `tests/agent/test_signal_handler.py`
