# An assistant `tool_calls` message is persisted before the tool results, and no results are written when tool execution fails

## Priority
High

## Summary
Make a tool round atomic: if tool execution fails, either write tool result messages for every
`tool_call` or remove the pending assistant message, so history never contains unanswered `tool_calls`.

## Background
`LLMTurnRunner.run` appends and persists the assistant message, then executes the tools with no
`except`: `await ctx.conv.append_message(message)` and `ctx.session.save("assistant", ..., tool_calls=...)`
(`scripts/agent/llm_turn_runner.py:108-113`) followed by `await execute_all_tool_calls(ctx, message["tool_calls"], ...)`
(`:116-120`). `LlmTurnExecutor.handle_llm_turn` wraps the turn in `try/finally` only, with no
`except` (`scripts/agent/llm_turn_executor.py:89-102`). Tool result history and persistence happen only at
the end of a successful batch (`scripts/agent/tool_runner.py:387`, `:391`).

## Problem
Any exception raised while executing or persisting the tools — `ToolExecutorUnavailableError`
(`tool_runner.py:160`), a re-raised `PolicyViolationError` (`:118`), or a DB failure inside
`ctx.session.save_many` — propagates out of the round. The assistant message with `tool_calls` is already
in `ctx.conv.history` and in the session DB, while zero `tool` messages exist for it. The next turn reuses
that history, so the provider receives a `tool_calls` block with no matching tool results — an invalid
request — and any side effects the tools already produced (file writes, shell commands) remain applied but
unrecorded.

## Reason for Change
This is history corruption that persists across turns and turns one tool failure into a broken session
that keeps failing.

## Implementation Intent
Handle the failure inside the round: synthesize a tool-result message for every `tool_call` id when the
round did not complete, and persist them with the same atomicity as the assistant message.

## Target Files or Areas
- `scripts/agent/llm_turn_runner.py` (round bracket)
- `scripts/agent/tool_runner.py` (`execute_all_tool_calls`, `_collect_tool_result_msgs`, `save_many`)
- `scripts/agent/llm_turn_executor.py` (exception propagation)

## Required Changes
- Wrap the tool-execution step so a failed round still produces one `tool` result per `tool_call` id
  (marked as an error), or explicitly removes the assistant message it just added.
- Do not leave the choice implicit: state which of the two is correct for which exception class.
- Keep history (`ctx.conv`) and the session DB (`ctx.session`) in the same state; a write to one without
  the other is the failure mode here.

## Constraints
- Tool side effects are not transactional and cannot be rolled back; the issue is only what history records.
- `_build_denied_messages` / approval-denied paths already synthesize tool messages
  (`tool_runner.py:393-395`); reuse that shape instead of inventing a second one.
- Do not change what the user sees for a normal, successful round.

## Acceptance Criteria
- After a forced failure in tool execution, every `tool_call` id in the assistant message has a
  corresponding `tool` message in both history and the session DB.
- A follow-up turn's request built from that history is well-formed (no unanswered `tool_calls`).
- Existing denied/approval-rejected behavior is unchanged.

## Testing Expectations
- Regression test: a stubbed tool execution raising each relevant exception class, asserting a tool result
  exists per `tool_call` id in history and in the DB.
- History-validity check comparing `tool_calls` ids against tool message `tool_call_id`s after a failed round.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the round as a unit (assistant message + tool results) and the guaranteed behavior when a round
fails, in the tool-execution and history docs. Note the durability consequence for existing sessions that
already contain unanswered `tool_calls`.

## Out of Scope
- Batch failure semantics for sibling calls (`tool003`).
- Retrying a failed tool round.
- Repairing already-persisted corrupted history.

## Dependencies
- Review together with `tool003` (same `tool_runner` failure handling) and `tool004`.

## Unresolved Questions
- Which is correct on failure: synthesize error results or discard the assistant message? Needs a decision
  before implementation.
- Should the assistant message and tool results be written in one DB transaction? Needs confirmation.

## AI Implementation Instruction
Fix the round, not the caller. Reuse the existing synthetic tool-message builder, and make history and DB
updates symmetric in the same failure path.

## Traceability
- **Workflow phase**: `python-code-review` (tool execution review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_runner.py`,
  `scripts/agent/llm_turn_executor.py`
