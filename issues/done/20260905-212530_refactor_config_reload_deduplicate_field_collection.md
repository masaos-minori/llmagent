# Refactor config_reload.py: Remove dead code and consolidate overlapping field collection

## Priority
Medium

## Summary
Remove `_collect_field_changes()` which is dead code, and address structural overlap between the six helper methods inside `_apply_rag_tool_params()` and downstream direct calls to `_apply_llm_prompt_params()` and `_apply_sse_reload_params()`.

## Background
Prior investigation identified concerns about potential duplication between `_collect_field_changes()` and `_apply_rag_tool_params()`. However, deeper trace-throughs revealed the actual situation differs from initial assumptions: `_collect_field_changes()` is entirely dead code (its results are never consumed), while `_apply_rag_tool_params()` creates independent local dicts and operates separately.

A prior plan at `plans/done/20260825-142225_plan.md` also documented similar concerns about these functions.

## Problem
1. `_collect_field_changes()` is dead code: line 180 passes empty dicts `{}` as arguments and neither return value is consumed anywhere in `apply_config_dict()` (lines 173-207).
2. Structural overlap exists: the six helpers inside `_apply_rag_tool_params()` independently populate local dicts (`llm_changes`, `rag_changes`, `tool_changes`), but downstream callers directly invoke `_apply_llm_prompt_params()` and `_apply_sse_reload_params()` on those same fields, creating inconsistent handling paths.
3. Magic string constants (e.g., `FIELD_CONTEXT_TOKEN_LIMIT`) serve as aliases for raw strings used inconsistently across callers — not duplicates but confusing indirection.

## Reason for Change
Dead code increases maintenance burden and misleads future developers about the module's architecture. The structural overlap between `_apply_rag_tool_params()`'s internal helpers and downstream direct calls creates confusion about which path handles which configuration fields.

## Implementation Intent
1. Remove `_collect_field_changes()` and all references to it (including its test coverage).
2. Consolidate the six helper methods inside `_apply_rag_tool_params()` into a single unified handler or clarify the boundary between internal vs. downstream field handling.
3. Evaluate whether magic string constants can be removed in favor of consistent raw string usage.
4. Update validator import consolidation if verified against actual inline imports within conditional blocks.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/services/config_reload.py`
- `/home/sugimoto/llmagent/tests/agent/services/test_config_reload.py`
- `/home/sugimoto/llmagent/scripts/agent/services/config_validators.py`

## Required Changes
- Remove `_collect_field_changes()` function definition and all call sites
- Remove test assertions referencing `_collect_field_changes()`
- Consolidate or document the boundary between `_apply_rag_tool_params()` internal helpers and downstream `_apply_llm_prompt_params()` / `_apply_sse_reload_params()` calls
- Evaluate removal of magic string constant aliases (e.g., `FIELD_CONTEXT_TOKEN_LIMIT`)
- Verify and update validator import consolidation claims against actual inline imports

## Constraints
- Must preserve existing runtime behavior after removing dead code
- Cannot change public API contracts of remaining functions
- Must maintain backward compatibility with any external consumers of `config_reload.py`

## Acceptance Criteria
- `_collect_field_changes()` no longer exists in the codebase
- No test failures related to removed dead code
- Clear documentation of which configuration fields are handled by which code path
- All existing functionality preserved after refactoring

## Testing Expectations
- Run full test suite: `uv run pytest`
- Verify no regressions in config reload behavior
- Confirm removed dead code had no hidden side effects

## Documentation Impact
Update module docstring and any inline comments referencing `_collect_field_changes()`. Document the clarified responsibility boundary between `_apply_rag_tool_params()` and downstream handlers.

## Out of Scope
- Changes to configuration schema definitions
- Changes to validation logic itself
- Changes to other modules depending on `config_reload.py`

## Dependencies
- Prior plan: `plans/done/20260825-142225_plan.md`
- Existing issue: `issues/20260905-192444_refactor_config_reload_deduplicate_field_collection.md` (contains false premise about consolidating those two functions)

## Unresolved Questions
- Should the six helpers inside `_apply_rag_tool_params()` be merged into a single method, or should their responsibilities be explicitly documented as separate concerns?
- Can magic string constants be safely removed without breaking external consumers?
- Are there any undocumented side effects of `_collect_field_changes()` that were relied upon indirectly?

## AI Implementation Instruction
Remove `_collect_field_changes()` first (dead code), then address structural overlap between `_apply_rag_tool_params()` internal helpers and downstream direct calls. Do NOT attempt to consolidate `_collect_field_changes()` with `_apply_rag_tool_params()` — they operate on different data structures and have different purposes (the former collects changes for comparison, the latter applies them).
