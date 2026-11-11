# Redundant empty-result guard evaluation in ToolLoopGuard.check_all

## Priority
Low

## Summary
Remove the empty-result-repeat guard call inside `ToolLoopGuard.check_all`, which is evaluated twice per turn and is provably inert: the same guard runs after tool execution each turn in `LLMTurnRunner.run` and terminates the turn on any threshold crossing. The turn-start call performs no useful work whether the guard is enabled or disabled by default.

## Background
`ToolLoopGuard` guards the inner tool-call loop against dedup, cycle, retry, consecutive-error, stagnation, and empty-result repeats. In `LLMTurnRunner.run`, `check_all` is called at the top of every loop iteration, before tool execution, and runs cycle, stagnation, dedup, retry, and empty-result checks in order. After `execute_all_tool_calls` returns, `LLMTurnRunner.run` calls `check_empty_result_repeat` a second time (followed by `check_unavailable_repeat` and `check_error_limit`). `tool_runner.py:execute_one_tool_call` is the sole writer of the per-tool `_empty_result_counts`; `tool_runner.py:_run_group_calls` and `_run_plan_batches` also break early on `guard.scan_empty_result_repeat()`. Both repeat guards default to disabled (`tool_empty_result_max_repeats = 0`, `tool_unavailable_repeat_max_repeats = 0`) per `config_dataclasses.py`, documented in `docs/23_agent/agent_08_03_configuration-tools-memory.md`.

The turn-start redundancy only becomes observable after the guard was actually wired. It was not, until `issues/done/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md` (High, resolved): previously `record_tool_result` was reached through `getattr(ctx, "guard", None)`, which always returned `None`, so both the turn-start and post-execution checks were inert. That fix passes the per-turn guard explicitly to `execute_one_tool_call`, so the post-execution check now fires. The tool001 verification also noted that `check_all` runs before execution and its empty-result arm "can only ever inspect counts recorded by previous inner rounds" — the seed of this follow-up cleanup.

## Problem
The empty-result check inside `check_all` can never fire when the guard is enabled: any per-tool empty-result count that reaches the threshold is caught by the post-execution `check_empty_result_repeat` in the same turn, which fails that turn (`TurnResult(action="fail", reason="empty_result_repeat")`). Counts therefore never persist past a threshold crossing, so at the start of the next turn the turn-start occurrence reads a count strictly below the threshold and returns `None`. When the guard is disabled (default), `scan_empty_result_repeat` returns `None` immediately and neither occurrence fires. Either way the turn-start call performs no useful work.

## Reason for Change
The dead call reduces clarity. A maintainer reading `check_all`'s docstring ("Run cycle, stagnation, dedup, retry, and empty result guards in order") may assume the turn-start empty-result check is meaningful, when in fact the single real evaluation point is the post-execution check in `LLMTurnRunner.run`. Removing it makes the one-evaluation-per-turn topology explicit and removes a misleading code path. Severity belongs in Priority; the timing here is purely maintainability, not runtime risk.

## Implementation Intent
Delete the `check_empty_result_repeat(message)` invocation from `ToolLoopGuard.check_all` and drop "empty result" from its docstring's ordered guard list. Add a one-line note that the empty-result guard is evaluated once per turn, after execution, in `LLMTurnRunner.run`. Keep the post-execution check in `LLMTurnRunner.run` untouched. Preserve the guard's disabled-by-default behavior and all other guard ordering.

## Target Files or Areas
`scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py`

## Required Changes
- Delete the `if msg := self.check_empty_result_repeat(message): return msg` line from `ToolLoopGuard.check_all`.
- Update `check_all`'s docstring to remove "empty result" from the listed guards and add a note pointing to the single post-execution evaluation in `LLMTurnRunner.run`.
- Do not modify `record_tool_result`, `scan_empty_result_repeat`, `check_empty_result_repeat`, or `observe_availability` — they remain the counting and post-execution-check machinery.

## Constraints
Do not change the post-execution empty-result check in `LLMTurnRunner.run`. Do not alter the disabled-by-default policy (`tool_empty_result_max_repeats = 0`). This is a behavior-preserving cleanup: the observable behavior when enabled and when disabled must stay identical.

## Acceptance Criteria
- `ToolLoopGuard.check_all` no longer calls `check_empty_result_repeat`.
- The empty-result repeat is still detected via the post-execution check in `LLMTurnRunner.run` and fails the turn with `reason="empty_result_repeat"`.
- With the guard disabled (`0`), no empty-result detection occurs (unchanged).
- `ruff`, `mypy`, and the affected test trees pass.

## Testing Expectations
Unit tests in `tests/agent/test_tool_loop_guard.py` and `tests/agent/test_llm_turn_runner.py`: confirm an empty-result sequence that crosses the threshold is still detected after the change, and that a disabled guard performs no detection. Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the two touched files.

## Documentation Impact
Not required. `docs/23_agent/agent_08_03_configuration-tools-memory.md` correctly documents the default-off policy; the per-turn evaluation topology addressed here is internal and not part of that document's scope.

## Out of Scope
Any change to empty-result counting (`record_tool_result`, `_empty_result_counts`), the early-break scan (`scan_empty_result_repeat`), the unavailable-repeat guard, or the `max_tool_turns` loop bound.

## Dependencies
- `issues/done/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md` — **depends on** (fix order first). This finding is only valid once the guard is wired; tool001's wiring fix is what makes the turn-start call redundant rather than merely dead. tool001 is archived, so the dependency is already satisfied at current HEAD.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Edit only `ToolLoopGuard.check_all` and its docstring in `scripts/agent/tool_loop_guard.py`. Do not touch `record_tool_result`, `scan_empty_result_repeat`, `check_empty_result_repeat`, `observe_availability`, or the post-execution check in `scripts/agent/llm_turn_runner.py`. Before editing, confirm `tool_runner.py:execute_one_tool_call` is the sole writer of `_empty_result_counts` (it is); if another in-turn writer exists, stop and report rather than removing the call. Then run `uv run ruff check`, `uv run mypy --no-namespace-packages`, and `uv run pytest` on `tests/agent/test_tool_loop_guard.py` and `tests/agent/test_llm_turn_runner.py`.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-212552
- **Related target files**: scripts/agent/tool_loop_guard.py, scripts/agent/llm_turn_runner.py
