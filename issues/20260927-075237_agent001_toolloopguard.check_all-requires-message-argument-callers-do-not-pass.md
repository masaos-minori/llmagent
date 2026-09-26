# ToolLoopGuard.check_all requires message argument callers do not pass

## Priority
High

## Summary
`ToolLoopGuard.check_all()` now requires a positional `message` argument that its existing callers (in `orchestrator`, and 12 tests across 5 files) do not pass, causing a `TypeError` at every call site that still uses the old signature.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`TypeError: ToolLoopGuard.check_all() missing 1 required positional argument: 'message'` occurs consistently in:
- `tests/agent/test_tool_loop_guard.py::TestCheckAll` (2 tests)
- `tests/agent/test_orchestrator.py::TestToolLoopGuardHelpers` (3 tests)
- `tests/integration/test_orchestrator_integration.py::TestToolCallFlow` (2 tests)
- `tests/integration/test_rag_llm_integration.py` (2 tests)
- `tests/integration/test_robustness_chaos.py::TestToolLoopGuardChaos` (3 tests)

This is one shared root cause (a signature change) surfacing across many call sites, not 12 independent bugs.

## Reason for Change
Either the signature change to `check_all()` was landed without updating all callers/tests (a regression), or the tests reflect an older contract that production code has already moved past. Left unresolved, this is a widespread correctness/test-coverage gap around the tool-loop-guard safety mechanism (duplicate/cycle detection), which is a loop-prevention safety feature.

## Implementation Intent
Locate `ToolLoopGuard.check_all`'s current definition and determine whether `message` was newly added as required. If production call sites (e.g. `agent/orchestrator.py`) already pass `message` correctly, the fix is limited to updating the 12 affected tests to pass a `message` argument consistent with current usage. If a production call site is also missing the argument, treat that as the primary fix and update tests to match the corrected call site.

## Target Files or Areas
- `scripts/agent/tool_loop_guard.py` (or wherever `ToolLoopGuard.check_all` is defined — confirm exact path)
- `scripts/agent/orchestrator.py` (caller — confirm whether it already passes `message`)
- `tests/agent/test_tool_loop_guard.py`
- `tests/agent/test_orchestrator.py`
- `tests/integration/test_orchestrator_integration.py`
- `tests/integration/test_rag_llm_integration.py`
- `tests/integration/test_robustness_chaos.py`

## Required Changes
- Confirm `check_all()`'s current required signature via source read.
- Confirm whether any production caller is missing the new argument (real bug) vs. only tests being stale.
- Update whichever side (production caller or test) does not match the intended contract.

## Constraints
Do not change `check_all()`'s public contract further than necessary to fix the mismatch — preserve its existing detection semantics (dedup guard, cycle guard).

## Acceptance Criteria
- All 12 listed tests pass.
- If a production caller was also broken, confirm no behavior regression via the existing `test_tool_loop_guard.py` coverage.

## Testing Expectations
Run the 5 affected test files; run the full suite once after the fix to confirm no new regressions.

## Documentation Impact
N/A: unless the fix changes `check_all`'s public contract, in which case update its docstring/any doc referencing it (Needs confirmation once root cause is pinned down).

## Out of Scope
Other unrelated failing tests from the same full-suite run (tracked as separate issues), including `test_orchestrator.py`'s non-ToolLoopGuard failures (see agent008).

## Dependencies
May share a root cause with `agent008` (orchestrator workflow-engine `run` not invoked) since both are in `test_orchestrator.py` — investigate together if evidence suggests a shared cause, but keep as separate issues unless confirmed identical.

## Unresolved Questions
Needs confirmation: whether the missing `message` argument is a genuine production regression or purely a stale-test issue — requires reading `ToolLoopGuard.check_all`'s current source and every caller.

## AI Implementation Instruction
Read `ToolLoopGuard.check_all`'s current definition first. Do not guess the fix direction — confirm via source whether production already passes `message` correctly before deciding whether to fix tests or production code. Keep the change minimal and scoped to this signature mismatch only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_tool_loop_guard.py, tests/agent/test_orchestrator.py, tests/integration/test_orchestrator_integration.py, tests/integration/test_rag_llm_integration.py, tests/integration/test_robustness_chaos.py
