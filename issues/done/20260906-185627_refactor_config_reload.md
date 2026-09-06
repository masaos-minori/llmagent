# Refactor config_reload.py: eliminate FIELD_* constants, consolidate field collection, reduce method sizes

## Priority
Medium

## Summary
Refactor `scripts/agent/services/config_reload.py` to replace 46 named FIELD_* constants with a dataclass-based field registry, consolidate duplicate field collection logic, extract small helpers from large methods, and improve overall maintainability without changing behavior.

## Background
The file has grown organically through multiple feature additions. It currently contains:
- 46 named FIELD_* constants (lines 46-91) used as dictionary keys throughout the module
- Duplicate field collection logic between `_collect_field_changes()` and `_apply_llm_prompt_params()`
- Hardcoded field mapping lists passed to `_reload_section()`
- Validation imports inside methods (can be moved to module level without circular dependency concerns)
- Inconsistent field naming (some use FIELD_* constants, others use raw strings)
- One method exceeding 100 lines (`_apply_rag_tool_params`: 109 lines), two methods exceeding 50 lines (`_collect_field_changes`: 83 lines, `_sync_services`: 51 lines)

This pattern makes it easy to introduce bugs when adding new fields (forgetting to update all locations) and difficult to audit which fields are hot-reloadable vs restart-required.

## Problem
The current structure creates three concrete problems:
1. **Duplication risk**: Adding a new configuration field requires updating multiple scattered locations (FIELD_* constant, `_collect_field_changes`, `_apply_*_params`, validation imports, and potentially `_reload_section` mappings). Missing one location silently breaks reload behavior.
2. **Audit difficulty**: It is impossible to determine which fields are hot-reloadable vs restart-required by reading the code; the distinction is only visible by tracing through each `_apply_*` method.
3. **Method size**: One method exceeds 100 lines (`_apply_rag_tool_params`: 109 lines), two exceed 50 lines (`_collect_field_changes`: 83 lines, `_sync_services`: 51 lines), making them hard to review and test independently.

## Reason for Change
The file has accumulated technical debt through incremental changes. A refactor now prevents future bugs and reduces the cost of adding new configuration fields.

## Implementation Intent
1. Replace FIELD_* constants with a dataclass-based field registry or enum that maps field names to their metadata (section, hot-reloadable flag, validator function).
2. Consolidate field collection into a single pass using the registry, eliminating `_collect_field_changes` and `_apply_llm_prompt_params`.
3. Derive `_reload_section` field mappings from the registry instead of maintaining separate hardcoded lists.
4. Move validation imports to module level (no circular dependency with `config_validators.py`).
5. Extract small helpers from large methods (`_apply_rag_tool_params`, `_collect_field_changes`, `_sync_services`) into focused private methods.
6. Ensure all existing tests pass after the refactor.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- `scripts/agent/services/config_validators.py` (validator references)
- `tests/agent/test_config_reload.py` (existing tests must still pass)

## Required Changes
- Remove all 46 FIELD_* constants (lines 46-91)
- Create a `ConfigFieldRegistry` class or dataclass that stores:
  - field name → section path mapping
  - field name → hot-reloadable flag
  - field name → validator callable reference
- Rewrite `apply_config_dict()` to iterate over the registry once, collecting changes and applying them
- Eliminate `_collect_field_changes()` and `_apply_llm_prompt_params()` entirely
- Rewrite `_reload_approval_config()`, `_reload_tool_allowlist()`, `_reload_memory_runtime()`, `_reload_security_profile()` to derive mappings from the registry
- Move validation imports from inside methods to module level (no circular dependency concern)
- Break `_apply_rag_tool_params()` (109 lines) into smaller methods per section (LLM, RAG, Tool)
- Update `_classify_mcp_server_changes()` docstring to reflect its role as the sole restart-required classifier
- Keep `_diff_mcp_server_config()` unchanged (already well-structured)

## Constraints
- Must not change any external API or behavior — `apply_config()` and `apply_config_dict()` signatures and return types must remain identical
- `ConfigReloadOutcome` fields (`applied`, `needs_restart`, `skipped`, `source_files`, `startup_only`, `always_live`) must retain their current semantics
- MCP server definition handling (restart-only by design) must not change
- All existing tests must pass without modification
- No new runtime dependencies may be added

## Acceptance Criteria
- [ ] Zero FIELD_* constants remain in the module — all field names come from the registry
- [ ] `_collect_field_changes()` and `_apply_llm_prompt_params()` are removed
- [ ] Validation imports are at module level, not inside methods
- [ ] Each `_reload_*` method derives its field mappings from the registry
- [ ] No method exceeds 80 lines (excluding blank lines and comments)
- [ ] All existing tests pass without modification
- [ ] Type hints are improved where possible (remove unnecessary `cast()` calls)

## Testing Expectations
- Run existing test suite: `uv run pytest tests/agent/test_config_reload.py`
- Verify no behavioral regression by comparing output of `/reload` command before and after refactor
- Add mutation testing coverage for edge cases: missing fields, invalid values, empty dicts

## Documentation Impact
- Update module docstring to describe the new registry-based approach
- Document the hot-reloadable vs restart-required classification criteria in `ConfigReloadOutcome` docstrings

## Out of Scope
- Adding new configuration fields
- Changing the behavior of existing fields
- Modifying `ConfigReloadRequest` model or `ConfigReloadOutcome` schema
- Refactoring other files in the agent service layer

## Dependencies
N/A: none

## Unresolved Questions
- Should the registry be a module-level singleton or instantiated per `ConfigReloadService`?
- Should field metadata include default values for validation fallback?
- Is there a way to derive field mappings automatically from dataclass fields rather than manual registration?

## AI Implementation Instruction
1. Read `scripts/agent/services/config_reload.py` and identify all 46 FIELD_* constants.
2. Design a `ConfigFieldRegistry` dataclass with fields: `name: str`, `section_path: str`, `hot_reloadable: bool`, `validator_fn: Optional[Callable]`.
3. Create instances for each field, grouping by section (llm, rag, tool, approval, memory, mcp).
4. Rewrite `apply_config_dict()` to iterate over the registry, calling `_get_*` helpers and collecting changes into section-specific dicts.
5. Apply changes using `dataclasses.replace()` per section, invoking validators from the registry.
6. Remove `_collect_field_changes()`, `_apply_llm_prompt_params()`, and all individual `_apply_*_params()` methods.
7. Rewrite `_reload_*` methods to query the registry for field mappings instead of maintaining hardcoded lists.
8. Move all validation imports to module level (no circular dependency concern).
9. Run `uv run pytest tests/agent/test_config_reload.py` to verify no regression.
10. Ensure no method exceeds 80 lines after refactor.
