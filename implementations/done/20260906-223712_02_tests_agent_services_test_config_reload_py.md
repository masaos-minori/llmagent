## Goal
Update tests to match new registry-based API; remove `TestCollectFieldChangesConsolidation` class if it only exercises `_collect_field_changes`.

## Scope
- **In-Scope**: Update tests to match new registry-based API; remove `TestCollectFieldChangesConsolidation` class if it only exercises `_collect_field_changes`.
- **Out-of-Scope**: Adding new test cases beyond what the current test suite covers; changing test assertions for existing functionality that remains unchanged.

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
`tests/agent/services/test_config_reload.py`

### Procedure
1. Remove `TestCollectFieldChangesConsolidation` class entirely — it only exercises `_collect_field_changes()` which is being deleted.
2. Update any remaining tests that reference FIELD_* constants to use the new registry-based approach.
3. Ensure all existing tests pass after the refactor.

### Method
**Phase 3: Verification — Update tests and validate**
- Update `TestCollectFieldChangesConsolidation` tests to match new registry-based API, or remove if they only exercise the deleted method (REQ-008; `tests/agent/services/test_config_reload.py`).
- Run `uv run pytest tests/agent/services/test_config_reload.py` to verify no regression (REQ-008; both target files).

### Details
**Phase 3: Verification — Update tests and validate**
1. Remove `TestCollectFieldChangesConsolidation` class entirely:
   - This class contains 5 test methods that only exercise `_collect_field_changes()`, which is being deleted.
   - The class definition spans lines 615-794 in the current file.
   - Removing this class eliminates dead-code test coverage.

2. Update any remaining tests that reference FIELD_* constants:
   - Check all test methods for direct references to FIELD_* constants.
   - Replace with the new registry-based approach where applicable.
   - Most tests already use raw string literals (e.g., `"http_timeout"`) rather than FIELD_* constants, so minimal updates may be needed.

3. Verify all existing tests pass:
   - Run `uv run pytest tests/agent/services/test_config_reload.py -v`
   - Confirm no behavioral regression by comparing output of `/reload` command before and after refactor
   - Add mutation testing coverage for edge cases: missing fields, invalid values, empty dicts

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

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | TestCollectFieldChangesConsolidation class removed |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated for registry-based API |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All tests pass; no new dead-code/lint/type/security finding |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No documentation changes required |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260906-185627_refactor_config_reload.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-193422_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-223712
- **Related target files**: tests/agent/services/test_config_reload.py
