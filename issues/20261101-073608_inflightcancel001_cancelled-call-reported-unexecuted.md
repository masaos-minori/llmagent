# A tool call interrupted in flight is recorded as "not executed"

## Priority
High

## Summary
When a tool round is cancelled (for example by a shutdown request during a turn), every declared call without a collected result is answered with the fixed text "Tool call not executed: the tool round did not complete." A call whose request had already been sent to the MCP server, but whose reply had not arrived, is in that group. The server may still complete it, so the stored history states that a possibly executed write did not happen. The next turn, or a later `/session load`, can then repeat it. Distinguish "never dispatched" from "dispatched, outcome unknown".

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- `execute_all_tool_calls` catches `BaseException` from the round, calls `complete_round` with `ToolCallStopReason.ROUND_NOT_COMPLETED`, and re-raises. `complete_round` writes real results from `RoundState.collected`, denials, and one synthesized row per declared id that has no answer (`pair_round_results`).
- `_recorded_call` writes into `collected` only after `execute_one_tool_call` returns, so a call that is awaiting the HTTP reply is not in `collected`.
- A shutdown request cancels the dispatch task in `ReplInputLoop._repl_loop` (the shutdown branch calls `dispatch_task.cancel()` and waits for the graceful timeout), so the cancellation happens in normal operation, not only in tests.
- `HttpTransport.call` already treats the equivalent ambiguity for transport failures of write tools as unknown ("server-side execution outcome is ambiguous", fail-closed, ADR-004), and the MCP server keeps handling a request after the client disconnects. The round-completion path does not carry that distinction.
- `issues/done/20261026-224729_turn002_repair-orphan-tool-call-rows.md` covers unpaired tool rows when a hard-killed session is loaded; it is background for the pairing logic and does not cover this cancellation text.

## Problem
Reproduction (throwaway script, not committed): a stub gateway that records the call and then waits, `_execute_with_dag` run as a task, the task cancelled after the gateway received the call, and `pair_round_results` with the resulting `collected` and `ROUND_NOT_COMPLETED`. Observed: the gateway had received the call (the request is "sent"), `collected` was empty, and the synthesized row text was "Tool call not executed: the tool round did not complete." No real server or database was used.

Effects:
- For a write, delete, or API-write tool, the model and the user are told the operation did not run when it may have. A repeat uses a new idempotency key at the transport, so the server does not deduplicate it; the result can be a duplicate write.
- For a read tool, the statement is also inaccurate, though a repeat is harmless.
- The row is persisted, so the wrong statement survives a restart.

## Reason for Change
Interrupting the agent while a tool call is running is routine (Ctrl-C, termination). The recorded history is the only account of what happened, and for writes a false "not executed" is worse than "unknown".

## Implementation Intent
Track the dispatch state of each call in the round: not started, dispatched without a result, finished. When completing a round that stopped early, synthesize the "not executed" text only for calls that were never dispatched, and a distinct "dispatched, outcome unknown; verify before repeating" text for calls that were in flight. Whether an in-flight write should instead be allowed to finish within the graceful shutdown window is a related design choice for the owner; the minimum change is the accurate text.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`_recorded_call`, `execute_one_tool_call`, `execute_all_tool_calls`)
- `scripts/agent/tool_round_completion.py` (`RoundState`, `complete_round`)
- `scripts/agent/tool_result_pairing.py` (`pair_round_results`, the stop texts)
- `scripts/agent/tool_enums.py` (`ToolCallStopReason`)
- `scripts/agent/repl_input_loop.py` (read-only reference for the cancellation path)
- `tests/agent/` tests for round completion and pairing

## Required Changes
- Record, per call id, that the call was dispatched (before the transport is awaited) and clear or keep that marker when a result is collected.
- In round completion, answer an in-flight call with an outcome-unknown text and a never-dispatched call with the existing not-executed text; keep one row per declared id.
- Keep the guard-stop text for calls skipped by a loop guard.
- Add tests: cancel while a call is in flight yields the outcome-unknown row; cancel before dispatch yields the not-executed row; completed calls keep their real result.

## Constraints
- Preserve the guarantee that every declared id is answered exactly once.
- Do not change the real result path, the denial text, or the persistence boundary.
- The new text must not include tool arguments or output.
- No schema change.

## Acceptance Criteria
- After a cancellation with a call in flight, the persisted tool row for that call says that the outcome is unknown and that the call may have run.
- A call that was never dispatched is still recorded as not executed.
- Every declared id still has exactly one tool row.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests with a stub gateway that blocks, cancellation of the round task, and assertions on the history and persisted rows through the round completion path.
- Regression: run the tool runner, round completion, pairing and turn persistence tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Needs confirmation: check whether the agent documentation states the text or semantics of the synthesized rows. If it does, describe the two cases (never dispatched, dispatched with unknown outcome) and the reason.

## Out of Scope
- Changing the shutdown sequence or the graceful timeout.
- Retrying or reconciling an in-flight call after restart.
- Repair of unpaired rows at session load.

## Dependencies
N/A: none. No open issue or plan targets round completion or pairing. `issues/done/20261026-224729_turn002_repair-orphan-tool-call-rows.md` is archived background only.

## Unresolved Questions
- Whether the repair of unpaired rows at session load writes a similar "not executed" statement for rows left by a hard kill: `Needs confirmation`; if it does, the same distinction may be needed there.
- Whether in-flight write calls should be awaited to completion during graceful shutdown instead of cancelled: a design choice for the owner.

## AI Implementation Instruction
Write the failing cancellation test first. Change only dispatch tracking, the synthesized texts, and tests. Do not alter the shutdown logic, the persistence boundary, or tool execution itself. Stop and report if tracking dispatch requires changing the gateway or transport interfaces.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073608
- **Related target files**: scripts/agent/tool_runner.py, scripts/agent/tool_round_completion.py, scripts/agent/tool_result_pairing.py, scripts/agent/tool_enums.py, scripts/agent/repl_input_loop.py
