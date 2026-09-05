# Refactor config_reload.py: eliminate duplicate field collection and consolidate validation

## Priority
Medium

## Summary
Refactor `scripts/agent/services/config_reload.py` to eliminate duplicate field-collection logic, reduce magic-string constant sprawl, and consolidate inline validator imports into a single validation pass per config section.

## Background
`config_reload.py` was migrated from `_ConfigMixin` methods into a new `ConfigReloadService`. During migration, field-collection logic was duplicated across two entry points: `_collect_field_changes()` (used by `apply_config()`) and `_apply_llm_prompt_params()` (used by `_apply_rag_tool_params()`). Both methods iterate over the same set of config keys and populate the same change dicts with nearly identical code. Additionally, the file defines ~50 magic string constants (lines 45-94) that duplicate field names already present in the dataclasses, creating a fragile mapping layer. Validation imports are also duplicated inside each `_apply_*_params` method, leading to repeated `from agent.services.config_validators import (...)` blocks.

## Problem
1. **Duplicate field collection**: `_collect_field_changes()` and `_apply_llm_prompt_params()` share ~80% identical logic for collecting LLM/RAG/tool/SSE fields into change dicts. Any new field added to one must be manually mirrored in the other.
2. **Magic string constant sprawl**: 50+ constants map raw dict keys to dataclass attribute names. New fields require adding a constant AND updating every usage site.
3. **Inconsistent key references**: Some code paths use constants (e.g., `FIELD_CONTEXT_TOKEN_LIMIT`), others use raw strings (e.g., `"context_char_limit"`), causing subtle bugs when a field name is updated in one place but not the other.
4. **Repeated validator imports**: Each `_apply_*_params` method imports validators inline, bloating the file and making it hard to see the full validation surface.

## Reason for Change
- Maintenance risk: adding a new config field requires changes in 3+ locations (constant, `_collect_field_changes`, `_apply_llm_prompt_params`, possibly `_apply_*_params`).
- Bug surface: inconsistent key references cause silent misconfiguration during hot-reload.
- Readability: the file is 753 lines with heavy nesting and scattered concern boundaries.

## Implementation Intent
1. Replace magic string constants with a centralized field-key registry that maps dataclass attribute names to their raw dict keys. Use this registry as the single source of truth for both collection and application.
2. Consolidate `_collect_field_changes()` and `_apply_llm_prompt_params()` into a single field-collection function that populates change dicts once, then delegates to existing `_apply_*_params` methods.
3. Move validator imports to module-level and batch-validate after applying changes, reducing the number of inline import blocks.
4. Keep `ConfigReloadOutcome` structure unchanged — it serves a clear reporting purpose.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- `scripts/agent/services/config_validators.py` (validator import consolidation)
- `scripts/agent/services/models.py` (ConfigReloadRequest — verify field mappings)
- `scripts/agent/config_dataclasses.py` (verify attribute names match raw dict keys)

## Required Changes
- Create a module-level `FieldKeyRegistry` (dict or enum-based mapping) that maps dataclass attribute names → raw dict keys. Remove the 50+ magic string constants.
- Merge `_collect_field_changes()` and `_apply_llm_prompt_params()` into a single `_collect_changes()` function that uses the registry to populate `llm_changes`, `rag_changes`, and `tool_changes` dicts.
- Update `apply_config()` to call `_collect_changes()` instead of `_collect_field_changes()`.
- Move all validator imports to module level in `config_reload.py`.
- After each section's changes dict is populated, apply changes via `dataclasses.replace()` and run batched validation in a single try/except block per section.
- Ensure all callers of field-access patterns use the registry consistently (no raw strings).

## Constraints
- Must preserve public API: `apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome` fields, and all return types.
- Must preserve behavior: same fields applied live vs. restart-required, same validation errors raised.
- Must not change `ConfigReloadRequest` model or its serialization contract.
- MCP server diff logic (`_diff_mcp_server_config`, `_classify_mcp_server_changes`) is correct as-is; do not modify.

## Acceptance Criteria
- [ ] No magic string constants remain for config field names in `config_reload.py`
- [ ] `_collect_field_changes()` and `_apply_llm_prompt_params()` are consolidated into a single function
- [ ] All validator imports are at module level (no inline `from ... import` inside methods)
- [ ] All field access uses the centralized registry — no raw string literals for known fields
- [ ] Public APIs (`apply_config`, `apply_config_dict`, `ConfigReloadOutcome`) unchanged
- [ ] Hot-reload behavior preserved: same fields applied immediately, same fields require restart
- [ ] Existing tests pass without modification

## Testing Expectations
- Run existing test suite for `config_reload.py` and related modules
- Verify unit tests covering `_diff_mcp_server_config` still pass
- Add regression tests for any newly consolidated field-collection paths
- Type check with `mypy` on the modified file
- Lint check with project lint tool

## Documentation Impact
Update docstrings for the consolidated `_collect_changes()` function to explain its dual role (collection + delegation). Update `ConfigReloadService.__init__` docstring if responsibility description needs adjustment.

## Out of Scope
- Restructuring `ConfigReloadOutcome` dataclass
- Modifying `ConfigReloadRequest` model
- Changing MCP server lifecycle management (`_classify_mcp_server_changes`, cleanup calls)
- Adding new config fields
- Modifying `config_validators.py` logic (only import placement)
- Refactoring `AgentContext` or service interfaces

## Dependencies
- N/A: none

## Unresolved Questions
- Should the field-key registry be an `Enum` (for type safety) or a plain `dict` (for flexibility)? Enum would prevent typos but adds verbosity. Dict is simpler but allows runtime errors.
- Can `_get_bool`, `_get_int`, etc. typed validators be moved to a shared location outside `typed_validators.py`? They are currently imported from there but used only in this file.
- Is `_collect_field_changes()` still referenced anywhere besides `apply_config()`? Need to confirm no external callers before removing it.

## AI Implementation Instruction
1. Do NOT rewrite unrelated files. Focus only on `config_reload.py` and import adjustments in `config_validators.py`.
2. Preserve all public APIs and return types exactly as they are.
3. When consolidating field collection, ensure the merged function handles ALL fields currently covered by BOTH `_collect_field_changes()` and `_apply_llm_prompt_params()`.
4. After changes, run `uv run pytest` on affected test files and verify no regressions.
5. Stop and report if you find evidence that `_collect_field_changes()` has external callers beyond `apply_config()`.
