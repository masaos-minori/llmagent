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
- Verified against source 2026-11-25 (execution): the first two assumptions hold, and the third is deferred by the batch decision. `repl.py:85` still passes no budget, and row 7 lands in R4, so the budget argument is keyword-only and optional here and `_GRACEFUL_TIMEOUT_S` stays as the no-budget fallback; row 7 removes it when the loop is always given a budget. `tests/agent/test_repl.py:925` monkeypatches the constant and keeps passing until then.
- Verified against source 2026-11-25 (execution): the pending-approval release point is `ReplInputController.shutdown()` (`scripts/agent/repl_input_controller.py:246-249`), which `SignalHandler._sigterm_handler` already calls (`scripts/agent/signal_handler.py:102`). The loop calls the same method when it observes the phase left accepting; the coordinator's `enter_shutdown` (row 5) is the production caller the Plan names.

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
1. Take the budget as a keyword-only optional argument in `__init__` alongside the shutdown event (`scripts/agent/repl_input_loop.py:65-84`); `None` keeps the behavior the loop has today.
2. Add `_accepts_work()` and apply it at the two points where work is accepted: the top of each `_repl_loop` iteration and the head of `_dispatch_line` (`scripts/agent/repl_input_loop.py:229-246`), so a line read before shutdown began is refused before it reaches a command or the orchestrator.
3. `_graceful_window()` is the budget's remaining deadline when a budget is present and `_GRACEFUL_TIMEOUT_S` otherwise; the timeout message (`scripts/agent/repl_input_loop.py:130-134`) reports the window that was actually used, because `remaining()` read back after the window expired clamps to `0.0`. Row 7 removes the fallback constant once `repl.py` supplies the budget.
4. When the loop observes the phase left accepting it reports the refusal once and calls `ReplInputController.shutdown()`, which resolves a pending approval or transition wait with `InputOutcome.SHUTDOWN`.
5. Route an interrupt that arrives after shutdown began: the turn-cancel callback registered by `_begin_turn_state` records `budget.request_interrupt()` when the phase is not accepting, and `_flow_after_interrupt` ends the loop instead of prompting again. `SignalHandler` (row 10) is the side that calls `request_interrupt()` on the second SIGINT.

### Method
- The check is a read of the shared phase at the two points where work is accepted, so refusal cannot be bypassed by a path that does not go through the prompt.
- Refusal is reported once per shutdown, not per keystroke: the loop states that shutdown is in progress and stops offering prompts.

### Details
- The refusal message names the phase and the work that is refused, with no internal state dump (REQ-013). The budget carries no current-step name, so the step in progress is stated by the shutdown report (rows 5 and 43), not by the loop.

### Companion test files
- `tests/agent/test_repl_shutdown_machine.py` (new)
  - Procedure: a command and a turn submitted after the phase stops accepting are refused with a visible reason, `CommandRegistry.dispatch` and `Orchestrator.handle_turn` are not reached, the dispatch gate refuses a line that was already read, the refusal is reported once, a pending wait is released with `InputOutcome.SHUTDOWN`, the window is the budget's remaining deadline (and the legacy constant when no budget is supplied), an uncooperative turn is bounded by the budget, a turn that times out while shutdown was requested ends the loop with the window it was given, an interrupt after shutdown began ends the loop and reaches `budget.interrupt_requested`, with and without a shutdown event, while an interrupt before shutdown still cancels only the turn. 14 cases.
  - Validation: `uv run pytest tests/agent/test_repl_shutdown_machine.py -q` (REQ-003; AC-2).
- `tests/agent/test_repl_error_handling.py`
  - Procedure: no change in this row. The budget argument is keyword-only and optional, so the constructions at `:97` and `:136` are untouched; the `finally`-block expectations belong to row 7 in R4 (companion row 32).
  - Validation: `uv run pytest tests/agent/test_repl_error_handling.py -q` (REQ-001, REQ-003).

## Compatibility considerations

- Tests that construct `ReplInputLoop` need no change in this row: the budget argument is optional (`tests/agent/test_repl.py:97`, `:709`, `tests/agent/test_repl_error_handling.py:97`, `:136`). Companion row 32 and row 7 add the budget where the REPL owns one.
- Ctrl-C semantics change for a press after shutdown began: it interrupts the running step and ends the input loop rather than cancelling only the current turn (documented in row 47). While the budget accepts work the behavior is unchanged.

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
- The graceful window equals the remaining budget, and no independent timeout constant remains in the loop. Verified 2026-11-25: the second half completes in row 7, which is the row that supplies the budget; until then `_GRACEFUL_TIMEOUT_S` is the documented no-budget fallback.

## Out of Scope

- Arming the budget, the step order, and the signal-handler force-exit configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-091128 | 20261125-091128 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261125-091128 | 20261125-091128 | companion rows 22, 32 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-092708 | 20261125-092708 |  |

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