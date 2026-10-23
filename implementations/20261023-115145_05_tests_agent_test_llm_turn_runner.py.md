# Implementation Procedure: `tests/agent/test_llm_turn_runner.py`

## Goal

Pin the observable consequence this Plan introduces: a round whose calls all fail is now counted by the turn-level error guard and stops the turn at the configured limit. Implements `REQ-009` — the newly reachable `check_error_limit` path (`scripts/agent/tool_loop_guard.py:392-405`) fed from the `ctx.stats.stat_tool_errors` delta (`scripts/agent/llm_turn_runner.py:114-124`).

## Scope

Add to `tests/agent/test_llm_turn_runner.py`: one class `TestAllFailingRoundGuardReachable` with a full-failure case (all calls fail → turn stops with `reason="error_limit"` after `tool_error_max_consecutive` rounds) and a partial-failure case (count maintained, not incremented, per `tool_loop_guard.py:385-389`). Do not modify any existing test, including `test_check_error_limit_triggers` (`tests/agent/test_llm_turn_runner.py:475`).

## Assumptions

- The `runner` fixture (`:44-48`) builds `LLMTurnRunner(ctx, guard)` with a **MagicMock** guard whose `update_errors.return_value = 0` and `check_error_limit.return_value = None` (`:36-41`). The existing `test_check_error_limit_triggers` (`:475`) relies on that mock and stubs `execute_all_tool_calls`.
- To exercise the **real** counting path, the new tests need a **real** `ToolLoopGuard` bound to `ctx`, not the mock fixture — so construct the runner directly with `ToolLoopGuard(ctx)` rather than using the `runner` fixture.
- Make every call fail through the real per-call boundary by patching `agent.tool_runner.execute_one_tool_call` to raise, so the real `execute_all_tool_calls` records error rows and increments `ctx.stats.stat_tool_errors` (the delta `run()` reads at `scripts/agent/llm_turn_runner.py:121`).
- Drive repeated tool-call turns by patching `runner._stream_llm` with an `AsyncMock(side_effect=[tool_response, tool_response, ...])` where `tool_response` carries `finish_reason="tool_calls"`.

## Design decisions

- **Real guard, real counting.** The consequence this Plan adds is that an all-failing round now increments `stat_tool_errors` and thus `consecutive_errors`. A mock guard returns a fixed value and cannot observe that; a real `ToolLoopGuard` running `update_errors` (`:380-390`) and `check_error_limit` (`:392-405`) against the real `ctx.stats` delta is what pins reachability.
- **Full vs partial distinction.** `update_errors` increments only when `n_errors == n_tool_calls` (`:386`) and maintains the count on partial failure (`:388`); the two tests mirror exactly that branch split.

## Alternatives considered

- **Stubbing `execute_all_tool_calls` and asserting `check_error_limit` fires.** Rejected: that only re-tests the wiring already covered by `test_check_error_limit_triggers` (`:475`); it does not prove the all-failing round now *produces* the error count. The new test must let the real `execute_all_tool_calls` record the failures.

## Implementation

### Target file

`tests/agent/test_llm_turn_runner.py`

### Procedure

1. Import `ToolLoopGuard` alongside the existing `LLMTurnRunner` import, so the new runner can be built with a real guard.

2. Add `class TestAllFailingRoundGuardReachable`:
   - **`test_full_failure_stops_turn_at_error_limit` (`AC-7`):** build a runner with a real `ToolLoopGuard(ctx)` (so `update_errors`/`check_error_limit` run for real; `cfg.tool_error_max_consecutive` is 3 from `_make_ctx` at `:27`). Patch `runner._stream_llm` to yield a `tool_calls` response each turn. Patch `agent.tool_runner.execute_one_tool_call` so every call raises. Run `runner.run(...)`. Assert the result is `TurnResult(action="fail", reason="error_limit")` — i.e. after 3 consecutive all-failing rounds the real guard aborts. This proves the round now records errors and the guard becomes reachable.
   - **`test_partial_failure_maintains_count` (`REQ-009`, `tool_loop_guard.py:385-389`):** one round mixing a succeeding call and a failing call. Assert that `update_errors` maintains `consecutive_errors` (partial failure: `n_errors > 0` but `!= n_tool_calls`) rather than incrementing, so a single partially-failing round does not itself stop the turn.

3. Confirm the existing `TestRun` cases — especially `test_check_error_limit_triggers` (`:475`) and `test_executes_tool_calls_then_returns` (`:377`) — still pass unmodified.

### Method

Edit in place: add the import (one edit), append the new class at the end of the file (one edit). Verify with `git diff` that no existing test changed.

### Details

- If driving the full real `execute_all_tool_calls` path with a `MagicMock` ctx is impractical (preparation needs a real registry), the alternative that still exercises the real guard is: patch `agent.llm_turn_runner.execute_all_tool_calls` with an `AsyncMock` whose `side_effect` increments `ctx.stats.stat_tool_errors` by the number of calls in the round (mirroring the real recording at `scripts/agent/llm_turn_runner.py:121`), then let the real guard count it. Either way the asserted invariant is identical: all-failing → count increments → turn stops; partial → count maintained.
- `WF_CTX` is the existing workflow-context unpack used by the other `TestRun` cases (`:402`, `:443`, `:469`, `:492`); reuse it.

## Compatibility considerations

N/A to production: test-only. Adds cases; the existing `TestRun` suite must keep passing.

## Security considerations

N/A: test-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_llm_turn_runner.py -v`: the two new cases pass; `test_check_error_limit_triggers` (`:475`) and all other existing cases pass unmodified.
- Full suite: `uv run pytest -q`.

## Completion criteria

- `TestAllFailingRoundGuardReachable` asserts the full-failure round stops the turn with `reason="error_limit"` after `tool_error_max_consecutive` rounds, and the partial-failure round maintains (not increments) the consecutive-error count.
- Every existing test in the file passes.

## Out of Scope

- The production wrapper in `scripts/agent/tool_runner.py` (row 1).
- The failure-text builder in `scripts/agent/tool_result_formatter.py` (row 2) and its unit test (row 4).
- The batch-total cases in `tests/agent/test_tool_runner.py` (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestAllFailingRoundGuardReachable` (full-failure + partial-failure) with a real `ToolLoopGuard` | Pending | — | — | Exercises the newly reachable `check_error_limit` path |
| 2 | Run the llm_turn_runner unit tests + full suite | Pending | — | — | Existing `TestRun` cases must pass unmodified |

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
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: tests/agent/test_llm_turn_runner.py
