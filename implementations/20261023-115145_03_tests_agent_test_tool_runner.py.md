# Implementation Procedure: `tests/agent/test_tool_runner.py`

## Goal

Lock today's loss first, then assert the batch-total contract for both grouping shapes. Implements `REQ-001` (one tuple per started call), `REQ-003` (the failure row shape and `tool_call_id`), `REQ-006` (the unchanged per-call raise contract), `REQ-007` (a failure does not stop later calls or later batches), `REQ-008` (ordering preserved, no exception object reaches `results`), and `REQ-009` (stats increment per failed call, failed keys reach `out_failed_keys`).

## Scope

Add to `tests/agent/test_tool_runner.py`: one characterization class `TestBatchFailureAtHead` (Phase 1, run against unchanged production code), then replace its assertions with the batch-total contract plus the sibling, sequential-continuation, multi-batch, row-text, `ToolExecutorUnavailableError`, cancellation, and stats cases. Do NOT modify `TestExecutorUnavailableGuard` (`tests/agent/test_tool_runner.py:1154`), `TestGatewayBypassPreflightDenial` (`:1169`), the 15 direct `_execute_with_dag` assertions in `TestExecuteWithDag`, or any scheduler test.

## Assumptions

- Drive the round through `_execute_with_dag(ctx, [pcs])` or `execute_all_tool_calls(ctx, [tcs], turn, out_failed_keys=...)` using the existing `_make_ctx`, `_pc`, `_tc`, `_runtime_tools`, `_cfg` helpers (lines `tests/agent/test_tool_runner.py:109`, `:136`, `:165`, `:230`, `:518`).
- Make a single call raise by patching `agent.tool_runner.execute_one_tool_call` with an `AsyncMock`/side effect that raises for one `call_id` and returns a valid six-field tuple for the others. The wrapper in `scripts/agent/tool_runner.py` catches what `execute_one_tool_call` raises, so this exercises the real capture path.
- `ctx.stats.stat_tool_calls` / `stat_tool_errors` are plain ints in `_make_ctx` (`:123-124`), so `_update_stats_for_result`'s `+= 1` is observable.

## Design decisions

- **Characterization before fix.** Add `TestBatchFailureAtHead` asserting today's loss (gathered group with one raising call persists no row for any call; sequential group stops at the failing call) and run it against unchanged production code first. Phase 2 replaces its assertions with the batch-total contract and records the change in the docstring — this is the characterization lock the issue's Testing Expectations require.
- **One patch target for all cases.** Patching `agent.tool_runner.execute_one_tool_call` drives every case (sibling retention, sequential continuation, multi-batch, row-text, `ToolExecutorUnavailableError`, cancellation, stats) through the same real `_run_group_calls` / `_execute_with_dag` / `_collect_tool_result_msgs` path, so the tests exercise the actual wiring rather than the wrapper in isolation.

## Alternatives considered

- **Configuring the stub `tools.execute` to raise.** Rejected: transport/lifecycle failures are converted to error results before they reach this boundary (`scripts/shared/tool_transport_invoker.py:245`), so a stub raising inside `execute` would not exercise the per-call capture path the way a raise from `execute_one_tool_call` does.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. **Phase 1 — characterization lock.** Add `class TestBatchFailureAtHead` near the other characterization classes. It patches `agent.tool_runner.execute_one_tool_call` so one call in a group raises `RuntimeError("boom")` and the others return a valid tuple, then asserts the CURRENT behavior:
   - For a gathered group (`_execute_with_dag(ctx, [pc_a, pc_bad, pc_b])`), the call raises `RuntimeError` and no results are returned.
   - For a sequential (write-conflict) group, calls after the failing one never run.
   Run this class against unchanged production code and confirm it passes.

2. **Phase 2 — replace with the batch-total contract.** Rewrite `TestBatchFailureAtHead` (and rename to reflect the fixed behavior) and add these cases:
   - **Sibling retention (gathered, `REQ-001`, `REQ-007`, `REQ-008`):** a group where one call raises still returns one tuple per started call; the failing call's tuple has `is_error=True` at position 4 and `tool_call_id` at position 0 equal to its id; results are in original `tool_calls` order.
   - **Sequential continuation (`AC-3`):** a sequential group whose first call raises still runs the remaining calls in order; all rows persisted.
   - **Multi-batch (`REQ-007`):** a plan whose later batch still runs after an earlier batch has a failing call.
   - **Row text and truncation (`REQ-003`, `REQ-004`, `AC-2`):** the failing call's `tool` message content contains the `[Tool execution failed: ...]` marker, the exception class name, and `str(exc)`; its length respects `tool.tool_result_max_llm_chars`.
   - **`ToolExecutorUnavailableError` (`REQ-001`):** a `ToolExecutorUnavailableError` case now yields one error row per call instead of raising.
   - **Cancellation (`REQ-002`, `AC-5`):** a `asyncio.CancelledError` raised by `execute_one_tool_call` still escapes `_execute_with_dag`; it does not become a set of error rows.
   - **Stats (`REQ-009`, `AC-7`):** a round where every call fails increments `ctx.stats.stat_tool_calls` and `ctx.stats.stat_tool_errors` by one per call, and each failed key reaches `out_failed_keys` through the unchanged `_collect_tool_result_msgs` path (assert via `tool_hash_key(name, args)`).

3. **Confirm the unchanged classes still pass unmodified:** `TestExecutorUnavailableGuard` (`:1154`), `TestGatewayBypassPreflightDenial` (`:1169`), the 15 direct `_execute_with_dag` assertions in `TestExecuteWithDag`, and the order test `test_results_restored_to_original_order_despite_concurrent_grouping` (`:1028`). A change to any of them means this Plan's scope was exceeded.

### Method

Edit in place: add `TestBatchFailureAtHead` (one edit), then rewrite its body and append the new case methods (one edit per method). Verify with `git diff` that `TestExecutorUnavailableGuard`, `TestGatewayBypassPreflightDenial`, `TestExecuteWithDag`, and `TestExecuteAllToolCalls` are byte-identical to HEAD except for the replaced `TestBatchFailureAtHead`.

### Details

- Import `tool_hash_key` from `agent.tool_runner` for the stats case (`_update_stats_for_result` hashes with it at `scripts/agent/tool_runner.py:237`).
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

- `TestBatchFailureAtHead` exists and, after Phase 2, asserts the batch-total contract for both grouping shapes.
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
| 1 | Phase 1: `TestBatchFailureAtHead` characterization lock, run against unchanged production code | Pending | — | — | Characterization lock the issue requires |
| 2 | Phase 2: batch-total cases (sibling, sequential-continuation, multi-batch, row-text, ToolExecutorUnavailableError, cancellation, stats) | Pending | — | — | Replace the characterization assertions |
| 3 | Run validation (per-file + full suite + regenerated coverage) | Pending | — | — | Existing unchanged classes must pass unmodified |

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
