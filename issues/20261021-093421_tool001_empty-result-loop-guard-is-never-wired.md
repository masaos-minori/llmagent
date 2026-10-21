# The empty-result tool loop guard is never wired: `ctx.guard` is never assigned

## Priority
High

## Summary
Wire `ToolLoopGuard` into the tool-result collection path so `tool_empty_result_max_repeats` actually
limits empty-result loops, or remove the option and the detection code.

## Background
`ToolLoopGuard.record_tool_result()` is the only producer of `_empty_result_counts`
(`scripts/agent/tool_loop_guard.py:156-167`), and `check_empty_result_repeat()` is the consumer
(`:169-189`). `ToolLoopGuard` is constructed once per turn in `LlmTurnExecutor`
(`scripts/agent/llm_turn_executor.py:83`) and handed to `LLMTurnRunner` (`:51-57`).

## Problem
The only call site of `record_tool_result` is behind `guard = getattr(ctx, "guard", None)`
(`scripts/agent/tool_runner.py:201`, `:210`). No code anywhere under `scripts/` assigns an attribute
named `guard` on `AgentContext` (verified: `grep -rn 'ctx\.guard|"guard"' scripts/` matches only that
`getattr` line), so `guard` is always `None` and the counter map is always empty.
`check_empty_result_repeat()` — called from `llm_turn_runner.py:125` and from inside
`tool_loop_guard.py:371` — therefore always returns `None`. The guard configured by
`tool.tool_empty_result_max_repeats` (`scripts/agent/config_dataclasses.py:178`) is dead on every path,
while the startup self-report in `tool_loop_guard.py` describes the option as enabled
(`_STARTUP_REPORTED`, `:36`, `:95-97`), so the operator is told the protection is active.

## Reason for Change
A tool that repeatedly returns empty results is one of the loop patterns this guard exists to stop. Today
the only remaining protections are the error-count and fingerprint/dedup checks, so a silently-empty tool
can consume the whole turn budget.

## Implementation Intent
Pass the guard explicitly instead of discovering it through `getattr` on the shared context. `ToolLoopGuard`
is already created per turn; make it an explicit argument of the tool-execution entry point, or move the
recording to the component that already holds the guard.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`_collect_tool_result_msgs`)
- `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`
- `scripts/agent/tool_loop_guard.py` (startup self-report)
- `scripts/agent/config_dataclasses.py` (option semantics)

## Required Changes
- Remove the `getattr(ctx, "guard", None)` discovery and pass the per-turn guard explicitly.
- Keep the guard's lifetime per turn (it is constructed per turn today) and record every tool result,
  including batch and DAG paths.
- Make the startup diagnostic report the option only when the wiring exists, or drop the report.
- Add a test that proves the configured limit triggers a turn stop.

## Constraints
- `execute_all_tool_calls()`'s existing signature is used by `llm_turn_runner.py:116-120` and other
  callers; extend it explicitly rather than smuggling state through `AgentContext`.
- `tool_empty_result_max_repeats <= 0` must keep meaning "disabled".
- Per `skills/DESIGN.md` Shared Vocabulary, do not add new mutable state to the shared context.

## Acceptance Criteria
- With `tool_empty_result_max_repeats = 2` and a tool that returns an empty result three times, the turn
  stops with `reason="empty_result_repeat"`.
- No `getattr`-based lookup of the guard remains.
- The startup report and the configuration state agree (assert both).

## Testing Expectations
- Regression test at the turn level with a stub tool that returns `""` repeatedly, asserting the guard
  fires and the recorded counts increase.
- A test that fails if the guard is not passed (mutation check on the wiring line).
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
State in the tool-loop docs which guards exist, what each one counts, and which configuration key enables
it. If the option is removed instead of wired, record the removal and its reason.

## Out of Scope
- Other loop guards (error-count, fingerprint/dedup) and their thresholds.
- Tool result masking (`tool005`).

## Dependencies
- Same code region as `tool002` and `tool003`; sequence so the batch-execution refactor lands first.

## Unresolved Questions
- Should the guard be per turn or per session? It is constructed per turn today; the empty-result counter
  semantics for a multi-round turn need to be stated. Needs confirmation.
- Is the startup diagnostic report required by `docs/`? Needs confirmation before deleting it.

## AI Implementation Instruction
Delete the implicit lookup; make the dependency visible in the signature. Do not implement the wiring by
assigning a new attribute onto `AgentContext`.

## Traceability
- **Workflow phase**: `python-code-review` (tool execution review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/tool_runner.py`, `scripts/agent/llm_turn_executor.py`,
  `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_loop_guard.py`,
  `scripts/agent/config_dataclasses.py`
