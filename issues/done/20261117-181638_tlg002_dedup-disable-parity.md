# ToolLoopGuard dedup guard ignores <= 0 disable parity

## Priority
Low

## Summary
`ToolLoopGuard.check_dedup` does not honor the `<= 0` disables-the-guard convention that every sibling guard in the class follows. Add the missing early-return so a zero or negative `tool_dedup_max_repeats` cleanly disables dedup instead of blocking every tool call on its first occurrence.

## Background
The tool-loop guard in `scripts/agent/tool_loop_guard.py` guards the inner tool-call loop against dedup, cycle, retry, consecutive-error, stagnation, and empty/unavailable repeats. Every other guard in the class treats a `<= 0` config value as a clean disable: `check_retry`, `check_cycle`, `check_error_limit`, `scan_empty_result_repeat`, `scan_unavailable_repeat`, and `record_tool_result` all return early when their config is `<= 0`. `check_unavailable_repeat` even documents this contract in its docstring ("limit <= 0 disables the check entirely (default-off)").

`check_dedup` has no such guard. Config validation (`validate_tool_dedup_max_repeats`, invoked from `ToolConfig.__post_init__`) currently enforces a minimum of `1`, so the divergent value cannot reach the runtime guard through the normal config path.

## Problem
`check_dedup` increments `seen_calls[key]` and compares `seen_calls[key] >= cfg.tool_dedup_max_repeats` with no `<= 0` short-circuit. When `tool_dedup_max_repeats` is `0` or negative, the comparison is always true, so the very first occurrence of any `(tool, args)` pair is reported as a duplicate and the turn exits with "Repeated tool call detected." — the agent cannot execute any tool call once. This contradicts the module-wide "`<= 0` disables" contract that all siblings implement and that a maintainer expects from reading the class.

## Reason for Change
The divergence is a latent footgun. Right now config validation masks it, but the guard boundary itself is wrong: if validation ever loosens, if the guard is invoked programmatically or from a test with a `0` value, or if a future refactor bypasses `__post_init__`, dedup silently becomes "block everything." Adding the parity guard makes the one-disable-per-class semantics uniform across the class and removes the catastrophic-zero case. Severity is Low because the defect is currently gated by config validation and cannot manifest through the normal config path; the timing is maintainability/robustness, not a live runtime risk.

## Implementation Intent
Add an early-return to `check_dedup` that mirrors the sibling guards: when `cfg.tool_dedup_max_repeats <= 0`, return `None` before mutating `seen_calls`. Preserve the existing increment-and-compare logic for the enabled case and leave all other guards, the counting machinery, and the disabled-by-default policy untouched. Do not change `validate_tool_dedup_max_repeats` or its `>= 1` enforcement.

## Target Files or Areas
`scripts/agent/tool_loop_guard.py`

## Required Changes
- Add a `if ctx.cfg.tool.tool_dedup_max_repeats <= 0: return None` early-return at the top of `check_dedup`, before the `seen_calls` mutation loop.
- Leave `check_retry`, `check_cycle`, `check_error_limit`, `scan_empty_result_repeat`, `scan_unavailable_repeat`, and `record_tool_result` unchanged — they already implement the parity.

## Constraints
- Behavior-preserving for the current config space (`tool_dedup_max_repeats >= 1`): the enabled path must behave exactly as before.
- Do not alter the `>= 1` config validation or any other guard.
- The fix is defensive; it must not change observable behavior for any currently-valid configuration.

## Acceptance Criteria
- `check_dedup` returns `None` without touching `seen_calls` when `tool_dedup_max_repeats <= 0`.
- For any `tool_dedup_max_repeats >= 1`, dedup detection behaves exactly as before (first block on the Nth identical call).
- With the guard effectively disabled via a `<= 0` value, no tool call is blocked.

## Testing Expectations
- Unit tests in `tests/agent/test_tool_loop_guard.py`: add a case asserting `check_dedup` returns `None` and leaves `seen_calls` empty when `tool_dedup_max_repeats` is `0` (and/or negative), and a regression case confirming detection is unchanged for a positive value.
- Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the touched file.

## Documentation Impact
Not required. The disable semantics are already documented for the sibling guards; making dedup consistent is internal. If the config documentation lists per-guard disable semantics in prose, dedup's `<= 0` disable could be added there for completeness — but do not introduce a new config-field table (see `skills/DESIGN.md` "Docs content policy — remove" and "Avoid implementation-reference duplication").

## Out of Scope
- Any change to `check_retry`, `check_cycle`, `check_error_limit`, `scan_empty_result_repeat`, `scan_unavailable_repeat`, `record_tool_result`, or `report_effective_state`.
- Any change to config validation (`validate_tool_dedup_max_repeats`) or default values.
- Any change to the DAG scheduler, `execute_all_tool_calls`, or `LLMTurnRunner.run`.

## Dependencies
N/A: none. Related (already resolved): `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md` documented the `> 0` enables / `<= 0` disables semantics for the retry and empty-result guards but did not cover dedup; if its documentation note is revisited, dedup's disable semantics can be added alongside.

## Unresolved Questions
- Whether `tool_dedup_max_repeats` should remain strictly `>= 1` (dedup always enabled) or whether a `<= 0` disable should be a supported, documented policy. The parity fix is harmless either way (dead-code protection when always-on, correct disable when disableable), but the intent should be confirmed before treating `<= 0` as a first-class "off" switch. `不明`: confirm intended policy.

## AI Implementation Instruction
Edit only `check_dedup` in `scripts/agent/tool_loop_guard.py`. Add a single early-return mirroring the sibling guards; do not touch any other method. Before editing, confirm the sibling guards (`check_retry`, `check_cycle`, `check_error_limit`, `scan_empty_result_repeat`, `scan_unavailable_repeat`, `record_tool_result`) all gate on `<= 0` (they do) so the parity is real, not assumed. Confirm `validate_tool_dedup_max_repeats` enforces `>= 1` (it does) so this is a defensive fix, not a runtime repair. Then run `uv run ruff check`, `uv run mypy --no-namespace-packages`, and `uv run pytest` on `tests/agent/test_tool_loop_guard.py`.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-181638
- **Related target files**: scripts/agent/tool_loop_guard.py
