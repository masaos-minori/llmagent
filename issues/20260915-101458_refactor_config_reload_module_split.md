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

2. **Section reload**: `config_section_reload.py` holds two separate functions, not one — **resolved this revision, see Unresolved Questions**: the current code already implements two distinct algorithms under "section reload," and collapsing them into a single function would hide that difference rather than isolate it.
   - `reload_validated_section(ctx, section_path, new_cfg) -> (applied: list[str], validated: bool, error: str | None)`: replaces the three `for section_path in ("llm", "rag", "tool")` loop bodies — `dataclasses.replace()` + validator-function invocation + whole-section `setattr`.
   - `reload_direct_fields(ctx, new_cfg, section_path, field_filter=None) -> None`: the existing `_reload_section_fields()`, renamed and moved as-is — per-field direct `setattr`, no validation. Used for approval/memory/mcp.

3. **Service sync**: Replace `_sync_services()` parameter passing with typed config object access: `ctx.cfg.llm`, `ctx.cfg.rag`, `ctx.cfg.tool`. Remove the explicit `llm_service.apply_config(...)` / `hist_mgr_service.apply_config(...)` / `runtime_tools_service.apply_policy(...)` calls and delegate to a `ServiceSyncer` class that knows how to propagate each config section.

4. **Outcome classification**: Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, and `_detect_diagnostics_live_fields()` into standalone functions that take only their inputs (no `self._ctx` dependency) and return pure results. These can then be tested independently. `_classify_mcp_server_changes()` is a partial precedent, not a finished template — **corrected this revision**: it already avoids `self._ctx` in favor of an explicit `ctx` argument, but it still receives the whole `ctx` object rather than the specific values it needs (e.g. `ctx.cfg.mcp.mcp_servers`). Use it only for the "no `self._ctx`" half of the pattern; go one step further for all three functions and accept the narrowest inputs each one actually uses (see Unresolved Questions). Import `_build_mcp_servers` at module level from `shared.mcp_config` directly (not `agent.config_builders`, which only re-exports it) — **resolved this revision, see Unresolved Questions**; verified no circular import results.

Keep `ConfigReloadService` as the thin orchestrator that composes these pieces — it keeps holding `self._ctx` (see Unresolved Questions: a fully stateless service is not achievable without breaking the Constraints' public-API guarantee). Keep `ConfigReloadOutcome` and `ConfigReloadValidationError` where they are.

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
- Split `apply_config_dict()` into section-by-section dispatch via extracted `reload_validated_section()` (llm/rag/tool) and `reload_direct_fields()` (approval/memory/mcp) functions — see Implementation Intent #2
- Replace `_sync_services()` scalar parameter passing with typed config access
- Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` as standalone functions, each taking only the specific values it needs (not `ctx` or `self._ctx` wholesale) — `_classify_mcp_server_changes()`'s existing explicit-`ctx`-argument style is only a partial precedent (it still takes the whole `ctx`, not narrowed values); go further than it for all three
- Import `_build_mcp_servers` at module level in `config_outcome_classification.py`, from `shared.mcp_config` (its actual definition), not `agent.config_builders`
- Update the 3 `unittest.mock.patch("agent.config_builders._build_mcp_servers", ...)` call sites in `tests/agent/services/test_config_reload.py` (currently at lines 301, 725, 879) to patch the new import location instead — required by the module-level import change above; see Constraints
- Update `ConfigReloadService.__init__` to accept only `AgentContext` (remove service dependencies from constructor)
- Ensure all existing tests pass, with the 3 `unittest.mock.patch`-target updates above as the only permitted modification (behavior-preserving refactor otherwise)
- Add unit tests for the four new standalone functions (minimum coverage)

## Constraints
- Behavior-preserving: public API (`ConfigReloadService.apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome`) must remain unchanged
- No changes to config dataclass schemas or validator functions
- No changes to `ConfigReloadRequest` DTO shape
- ~~Must not introduce new circular imports (current lazy import of `_build_mcp_servers` inside `_classify_mcp_server_changes` must be preserved or resolved)~~ **Resolved this revision**: moved to a module-level import from `shared.mcp_config` in `config_outcome_classification.py`. Verified by temporarily patching and running `import agent`, `import agent.repl`, `import agent.commands.cmd_config`, `import agent.services.config_reload` — no circular import in any case.
- Existing test fixtures in `tests/agent/services/test_config_reload*.py` must work without modification — **known exception, confirmed necessary**: the 3 `unittest.mock.patch("agent.config_builders._build_mcp_servers", ...)` sites (lines 301, 725, 879) must be repointed to the new import location, because a module-level `from ... import` binds the function locally and no longer observes patches to the origin module's attribute. No other test file or assertion needs to change.

## Acceptance Criteria
- [ ] CONFIG_FIELD_REGISTRY moved to `config_field_registry.py` with `registry_for()` accessor
- [ ] `apply_config_dict()` reduced to < 40 lines (from 70+)
- [ ] `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` are standalone functions accepting only their inputs
- [ ] `_sync_services()` uses typed config objects instead of scalar parameters
- [ ] `reload_validated_section()` and `reload_direct_fields()` exist as two distinct functions in `config_section_reload.py` (not merged into one)
- [ ] `_build_mcp_servers` is imported at module level in `config_outcome_classification.py`, from `shared.mcp_config`
- [ ] The 3 `unittest.mock.patch` call sites in `tests/agent/services/test_config_reload.py` are repointed to the new import location — this is the only permitted test-file modification
- [ ] All existing tests pass: `pytest tests/agent/services/test_config_reload*.py -q`
- [ ] New unit tests exist for the four standalone functions (minimum 1 test each)
- [ ] No new circular imports introduced (re-verify with the actual final module layout, not just this issue's own verification)
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
All three questions below are resolved as of this revision; each entry keeps the original question (struck through) for history alongside its resolution.

- ~~Should `_build_mcp_servers` lazy import be moved to module level in the new classification module?~~ **Resolved: yes, move to module level, importing from `shared.mcp_config` directly (not `agent.config_builders`).** Verified by temporarily patching `config_reload.py` and running `import agent`, `import agent.repl`, `import agent.commands.cmd_config`, `import agent.services.config_reload` — no circular import occurred in any case; the original "avoids circular import at module level" comment no longer reflects the current codebase and should not be carried into the new module. `_build_mcp_servers`'s actual definition lives in `shared/mcp_config.py:244` — `agent/config_builders.py` only re-exports it (`# noqa: F401 — used by config_reload.py (lazy import)`), and `config_reload.py` already imports `McpServerConfig` from `shared.mcp_config` at module level, so importing `_build_mcp_servers` from the same module is more direct than going through `agent.config_builders`.
  **Caveat found during verification**: moving the import to module level breaks 7 existing tests in `tests/agent/services/test_config_reload.py` (lines 301, 725, 879), which `unittest.mock.patch("agent.config_builders._build_mcp_servers", ...)` — a module-level `from ... import _build_mcp_servers` binds the function locally at import time, so patching the origin module's attribute afterward has no effect. This is now a **known, required exception** to the Constraints section's "Existing test fixtures ... must work without modification": these three `unittest.mock.patch` targets must be updated to patch wherever `_build_mcp_servers` is imported into (the new `config_outcome_classification.py`, or `shared.mcp_config` directly) instead of `agent.config_builders`. No other test changes are needed.

- ~~Should `ConfigReloadService` become stateless (no `self._ctx`)?~~ **Resolved: no, keep `ConfigReloadService` holding `self._ctx`; make the four extracted modules' functions stateless instead.** The Constraints section fixes `ConfigReloadService.apply_config()`/`apply_config_dict()`'s public signatures, which in turn fixes `__init__(ctx)` storing `self._ctx` — a fully stateless service is not achievable without breaking that constraint. The existing code is already inconsistent here: `_classify_mcp_server_changes()` and `_reload_section_fields()` already take `ctx` as an explicit argument (not `self._ctx`), while `_sync_services()`, `_classify_startup_only_fields()`, and `_detect_diagnostics_live_fields()` reach into `self._ctx` directly. Recommendation: keep `ConfigReloadService` as the thin orchestrator holding `self._ctx` (per the Design Intent's own framing), and make every function in the four new modules accept only the specific values they need (e.g. `ctx.cfg.llm`, not `ctx`) rather than reaching into a context object. **Correction (found via independent verification)**: `_classify_mcp_server_changes()` is not a full example of this end state — it already avoids `self._ctx`, but it still takes the whole `ctx` object as its argument rather than a narrowed value. Treat it as a partial precedent for "explicit argument over `self._ctx`" only; the narrowed-inputs goal itself needs to be applied fresh to all three functions, `_classify_mcp_server_changes()` included. This satisfies the Acceptance Criteria's "standalone functions accepting only their inputs" without requiring the orchestrator itself to become stateless.

- ~~Is the current 4-module split sufficient, or should section-level reload logic be further split by domain?~~ **Resolved: keep the 4-module split; do not split further by domain.** Current code already contains two distinct algorithms under "section reload": llm/rag/tool sections use `dataclasses.replace()` + validator-function invocation + whole-section `setattr`, while approval/memory/mcp sections use `_reload_section_fields()`'s per-field direct `setattr` with no validation. Splitting `config_section_reload.py` further by domain (e.g. into 5-6 files) would fragment this concern past the point of clarity and works against the Acceptance Criteria's "no cross-cutting dependencies between the four new modules." Recommendation: keep both algorithms in `config_section_reload.py` as two clearly separate, named functions — `reload_validated_section(ctx, section_path, new_cfg)` (llm/rag/tool, dataclasses.replace + validate) and `reload_direct_fields(ctx, new_cfg, section_path, field_filter=None)` (approval/memory/mcp, the existing `_reload_section_fields()` renamed) — rather than one function trying to cover both, and rather than separate files per domain.

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
