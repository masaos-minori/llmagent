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

### Verification (re-read at HEAD `6e146bcf1`, 2026-10-23)

Confirmed at HEAD:
- Both group shapes propagate. `_run_group_calls` (`scripts/agent/tool_runner.py:63-74`) awaits
  `execute_one_tool_call` with no `try` in the sequential branch (`:69-73`) and gathers without
  `return_exceptions` at `:74`. `_run_plan_batches` (`:274-298`) gathers the groups of a batch the same
  way at `:291-296`, so a raising group also loses every **later batch**: the `for batch in
  plan.batches` loop at `:281` never reaches them. The issue names the sibling-group loss but not the
  batch loop.
- Measured at runtime (probe at `/tmp/opencode/probe_gather.py`, repo venv Python 3.14.7): `asyncio.gather`
  with one failing child raises the first exception and discards a sibling that had **already completed**;
  a still-pending sibling is cancelled. `return_exceptions=True` returns the exception **as a value inside
  the results list**, and does not swallow an outer cancellation (that still raises `CancelledError`).
- Nothing records the round when it raises. The sort at `:332`, the merge and second sort at `:384-385`,
  `_collect_tool_result_msgs` at `:387` and `ctx.session.save_many(tool_msgs)` at `:391` all sit after
  execution. The issue cites only `:385`; the first sort is at `:332`, and that is the one a group failure
  skips. The round also leaves no audit trail: `_record_serialization_stats` (`:328`),
  `_record_round_serialization_events` (`:335`) and `_record_round_exec` (`:336-343`) are after
  `_run_plan_batches` (`:331`) as well.
- Cancellation is worse than "executed but unrecorded": a gathered sibling cancelled mid-call may already
  have applied its effect on the MCP server while its `ToolCallResult` never exists, so neither
  `_record_transport_failure` (`:122-137`) nor `audit_tool_exec` (`:169-178`) ever sees that call.
- `execute_one_tool_call` raises `ToolExecutorUnavailableError` at `:159-162`, and its docstring (`:154`)
  states that contract.
- The shape to reuse already exists and is the same in all three places: `_PrepFailure =
  tuple[str, str, dict, str, bool, str]` (`scripts/agent/tool_preparation.py:37`, built by `_reject` at
  `:51-72`), `execute_one_tool_call`'s documented return `(tc_id, name, args, full_text, is_error,
  llm_text)` (`tool_runner.py:150`, `:153`), and the unpack in `_collect_tool_result_msgs` (`:202`).

Gaps between the issue text and HEAD:
- "can propagate transport, MCP, truncation, or DB errors" — two of the four are wrong. `TransportError` is
  converted into an error result (`scripts/shared/tool_transport_invoker.py:245` → `_record_transport_error`
  → `_error_result(..., error_type="transport")` at `:211`) and a permitted lifecycle failure the same way
  (`:280-283`, `:219`), so a transport failure already produces a tool row today. `_truncate_for_llm`
  (`tool_runner.py:140-144`) and `_apply_turn_char_limit` (`:256-271`) cannot raise. What can actually
  raise at the per-call boundary is: `ToolExecutorUnavailableError` (`:159-162`); a re-raised
  `PolicyViolationError` on the gateway-less path (`:114-118` — `repository_gateway.py:103-105` converts it
  instead); `ValueError` from `ToolRouteResolver.resolve()` (`scripts/shared/route_resolver.py:63-76`),
  reachable only on that same gateway-less path (`:98-101`); `AssertionError` from `audit_tool_exec`'s
  `assert ctx.workflow.workflow_id` (`scripts/agent/tool_audit.py:154-156`); `sqlite3.Error` from
  `ctx.diagnostics.save_transport_failure` (`:132-137`); and any non-`TransportError` a transport's `call()`
  raises, because only `TransportError` is caught (`tool_transport_invoker.py:245`).
- Required Changes bullet 1 does not fit the code at HEAD. `return_exceptions=True` puts exception objects in
  the same list as result tuples (probe Q4), and the consumers run before any conversion could be inserted:
  `_execute_with_dag`'s sort indexes `r[0]` at `:332`, and `_collect_tool_result_msgs` unpacks six fields at
  `:202`. Adding it at the batch site (`:291-296`) would additionally turn a programming error inside
  `_run_group_calls` into a fabricated tool result. Corrected mechanism: capture at the single per-call
  boundary inside `_run_group_calls`; with nothing raised there, neither `gather` site needs
  `return_exceptions=True`, and the batch-level gather stays as it is.
- Line drift: `_run_group_calls` is `:63-74` (issue: `:63-75`), the batch gather is `:291-296` (issue:
  `:291-297`), the raise is `:159-162` (issue: `:158-162`), and `_PrepFailure` is `tool_preparation.py:37`
  with `_reject` at `:51-72` (issue: `:66-72`). `:385`, `:387` and `:391` are exact.
- Preparation is total only for the failures it names. `_prepare_one` catches `orjson.JSONDecodeError`
  (`tool_preparation.py:93`) and `KeyError` (`:123`, `:139`) only; an unexpected exception from
  `registry.get` or `tool_spec_for_call` escapes `prepare_tool_calls` and loses the whole round before any
  call runs. That is a different boundary and stays outside this issue.
- The issue does not name the consequence for the turn loop: today a raising round counts **zero** tool
  errors, because `_update_stats_for_result` (`:225-237`) runs only inside `_collect_tool_result_msgs`
  (`:203`), which never runs. `LLMTurnRunner.run()` derives `n_errors` from the
  `ctx.stats.stat_tool_errors` delta (`scripts/agent/llm_turn_runner.py:114-123`) and feeds
  `check_error_limit` (`:129`; `scripts/agent/tool_loop_guard.py:392-404`), configured at
  `tool_error_max_consecutive = 3` (`config/agent.toml:59`, built-in default 3 at
  `scripts/agent/config_section_builders.py:197-198`).
  The behavior `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md:100` documents is therefore
  unreachable for exactly this failure class.
- No test locks the current behavior. `tests/agent/test_tool_runner.py` asserts the raises only at
  `execute_one_tool_call` level (`TestExecutorUnavailableGuard` at `:1154`, `:1161`;
  `TestGatewayBypassPreflightDenial` at `:1169`), and nothing asserts what a batch does when one of its
  calls raises. The 15 direct `_execute_with_dag` call sites in that file assert on the returned list, so
  the row shape those tests observe is part of the blast radius.
- Stale claim found while reading the documentation target:
  `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md:84` states `_check_type_validation()`
  does not catch `jsonschema.SchemaError`; at HEAD it catches it
  (`scripts/agent/tool_arg_validator.py:195-199`). It belongs to the preparation phase, so this issue does
  not correct it; carried as `UNK-03` in the Plan.

Answers to the issue's Unresolved Questions:
- "Should a raising call cancel sibling calls in the same group (fail-fast) or let them finish?" — Let them
  finish. Decided 2026-10-23. This issue's own goal is to record what already ran, and the probe shows an
  outer cancellation still propagates, so finishing siblings does not weaken cancellation semantics. The
  repository already uses this shape where every outcome must be reported
  (`scripts/agent/resource_shutdown_coordinator.py:127`, `:140`; `scripts/rag/stages/search.py:42`).
- "Should a batch-level failure stop the turn or only mark that round as errored?" — Only the round.
  Decided. The turn-level decision already has an owner: `check_error_limit`
  (`tool_loop_guard.py:392-404`) fed from `llm_turn_runner.py:114-123`, active at HEAD at 3
  (`config/agent.toml:59`). It cannot see an exception round today; making the batch total is what makes the
  already-documented guard reachable. `execute_one_tool_call`'s raise contract (`:154`, `:159-162`) and the
  two characterization classes in `tests/agent/test_tool_runner.py` are not changed by this issue.
- Required Changes bullet 2 ("decide and state whether a failure stops later calls or each call is
  independent") — Each call is independent; a failure does not stop the group. The scheduler expresses only
  resource-scope conflicts (`scripts/agent/tool_scheduler.py:131`, `:152-208`); no call consumes another
  call's result, so nothing after a failing call depends on it having succeeded. Stopping the group would
  re-create the defect this issue is about. The implicit dependency inside a `requires_serial=True` barrier
  (for example two `shell` calls in sequence) is recorded as a Risk with a mitigation.

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
