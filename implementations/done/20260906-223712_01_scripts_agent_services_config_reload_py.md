## Goal
Replace 46 FIELD_* constants with a ConfigFieldRegistry dataclass; eliminate dead `_collect_field_changes()` method and its orphaned constants; consolidate inline validator imports to module level; extract small helpers from large methods (`_apply_rag_tool_params`, `_collect_field_changes`, `_sync_services`); improve overall maintainability without changing behavior.

## Scope
- **In-Scope**: Replace 46 named FIELD_* constants with a dataclass-based field registry; consolidate duplicate field collection logic; extract small helpers from large methods; move validation imports to module level; ensure all existing tests pass after refactor.
- **Out-of-Scope**: Adding new configuration fields; changing the behavior of existing fields; modifying `ConfigReloadRequest` model or `ConfigReloadOutcome` schema; refactoring other files in the agent service layer; adding new runtime dependencies.

## Assumptions
- The registry should be a module-level singleton rather than instantiated per `ConfigReloadService` — this avoids unnecessary object creation on every config reload call.
- Field metadata should include default values for validation fallback — this allows the registry to serve as both a source of truth for field definitions and a validation configuration.
- There is no way to derive field mappings automatically from dataclass fields — manual registration is required because the hot-reloadable flag and validator function are domain-specific decisions not derivable from dataclass introspection.

## Design decisions
- Use a dataclass-based `ConfigFieldRegistry` instead of an Enum because each field requires additional metadata (section path, hot-reloadable flag, validator callable reference) that an Enum cannot express.
- Make the registry a module-level singleton to avoid repeated instantiation overhead during config reload operations.
- Keep `_apply_llm_prompt_params()` — verification found it is actively called from `_apply_rag_tool_params()` (line 376), unlike `_collect_field_changes()` which is dead code (its output is discarded at its only call site).
- Derive `_reload_section` field mappings from the registry instead of maintaining separate hardcoded lists.

## Alternatives considered
- Simple deletion of `_collect_field_changes()` without introducing a registry — rejected because the issue explicitly requests a registry-based approach to prevent future drift between field definitions and their usage sites.
- Using `typing.Literal` types for field names — insufficient because the registry must also carry section-path mapping, hot-reloadable flags, and validator references.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Define `ConfigFieldRegistry` dataclass with fields: `name: str`, `section_path: str`, `hot_reloadable: bool`, `validator_fn: Optional[Callable]`.
2. Create instances for each field, grouping by section (llm, rag, tool, approval, memory, mcp).
3. Rewrite `apply_config_dict()` to iterate over the registry once, collecting changes and applying them, eliminating `_collect_field_changes()` and `_apply_llm_prompt_params()`.
4. Apply changes using `dataclasses.replace()` per section, invoking validators from the registry.
5. Rewrite `_reload_*` methods to query the registry for field mappings instead of maintaining hardcoded lists.
6. Move all validation imports from inside methods to module level.
7. Break `_apply_rag_tool_params()` (108 lines) into smaller methods per section (LLM, RAG, Tool).
8. Update `_classify_mcp_server_changes()` docstring to reflect its role as the sole restart-required classifier.
9. Keep `_diff_mcp_server_config()` unchanged.

### Method
**Phase 1: Preparation — Define the ConfigFieldRegistry**
- Create `ConfigFieldRegistry` dataclass with fields: `name: str`, `section_path: str`, `hot_reloadable: bool`, `validator_fn: Optional[Callable]` (REQ-001; `scripts/agent/services/config_reload.py`).
- Create instances for each field, grouping by section (llm, rag, tool, approval, memory, mcp) (REQ-001; `scripts/agent/services/config_reload.py`).

**Phase 2: Core Logic — Eliminate dead code and rewrite methods**
- Rewrite `apply_config_dict()` to iterate over the registry, calling `_get_*` helpers and collecting changes into section-specific dicts (REQ-002; `scripts/agent/services/config_reload.py`).
- Apply changes using `dataclasses.replace()` per section, invoking validators from the registry (REQ-002; `scripts/agent/services/config_reload.py`).
- Remove `_collect_field_changes()` entirely (REQ-002; `scripts/agent/services/config_reload.py`).
- Keep `_apply_llm_prompt_params()` — it is actively called from `_apply_rag_tool_params()` (line 376), unlike `_collect_field_changes()` which is dead code (REQ-002; `scripts/agent/services/config_reload.py`).
- Rewrite `_reload_*` methods to query the registry for field mappings instead of maintaining hardcoded lists (REQ-003; `scripts/agent/services/config_reload.py`).
- Move all validation imports to module level (REQ-004; `scripts/agent/services/config_reload.py`).
- Break `_apply_rag_tool_params()` (108 lines) into smaller methods per section (LLM, RAG, Tool) (REQ-005; `scripts/agent/services/config_reload.py`).
- Update `_classify_mcp_server_changes()` docstring to reflect its role as the sole restart-required classifier (REQ-006; `scripts/agent/services/config_reload.py`).
- Keep `_diff_mcp_server_config()` unchanged (REQ-007; `scripts/agent/services/config_reload.py`).

### Details
**Phase 1: Preparation — Define the ConfigFieldRegistry**
1. Define the `ConfigFieldRegistry` dataclass:
   ```python
   @dataclass(frozen=True)
   class ConfigFieldRegistry:
       name: str
       section_path: str
       hot_reloadable: bool
       validator_fn: Optional[Callable[[Any], None]] = None
   
       @property
       def field_name(self) -> str:
           return self.name
   ```

2. Create module-level registry entries grouped by section:
   - LLM section: `FIELD_HTTP_TIMEOUT`, `FIELD_CONTEXT_TOKEN_LIMIT`, `FIELD_LLML_TEMPERATURE`, `FIELD_LLML_MAX_TOKENS`, `FIELD_LLML_URL`, `FIELD_LLML_MAX_RETRIES`, `FIELD_LLML_RETRY_BASE_DELAY`, `FIELD_SSE_HEARTBEAT_TIMEOUT`, `FIELD_SSE_MALFORMED_RETRY`, `FIELD_SSE_RECONNECT_MAX`, `FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT`, `FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK`
   - RAG section: `FIELD_EMBED_URL`, `FIELD_WEB_SEARCH_URL`, `FIELD_USE_REFINER`, `FIELD_REFINER_MAX_TOKENS`, `FIELD_REFINER_TIMEOUT`, `FIELD_REFINER_MAX_CHARS_PER_CHUNK`
   - Tool section: `FIELD_MAX_TOOL_TURNS`, `FIELD_TOOL_RESULT_MAX_LLM_CHARS`, `FIELD_SERIAL_TOOL_CALLS`, `FIELD_TOOL_DEFINITIONS_STRICT`, `FIELD_PLAN_BLOCKED_TOOLS`, `FIELD_SYSTEM_PROMPT_TOOL`, `FIELD_SYSTEM_PROMPTS`, `FIELD_TOOL_DEFINITIONS`
   - Approval section: `FIELD_APPROVAL_RISK_RULES`, `FIELD_APPROVAL_PROTECTED_PATHS`, `FIELD_APPROVAL_HIGH_RISK_BRANCHES`, `FIELD_APPROVAL_SHELL_SAFE_PREFIXES`, `FIELD_APPROVAL_RESOURCE_KEYS`, `FIELD_APPROVAL_DRY_RUN_TOOLS`, `FIELD_TOOL_SAFETY_TIERS`, `FIELD_ALLOWED_ROOT`, `FIELD_APPROVAL_GITHUB_ALLOWED_REPOS`, `FIELD_GITOPS_PUSH_BLOCKED`
   - Memory section: `FIELD_MEMORY_RETENTION_DAYS`, `FIELD_MEMORY_LOCAL_ONLY`
   - MCP section: `FIELD_SECURITY_PROFILE`, `FIELD_SECURITY_LOCKDOWN_ENABLED`

3. Create a module-level dictionary mapping field names to registry entries:
   ```python
   CONFIG_FIELD_REGISTRY: Mapping[str, ConfigFieldRegistry] = {
       entry.field_name: entry for entry in [
           # ... all field entries ...
       ]
   }
   ```

**Phase 2: Core Logic — Eliminate dead code and rewrite methods**
1. In `apply_config_dict()`, replace the call to `_collect_field_changes(new_cfg, {}, {}, {})` with iteration over `CONFIG_FIELD_REGISTRY`:
   ```python
   llm_changes: dict[str, Any] = {}
   rag_changes: dict[str, Any] = {}
   tool_changes: dict[str, Any] = {}
   
   for field_entry in CONFIG_FIELD_REGISTRY.values():
       value = new_cfg.get(field_entry.field_name)
       if value is None:
           continue
       
       # Use typed validators to coerce and validate the value
       # Collect into appropriate change dict based on section_path
       if field_entry.section_path.startswith("llm"):
           llm_changes[field_entry.field_name] = value
       elif field_entry.section_path.startswith("rag"):
           rag_changes[field_entry.field_name] = value
       else:
           tool_changes[field_entry.field_name] = value
   ```

2. After collecting changes, apply them using `dataclasses.replace()` per section, invoking validators from the registry:
   ```python
   if llm_changes:
       try:
           new_llm = dataclasses.replace(cfg.llm, **llm_changes)
       except ValueError as e:
           raise ConfigReloadValidationError(str(e)) from e
       
       # Re-validate after replacement using registry's validator_fn
       for field_entry in CONFIG_FIELD_REGISTRY.values():
           if field_entry.section_path == "llm" and field_entry.validator_fn:
               try:
                   field_entry.validator_fn(new_llm)
               except ValueError as e:
                   raise ConfigReloadValidationError(str(e)) from e
       cfg.llm = new_llm
   ```

3. Remove `_collect_field_changes()` method entirely.

4. Keep `_apply_llm_prompt_params()` — it is actively called from `_apply_rag_tool_params()` (line 376).

5. Rewrite `_reload_*` methods to query the registry for field mappings:
   ```python
   def _reload_approval_config(
       self,
       ctx: AgentContext,
       new_cfg: dict[str, Any],
   ) -> None:
       """Update ApprovalConfig fields in ctx.cfg when present in new_cfg."""
       field_mappings = [
           (entry.field_name, entry.field_name)
           for entry in CONFIG_FIELD_REGISTRY.values()
           if entry.section_path == "approval"
       ]
       self._reload_section(ctx, new_cfg, "approval", field_mappings)
   ```

6. Move all validation imports from inside methods to module level:
   ```python
   from agent.services.config_validators import (
       validate_llm_context_char_limit,
       validate_llm_context_token_limit,
       validate_llm_http_timeout,
       validate_llm_max_retries,
       validate_llm_max_tokens,
       validate_llm_retry_base_delay,
       validate_llm_sse_heartbeat_timeout,
       validate_llm_sse_malformed_retry,
       validate_llm_sse_reconnect_max,
       validate_llm_temperature,
       validate_rag_refiner_max_chars_per_chunk,
       validate_rag_refiner_max_tokens,
       validate_rag_refiner_timeout,
       validate_progress_stagnation_window,
       validate_tool_cycle_detect_window,
       validate_tool_dedup_max_repeats,
       validate_tool_error_max_consecutive,
       validate_tool_error_retry_max,
       validate_tool_max_tool_turns,
       validate_tool_result_max_llm_chars,
   )
   ```

7. Break `_apply_rag_tool_params()` (108 lines) into smaller methods per section (LLM, RAG, Tool):
   ```python
   def _apply_rag_tool_params(
       self,
       ctx: AgentContext,
       new_cfg: dict[str, Any],
   ) -> ConfigReloadOutcome:
       """Apply LLM/RAG/Tool settings with validation re-execution."""
       result = ConfigReloadOutcome()
       cfg = ctx.cfg
       
       llm_changes: dict[str, Any] = {}
       rag_changes: dict[str, Any] = {}
       tool_changes: dict[str, Any] = {}
       
       self._apply_llm_context_params(cfg, new_cfg, llm_changes)
       self._apply_tool_params(cfg, new_cfg, tool_changes)
       self._apply_rag_params(cfg, new_cfg, rag_changes)
       self._apply_llm_retry_params(cfg, new_cfg, llm_changes)
       self._apply_llm_prompt_params(
           ctx, new_cfg, llm_changes, rag_changes, tool_changes
       )
       self._apply_sse_reload_params(ctx, new_cfg, llm_changes)
       
       # Apply changes per section...
       return result
   ```

8. Update `_classify_mcp_server_changes()` docstring to reflect its role as the sole restart-required classifier.

9. Keep `_diff_mcp_server_config()` unchanged.

## Compatibility considerations
- The registry replaces 46 FIELD_* constants — all callers must use `CONFIG_FIELD_REGISTRY[name].field_name` instead of `FIELD_<NAME>`.
- The registry approach preserves parse-time typo-safety benefit of the original constants because field names are derived from the registry entries rather than raw strings.
- The registry should be a module-level singleton rather than instantiated per `ConfigReloadService` — this avoids unnecessary object creation on every config reload call.
- Field metadata should include default values for validation fallback — this allows the registry to serve as both a source of truth for field definitions and a validation configuration.

## Security considerations
- No security implications — this is a pure refactor that does not change behavior or introduce new dependencies.

## Rollback considerations
- If the registry approach introduces unexpected complexity, revert to simply deleting `_collect_field_changes()` without introducing the registry — this was the approach taken in the previous plan for issues/20260905-192444_refactor_config_reload_deduplicate_field_collection.md.
- All existing tests must pass without modification — if they fail, the implementation needs adjustment before proceeding.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit + Static | `uv run pytest tests/agent/services/test_config_reload.py -v`; `uv run vulture scripts/agent/services/config_reload.py --min-confidence 80`; `uv run ruff check`; `uv run mypy`; `uv run bandit` | All tests pass; no new dead-code/lint/type/security finding vs. this cycle's baseline |
| `scripts/agent/` (full) | Regression | `uv run pytest tests/agent/` | No new failure — confirms the six active _apply_*_params/four _reload_* methods' external behavior is unchanged |
| `tests/agent/services/test_config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload.py -v` | TestCollectFieldChangesConsolidation updated or removed; every other test class passes unmodified |

## Completion criteria
- Zero FIELD_* constants remain in the module — all field names come from the registry.
- `_collect_field_changes()` and `_apply_llm_prompt_params()` are removed.
- Each `_reload_*` method derives its field mappings from the registry.
- Validation imports are at module level, not inside methods.
- No method exceeds 80 lines (excluding blank lines and comments).
- `_classify_mcp_server_changes()` docstring reflects its role as the sole restart-required classifier.
- `_diff_mcp_server_config()` is unchanged.
- All existing tests pass without modification.

## Out of scope
- Adding new configuration fields.
- Changing the behavior of existing fields.
- Modifying `ConfigReloadRequest` model or `ConfigReloadOutcome` schema.
- Refactoring other files in the agent service layer.
- Adding new runtime dependencies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-007
- **Source issue**: issues/20260906-185627_refactor_config_reload.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-193422_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-223712
- **Related target files**: scripts/agent/services/config_reload.py
