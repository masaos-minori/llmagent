# Implementation Procedure: Refactor config_reload.py — eliminate CONFIG_FIELD_REGISTRY duplication and consolidate reload paths

## Goal

Eliminate duplicate hot-reload classification between `CONFIG_FIELD_REGISTRY.hot_reloadable` and `_detect_startup_only`, consolidate four `_reload_*` thin wrappers into one method, derive `_MCP_SERVER_FIELDS` from `McpServerConfig` dataclass fields, and remove redundant `ConfigFieldRegistry.field_name` property.

## Scope

- Modify `scripts/agent/services/config_reload.py`: remove `_detect_startup_only`, consolidate `_reload_*` methods, derive `_MCP_SERVER_FIELDS`, remove `field_name` property
- No changes to public contracts: `apply_config`, `apply_config_dict`, `ConfigReloadOutcome`, `ConfigReloadRequest`, `ConfigReloadValidationError` remain unchanged

## Assumptions

- No caller outside `apply_config_dict` invokes the four `_reload_*` methods directly (confirmed by grep search showing no external callers)
- `ConfigReloadOutcome.startup_only` semantics are preserved: fields with `hot_reloadable=False` that differ between new and running cfg should still be reported there
- The lazy import of `_build_mcp_servers` in `_classify_mcp_server_changes` must be preserved to avoid circular imports

## Design decisions

- Use `CONFIG_FIELD_REGISTRY[entry.name].hot_reloadable == False` as the single source of truth for hot-reload classification, replacing `_detect_startup_only`'s manual field-name checks
- Replace four `_reload_*` methods with a single `_reload_section_fields(ctx, section_path, field_filter=None)` method; when `field_filter` is None, iterate all registry entries for the given section
- Derive `_MCP_SERVER_FIELDS` from `dataclasses.fields(McpServerConfig)` to prevent drift when `McpServerConfig` gains/removes fields
- Remove `ConfigFieldRegistry.field_name` property; replace all references with `.name`

## Alternatives considered

- Keep `_detect_startup_only` but have it read from `CONFIG_FIELD_REGISTRY` — rejected because it still creates a separate code path for the same classification logic
- Add a `section_entries()` helper to `CONFIG_FIELD_REGISTRY` instead of consolidating `_reload_*` — rejected because the consolidation eliminates unnecessary parameter-passing indirection
- Hardcode `_MCP_SERVER_FIELDS` order manually — rejected because it risks drift from `McpServerConfig` changes

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

#### Phase 1: Preparation — Remove redundant items

##### Method 1: Remove `ConfigFieldRegistry.field_name` property

Replace all `.field_name` accesses with `.name`.

###### Details

1. Remove lines 62-64 (`@property` block returning `self.name`)
2. Update line 68: `entry.field_name` → `entry.name`
3. Update line 244: `field_entry.field_name` → `field_entry.name`
4. Update line 245: `getattr(cfg, field_entry.field_name)` → `getattr(cfg, field_entry.name)`
5. Update line 247: `changed_fields[field_entry.field_name]` → `changed_fields[field_entry.name]`
6. Update line 262: `f"{section_path}.{field_entry.field_name}"` → `f"{section_path}.{field_entry.name}"`
7. Update line 436: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
8. Update line 449: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
9. Update line 451: `entry.field_name == "allowed_tools"` → `entry.name == "allowed_tools"`
10. Update line 462: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
11. Update line 477: `field_entry.field_name` → `field_entry.name`
12. Update line 480: `field_entry.field_name == "security_profile"` → `field_entry.name == "security_profile"`
13. Update line 487: `field_entry.field_name == "security_lockdown_enabled"` → `field_entry.name == "security_lockdown_enabled"`

##### Method 2: Derive `_MCP_SERVER_FIELDS` from dataclass

Replace hardcoded tuple with dynamic derivation.

###### Details

1. Remove lines 153-164 (`_MCP_SERVER_FIELDS` tuple definition)
2. After `import dataclasses`, add:
   ```python
   _MCP_SERVER_FIELDS = tuple(f.name for f in dataclasses.fields(McpServerConfig))
   ```
   This line goes after the `McpServerConfig` import (line 20) and before the first use of `_MCP_SERVER_FIELDS` in `_diff_mcp_server_config` (line 167). Since `McpServerConfig` is imported at module level, this can be evaluated at import time.

### Phase 2: Core Logic — Consolidate reload methods

##### Method 3: Merge four `_reload_*` methods into one

Replace `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile` with a single `_reload_section_fields` method.

###### Details

1. Replace the four methods (lines 429-488) with:
   ```python
   def _reload_section_fields(
       self,
       ctx: AgentContext,
       section_path: str,
       field_filter: Callable[[ConfigFieldRegistry], bool] | None = None,
   ) -> None:
       """Apply a batch of field updates to a config section.

       Args:
           ctx: AgentContext for accessing cfg
           section_path: Dot-separated path to the target section (e.g., "approval")
           field_filter: Optional predicate on ConfigFieldRegistry entries.
               When None, iterate all entries for the given section_path.
       """
       parts = section_path.split(".")
       obj = ctx.cfg
       for part in parts:
           obj = getattr(obj, part)
       for field_entry in CONFIG_FIELD_REGISTRY.values():
           if field_entry.section_path != section_path:
               continue
           if field_filter is not None and not field_filter(field_entry):
               continue
           # Special handling for security_profile and security_lockdown_enabled
           if field_entry.name == "security_profile":
               value = new_cfg.get(field_entry.name)
               if value is None:
                   continue
               try:
                   from shared.mcp_config import SecurityProfile
                   obj.security_profile = SecurityProfile(value)
               except ValueError:
                   pass
           elif field_entry.name == "security_lockdown_enabled":
               value = new_cfg.get(field_entry.name)
               if value is None:
                   continue
               obj.security_lockdown_enabled = bool(value)
           else:
               value = new_cfg.get(field_entry.name)
               if value is None:
                   continue
               if isinstance(value, dict):
                   setattr(obj, field_entry.name, dict(value))
               elif isinstance(value, list):
                   setattr(obj, field_entry.name, list(value))
               else:
                   setattr(obj, field_entry.name, value)
   ```
   Note: `new_cfg` must be captured from the caller context. Since `_reload_section_fields` is called from `apply_config_dict`, we need to pass `new_cfg` as an additional parameter or capture it via closure. The simplest approach: add `new_cfg` as a parameter to `_reload_section_fields`.

2. Update callers in `apply_config_dict`:
   - Line 266: `self._reload_approval_config(ctx, new_cfg)` → `self._reload_section_fields(ctx, "approval", new_cfg)`
   - Line 267: `self._reload_memory_runtime(ctx, new_cfg)` → `self._reload_section_fields(ctx, "memory", new_cfg)`
   - Lines 268-269: `self._reload_security_profile(ctx, new_cfg)` → `self._reload_section_fields(ctx, "mcp", new_cfg)`
   - For `_reload_tool_allowlist`: since it filters on `entry.field_name == "allowed_tools"`, update to:
     ```python
     self._reload_section_fields(ctx, "tool", lambda e: e.name == "allowed_tools", new_cfg)
     ```

Wait — the above signature doesn't work cleanly. Let me revise:

```python
def _reload_section_fields(
    self,
    ctx: AgentContext,
    section_path: str,
    field_filter: Callable[[ConfigFieldRegistry], bool] | None = None,
    new_cfg: dict[str, Any] | None = None,
) -> None:
```

Callers:
- `self._reload_section_fields(ctx, "approval", new_cfg=new_cfg)`
- `self._reload_section_fields(ctx, "memory", new_cfg=new_cfg)`
- `self._reload_section_fields(ctx, "mcp", new_cfg=new_cfg)`
- `self._reload_section_fields(ctx, "tool", field_filter=lambda e: e.name == "allowed_tools", new_cfg=new_cfg)`

### Phase 3: Eliminate duplicate classification

##### Method 4: Remove `_detect_startup_only` and replace its call site

###### Details

1. Remove lines 490-508 (`_detect_startup_only` method)
2. In `apply_config_dict`, replace line 292:
   ```python
   outcome.startup_only = self._detect_startup_only(new_cfg)
   ```
   with:
   ```python
   outcome.startup_only = self._classify_startup_only(new_cfg)
   ```
3. Add new `_classify_startup_only` method:
   ```python
   def _classify_startup_only(
       self,
       new_cfg: dict[str, Any],
   ) -> list[str]:
       """Return names of startup-only fields that differ between new_cfg and running cfg.

       Uses CONFIG_FIELD_REGISTRY as the single source of truth for
       hot-reload classification: fields with hot_reloadable=False that
       differ between new and running cfg are classified as startup-only.
       """
       changed: list[str] = []
       ctx = self._ctx
       for field_entry in CONFIG_FIELD_REGISTRY.values():
           if field_entry.hot_reloadable:
               continue
           value = new_cfg.get(field_entry.name)
           if value is None:
               continue
           current = getattr(getattr(ctx.cfg, field_entry.section_path), field_entry.name, None)
           if value != current:
               changed.append(field_entry.name)
       return changed
   ```

## Compatibility considerations

- Public contracts unchanged: `apply_config`, `apply_config_dict`, `ConfigReloadOutcome`, `ConfigReloadRequest`, `ConfigReloadValidationError` remain identical
- `ConfigReloadOutcome.startup_only` semantics preserved: fields with `hot_reloadable=False` that differ between new and running cfg are still reported there
- No API surface change for callers of `ConfigReloadService`

## Security considerations

- No security impact: no new secrets, credentials, or access patterns introduced
- `auth_token` restart-only behavior preserved (it remains in `_MCP_SERVER_FIELDS` derived from dataclass)

## Rollback considerations

- If `_detect_startup_only` removal breaks `startup_only` semantics, revert to registry-driven classification with manual verification
- If consolidated `_reload_section_fields` introduces unexpected side effects, restore individual `_reload_*` methods
- If deriving `_MCP_SERVER_FIELDS` changes comparison semantics, restore hardcoded tuple temporarily

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/config_reload.py | Unit: verify _detect_startup_only removal, _reload_* consolidation, _MCP_SERVER_FIELDS derivation | uv run pytest tests/agent/services/test_config_reload_classification.py -v | All tests pass |
| scripts/agent/services/config_reload.py | Integration: verify ConfigReloadOutcome values match pre-refactor behavior | uv run pytest tests/agent/ -v --tb=short | All tests pass |
| scripts/agent/services/config_reload.py | Manual: verify hot_reloadable=False fields still classified as startup_only | Manual verification of ConfigReloadOutcome.startup_only | startup_only populated correctly |
| scripts/agent/services/config_reload.py | Static: verify no circular imports | python -c "import agent.services.config_reload" | Import succeeds |

## Completion criteria

- [ ] `ConfigFieldRegistry.field_name` property removed; all `.field_name` accesses replaced with `.name`
- [ ] `_MCP_SERVER_FIELDS` derives from `dataclasses.fields(McpServerConfig)`; no hardcoded tuple
- [ ] Four `_reload_*` methods consolidated into one `_reload_section_fields` method; callers updated accordingly
- [ ] `_detect_startup_only` method removed; `startup_only` classification driven by `CONFIG_FIELD_REGISTRY[entry.name].hot_reloadable == False`
- [ ] `apply_config_dict` uses the consolidated reload path; no behavioral regression
- [ ] `ConfigReloadOutcome.startup_only` semantics unchanged
- [ ] Existing tests (`test_config_reload_classification.py`) still pass
- [ ] No circular imports introduced

## Out of scope

- Adding new config fields to `CONFIG_FIELD_REGISTRY`
- Modifying `config_validators.py` validation functions
- Changing `ConfigReloadRequest` model or `ConfigReloadValidationError` exception
- Refactoring `ConfigReloadService._sync_services` service propagation logic
- Adding new `ConfigReloadOutcome` fields
- Modifying `McpServerConfig` dataclass definition

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — Remove redundant items | Pending | — | — | REQ-003, REQ-004 |
| 2 | Phase 2: Core Logic — Consolidate reload methods | Pending | — | — | REQ-002, REQ-005 |
| 3 | Phase 3: Eliminate duplicate classification | Pending | — | — | REQ-001 |
| 4 | Update tests per Validation plan | Pending | — | — | REQ-001, REQ-002 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-005, REQ-006 |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation files need updating |

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
- **Requirement ID**: REQ-001 through REQ-006
- **Source issue**: issues/20260913-064743_refactor_config_reload_eliminate_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-070431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-072938
- **Related target files**: scripts/agent/services/config_reload.py
