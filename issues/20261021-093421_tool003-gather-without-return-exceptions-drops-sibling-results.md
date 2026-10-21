# A single raising tool call discards every sibling tool result in the same batch

## Priority
High

## Summary
Make tool batch execution collect per-call failures as tool results instead of letting one exception
abort the whole batch, so already-executed side effects are always recorded.

## Background
Tool calls are prepared (fail-closed) in `agent.tool_preparation.prepare_tool_calls`, then executed in
groups. `agent/tool_runner.py:63-75` runs each group either sequentially or with
`asyncio.gather(*(execute_one_tool_call(ctx, pc) for pc in group))`, and the batch level repeats the
pattern at `:291-297` with `asyncio.gather(*(_run_group_calls(...)))`. Neither `gather` passes
`return_exceptions=True`. Results are only turned into messages and persisted after the whole batch has
succeeded: `results.sort(key=lambda r: call_order.get(r[0], 0))` (`:385`),
`_collect_tool_result_msgs(...)` (`:387`), `ctx.session.save_many(tool_msgs)` (`:391`).

## Problem
`execute_one_tool_call` raises `ToolExecutorUnavailableError` (`tool_runner.py:158-162`) and can propagate
transport, MCP, truncation, or DB errors. With no `return_exceptions=True`:
- In a concurrent group, the first raising call cancels its sibling coroutines and the outer gather
  aborts, so results of other groups are lost too.
- In a sequential group, calls after the failing one never run.
- Either way the code after `:385` never executes, so no `tool` message is written for any call in the
  batch — including calls that already completed and produced real side effects (file writes, shell
  commands, MCP mutations). Their effects remain applied while the conversation records nothing.
This is the same corruption `tool002` describes, but caused by sibling failure rather than by an
exception escaping the round.

## Reason for Change
Partial results are the normal case for concurrent tool batches. Silently dropping them makes the model
re-issue calls whose side effects already happened, and makes the session history disagree with the
filesystem.

## Implementation Intent
Keep concurrency, make the batch total: every prepared call yields a result tuple (value or error), and
only then format and persist.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`_run_group_calls`, `_execute_with_dag`, `execute_all_tool_calls`)
- `scripts/agent/tool_preparation.py` (fail-closed preparation shape to reuse)

## Required Changes
- Pass `return_exceptions=True` to both `gather` sites and convert any returned exception into the same
  error-result tuple the preparation phase already produces for a rejected call.
- In sequential groups, decide and state whether a failure stops later calls or each call is independent;
  do not let it abort the batch implicitly.
- Keep results ordered by original `tool_calls` order after the change.
- Never leave a completed call unrecorded because a sibling failed.

## Constraints
- `_PrepFailure` already carries `(tc_id, name, args, output, is_error, output)`
  (`tool_preparation.py:66-72`); reuse that shape rather than inventing a second error tuple.
- `ctx.cfg.tool.serial_tool_calls` and the DAG/concurrency grouping must keep working.
- Do not retry failed tools in this issue.
- Tool side effects cannot be rolled back; only the recording is in scope.

## Acceptance Criteria
- A batch of three calls where the second raises still produces three `tool` messages in the original
  order, one of them marked as an error.
- No already-executed call is missing from `ctx.conv.history` or from `ctx.session.save_many` input.
- The behavior is identical for the sequential and concurrent grouping.

## Testing Expectations
- Regression test per grouping: a stubbed tool set where one call raises, asserting a result exists per
  call id and that ordering is preserved.
- Characterization test for the current behavior before the change.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document per-call failure semantics for a tool batch in the tool-execution docs: what the model sees for
a failed call, what happens to siblings, and that side effects are not undone.

## Out of Scope
- The assistant-message/tool-result atomicity of the round (`tool002`).
- Missing `tool_calls` id handling (`tool004`).
- Retries and idempotency-key behavior.

## Dependencies
- Implement with `tool002` and `tool004`: all three change `execute_all_tool_calls` failure handling.
- `tool001` touches the same result-collection function; sequence after this one.

## Unresolved Questions
- Should a raising call cancel sibling calls in the same group (fail-fast) or let them finish? Needs a
  decision; the current behavior is neither by design.
- Should a batch-level failure stop the turn or only mark that round as errored? Needs confirmation.

## AI Implementation Instruction
Make the batch total, not best-effort: every prepared call yields exactly one result tuple. Reuse the
existing preparation-failure representation, and do not change concurrency grouping.

## Traceability
- **Workflow phase**: `python-code-review` (tool execution review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/tool_runner.py`, `scripts/agent/tool_preparation.py`
