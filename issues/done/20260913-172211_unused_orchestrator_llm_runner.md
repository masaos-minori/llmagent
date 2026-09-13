# Unused Orchestrator._llm_runner and _guard fields

## Priority
Medium

## Summary
Remove the unused `Orchestrator._llm_runner` and `Orchestrator._guard` fields that were left behind during refactoring, eliminating dead code and preventing confusion about which `ToolLoopGuard` instance is authoritative.

## Background
During refactoring, `LLMTurnRunner` was extracted into `LlmTurnExecutor`, and the main execution path was updated to use `self._llm_executor.handle_llm_turn()` (orchestrator.py:283). However, the original `self._llm_runner` field and its associated `self._guard` (`ToolLoopGuard`) were not removed.

Evidence:
- `orchestrator.py:111`: `self._guard = ToolLoopGuard(ctx)` — created but never used
- `orchestrator.py:115-119`: `self._llm_runner = LLMTurnRunner(ctx, self._guard, ...)` — created but never called
- `orchestrator.py:283`: `await self._llm_executor.handle_llm_turn(...)` — actual execution path uses executor, not `_llm_runner`
- `rg` search for `_llm_runner` returns only one match (line 115), confirming it's never called

## Problem
1. **Dead code**: `Orchestrator._llm_runner` and `Orchestrator._guard` are never invoked, wasting memory and creating maintenance burden.
2. **Confusion about authority**: Having two `ToolLoopGuard` instances operating on the same `ctx` makes it unclear which guard is authoritative for dedup/cycle/retry checks.
3. **Inconsistent guard state**: If someone later tries to use `self._llm_runner`, they would get different guard behavior than the active path because the two `ToolLoopGuard` instances have separate `_empty_result_counts` dicts.

## Reason for Change
Dead code violates the principle of least surprise and increases maintenance cost. Removing these fields clarifies that `LlmTurnExecutor` is the sole owner of tool-loop guard logic for the current execution path.

## Implementation Intent
Remove `Orchestrator._guard` and `Orchestrator._llm_runner` fields entirely. Update `__init__` to stop creating them. No behavioral change expected since neither was ever called.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/orchestrator.py`

## Required Changes
- Remove `self._guard = ToolLoopGuard(ctx)` from `Orchestrator.__init__`
- Remove `self._llm_runner = LLMTurnRunner(ctx, self._guard, ...)` from `Orchestrator.__init__`
- Remove `from agent.tool_loop_guard import ToolLoopGuard` import if no longer needed
- Verify no other code references `Orchestrator._llm_runner` or `Orchestrator._guard`

## Constraints
- Must not break any existing callers that might access these fields (though none exist based on rg search)
- Must preserve backward compatibility for any test code that may reference these fields

## Acceptance Criteria
- `Orchestrator._llm_runner` and `Orchestrator._guard` are removed
- No regressions in turn execution (same behavior as before)
- No test failures from removing these fields

## Testing Expectations
- Unit test verifying `Orchestrator` still handles turns correctly after removal
- Verify no test code accesses `Orchestrator._llm_runner` or `Orchestrator._guard`
- Regression test for LLM turn execution through `LlmTurnExecutor`

## Documentation Impact
Update docstrings for `Orchestrator.__init__` to remove references to `_llm_runner` and `_guard`.

## Out of Scope
- Refactoring `LlmTurnExecutor` to share guard state across turns
- Adding new guard functionality

## Dependencies
N/A: none

## Unresolved Questions
- Are there any test files that directly access `Orchestrator._llm_runner` or `Orchestrator._guard`?
- Should the removal be done as a separate commit from other orchestrator changes?

## AI Implementation Instruction
Do not add any new functionality. Simply remove the unused `self._guard` and `self._llm_runner` assignments from `Orchestrator.__init__`. Verify no test code references these fields before committing.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-172211
- **Related target files**: scripts/agent/orchestrator.py
