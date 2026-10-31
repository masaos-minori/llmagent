# Two tool calls with the same id in one round run the wrong call twice

## Priority
High

## Summary
The tool round keys its working data by the model-supplied tool call id and never checks that the ids in one assistant message are unique. When two calls share an id, both scheduled entries resolve to the last prepared call: the second call's arguments execute twice and the first call's arguments never execute, even though the user approved each call separately. Only one result is collected for the two declared calls. Reject or otherwise disambiguate duplicate ids before approval and execution.

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- `prepare_tool_calls` (in `tool_preparation.py`) rejects only a missing id; it builds one `PreparedToolCall` per raw call, so two calls with the same id both pass preparation and approval (each is approved with its own arguments in `run_approval_checks`).
- `_execute_with_dag` (in `tool_runner.py`) builds `call_specs` and `pc_by_id` as dictionaries keyed by `call_id`, so the later entry replaces the earlier one. `build_execution_groups` (in `tool_scheduler.py`) walks the raw calls and looks each one up by id in `call_specs`, so two raw calls produce two scheduled entries that both map to the same spec. The conflict graph is also keyed by id. `_run_group_calls` then fetches the prepared call by id, which is the last one for both entries.
- `_recorded_call` stores the result in `collected[pc.call_id]`, one slot per id. `complete_round` merges results in declared order, consuming one result per id; `pair_round_results` treats an id in `collected` as answered.
- The LLM client layer passes `tool_calls` through unchanged: `LLMTurnRunner` hands `message["tool_calls"]` to `execute_all_tool_calls`, and the stream accumulator copies the id from each delta. No id uniqueness check exists on that path (searched `llm_sse_helpers`, `llm_turn_runner`, `tool_preparation`).

## Problem
Reproduction (throwaway script, not committed): two prepared write calls with the same id and different arguments, a stub gateway that records the arguments it receives, and `_execute_with_dag` with the real scheduler. Observed: the stub received the second call's arguments twice, in order, and never received the first call's; the collected results held one entry for the shared id. No real tool server or database was used.

Effects:
- A write the user approved is silently not performed, while a different write is performed twice. Each execution uses a fresh idempotency key at the transport, so the server does not deduplicate them.
- The history then has two declared calls and one answer for that id, which is an inconsistent pairing for the next request.
- Model output is untrusted input at this boundary: the id is chosen by the model or by the serving layer, and uniqueness is a convention, not something this code enforces. Whether a given model or server emits duplicate ids is `Needs confirmation`.

## Reason for Change
The preparation phase is documented as fail-closed ("parse, resolve, validate before approval"), but this property is not part of it, and the consequence is a wrong side-effecting call. The failure needs no bug in the model other than a repeated id.

## Implementation Intent
Treat a duplicated call id in one round as a preparation failure, before approval and scheduling, so that no call with a duplicated id executes and every declared occurrence is answered consistently. The owner decides the exact reporting (for example one tool error row per id explaining the duplication) within the constraint that no call may run with another call's arguments and that no approved call is silently dropped.

## Target Files or Areas
- `scripts/agent/tool_preparation.py` (`prepare_tool_calls`, `_prepare_one`)
- `scripts/agent/tool_runner.py` (`_execute_with_dag`, `execute_all_tool_calls`)
- `scripts/agent/tool_scheduler.py` (`build_execution_groups`; its assumption that ids are unique)
- `scripts/agent/tool_round_completion.py`, `scripts/agent/tool_result_pairing.py` (answering declared ids)
- `tests/agent/` tests for preparation, scheduling and round completion

## Required Changes
- Detect duplicate ids in the batch during preparation and mark the affected calls as failures with a distinct failure kind.
- Make the scheduler fail loudly if it is given duplicate ids, instead of silently collapsing them.
- Ensure the history and the persisted rows contain a consistent answer for each declared id after such a round.
- Add tests: a round with two calls sharing an id executes neither with the wrong arguments nor twice; the approval prompt is not shown for a call that will be rejected.

## Constraints
- Do not change how unique ids are processed (order, concurrency, results).
- Do not rewrite the model's ids in the assistant message that is sent back to the provider unless the provider contract is checked; the pairing between `tool_calls[].id` and `tool_call_id` must stay valid.
- Keep the existing missing-id rejection.

## Acceptance Criteria
- With two calls sharing an id, no tool is executed with arguments from a different call, and no call is executed more than once.
- The user is not asked to approve a call that is rejected for a duplicate id.
- Each declared id has a consistent, explicit answer in the history.
- Rounds with unique ids behave as before.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests for `prepare_tool_calls` and `build_execution_groups` with duplicate ids, plus a round-level test with a stub gateway that records executed arguments.
- Regression: run the tool runner, scheduler, preparation, approval and round completion tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Needs confirmation: check whether the agent tool-execution documentation lists the preparation checks. If it does, add the id uniqueness check and the reporting behavior; describe intent only.

## Out of Scope
- Normalizing or generating ids for providers that omit them.
- The LLM streaming and accumulation logic.
- Approval prompt content.

## Dependencies
N/A: none. `issues/done/20261026-224729_turn002_repair-orphan-tool-call-rows.md` is archived background about unpaired tool rows at history load and does not cover duplicate ids within a round.

## Unresolved Questions
- Whether any supported model or serving layer emits duplicate ids in one message: `Needs confirmation`; the severity assumes it can happen because nothing enforces uniqueness.
- Whether a duplicated id should reject all calls that share it or keep the first: a design choice for the implementer (the constraint is that none runs with wrong arguments).

## AI Implementation Instruction
Write the failing round-level test first. Change only preparation, the scheduler's input check, and answering of declared ids. Do not alter unique-id behavior, provider message shapes, or approval logic. Stop and report if the fix requires changing how ids are sent to the provider.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073525
- **Related target files**: scripts/agent/tool_preparation.py, scripts/agent/tool_runner.py, scripts/agent/tool_scheduler.py, scripts/agent/tool_round_completion.py, scripts/agent/tool_result_pairing.py
