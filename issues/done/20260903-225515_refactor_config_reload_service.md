# Refactor `scripts/agent/services/config_reload.py` to reduce duplication and improve testability

## Priority
Medium

## Summary
Refactor `scripts/agent/services/config_reload.py` to eliminate magic string constants, consolidate duplicate field-collection logic, introduce a configuration schema layer, and improve overall testability through dependency injection.

## Background
`config_reload.py` is the central service for applying reloaded configuration to live service instances. It was migrated from `_ConfigMixin._apply_config_params()` + scattered `_apply_*` helpers into a dedicated `ConfigReloadService` class. The migration introduced new infrastructure (`ConfigReloadOutcome`, typed validators), but left significant structural debt: ~50 magic string constants, duplicate field-collection logic across multiple methods, tight coupling to `AgentContext`, and a long `apply_config_dict()` method with unclear responsibility boundaries.

## Problem
The current implementation has five concrete problems:

1. **Magic string constants** — Lines 46-94 define `FIELD_*` constants that are used inconsistently. Some methods use raw string literals instead of these constants, creating inconsistency and maintenance risk.

2. **Duplicate field-collection logic** — `_collect_field_changes()` (lines 210-295) collects LLM/RAG/tool fields into separate dicts, while `_apply_llm_prompt_params()` (lines 539-573) collects overlapping fields again. The `_apply_*_params()` methods also duplicate field-name lookups that `_collect_field_changes()` already handles.

3. **Tight coupling to AgentContext** — Methods like `_apply_rag_tool_params()`, `_reload_approval_config()`, and `_detect_startup_only()` directly access `ctx.cfg.llm`, `ctx.cfg.rag`, `ctx.cfg.tool`, etc. This makes unit testing impossible without spinning up a full `AgentContext`.

4. **Long method with unclear boundaries** — `apply_config_dict()` (lines 173-207) orchestrates field collection, RAG/LLM/tool parameter application, approval config reload, tool allowlist reload, memory runtime reload, security profile reload, MCP server classification, service sync, and diagnostics detection — all in one method.

5. **Inconsistent validation** — Some config sections use typed validators (`typed_validators`) for extraction, while others use direct dict access. Validation after `dataclasses.replace()` is ad-hoc per section.

## Reason for Change
This refactor addresses maintainability, testability, and correctness risks. The magic string constants and duplicate field-collection logic make it easy to miss updating a field reference when adding new config options. The tight coupling to `AgentContext` prevents isolated unit testing of config-reload logic, which is essential for safe hot-reload behavior. The long method obscures which operations can run independently versus which must be sequenced.

## Implementation Intent
At a high level, the refactor should:

1. Replace magic string constants with a configuration schema/mapping layer that maps config keys to their target paths within `AgentConfig` dataclass hierarchies.
2. Consolidate field-collection logic into a single pass over the config schema, eliminating the overlap between `_collect_field_changes()` and `_apply_llm_prompt_params()`.
3. Introduce a `ConfigTarget` abstraction that encapsulates how to read/write a config value (source key, target path, validator, restart requirement). This decouples config-reload logic from `AgentContext` and enables unit testing.
4. Split `apply_config_dict()` into smaller, focused steps with clearer boundaries — e.g., validate-and-collect, apply-sections, classify-changes, sync-services.
5. Preserve all public behavior: `ConfigReloadOutcome` structure, `needs_restart` semantics, `startup_only` detection, `always_live` detection, and MCP server lifecycle cleanup.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- `scripts/agent/config_dataclasses.py` (for understanding config hierarchy)
- `scripts/agent/services/typed_validators.py` (validator functions)
- `scripts/agent/services/models.py` (ConfigReloadRequest)
- `scripts/agent/services/exceptions.py` (ConfigReloadValidationError)
- `tests/unit/test_config_reload*.py` (existing tests to verify against)

## Required Changes
- Remove the `FIELD_*` constant block (lines 46-94) and replace with a schema-driven approach.
- Merge `_collect_field_changes()` and `_apply_llm_prompt_params()` into a unified field-collection step driven by the schema.
- Create a `ConfigTarget` (or similar) dataclass that encodes: source key, target attribute path, type validator, whether it requires restart, and whether it takes effect immediately.
- Rewrite `apply_config_dict()` to iterate over targets, collecting changes, then applying them section by section.
- Extract `_apply_rag_tool_params()` into smaller section-specific methods: `_apply_llm_params()`, `_apply_rag_params()`, `_apply_tool_params()`.
- Inject config dependencies (e.g., `cfg` accessor) into `ConfigReloadService.__init__()` instead of requiring the full `AgentContext`.
- Ensure `_classify_mcp_server_changes()` remains unchanged (it is already clean).
- Keep `ConfigReloadOutcome` structure as-is; its design is sound.

## Constraints
- Must preserve all public API contracts: `apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome` fields, `ConfigReloadValidationError` exceptions.
- Must not change the semantics of `needs_restart`, `skipped`, `startup_only`, `always_live`, or `applied` lists.
- Must not alter MCP server lifecycle management (`cleanup_server_resources`).
- Must remain compatible with the existing `ConfigReloadRequest` model.
- All existing unit tests must continue to pass.

## Acceptance Criteria
- [ ] No `FIELD_*` magic string constants remain in `config_reload.py`.
- [ ] Field-collection logic exists in exactly one place, driven by a schema/mapping structure.
- [ ] `ConfigReloadService` can be instantiated and tested with a mock config object (no full `AgentContext` required).
- [ ] `apply_config_dict()` is split into at least 3 logically separated private methods.
- [ ] All existing unit tests pass without modification.
- [ ] Hot-reload behavior for each config section (LLM, RAG, Tool, Approval, Memory, Security, Diagnostics) is preserved.
- [ ] `ConfigReloadOutcome` reports are identical to pre-refactor output for the same inputs.

## Testing Expectations
- Run existing unit tests for `config_reload` module before and after refactor.
- Add unit tests for the new `ConfigTarget` abstraction and schema-driven collection.
- Verify that `ConfigReloadService` works with a minimal mock config (not full `AgentContext`).
- Regression test: ensure `needs_restart` list contains the same entries for MCP server changes.
- Integration test: verify end-to-end `/reload` flow with mixed config changes (hot-reloadable + restart-required).

## Documentation Impact
Update the module docstring to reflect the new schema-driven architecture. Document the `ConfigTarget` abstraction and its role in replacing magic constants. Update any inline comments that reference the old `_apply_*` helper naming convention.

## Out of Scope
- Adding new config fields or removing existing ones.
- Changing the `ConfigReloadRequest` model or its serialization.
- Modifying `AgentConfig` dataclass definitions.
- Refactoring other services' `apply_config()` methods (only `config_reload.py`).
- Changing the MCP server lifecycle management logic.
- Migrating to a different config format (YAML, TOML, etc.).

## Dependencies
N/A: none

## Unresolved Questions
- Should `ConfigTarget` be defined in `config_reload.py` or extracted to a shared module? Depends on whether other services need similar abstractions.
- How granular should the schema be — per-field granularity vs. per-section granularity? Per-field gives more flexibility but increases boilerplate.
- Is there a preference for using Python's `typing.Protocol` or plain dataclasses for the `ConfigTarget` abstraction?

## AI Implementation Instruction
When implementing this issue: do not rewrite unrelated files outside `config_reload.py` and its immediate test files. Keep changes minimal and incremental — refactor one section at a time (e.g., start with schema definition, then field collection, then apply logic). Preserve all public behavior: `ConfigReloadOutcome` structure, exception types, and `needs_restart` semantics must remain identical. Stop and report if you find that the `AgentConfig` dataclass structure prevents a clean schema-driven approach. Do not add new features or config fields during this refactor.
