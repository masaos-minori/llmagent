# Refactor config_reload.py: unify duplicate logic and consolidate validation

## Priority
Medium

## Summary
Consolidate duplicated configuration reload logic in `scripts/agent/services/config_reload.py` and establish a single, consistent pattern for field iteration, validation, and service syncing.

## Background
`ConfigReloadService` was introduced to replace `_ConfigMixin._apply_config_params()` and its `_apply_*` helpers. The migration produced two parallel implementations: `apply_config_dict()` (new) and `_apply_rag_tool_params()` (old). Both exist simultaneously and implement nearly identical logic — iterating CONFIG_FIELD_REGISTRY, grouping by section, applying dataclasses.replace(), and running validators.

## Problem
The file contains two parallel implementations of the same core algorithm, leading to:
- Duplicated iteration/validation logic between `apply_config_dict()` and `_apply_rag_tool_params()`
- Inconsistent validation approaches: `apply_config_dict()` uses `field_entry.validator_fn` from the registry, while `_apply_rag_tool_params()` hardcodes individual validator function calls
- Fragile section-specific branches (`if section == "llm"` / `"rag"` / `"tool"`) that must be updated manually when new sections are added
- Unclear ownership: callers may invoke either method, risking inconsistent behavior

## Reason for Change
The dual implementation increases maintenance burden and risk of divergence. Adding a new config section requires updating both paths. The inconsistent validation approach means the two methods may behave differently under edge cases. A single unified path eliminates these risks.

## Implementation Intent
Establish one canonical flow for config reload:
1. Define a reusable helper that iterates CONFIG_FIELD_REGISTRY, collects changes per section, applies dataclasses.replace(), and runs validators — using the registry's `validator_fn` consistently
2. Eliminate `_apply_rag_tool_params()` entirely; its callers should use `apply_config_dict()` instead
3. Extract section update logic into a private method like `_update_section(cfg, section_path, changes)` to remove inline section branching from `apply_config_dict()`
4. Keep the existing public API surface (`apply_config`, `apply_config_dict`) unchanged for backward compatibility

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- Callers of `_apply_rag_tool_params()` (identify via grep)
- Related tests for config reload

## Required Changes
- Create a private helper `_update_section(ctx, section_path, changes)` that handles dataclasses.replace + registry-driven validation for a single section
- Refactor `apply_config_dict()` to use `_update_section()` instead of inline section branches
- Remove `_apply_rag_tool_params()` method and all references to it
- Ensure all validation uses `field_entry.validator_fn` from CONFIG_FIELD_REGISTRY (no hardcoded validator calls)
- Update any callers of `_apply_rag_tool_params()` to use `apply_config_dict()` instead
- Preserve the existing return type (`ConfigReloadOutcome`) and public method signatures

## Constraints
- Do not change the public API contract: `apply_config(req: ConfigReloadRequest) -> ConfigReloadOutcome` and `apply_config_dict(new_cfg: dict[str, Any]) -> ConfigReloadOutcome` must continue to work identically
- `ConfigReloadOutcome` fields (`applied`, `needs_restart`, `skipped`, `source_files`, `startup_only`, `always_live`) must retain their semantics
- `_diff_mcp_server_config()` and `CONFIG_FIELD_REGISTRY` must remain unchanged
- `ConfigReloadValidationError` must still be raised on validation failures
- No behavioral changes to how MCP server changes, approval config, memory runtime, security profile, or diagnostics live fields are handled

## Acceptance Criteria
- [ ] `_apply_rag_tool_params()` is removed and no longer referenced anywhere
- [ ] `apply_config_dict()` uses a single `_update_section()` helper for LLM/RAG/tool section updates instead of inline branches
- [ ] All validation in the consolidated path uses `field_entry.validator_fn` from CONFIG_FIELD_REGISTRY
- [ ] Existing tests pass without modification
- [ ] No regression in `ConfigReloadOutcome` report contents for any section

## Testing Expectations
- Run existing unit tests for `ConfigReloadService` and ensure they pass
- Verify `apply_config_dict()` produces identical `ConfigReloadOutcome` as before for each section (llm, rag, tool)
- Add regression test confirming `_apply_rag_tool_params()` is no longer accessible
- Type check the modified file
- Lint check the modified file

## Documentation Impact
Update the module docstring to reflect the new internal structure (single canonical flow via `_update_section`). No user-facing documentation changes required.

## Out of Scope
- Adding new config fields or sections
- Changing the CONFIG_FIELD_REGISTRY schema
- Modifying MCP server lifecycle management
- Changing ConfigReloadOutcome semantics
- Refactoring other services' apply_config interfaces

## Dependencies
N/A: none

## Unresolved Questions
- Are there external callers outside this repository that depend on `_apply_rag_tool_params()`? If so, deprecation strategy needed.
- Should `_update_section()` also handle the special cases currently done inline after section updates (e.g., `ctx.conv.system_prompt_content`, `ctx.cfg.tool.allowed_tools`)? Currently those are handled separately in `apply_config_dict()`.

## AI Implementation Instruction
Do not rewrite unrelated files. Keep changes minimal and focused on consolidating the two parallel implementations into one. Preserve all public method signatures and ConfigReloadOutcome semantics. Before removing `_apply_rag_tool_params()`, confirm no external callers exist. Use the registry's `validator_fn` consistently — do not introduce hardcoded validator calls. After changes, run existing tests and type check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-214628
- **Related target files**: scripts/agent/services/config_reload.py
