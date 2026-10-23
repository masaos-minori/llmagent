# Implementation Procedure: `scripts/agent/tool_runner.py`

## Goal

Make one tool round total: every call `_run_group_calls` starts yields exactly one result tuple, whether that call succeeds or raises. A call's exception is captured at the single per-call execution boundary and turned into the same six-field error-result tuple the preparation phase already produces (`scripts/agent/tool_preparation.py:37`), so a sibling's results, already-applied side effects, the round's ordering, and the round's own audit records all survive one failing call. Implements `REQ-001` (one tuple per started call), `REQ-002` (`try` covers only the awaited call; `except Exception` keeps cancellation propagating), `REQ-003` (reuse the existing failure-row shape), `REQ-005` (log the captured exception with traceback), `REQ-007` (a failure does not stop later calls or later batches), `REQ-008` (ordering preserved, no new conversion step, no `return_exceptions=True`), `REQ-009` (downstream wiring unchanged and now reachable for execution failures), and `REQ-013` (stays under the 16384 B module-size gate).

## Scope

Modify only `scripts/agent/tool_runner.py`: add one private per-call wrapper and route both branches of `_run_group_calls` through it. Add one cross-module private import of the failure-text builder from `scripts/agent/tool_result_formatter.py`. Do not modify `_run_plan_batches`, either `asyncio.gather` site, either order-restoring sort, `_collect_tool_result_msgs`, `_update_stats_for_result`, `execute_all_tool_calls`, `save_many`, or `execute_one_tool_call`. The failure-text builder itself is added in `scripts/agent/tool_result_formatter.py` (this document's row 2); this document only imports and calls it.

## Assumptions

- A `tool` message carrying `is_error=True` in its row is sufficient for the model to act on a failed call; the persisted six-field shape needs no structured error field (this is how preparation rejections and transport errors are represented today).
- `ToolExecutorUnavailableError` is captured like any other failure, so the batch-total rule does not depend on the exception class; it remains observable through logging (`REQ-005`) and the guard (`REQ-009`).
- `Exception` (not `BaseException`) is the correct catch class for a per-call boundary here, matching `scripts/agent/tool_arg_validator.py:134` and `scripts/agent/context.py:327`.
- Nothing raised at the per-call boundary means neither `asyncio.gather` site needs `return_exceptions=True`.

## Design decisions

- **One per-call wrapper, not two batch-level conversions.** At HEAD the two consumers that shape the round — the order-restoring sort at `scripts/agent/tool_runner.py:332` and the six-field unpack at `:202` — run before any conversion could be inserted, and `return_exceptions=True` puts exception objects inside the results list (`probe` Q4). Capturing inside a per-call wrapper means the values that reach those consumers are always tuples, so no conversion step is added anywhere and the batch-level gather at `:291-296` stays as-is.
- **The `try` covers only the awaited call.** Its own row-building is outside the `try`, so a bug in this Plan's new code is not converted into a tool error. `except Exception` is deliberate: `BaseException` would swallow `asyncio.CancelledError`, and the probe confirms cancellation must keep propagating (`AC-5`). The catch is annotated `# noqa: BLE001` with an em-dash justification, because `BLE001` is selected in `pyproject.toml:96` and that is the established form (`scripts/agent/tool_arg_validator.py:134`, `scripts/agent/context.py:327`).

## Alternatives considered

- **Batch-level `return_exceptions=True` at both gather sites** (the issue's original Required Changes). Rejected: it puts exception objects into the same list as result tuples, and both consumers (`:332`, `:202`) run before any conversion could be inserted; adding it at the batch site would additionally launder a programming error inside `_run_group_calls` into a fabricated tool result.
- **Catching inside `execute_one_tool_call` itself.** Rejected: `REQ-006` keeps `execute_one_tool_call`'s raise contract (`:154`, `:159-162`) intact, and `TestExecutorUnavailableGuard` / `TestGatewayBypassPreflightDenial` (`tests/agent/test_tool_runner.py:1154`, `:1169`) must pass unmodified.

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. Add the cross-module private import near the existing `tool_run_recorder` import block (`scripts/agent/tool_runner.py:43-48`). Import the failure-text builder by name from `agent.tool_result_formatter`:

   ```python
   from agent.tool_result_formatter import build_execution_failure_text
   ```

   Keep it in the same grouped third-party/first-party import style as the surrounding imports; do not add a second import group. This is the same cross-module private-import pattern the module already uses for `_log_dag_buckets`, `_record_round_exec`, `_record_serialization_stats`, `_record_round_serialization_events`.

2. Add the private per-call wrapper as a module-level async function directly above `_run_group_calls` (before `scripts/agent/tool_runner.py:63`). It returns `tuple[str, str, dict, str, bool, str]` for both outcomes:

   ```python
   async def _run_group_call(
       ctx: AgentContext,
       pc: PreparedToolCall,
   ) -> tuple[str, str, dict, str, bool, str]:
       """Execute one prepared call, capturing its failure as an error row.

       Returns the same six-field tuple `execute_one_tool_call` documents
       (`scripts/agent/tool_runner.py:150`, `:153`) for a success and for a
       failure: `(tc_id, name, args, full_text, is_error, llm_text)`. Only this
       call's exception is converted; nothing is raised out of here, so the
       surrounding `asyncio.gather` sites need no `return_exceptions`.
       """
       try:
           return await execute_one_tool_call(ctx, pc)
       except Exception as exc:  # noqa: BLE001 — per-call boundary: one raising call must not abort its siblings; CancelledError (BaseException) intentionally propagates
           logger.exception(
               "tool execution failed tool=%r call_id=%s", pc.name, pc.call_id
           )
           failure_text = build_execution_failure_text(exc)
           llm_text = _truncate_for_llm(
               failure_text, ctx.cfg.tool.tool_result_max_llm_chars
           )
           return pc.call_id, pc.name, pc.args, failure_text, True, llm_text
   ```

   The `try` covers only the awaited `execute_one_tool_call` call. The row-building (`build_execution_failure_text`, `_truncate_for_llm`, the return tuple) is outside the `try`, so a bug in this new code stays a bug rather than becoming a tool error. `str(exc)` in the LLM-facing text follows the existing precedent at `scripts/shared/tool_transport_invoker.py:209`, `:219`.

3. Route both branches of `_run_group_calls` (`scripts/agent/tool_runner.py:63-74`) through the wrapper. The sequential branch (`:69-73`) awaits each call through `_run_group_call`; the concurrent branch (`:74`) gathers `_run_group_call` coroutines. Leave the function's signature, docstring, and the `serialize` branch selection unchanged. Because nothing raises at the boundary, the concurrent `asyncio.gather` keeps its current form (no `return_exceptions=True`).

4. Do not touch `_run_plan_batches` (`:274-298`), either order-restoring sort (`:332`, `:383-385`), `_collect_tool_result_msgs` (`:187-222`), `_update_stats_for_result` (`:225-237`), `execute_all_tool_calls` (`:347-391`), or `execute_one_tool_call` (`:147-184`). Every element of `results` is still a tuple, so both sorts keep working and downstream consumers already handle `is_error=True` rows.

### Method

Edit in place with the `edit` tool: add the import (one edit), add the wrapper function (one edit before `_run_group_calls`), and replace the two body lines of `_run_group_calls` (one edit). Verify with `git diff` that only these three regions changed and that `_run_plan_batches`, both sorts, and `execute_one_tool_call` are byte-identical to HEAD.

### Details

- The failure row's position 3 (`full_text`) carries `failure_text`; position 5 (`llm_text`) carries the `_truncate_for_llm`-truncated copy, mirroring `execute_one_tool_call`'s own return at `:184`.
- `logger.exception` (not `logger.error`) emits the captured traceback, so a failure the round converts into a row is never silent (`REQ-005`). The message carries the tool name and call id so the row is traceable to its origin.
- `build_execution_failure_text` lives in `scripts/agent/tool_result_formatter.py` (row 2), not here, to keep `tool_runner.py` inside its 858 B headroom before the 16384 B gate (`tools/check_module_size.py:5`, measured 15526 B at HEAD) and to avoid a new row in the generated agent reference table (`docs/23_agent/agent_13_reference-api-generated.md:179`, `:184` list public symbols only; the helper is private).

## Compatibility considerations

Downstream wiring is unchanged: `_collect_tool_result_msgs` already produces tool messages, counts stats, and records guard state for `is_error=True` rows produced by preparation and transport failures; the captured row is simply one more such row. Consequence: an all-failing round now increments `ToolLoopGuard.update_errors` (`scripts/agent/tool_loop_guard.py:381-389`) and can stop a turn at `check_error_limit` (`:392-405`, configured 3 at `config/agent.toml:59`) — the behavior `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md:100` already documents (`REQ-009`, `AC-7`). Grouping and configuration behavior is unchanged: `tool.serial_tool_calls`, `scripts/agent/tool_scheduler.py`, and every `build_execution_groups` call site are untouched (`REQ-010`).

## Security considerations

Exception messages can contain paths or URLs, and they now reach the conversation as a `tool` result. This is the same exposure the round already has for transport and lifecycle failures (`scripts/shared/tool_transport_invoker.py:209`, `:219`); the logging path is redacted by `scripts/shared/logger.py:64` `_RedactionFilter`, and the row is truncated like any other result through `_truncate_for_llm`. No new secret is written beyond what the round already carries.

## Rollback considerations

Revert the commit (single logical change: one import, one wrapper, two routed calls).

## Validation plan

- Unit + integration through `execute_all_tool_calls`: `uv run pytest tests/agent/test_tool_runner.py -v`, then `uv run pytest -q`. The 15 existing `_execute_with_dag` assertions, `TestExecutorUnavailableGuard`, and `TestGatewayBypassPreflightDenial` must pass unmodified.
- Type, lint, complexity, dead code: `uv run ruff format scripts/ && uv run ruff check scripts/ --fix && uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run radon cc scripts/agent/tool_runner.py -s -n C`, `uv run vulture scripts/ --min-confidence 80`. No new ruff or mypy finding; `_run_group_calls` stays complexity grade A; no new vulture finding.
- Security and suppression governance: `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_suppression_justification.py`. No high or medium finding; the added `# noqa: BLE001` carries a rule code and an em-dash justification.
- Module-size gate: `uv run python tools/check_module_size.py --top 5`. `tool_runner.py` stays under 16384 B.
- Architecture boundary: `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_dependency_graph_cycles.py`. All 6 import contracts kept, 0 broken, no new cycle.

## Completion criteria

- `_run_group_call` exists as a private module-level async function returning `tuple[str, str, dict, str, bool, str]` for both success and failure.
- Both branches of `_run_group_calls` await their calls through `_run_group_call`; the concurrent branch's `asyncio.gather` has no `return_exceptions=True`.
- No exception object reaches `results`; both sorts (`:332`, `:383-385`) and `_collect_tool_result_msgs` unpack are unchanged in form.
- `execute_one_tool_call` is byte-identical to HEAD; `TestExecutorUnavailableGuard` and `TestGatewayBypassPreflightDenial` pass unmodified.
- The `# noqa: BLE001` annotation carries an em-dash justification; `bandit`, `check_suppression_justification.py`, `lint-imports`, `check_module_size.py`, and `generate_reference_table.py --check` all pass with no new finding.

## Out of Scope

- The failure-text builder (`scripts/agent/tool_result_formatter.py`) — this document imports and calls it; row 2 adds it.
- `tests/agent/test_tool_runner.py` characterization/batch-total cases — row 3.
- `tests/agent/test_llm_turn_runner.py` guard-reachability cases — row 5.
- Retry, idempotency-key behavior, `_execute_with_dag`'s recording steps (`:328`, `:335-343`), scheduler and DAG grouping, and any config key (`REQ-011`, `REQ-010`).
- The round-pairing invariant owned by `plans/20261022-105432_plan.md` — this Plan does not restate it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the per-call wrapper and route both `_run_group_calls` branches in `scripts/agent/tool_runner.py` | Pending | — | — | `# noqa: BLE001` with justification; no change to `_run_plan_batches` or the sorts |
| 2 | Add/update tests in `tests/agent/test_tool_runner.py` per Validation plan | Pending | — | — | Includes cancellation and stats cases |
| 3 | Run the validation sequence (`rules/toolchain.md`) plus module-size/import/reference checks | Pending | — | — | See Validation plan |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`, `REQ-007`, `REQ-008`, `REQ-009`, `REQ-013`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: scripts/agent/tool_runner.py
