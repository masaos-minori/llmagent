# Implementation Procedure: Refactor config_reload.py

## Goal

Refactor `scripts/agent/services/config_reload.py` to eliminate duplicate responsibility between `CONFIG_FIELD_REGISTRY.hot_reloadable` and `_detect_startup_only`, consolidate the four `_reload_*` thin wrappers into a single unified path, derive `_MCP_SERVER_FIELDS` from dataclass fields, and remove redundant `ConfigFieldRegistry.field_name` property. (REQ-001 through REQ-006)

## Scope

- Modify `scripts/agent/services/config_reload.py` and `tests/agent/services/test_config_reload_classification.py` only
- Eliminate `_detect_startup_only` manual classification
- Consolidate four `_reload_*` methods into one
- Derive `_MCP_SERVER_FIELDS` from dataclass
- Remove `ConfigFieldRegistry.field_name` property
- Preserve public behavior: no change to `apply_config`, `apply_config_dict`, `ConfigReloadOutcome`, or `ConfigReloadRequest` contracts

## Assumptions

- No caller outside `apply_config_dict` invokes the four `_reload_*` methods directly (confirmed by grep search showing no external callers)
- `ConfigReloadOutcome.startup_only` semantics are preserved: fields with `hot_reloadable=False` that differ between new and running cfg should still be reported there
- The lazy import of `_build_mcp_servers` in `_classify_mcp_server_changes` must be preserved to avoid circular imports
- `dataclasses.fields(McpServerConfig)` returns fields in declaration order, matching the previous hardcoded tuple order

## Design decisions

- **Hot-reload classification unification**: Use `CONFIG_FIELD_REGISTRY[entry.name].hot_reloadable == False` as the single source of truth. Fields with `hot_reloadable=False` that differ between new and running cfg are classified as startup-only via the registry lookup, eliminating the need for `_detect_startup_only`.
- **Method consolidation**: Single `_reload_section_fields(ctx, section_path, field_filter=None)` method. When `field_filter` is None, iterate all registry entries for the given section. When provided, apply the filter predicate to select which entries to process.
- **MCP server field derivation**: Derive from `McpServerConfig` dataclass using `tuple(f.name for f in dataclasses.fields(McpServerConfig))`. This ensures automatic drift prevention when `McpServerConfig` gains/removes fields.
- **ConfigFieldRegistry cleanup**: Remove the `field_name` property. All references updated to `.name`.

## Alternatives considered

- Keeping `_detect_startup_only` but having it delegate to `CONFIG_FIELD_REGISTRY` — rejected because it would still maintain two separate classification mechanisms; full elimination is cleaner.
- Always iterating the full registry in `_reload_section_fields` without a `field_filter` parameter — chosen as simpler approach; the caller can decide which section to reload.
- Using `dataclasses.asdict()` to compare MCP server configs instead of field-by-field comparison — rejected because `_diff_mcp_server_config` needs deterministic output order.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

**Phase 1: Preparation — Remove redundant items**

1. Remove `ConfigFieldRegistry.field_name` property (lines 62-64)
   - Delete the `@property` method and its `return self.name` body
   - Replace all `.field_name` accesses with `.name`:
     - Line 68: `CONFIG_FIELD_REGISTRY` dict comprehension key — `entry.field_name` → `entry.name`
     - Line 244: `value = new_cfg.get(field_entry.field_name)` → `value = new_cfg.get(field_entry.name)`
     - Line 245: `getattr(cfg, field_entry.field_name)` → `getattr(cfg, field_entry.name)`
     - Line 247: `changed_fields[field_entry.field_name] = value` → `changed_fields[field_entry.name] = value`
     - Line 262: `f"{section_path}.{field_entry.field_name}: {e}"` → `f"{section_path}.{field_entry.name}: {e}"`
     - Line 436: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
     - Line 449: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
     - Line 462: `(entry.field_name, entry.field_name)` → `(entry.name, entry.name)`
     - Line 477: `value = new_cfg.get(field_entry.field_name)` → `value = new_cfg.get(field_entry.name)`
     - Line 480: `if field_entry.field_name == "security_profile"` → `if field_entry.name == "security_profile"`
     - Line 484: `ctx.cfg.mcp.security_profile = SecurityProfile(value)` — unchanged
     - Line 487: `elif field_entry.field_name == "security_lockdown_enabled"` → `elif field_entry.name == "security_lockdown_enabled"`
   - REQ-004; File: scripts/agent/services/config_reload.py

2. Replace `_MCP_SERVER_FIELDS` hardcoded tuple with dataclass derivation
   - Delete lines 153-164 (`_MCP_SERVER_FIELDS = (...)`)
   - Add module-level constant after line 164:
     ```python
     _MCP_SERVER_FIELDS: tuple[str, ...] = tuple(
         f.name for f in dataclasses.fields(McpServerConfig)
     )
     ```
   - Verify field order matches previous hardcoded tuple: transport, url, startup_mode, call_timeout_sec, startup_timeout_sec, tool_names, auth_token, role, cmd, env
   - REQ-003; File: scripts/agent/services/config_reload.py

**Phase 2: Core Logic — Consolidate reload methods**

3. Replace four `_reload_*` methods with single `_reload_section_fields` method
   - Delete `_reload_approval_config` (lines 429-440)
   - Delete `_reload_tool_allowlist` (lines 442-453)
   - Delete `_reload_memory_runtime` (lines 455-466)
   - Delete `_reload_security_profile` (lines 468-488)
   - Add consolidated method:
     ```python
     def _reload_section_fields(
         self,
         ctx: AgentContext,
         section_path: str,
         field_filter: Callable[[ConfigFieldRegistry], bool] | None = None,
     ) -> None:
         """Apply field updates to a config section based on CONFIG_FIELD_REGISTRY.
         
        Args:
            ctx: AgentContext for accessing cfg
            section_path: Dot-separated path to the target section (e.g., "approval")
            field_filter: Optional callable that takes a ConfigFieldRegistry entry
                and returns True if the field should be processed. If None,
                processes all entries whose section_path matches.
        """
        parts = section_path.split(".")
        obj = ctx.cfg
        for part in parts:
            obj = getattr(obj, part)
        
        # Determine which entries to process
        entries_to_process = [
            entry for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == section_path
        ]
        if field_filter is not None:
            entries_to_process = [e for e in entries_to_process if field_filter(e)]
        
        for entry in entries_to_process:
            value = new_cfg.get(entry.name)
            if value is None:
                continue
            if isinstance(value, dict):
                setattr(obj, entry.name, dict(value))
            elif isinstance(value, list):
                setattr(obj, entry.name, list(value))
            else:
                setattr(obj, entry.name, value)
    ```
   - Wait — this method needs access to `new_cfg`. Looking at the current callers, they all pass `new_cfg` separately. The consolidated method signature should include `new_cfg`:
     ```python
     def _reload_section_fields(
         self,
         ctx: AgentContext,
         new_cfg: dict[str, Any],
         section_path: str,
         field_filter: Callable[[ConfigFieldRegistry], bool] | None = None,
     ) -> None:
     ```
   - Update `_reload_section` similarly to accept `new_cfg` as well (it currently receives `field_mappings` which was the old pattern). Actually, looking more carefully, `_reload_section` is only called by the four `_reload_*` methods. After consolidation, we can inline its logic into `_reload_section_fields` since the `field_mappings` pattern is eliminated.
   - REQ-002; File: scripts/agent/services/config_reload.py

4. Update callers in `apply_config_dict` to use the consolidated method
   - Replace line 266: `self._reload_approval_config(ctx, new_cfg)` → `self._reload_section_fields(ctx, new_cfg, "approval")`
   - Replace line 267: `self._reload_memory_runtime(ctx, new_cfg)` → `self._reload_section_fields(ctx, new_cfg, "memory")`
   - Replace line 268: `self._reload_security_profile(ctx, new_cfg)` → 
     ```python
     self._reload_section_fields(
         ctx, new_cfg, "mcp",
         field_filter=lambda e: e.name in ("security_profile", "security_lockdown_enabled")
     )
     ```
   - Also update the `allowed_tools` handling (line 271-272) — this is separate from `_reload_section_fields` because it has special list conversion logic. Keep it as-is since it's not a thin wrapper around `_reload_section`.
   - REQ-005; File: scripts/agent/services/config_reload.py

**Phase 3: Eliminate duplicate classification**

5. Remove `_detect_startup_only` method (lines 490-508)
   - Delete the entire method definition
   - REQ-001; File: scripts/agent/services/config_reload.py

6. Replace `_detect_startup_only` call site in `apply_config_dict` with registry-driven classification
   - Replace line 292: `outcome.startup_only = self._detect_startup_only(new_cfg)` with:
     ```python
     outcome.startup_only = self._classify_startup_only_fields(new_cfg)
     ```
   - Add new helper method:
     ```python
     def _classify_startup_only_fields(
         self,
         new_cfg: dict[str, Any],
     ) -> list[str]:
         """Return names of startup-only fields that differ between new_cfg and running cfg.
         
         Uses CONFIG_FIELD_REGISTRY.hot_reloadable as the single source of truth:
         fields with hot_reloadable=False that differ between new and running cfg
         are reported here.
         """
         changed: list[str] = []
         ctx = self._ctx
         for entry in CONFIG_FIELD_REGISTRY.values():
             if entry.hot_reloadable:
                 continue
             value = new_cfg.get(entry.name)
             if value is None:
                 continue
             current = getattr(getattr(ctx.cfg, entry.section_path), entry.name)
             if value != current:
                 changed.append(entry.name)
         return changed
     ```
   - REQ-001; File: scripts/agent/services/config_reload.py

### Method

Each phase above is independently verifiable. Phase 1 removes no-op properties and hardcodes. Phase 2 consolidates methods — this requires careful testing since callers may depend on specific behavior. Phase 3 eliminates duplicate classification.

### Details

**Phase 1 details:**
- `ConfigFieldRegistry.field_name` removal: The property adds no value beyond `self.name`. All 11 references across the file must be updated.
- `_MCP_SERVER_FIELDS` derivation: Must verify field order matches previous hardcoded tuple. Use `dataclasses.fields(McpServerConfig)` which returns fields in declaration order.

**Phase 2 details:**
- `_reload_section_fields` signature: `(self, ctx, new_cfg, section_path, field_filter=None)`
- When `field_filter` is None, iterate all registry entries for the given section
- When provided, apply the filter predicate to select which entries to process
- The `field_filter` parameter enables selective reloading (e.g., only `security_profile` and `security_lockdown_enabled` for MCP section)
- `_reload_section` can be removed entirely since its `field_mappings` pattern is eliminated

**Phase 3 details:**
- `_classify_startup_only_fields` replaces `_detect_startup_only`
- Uses `CONFIG_FIELD_REGISTRY[entry.name].hot_reloadable == False` as the single source of truth
- For each non-hot-reloadable field present in `new_cfg`, compare against running cfg value
- Report differing fields as startup-only

## Compatibility considerations

- **Public API**: All public method signatures preserved (`apply_config`, `apply_config_dict`). No change to `ConfigReloadOutcome` or `ConfigReloadRequest` contracts.
- **Internal API changes**: Four private methods (`_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile`) are removed and replaced with one (`_reload_section_fields`). Since these are private and have no external callers (confirmed by grep), this is safe.
- **`_detect_startup_only` removal**: Replaced by `_classify_startup_only_fields` with equivalent semantics — both report fields with `hot_reloadable=False` that differ between new and running cfg.
- **Injected component contracts**: Unchanged — `ConfigReloadService` still depends on `AgentContext` via constructor injection.

## Security considerations

- No new security surface introduced — refactoring does not add new external-facing APIs or change authentication/authorization boundaries
- `auth_token` remains restart-only by design: the derived `_MCP_SERVER_FIELDS` preserves `auth_token` in the tuple, so credential changes still require restart
- No changes to validation logic — validators remain unchanged

## Rollback considerations

- Each phase is independently revertible: revert the git commit for that phase
- Phase 2 (method consolidation) is the riskiest rollback scenario — if the consolidated method introduces behavioral differences, reverting requires restoring the four original methods
- Phase 3 (_detect_startup_only removal) is low-risk — the replacement method has identical semantics
- Test suite serves as the rollback safety net: if any phase's tests fail, revert that phase immediately

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/config_reload.py | Unit: verify _detect_startup_only removal, _reload_* consolidation, _MCP_SERVER_FIELDS derivation | uv run pytest tests/agent/services/test_config_reload_classification.py -v | All tests pass |
| scripts/agent/services/config_reload.py | Integration: verify ConfigReloadOutcome values match pre-refactor behavior | uv run pytest tests/agent/ -v --tb=short | All tests pass |
| scripts/agent/services/config_reload.py | Manual: verify hot_reloadable=False fields still classified as startup_only | Manual verification of ConfigReloadOutcome.startup_only | startup_only populated correctly |
| scripts/agent/services/config_reload.py | Static: verify no circular imports | python -c "import agent.services.config_reload" | Import succeeds |

## Completion criteria

- [ ] Phase 1 complete: `ConfigFieldRegistry.field_name` removed; all `.field_name` accesses replaced with `.name`; `_MCP_SERVER_FIELDS` derives from dataclass
- [ ] Phase 2 complete: Four `_reload_*` methods consolidated into one `_reload_section_fields`; callers updated accordingly
- [ ] Phase 3 complete: `_detect_startup_only` removed; `_classify_startup_only_fields` added with equivalent semantics; all tests pass
- [ ] All public method signatures preserved
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
| 1 | Phase 1: Preparation — Remove redundant items | Completed | 20260913-084038 | 20260913-084500 | REQ-003, REQ-004 |
| 2 | Phase 2: Core Logic — Consolidate reload methods | Completed | 20260913-084500 | 20260913-084600 | REQ-002, REQ-005 |
| 3 | Phase 3: Eliminate duplicate classification | Completed | 20260913-084600 | 20260913-084700 | REQ-001 |
| 4 | Update tests for removed methods | Completed | 20260913-084700 | 20260913-084800 | REQ-001, REQ-002 |
| 5 | Verification — run test suites and static checks | Completed | 20260913-084800 | 20260913-084900 | REQ-005, REQ-006 |

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
- **Generated at**: 20260913-084038
- **Related target files**: scripts/agent/services/config_reload.py
