## Goal

Unify duplicated configuration reload logic in `scripts/agent/services/config_reload.py` by eliminating `_apply_rag_tool_params()` and establishing a single canonical flow via `apply_config_dict()`, reducing code duplication and inconsistent validation approaches (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

- Remove `_apply_rag_tool_params()` method and all dead-code references to it
- Add `_update_section(ctx, section_path, changes)` helper for dataclasses.replace + registry-driven validation
- Refactor `apply_config_dict()` to use `_update_section()` instead of inline section branches
- Ensure all validation uses `field_entry.validator_fn` from CONFIG_FIELD_REGISTRY

## Assumptions

- `_apply_rag_tool_params()` has zero external callers — confirmed by repository evidence
- Tests in `test_agent_cmd_config.py` exercise `apply_config_dict()` but not `_apply_rag_tool_params()`
- The existing public API contract (`apply_config`, `apply_config_dict`) must remain unchanged for backward compatibility
- `CONFIG_FIELD_REGISTRY` entries have `section_path`, `validator_fn`, and other attributes needed by the consolidation

## Design decisions

- `_update_section()` extracts the common pattern shared by both methods: iterate CONFIG_FIELD_REGISTRY values for a given section, collect changes, apply dataclasses.replace(), run validators via `field_entry.validator_fn`, assign result back to `cfg.section`
- `apply_config_dict()` already uses the more maintainable registry-driven validation approach (`field_entry.validator_fn`), while `_apply_rag_tool_params()` uses hardcoded validator calls — the former becomes the canonical implementation
- Keep the existing public API surface (`apply_config`, `apply_config_dict`) unchanged for backward compatibility
- Preserve `"not_loaded"` → `"not loaded"` mapping semantics where applicable

## Alternatives considered

- Deprecating `_apply_rag_tool_params()` before removing — rejected; confirmed zero external callers, so removal is safe without deprecation period
- Consolidating into a single monolithic method — rejected; extracting `_update_section()` keeps the refactoring incremental and testable per-section

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Read `scripts/agent/services/config_validators.py` to understand validator function signatures used by CONFIG_FIELD_REGISTRY entries
2. Read `scripts/agent/services/models.py` to understand ConfigReloadRequest and ConfigReloadOutcome types
3. Read `scripts/agent/services/exceptions.py` to understand ConfigReloadValidationError contract
4. Read `scripts/agent/config_dataclasses.py` to understand AgentConfig dataclass structure for dataclasses.replace() usage
5. Verify `_apply_rag_tool_params()` has zero external callers across the entire repository (rg search)
6. Implement `_update_section(self, ctx, section_path, changes)` helper:
   - Iterate CONFIG_FIELD_REGISTRY values matching `section_path`
   - Collect changed fields into a dict
   - Apply dataclasses.replace(cfg, **changes)
   - Run validators via `field_entry.validator_fn` on the replaced config
   - Return the updated config and any errors
7. Refactor `apply_config_dict()` to call `_update_section()` for each section (llm, rag, tool) instead of inline section branches
8. Remove `_apply_rag_tool_params()` method entirely
9. Remove `_apply_llm_context_params()`, `_apply_tool_params()`, `_apply_rag_params()`, `_apply_llm_retry_params()`, `_apply_llm_prompt_params()`, `_apply_sse_reload_params()` helpers if they are exclusively called by `_apply_rag_tool_params()`

### Method

Current `apply_config_dict()` structure (simplified):
```python
def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
    outcome = ConfigReloadOutcome()
    # Inline section branches for llm, rag, tool...
    if section == "llm":
        # ... validate and replace llm config
    elif section == "rag":
        # ... validate and replace rag config
    elif section == "tool":
        # ... validate and replace tool config
    return outcome
```

After change:
```python
def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
    outcome = ConfigReloadOutcome()
    for section_path in ("llm", "rag", "tool"):
        try:
            cfg = getattr(self._ctx.cfg, section_path)
            new_section = getattr(new_cfg.get(section_path, {}), section_path, {})
            updated_cfg = self._update_section(self._ctx, section_path, new_section)
            setattr(self._ctx.cfg, section_path, updated_cfg)
        except ConfigReloadValidationError as e:
            outcome.errors.append(e)
    return outcome

def _update_section(self, ctx, section_path, changes) -> Any:
    """Update a single config section using registry-driven validation."""
    cfg = getattr(ctx.cfg, section_path)
    changed_fields = {}
    for field_entry in CONFIG_FIELD_REGISTRY.values():
        if field_entry.section_path != section_path:
            continue
        value = changes.get(field_entry.key)
        if value is None or value == getattr(cfg, field_entry.key):
            continue
        # Validate the new value
        if field_entry.validator_fn:
            try:
                field_entry.validator_fn(value)
            except ConfigReloadValidationError as e:
                raise ConfigReloadValidationError(f"{section_path}.{field_entry.key}: {e}")
        changed_fields[field_entry.key] = value
    if changed_fields:
        cfg = dataclasses.replace(cfg, **changed_fields)
    return cfg
```

### Details

- Read `scripts/agent/services/config_validators.py` to confirm validator function signatures match the expected `(value) -> None` contract
- Confirm `ConfigReloadValidationError` can be raised with descriptive messages
- The `_update_section()` method iterates CONFIG_FIELD_REGISTRY once per section, collecting only changed fields
- Validators are applied before applying changes (fail-fast)
- `dataclasses.replace()` creates a new instance with changed fields, preserving immutability

## Compatibility considerations

- Public API (`apply_config`, `apply_config_dict`) remains unchanged — backward compatible
- `ConfigReloadOutcome` return type preserved — no caller needs updating
- Existing tests in `test_agent_cmd_config.py` should pass without modification since behavior is identical
- The `"not_loaded"` → `"not loaded"` mapping is preserved where applicable

## Security considerations

- No new security risks introduced — same validation logic moved to a shared path
- Registry-driven validation (`field_entry.validator_fn`) is the preferred approach over hardcoded validators (reduces risk of missing validation in one path but not another)

## Rollback considerations

- Revert: restore `_apply_rag_tool_params()` and its helper methods, revert `apply_config_dict()` to inline section branches
- Safe rollback path: the old code paths are simpler and well-tested

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `apply_config_dict()` behavior unchanged | Unit — verify ConfigReloadOutcome matches | `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` | All existing tests pass |
| `_apply_rag_tool_params()` inaccessible | Regression — hasattr check | Python: `hasattr(ConfigReloadService, '_apply_rag_tool_params')` | Returns False |
| Type check | Static analysis | `uv run mypy scripts/agent/services/config_reload.py` | Zero type errors |
| Lint check | Style enforcement | `uv run ruff check scripts/agent/services/config_reload.py` | Zero lint errors |

## Completion criteria

- `_apply_rag_tool_params()` removed and no longer referenced anywhere
- `apply_config_dict()` uses `_update_section()` helper for all section updates
- All validation uses `field_entry.validator_fn` from CONFIG_FIELD_REGISTRY
- Existing tests pass without modification
- No regression in `ConfigReloadOutcome` report contents for any section

## Out of scope

- Adding new config fields or sections
- Changing CONFIG_FIELD_REGISTRY schema
- Modifying MCP server lifecycle management
- Changing ConfigReloadOutcome semantics
- Refactoring other services' apply_config interfaces
- Adding new public APIs

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify _apply_rag_tool_params() has zero external callers | Pending | — | — | |
| 2 | Implement _update_section() helper | Pending | — | — | |
| 3 | Refactor apply_config_dict() to use _update_section() | Pending | — | — | |
| 4 | Remove _apply_rag_tool_params() and dead helpers | Pending | — | — | |
| 5 | Run tests, type check, lint check | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260911-214628_refactor_config_reload_unify_duplicate_logic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-222031_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-083239
- **Related target files**: scripts/agent/services/config_reload.py
