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

### Verification (re-read at HEAD `8e7ca8b49`, 2026-10-22)

Confirmed at HEAD:
- The order is as described. `LLMTurnRunner.run()` appends the assistant message
  (`scripts/agent/llm_turn_runner.py:107`) and persists it with its `tool_calls` (`:108-112`), then calls
  `execute_all_tool_calls` (`:115-120`) with no `except` around it. Guard checks exist only *before*
  execution (`:98-104`) and *after* a completed round (`:125`, `:129`).
- `LlmTurnExecutor.handle_llm_turn` is `try:` / `finally:` with no `except`
  (`scripts/agent/llm_turn_executor.py:89-102`), exactly as stated; nothing between the round and the REPL
  per-turn handler (`scripts/agent/repl_input_loop.py:311`) turns a round failure into a repaired round.
- Tool results are written only after the whole batch returns: `_execute_with_dag` at
  `scripts/agent/tool_runner.py:375-377`, then `_collect_tool_result_msgs` at `:387` (which is where each
  `tool` message is appended to history, `:218-220`), then `ctx.session.save_many(tool_msgs)` at `:391`.
  Both the history append and the DB write sit after every execution.
- Therefore the orphan is total, not partial. An exception inside execution loses *all* of the round's tool
  messages: the results of calls that already ran and produced real side effects, and even the
  approval-denial messages built at `:388-390`. Only the assistant `tool_calls` block survives.
- Exceptions that can actually escape the round, each traced: `ToolExecutorUnavailableError`
  (`tool_runner.py:159-162`); a re-raised `PolicyViolationError` on the gateway-less path
  (`:114-118`, `repository_gateway.py` never re-raises it — `_gate_write` converts a violation to a
  `_denied_result`); `ValueError` from `ToolRouteResolver.resolve()` for an unregistered tool on the same
  gateway-less path (`:98-101`); `KeyError` from `tc["id"]` when a raw tool call has no `id`, before any
  execution starts (`:383`); the first exception raised by `asyncio.gather` (`:74`, `:291-296`);
  `sqlite3.Error` propagating out of `save_many` (`scripts/agent/session_message_repo.py:89` states the
  propagation explicitly, `save_many` is the same open/executemany/commit shape at `:91-`) and a
  `RuntimeError` under `strict_mode` (`:109-112`).
- The surviving orphan does reach the provider. `_stream_llm` passes `ctx.conv.history` unchanged to
  `llm.stream()` (`scripts/agent/llm_turn_runner.py:292-296`) and `_stream_llm_final_answer` does the same
  (`:232-240`); nothing rebuilds or pairs the request between history and the provider.
- The failure is recorded; only the history is left unrepaired. `execute_turn`'s `finally` writes the
  `turn_end` diagnostic (`scripts/agent/workflow_engine_adapter.py:189-198`), `_run_stage` records the
  failed attempt (`scripts/agent/workflow/workflow_engine.py:236-244`) and `run()` marks the task `failed`
  (`:129-131`). With `execute` configured `retryable: true, max_attempts: 3`
  (`config/workflows/default.json`) and per-attempt idempotency ids
  (`workflow_engine.py:208-221`), the same turn then runs again and appends a **second** assistant message
  on top of the orphan. Duplicates *across* attempts are `turn002`; this issue is pairing *within* one round.
- No test asserts the pairing. `tests/agent/test_llm_turn_runner.py` patches
  `agent.llm_turn_runner.execute_all_tool_calls` out of every tool-round test (`:397`, `:436`, `:485`,
  `:518`, `:583`) and asserts in-memory history only; `tests/agent/test_agent_repl_tool_exec.py` stubs
  `ctx.session.save_many = MagicMock()` (`:377`) and asserts DAG/serial ordering; `tests/agent/test_tool_runner.py`
  asserts that the exceptions are raised (`:1156`, `:1171`) but never what history or the `messages` table
  contain afterwards. No test anywhere queries `tool_calls` ids against `tool_call_id` rows.
- No detector reports the state either. `scripts/db/session_consistency.py:27-32` counts messages whose
  *session* is missing, not unanswered `tool_calls`, and `grep -n "tool_call"
  docs/00_governance/governance_03_issue-and-uncertainty-management.md` matches nothing.

Gaps between the issue text and HEAD:
- Line drift only in two places: the assistant persist is `llm_turn_runner.py:107-112` (issue: `:108-113`)
  and the call is `:115-120` (issue: `:116-120`). `llm_turn_executor.py:89-102`, `tool_runner.py:387` and
  `:391` are exact.
- `_build_denied_messages` is defined at `tool_runner.py:412-428` and used at `:388-390` (issue:
  `:393-395`). Its shape — `tuple[list[LLMMessage], list[tuple[str, str, None, str]]]` with the fixed text
  `"Tool execution denied by user."` — is the shape to reuse.
- `chatml_assembler.py` does not exist at HEAD: `find scripts -name "*chatml*"` matches nothing and the
  string `chatml` appears in no file under `scripts/`. The conclusion is still correct, but the mechanism is
  `llm.stream(url, ctx.conv.history, tool_defs)` (`llm_turn_runner.py:292-296`), not an assembler.
- "one or more tools have already executed ... remain applied but unrecorded" understates the state: at HEAD
  *no* result of the round is recorded, successful ones included, because collection happens after execution.
- `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md:78` says "The original unexecuted
  assistant message is not persisted." That is true only of the guard's *fallback* response
  (`llm_turn_runner.py:271-276` never appends it); read against the main loop it states the opposite of
  `:107-112`. No document at HEAD describes the persist-before-execute order or any pairing guarantee.
- "state which of the two is correct for which exception class" is not the right axis at HEAD. Every path
  that reaches `:115-120` and does not return normally leaves the same unpaired state, so the rule must be
  per round-completion, not per exception class.

Answers to the issue's Unresolved Questions:
- "Which is correct on failure: synthesize error results or discard the assistant message?" — Synthesize.
  Decided 2026-10-22. It is what HEAD already does for the two failure classes *inside* a completed round:
  preparation failures become synthetic tool-error tuples (`scripts/agent/tool_preparation.py`) and denied
  calls become tool messages (`tool_runner.py:412-428`). Discarding the assistant message would also erase
  the model's stated intent, cannot undo the side effects the completed calls already applied, and interacts
  with the `execute`-stage retry semantics that `turn002` owns.
- "Should the assistant message and tool results be written in one DB transaction?" — No. Decided. They are
  today two separate connections and commits (`llm_turn_runner.py:108-112` → `session_message_repo.py:83-89`,
  `tool_runner.py:391` → `save_many` at `:91-`); merging them would hold a write transaction open for the
  whole tool round, including a hung MCP call. `save_many` already gives the tool messages one atomic write,
  and `replace_messages` (`:140-174`) is the repository's existing single-transaction shape, deliberately
  limited to history replacement after compression.
- Scope note: the mid-round trip handling that `plans/20261022-092413_plan.md:372-381` assigns to `tool002`
  (per-call checks in sequential groups, per-batch checks for concurrent groups, tool messages for the calls
  that are then skipped) is in scope for this issue, because a skipped call is exactly another declared id
  with no tool message. `tool003` (sibling failures inside `gather`) and `tool004` (`tc["id"]`) stay out of
  scope; they change *which* results exist, not whether every id is answered.

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
