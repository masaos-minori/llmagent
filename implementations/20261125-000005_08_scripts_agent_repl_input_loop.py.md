## Goal

Make the input loop stop accepting work once shutdown begins: refuse new commands and turns when the phase is not accepting, take the graceful window from the budget instead of its own constant, and release a pending approval with `InputOutcome.SHUTDOWN` (REQ-002: one global deadline; REQ-003: input acceptance stops at shutdown; REQ-011: a second SIGINT interrupts the running step; AC-2).

## Scope
**Release unit**: R3-acceptance-gate (Phase 3)

- In scope: the acceptance check, the graceful window, the pending-approval release, and routing the second SIGINT to the running step.
- Out of scope: arming the budget (row 10), the step machine (row 5), and the budget object itself (row 1).

## Assumptions

- The loop has no shutdown-phase check today: `_GRACEFUL_TIMEOUT_S: float = 10.0` (`scripts/agent/repl_input_loop.py:63`) is an independent constant, and the read path (`scripts/agent/repl_input_loop.py:258-313`) keeps offering prompts while a shutdown is in progress.
- The loop already treats `InputOutcome.EOF` and `InputOutcome.SHUTDOWN` as terminal (`scripts/agent/repl_input_loop.py:153`), so the shutdown outcome exists and only its production needs to change.
- The loop is constructed with the shutdown event at `scripts/agent/repl.py:85`; the budget is passed the same way (row 7).

## Design decisions

- Acceptance is decided by the budget's phase, not by a local flag: the loop reads the same phase the coordinator drives, so no consumer can accept input while another is draining (REQ-003).
- The graceful window is `remaining()` (row 1) rather than a constant, and `_GRACEFUL_TIMEOUT_S` is removed so there is one number to reason about (REQ-002).
- A pending approval is released with `InputOutcome.SHUTDOWN` rather than left waiting: an approval that can never be answered must not hold the sequence, and the existing terminal-outcome handling already understands the value.
- A second SIGINT interrupts the running step instead of starting a second shutdown, which is what makes the interrupt path in row 10 meaningful.
- Compatibility impact: commands and turns typed after shutdown begins are refused, which is a visible behavior change documented in row 47.

## Alternatives considered

- keep a local `_shutting_down` flag — rejected: two sources of truth is the failure mode the Plan's Problem section describes.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
1. Take the budget in `__init__` alongside the shutdown event (`scripts/agent/repl_input_loop.py:66-74`).
2. Add the phase check to the loop precondition (`scripts/agent/repl_input_loop.py:117-124`) and to the dispatch path (`scripts/agent/repl_input_loop.py:229-246`) so a refused line never reaches a command or the orchestrator.
3. Replace `_GRACEFUL_TIMEOUT_S` (`scripts/agent/repl_input_loop.py:63`) with the budget's remaining deadline, and update the timeout message (`scripts/agent/repl_input_loop.py:130-134`) to report the budget value.
4. Release a pending approval with `InputOutcome.SHUTDOWN` when the phase leaves accepting (`scripts/agent/repl_input_loop.py:158-164`, `scripts/agent/repl_input_loop.py:211`).
5. Route the second SIGINT to the running step through the budget's interrupt request (row 10) instead of cancelling only the current turn (`scripts/agent/repl_input_loop.py:258-313`).

### Method
- The check is a read of the shared phase at the two points where work is accepted, so refusal cannot be bypassed by a path that does not go through the prompt.
- Refusal is reported once per shutdown, not per keystroke: the loop states that shutdown is in progress and stops offering prompts.

### Details
- The refusal message names the phase and the step in progress, with no internal state dump (REQ-013).

### Companion test files
- `tests/agent/test_repl_shutdown_machine.py` (new)
  - Procedure: a command and a turn submitted after the phase stops accepting are refused with a visible reason, `CommandRouter.execute_command` and `AgentOrchestrator.handle_turn` are not reached, and a pending approval resolves `InputOutcome.SHUTDOWN`.
  - Validation: `uv run pytest tests/agent/test_repl_shutdown_machine.py -q` (REQ-003; AC-2).
- `tests/agent/test_repl_error_handling.py`
  - Procedure: update the `finally`-block expectations to the bounded sequence and to the refusal line shown after shutdown begins.
  - Validation: `uv run pytest tests/agent/test_repl_error_handling.py -q` (REQ-001, REQ-003).

## Compatibility considerations

- Tests that construct `ReplInputLoop` gain the budget argument (`tests/agent/test_repl_error_handling.py:11`, `:97`, `:136`), which is companion row 32.
- Ctrl-C semantics change for the second press: it interrupts the running step rather than only the current turn (documented in row 47).

## Security considerations

- N/A: no new data is exposed; the refusal text is fixed wording.

## Rollback considerations

- Revert this row's commit with rows 22 and 32: the new acceptance tests and the constructor expectations belong to the same release unit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Unit | `uv run pytest tests/agent/test_repl_shutdown_machine.py tests/agent/test_repl.py -q` | post-shutdown commands and turns are refused; a pending approval resolves with `InputOutcome.SHUTDOWN` |
| `scripts/agent/repl_input_loop.py` | Unit | `uv run pytest tests/agent/test_repl_error_handling.py -q` | the constructed loop and the bounded `finally` behave as wired by row 7 |

## Completion criteria

- No command or turn is dispatched after the phase leaves accepting, and a pending approval resolves with `InputOutcome.SHUTDOWN`.
- The graceful window equals the remaining budget, and no independent timeout constant remains in the loop.

## Out of Scope

- Arming the budget, the step order, and the signal-handler force-exit configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion rows 22, 32 |
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
- **Requirement ID**: REQ-002 (one global deadline), REQ-003 (input acceptance stops at shutdown), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/repl_input_loop.py`, `tests/agent/test_repl_shutdown_machine.py`, `tests/agent/test_repl_error_handling.py`, `tests/agent/test_repl_shutdown_machine.py` (new)
