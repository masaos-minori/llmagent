# Refactor scripts/agent/services/config_reload.py into smaller, testable units

## Priority
Medium

## Summary
Split `scripts/agent/services/config_reload.py` (481 lines) into focused modules: field registry definition, section-level reload logic, service sync, and outcome reporting. Reduce cyclomatic complexity and improve test isolation.

## Background
`config_reload.py` was consolidated from `_ConfigMixin._apply_*` helpers during the `/reload` command refactor. The consolidation replaced scattered private methods with a single `ConfigReloadService.apply_config_dict()` entry point. Since then, the file has grown to 481 lines with multiple responsibilities merged: CONFIG_FIELD_REGISTRY definition (147 lines), three section-level reload loops, service instance sync, MCP server change classification, startup-only/diagnostics-live classification, and ConfigReloadOutcome construction. The CONFIG_FIELD_REGISTRY itself contains 48 entries spread across 6 sections (llm, rag, tool, approval, memory, mcp), making it difficult to audit completeness against the actual config dataclasses.

## Problem
The file violates Single Responsibility Principle at two levels: (1) the module mixes schema definition (CONFIG_FIELD_REGISTRY) with runtime behavior (service sync, outcome classification); (2) `apply_config_dict()` handles section iteration, validator invocation, service propagation, and outcome assembly in one method with ~70 lines of control flow. This makes it impossible to test any single concern in isolation without mocking the entire service.

## Reason for Change
- CONFIG_FIELD_REGISTRY has 48 entries across 6 sections; adding/removing fields requires scrolling through an unstructured list with no cross-reference to config dataclass definitions
- `apply_config_dict()` has cyclomatic complexity exceeding 20 (multiple nested loops, conditional branches per section, validator try/catch blocks, outcome classification)
- Service sync (`_sync_services`) passes individual scalar parameters instead of typed config objects, creating silent drift risk when new LLM/RAG/tool config fields are added
- No unit tests exercise `_diff_mcp_server_config`, `_detect_diagnostics_live_fields`, or `_classify_startup_only_fields` independently
- Validator imports are duplicated: `config_validators.py` exports them, `config_dataclasses.py` imports them as `_v_*`, and `config_reload.py` re-imports them by full name

## Implementation Intent
Extract four concerns into separate modules/functions:

1. **Field registry**: Move CONFIG_FIELD_REGISTRY to its own module (`agent/services/config_field_registry.py`). Keep `ConfigFieldRegistry` dataclass there. Add a function `registry_for(section_path: str) -> Iterator[ConfigFieldRegistry]` to replace the current `section_path != section_path` filtering pattern.

2. **Section reload**: Replace the three `for section_path in ("llm", "rag", "tool")` loops + `_reload_section_fields()` calls with a single `reload_section(ctx, section_path, new_cfg)` function that returns `(applied: list[str], validated: bool, error: str | None)`. This isolates the section-level loop body.

3. **Service sync**: Replace `_sync_services()` parameter passing with typed config object access: `ctx.cfg.llm`, `ctx.cfg.rag`, `ctx.cfg.tool`. Remove the explicit `llm_service.apply_config(...)` / `hist_mgr_service.apply_config(...)` / `runtime_tools_service.apply_policy(...)` calls and delegate to a `ServiceSyncer` class that knows how to propagate each config section.

4. **Outcome classification**: Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, and `_detect_diagnostics_live_fields()` into standalone functions that take only their inputs (no `self._ctx` dependency) and return pure results. These can then be tested independently.

Keep `ConfigReloadService` as the thin orchestrator that composes these pieces. Keep `ConfigReloadOutcome` and `ConfigReloadValidationError` where they are.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` — primary refactor target
- `scripts/agent/services/config_field_registry.py` — new file for CONFIG_FIELD_REGISTRY
- `scripts/agent/services/config_section_reload.py` — new file for section-level reload logic
- `scripts/agent/services/config_service_sync.py` — new file for service sync
- `scripts/agent/services/config_outcome_classification.py` — new file for outcome classification
- `scripts/agent/services/config_validators.py` — no changes (validators stay here)
- `scripts/agent/services/models.py` — no changes (DTOs stay here)
- `tests/agent/services/test_config_reload*.py` — existing tests must still pass after refactor

## Required Changes
- Extract CONFIG_FIELD_REGISTRY and ConfigFieldRegistry to `config_field_registry.py`
- Add `registry_for(section_path)` generator to replace inline section filtering
- Split `apply_config_dict()` into section-by-section dispatch via extracted `reload_section()` function
- Replace `_sync_services()` scalar parameter passing with typed config access
- Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` as standalone functions
- Update `ConfigReloadService.__init__` to accept only `AgentContext` (remove service dependencies from constructor)
- Ensure all existing tests pass without modification (behavior-preserving refactor)
- Add unit tests for the four new standalone functions (minimum coverage)

## Constraints
- Behavior-preserving: public API (`ConfigReloadService.apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome`) must remain unchanged
- No changes to config dataclass schemas or validator functions
- No changes to `ConfigReloadRequest` DTO shape
- Must not introduce new circular imports (current lazy import of `_build_mcp_servers` inside `_classify_mcp_server_changes` must be preserved or resolved)
- Existing test fixtures in `tests/agent/services/test_config_reload*.py` must work without modification

## Acceptance Criteria
- [ ] CONFIG_FIELD_REGISTRY moved to `config_field_registry.py` with `registry_for()` accessor
- [ ] `apply_config_dict()` reduced to < 40 lines (from 70+)
- [ ] `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` are standalone functions accepting only their inputs
- [ ] `_sync_services()` uses typed config objects instead of scalar parameters
- [ ] All existing tests pass: `pytest tests/agent/services/test_config_reload*.py -q`
- [ ] New unit tests exist for the four standalone functions (minimum 1 test each)
- [ ] No new circular imports introduced
- [ ] `ruff check` and `mypy` pass on all modified/new files

## Testing Expectations
- Run existing test suite: `uv run pytest tests/agent/services/test_config_reload*.py -q`
- Run existing command-level tests: `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q`
- Add unit tests for each extracted standalone function
- Verify mypy passes: `uv run mypy scripts/agent/services/config_field_registry.py scripts/agent/services/config_section_reload.py scripts/agent/services/config_service_sync.py scripts/agent/services/config_outcome_classification.py`
- Verify ruff passes: `uv run ruff check scripts/agent/services/config_field_registry.py scripts/agent/services/config_section_reload.py scripts/agent/services/config_service_sync.py scripts/agent/services/config_outcome_classification.py`

## Documentation Impact
Update module docstrings in the four new files to describe responsibility boundaries. No external documentation updates needed — the public API surface is unchanged.

## Out of Scope
- Adding new config fields or validators
- Changing ConfigReloadRequest DTO shape
- Modifying config dataclass definitions
- Adding integration tests for the `/reload` command
- Changing ConfigReloadOutcome schema

## Dependencies
N/A: none

## Unresolved Questions
- Should `_build_mcp_servers` lazy import be moved to module level in the new classification module? Current approach avoids circular import but adds indirection.
- Should `ConfigReloadService` become stateless (no `self._ctx`)? Currently it needs ctx to access cfg and services — making it stateless would require passing both as arguments to every method.
- Is the current 4-module split sufficient, or should section-level reload logic be further split by domain (llm/rag/tool vs approval/memory/mcp)?

## AI Implementation Instruction
Do not rewrite unrelated files. Preserve the public API: `ConfigReloadService.apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome`, `ConfigReloadValidationError`. Each extracted module must have a clear responsibility boundary — do not create cross-cutting dependencies between the four new modules. Test after each extraction step, not just at the end. Stop and report if you find a circular import that cannot be resolved without changing the config dataclass layer.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-101458
- **Related target files**: scripts/agent/services/config_reload.py, scripts/agent/services/config_field_registry.py, scripts/agent/services/config_section_reload.py, scripts/agent/services/config_service_sync.py, scripts/agent/services/config_outcome_classification.py
