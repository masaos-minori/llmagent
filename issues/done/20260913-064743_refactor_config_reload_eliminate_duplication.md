# Refactor config_reload.py: eliminate CONFIG_FIELD_REGISTRY duplication and consolidate reload paths

## Priority
Medium

## Summary
Refactor `scripts/agent/services/config_reload.py` to eliminate duplicate responsibility between `CONFIG_FIELD_REGISTRY.hot_reloadable` and `_detect_startup_only`, consolidate the four `_reload_*` thin wrappers into a single unified path, derive `_MCP_SERVER_FIELDS` from dataclass fields, and remove redundant `ConfigFieldRegistry.field_name` property.

## Background
`config_reload.py` manages live config propagation after a `/reload` command. It uses `CONFIG_FIELD_REGISTRY` (~70 entries) to drive validation and field updates across LLM/RAG/Tool sections. Each registry entry carries a `hot_reloadable` flag indicating whether the field takes effect immediately or requires a restart. However, `_detect_startup_only` re-implements this classification manually by checking individual field names against `_get_bool()` results, creating two sources of truth for the same classification.

The four methods `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, and `_reload_security_profile` are all thin wrappers around `_reload_section`, differing only in their `section_path` and `field_mappings` parameters. They add no behavioral differentiation beyond parameter selection.

`_MCP_SERVER_FIELDS` is a hardcoded tuple of field names used by `_diff_mcp_server_config` to compare old/new `McpServerConfig` instances. This should derive from the dataclass definition to avoid drift.

`ConfigFieldRegistry.field_name` simply returns `self.name`, adding no value.

## Problem
Two sources of truth for hot-reload classification cause maintenance risk: when a new field is added with `hot_reloadable=False`, developers must update both `CONFIG_FIELD_REGISTRY` and `_detect_startup_only`. The four `_reload_*` wrappers add verbosity without behavioral benefit. Hardcoded `_MCP_SERVER_FIELDS` risks drift from `McpServerConfig` changes.

## Reason for Change
- `CONFIG_FIELD_REGISTRY.hot_reloadable` and `_detect_startup_only` encode the same classification independently
- Adding a new config field requires updating two separate locations
- Four wrapper methods exist solely to pass different parameters to `_reload_section`
- `_MCP_SERVER_FIELDS` can become stale if `McpServerConfig` gains/removes fields
- `ConfigFieldRegistry.field_name` is a no-op alias for `name`

## Implementation Intent
1. **Eliminate `_detect_startup_only`'s manual classification**: Use `CONFIG_FIELD_REGISTRY` as the single source of truth. Fields with `hot_reloadable=False` that differ between new and running cfg should be classified via the registry, not re-checked individually.
2. **Consolidate `_reload_*` methods**: Replace the four thin wrappers with a single method that accepts `section_path` and optional `field_filter` predicate. The existing callers pass static lists derived from the registry — this can be replaced with a filter closure.
3. **Derive `_MCP_SERVER_FIELDS` from dataclass**: Use `dataclasses.fields(McpServerConfig)` instead of a hardcoded tuple.
4. **Remove `ConfigFieldRegistry.field_name`**: Replace all references with `.name`.
5. **Preserve public behavior**: No change to `apply_config`, `apply_config_dict`, `ConfigReloadOutcome`, or `ConfigReloadRequest` contracts.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- `scripts/shared/mcp_config.py` (for `_MCP_SERVER_FIELDS` derivation)
- `tests/agent/services/test_config_reload_classification.py` (existing test)

## Required Changes
- Remove `_detect_startup_only` method; replace its call site in `apply_config_dict` with a registry-driven classification using `CONFIG_FIELD_REGISTRY[entry.field_name].hot_reloadable == False`
- Merge `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile` into a single `_reload_section_fields(ctx, section_path, field_filter=None)` method
- Replace `_MCP_SERVER_FIELDS` tuple with `tuple(f.name for f in dataclasses.fields(McpServerConfig))`
- Remove `ConfigFieldRegistry.field_name` property; update all `.field_name` accesses to `.name`
- Update `apply_config_dict` to use the consolidated reload path
- Keep `ConfigReloadOutcome.startup_only` semantics unchanged (still reports startup-only fields)

## Constraints
- Public API contract (`apply_config`, `apply_config_dict`, `ConfigReloadOutcome`) must remain unchanged
- `ConfigReloadOutcome` field semantics (`applied`, `needs_restart`, `skipped`, `startup_only`, `always_live`) must preserve their current meaning
- No change to validation behavior — validators in `config_validators.py` are out of scope
- No change to `ConfigReloadRequest` model in `models.py`
- Must not introduce circular imports (the lazy import of `_build_mcp_servers` in `_classify_mcp_server_changes` must be preserved)

## Acceptance Criteria
- [ ] `_detect_startup_only` is removed and replaced with registry-driven classification
- [ ] Four `_reload_*` methods are consolidated into one
- [ ] `_MCP_SERVER_FIELDS` derives from `McpServerConfig` dataclass fields
- [ ] `ConfigFieldRegistry.field_name` property is removed; all references updated to `.name`
- [ ] Existing tests (`test_config_reload_classification.py`) still pass
- [ ] No change to `ConfigReloadOutcome` field semantics or values
- [ ] No new circular imports introduced

## Testing Expectations
- Run existing test suite: `uv run pytest tests/agent/services/test_config_reload_classification.py -v`
- Run full agent test suite: `uv run pytest tests/agent/ -v --tb=short`
- Verify `ConfigReloadOutcome` values match pre-refactor behavior for a representative reload scenario (e.g., changing `llm_temperature` + `security_lockdown_enabled`)

## Documentation Impact
No documentation files need updating. Internal code comments about `hot_reloadable` classification should be updated to reflect the single-source-of-truth design.

## Out of Scope
- Adding new config fields to `CONFIG_FIELD_REGISTRY`
- Modifying `config_validators.py` validation functions
- Changing `ConfigReloadRequest` model or `ConfigReloadValidationError` exception
- Refactoring `ConfigReloadService._sync_services` service propagation logic
- Adding new `ConfigReloadOutcome` fields
- Modifying `McpServerConfig` dataclass definition

## Dependencies
N/A: none

## Unresolved Questions
- Should `_reload_section_fields` accept a callable predicate on `ConfigFieldRegistry` entries, or should it always iterate the full registry and let the caller decide? (Decision needed before implementation)
- Is there any caller outside `apply_config_dict` that invokes the four `_reload_*` methods directly? If so, consolidation may require additional interface analysis.

## AI Implementation Instruction
Do not rewrite unrelated files. Preserve public behavior of `apply_config`, `apply_config_dict`, `ConfigReloadOutcome`, and `ConfigReloadRequest`. After each step, verify the existing test suite passes. Do not modify `config_validators.py`, `models.py`, or `McpServerConfig`. Stop and report if you find unexpected callers of the four `_reload_*` methods.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-064743
- **Related target files**: scripts/agent/services/config_reload.py, scripts/shared/mcp_config.py, tests/agent/services/test_config_reload_classification.py
