# Implementation Procedure: `tests/agent/test_tool_runner.py`

## Goal

Lock today's loss first, then assert the batch-total contract for both grouping shapes. Implements `REQ-001` (one tuple per started call), `REQ-003` (the failure row shape and `tool_call_id`), `REQ-006` (the unchanged per-call raise contract), `REQ-007` (a failure does not stop later calls or later batches), `REQ-008` (ordering preserved, no exception object reaches `results`), and `REQ-009` (stats increment per failed call, failed keys reach `out_failed_keys`).

## Scope

Rewrite the three raise-expecting characterization classes in `tests/agent/test_tool_runner.py` to the batch-total contract, then add the sibling, sequential-continuation, multi-batch, row-text, `ToolExecutorUnavailableError`, cancellation, and stats cases. Do NOT modify `TestExecutorUnavailableGuard` (`tests/agent/test_tool_runner.py:1154`), `TestGatewayBypassPreflightDenial` (`:1169`), the 15 direct `_execute_with_dag` assertions in `TestExecuteWithDag`, or any scheduler test.

## Assumptions

- Drive the round through `_execute_with_dag(ctx, [pcs])` or `execute_all_tool_calls(ctx, [tcs], turn, out_failed_keys=...)` using the existing `_make_ctx`, `_pc`, `_tc`, `_runtime_tools`, `_cfg` helpers (lines `tests/agent/test_tool_runner.py:109`, `:136`, `:165`, `:230`, `:518`).
- Make a single call raise by patching `agent.tool_runner.execute_one_tool_call` with an `AsyncMock`/side effect that raises for one `call_id` and returns a valid six-field tuple for the others. The wrapper in `scripts/agent/tool_runner.py` catches what `execute_one_tool_call` raises, so this exercises the real capture path.
- `ctx.stats.stat_tool_calls` / `stat_tool_errors` are plain ints in `_make_ctx` (`:123-124`), so `_update_stats_for_result`'s `+= 1` is observable.

## Design decisions

- **Batch-total contract lock.** The rewritten classes assert the batch-total contract directly (a gathered group with one raising call still yields exactly one tuple per started call; a sequential group continues past the failing call). This is the contract lock the issue's Testing Expectations require.
- **One patch target for all cases.** Patching `agent.tool_runner.execute_one_tool_call` drives every case (sibling retention, sequential continuation, multi-batch, row-text, `ToolExecutorUnavailableError`, cancellation, stats) through the same real `_run_group_calls` / `_execute_with_dag` / `_collect_tool_result_msgs` path, so the tests exercise the actual wiring rather than the wrapper in isolation.

## Alternatives considered

- **Configuring the stub `tools.execute` to raise.** Rejected: transport/lifecycle failures are converted to error results before they reach this boundary (`scripts/shared/tool_transport_invoker.py:245`), so a stub raising inside `execute` would not exercise the per-call capture path the way a raise from `execute_one_tool_call` does.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. **Rewrite the three classes that encoded the pre-fix contract** (see the Adversarial-verification findings below for the full mapping). The batch-total cases to assert are:
   - **Sibling retention (gathered, `REQ-001`, `REQ-007`, `REQ-008`):** a group where one call raises still returns one tuple per started call; the failing call's tuple has `is_error=True` at position 4 and `tool_call_id` at position 0 equal to its id; results are in original `tool_calls` order.
   - **Sequential continuation (`AC-3`):** a sequential group whose first call raises still runs the remaining calls in order; all rows persisted.
   - **Multi-batch (`REQ-007`):** a plan whose later batch still runs after an earlier batch has a failing call.
   - **Row text and truncation (`REQ-003`, `REQ-004`, `AC-2`):** the failing call's `tool` message content contains the `[Tool execution failed: ...]` marker, the exception class name, and `str(exc)`; its length respects `tool.tool_result_max_llm_chars`.
   - **`ToolExecutorUnavailableError` (`REQ-001`):** a `ToolExecutorUnavailableError` case now yields one error row per call instead of raising.
   - **Cancellation (`REQ-002`, `AC-5`):** a `asyncio.CancelledError` raised by `execute_one_tool_call` still escapes `_execute_with_dag`; it does not become a set of error rows.
   - **Stats (`REQ-009`, `AC-7`):** a round where every call fails increments `ctx.stats.stat_tool_calls` and `ctx.stats.stat_tool_errors` by one per call, and each failed key reaches `out_failed_keys` through the unchanged `_collect_tool_result_msgs` path (assert via `tool_hash_key(name, args)`).

2. **Confirm the unchanged classes still pass unmodified:** `TestExecutorUnavailableGuard`, `TestGatewayBypassPreflightDenial`, the 15 direct `_execute_with_dag` assertions in `TestExecuteWithDag`, and the order test `test_results_restored_to_original_order_despite_concurrent_grouping`. A change to any of them means this Plan's scope was exceeded. (The `:1154` / `:1169` / `:1028` line numbers in the original pointed at the pre-refactor layout; the classes still exist and pass unmodified.)

### Method

Edit in place: rename + rewrite the three classes (three edits), add the two imports (two edits). Verify with `git diff` that `TestExecutorUnavailableGuard`, `TestGatewayBypassPreflightDenial`, `TestExecuteWithDag`, `TestExecuteOneToolCallRecordsOnGuard`, and `TestExecuteAllToolCalls` are byte-identical to HEAD except for the three rewritten classes.

### Details

- `tool_hash_key` lives in `shared.tool_executor_helpers` (already imported by the test module); `_update_stats_for_result` hashes with it at `scripts/agent/tool_runner.py:237`. Do not import it from `agent.tool_runner`.
- For the stats case, pass a fresh `set()` as `out_failed_keys` to `execute_all_tool_calls(..., out_failed_keys=failed)` and assert membership after the round.
- The cancellation case asserts `pytest.raises(asyncio.CancelledError)` around the `_execute_with_dag` call — proving the wrapper's `except Exception` does not swallow `BaseException`.

## Compatibility considerations

N/A to production: this file only asserts behavior. The 20 `execute_all_tool_calls` and 15 `_execute_with_dag` references in the same file must keep passing; adding cases does not alter their fixtures.

## Security considerations

N/A: test-only additions; no production code or secrets touched.

## Rollback considerations

Revert the commit (test-only change); the production behavior is unchanged by this row alone.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -v`: every new case passes; `TestExecutorUnavailableGuard`, `TestGatewayBypassPreflightDenial`, the 15 `_execute_with_dag` assertions, and the order test pass unmodified.
- Full suite: `uv run pytest -q`.
- Coverage gate: `uv run coverage run -m pytest tests/` then `uv run coverage xml` (regenerate the stale `coverage.xml`, last built 2026-10-19) before any production change, then `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- `TestBatchFailureTotality` asserts the batch-total contract for both grouping shapes.
- The sibling, sequential-continuation, multi-batch, row-text, `ToolExecutorUnavailableError`, cancellation, and stats cases exist and pass.
- `TestExecutorUnavailableGuard`, `TestGatewayBypassPreflightDenial`, the 15 `_execute_with_dag` assertions, and scheduler tests pass without edit.

## Out of Scope

- The production wrapper in `scripts/agent/tool_runner.py` (row 1).
- The failure-text builder in `scripts/agent/tool_result_formatter.py` (row 2) and its unit test (row 4).
- The guard-reachability cases in `tests/agent/test_llm_turn_runner.py` (row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the three raise-expecting test classes to the batch-total contract (rename + rewrite) | Completed | 20261023 | 20261023 | the round-pairing class → `TestBatchFailureTotality`, `TestCompletedResultsSurviveAFailure` rewritten, the stats-reachability class → `TestStatsForRealVsSynthesizedRows` (split into stats-reach + never-ran-skips) |
| 2 | Add sequential/multi-batch/row-text/truncation/cancellation/stats cases + `asyncio`/scheduler imports | Completed | 20261023 | 20261023 | Multi-batch drives `_execute_with_dag` with a hand-built two-batch `ExecutionPlan` via patched `build_execution_groups`; `tool_hash_key` already imported from `shared.tool_executor_helpers` |
| 3 | Run validation (per-file + full suite + regenerated coverage) | Completed | 20261023 | 20261023 | 64→70 tests pass; full suite 9947 passed/0 failed; ruff/mypy/import-contracts/bandit/suppression/module-size/radon all clean |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-006`, `REQ-007`, `REQ-008`, `REQ-009`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: tests/agent/test_tool_runner.py
