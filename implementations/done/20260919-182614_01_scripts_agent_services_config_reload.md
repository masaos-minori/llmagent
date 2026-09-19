## Goal

Extract five distinct responsibilities from `ConfigReloadService.apply_config_dict()` into smaller private methods, reducing complexity below 150 lines through delegation to concern-specific sub-modules.

## Scope

- **In-Scope**: Extracting private methods from `apply_config_dict()`, updating docstrings, fixing pre-existing test failures
- **Out-of-Scope**: Changes to `config_field_registry.py`, `config_validators.py`, `config_section_reload.py`, `config_service_sync.py`, `config_outcome_classification.py`; adding new features or changing public APIs

## Assumptions

- The four extracted methods will each return a partial `ConfigReloadOutcome` rather than mutating the outcome passed in — avoids shared mutable state and makes each method independently testable
- The 14 pre-existing test failures are caused by two distinct issues: (a) `_diff_mcp_server_config` moved to `config_outcome_classification.py` but tests still import from `config_reload.py`; (b) validators now raise `ValueError` directly instead of `ConfigReloadValidationError` — both fixable without changing the core refactoring logic

## Design decisions

- Each extracted method returns a partial `ConfigReloadOutcome` rather than mutating the outcome passed in — avoids shared mutable state and makes each method independently testable
- The `ConfigReloadOutcome` dataclass is reused as the merge mechanism — no new types introduced

## Alternatives considered

- Mutating a shared outcome object instead of returning partial outcomes — rejected because it introduces shared mutable state and reduces testability
- Introducing new intermediate types for partial results — rejected because the existing `ConfigReloadOutcome` dataclass already serves as a merge mechanism

## Implementation

### Target file

scripts/agent/services/config_reload.py

### Procedure

Extract five distinct operations from `apply_config_dict()` into separate private methods. Replace the monolithic body with sequential calls to these methods plus merging of their partial results.

### Method

#### Step 1: Verify current state

Verify `apply_config_dict()` spans approximately 44 lines (lines 89–132) and contains five distinct operations. Confirm helper methods `_classify_mcp_server_changes`, `_detect_diagnostics_live_fields`, and `_sync_services` already exist and delegate to standalone functions.

#### Step 2: Extract `_apply_sections(self, new_cfg)`

Extract section-based reload logic (current lines 97–104): iterate over section paths ("llm", "rag", "tool") calling `reload_validated_section`, then iterate over ("approval", "memory", "mcp") calling `reload_direct_fields`. Return a partial `ConfigReloadOutcome` with `applied` populated.

#### Step 3: Extract `_apply_direct_fields(self, new_cfg)`

Extract direct field updates (current lines 105–110): update `ctx.conv.system_prompt_content`, `ctx.cfg.tool.allowed_tools`, and `ctx.cfg.tool.masked_fields` from `new_cfg` keys. Return a partial `ConfigReloadOutcome` with `applied` populated.

#### Step 4: Extract `_handle_mcp_changes(self, ctx, new_cfg)`

Extract MCP server change classification + lifecycle cleanup (current lines 111–121): call `_classify_mcp_server_changes(ctx, new_cfg)`, iterate results — for removed servers call `lifecycle.cleanup_server_resources(server_key)`, for others append to `outcome.needs_restart`. Return a partial `ConfigReloadOutcome` with `needs_restart` populated.

#### Step 5: Extract `_sync_and_classify(self, new_cfg, ctx)`

Extract service sync + outcome classification (current lines 122–131): call `_sync_services(new_cfg, ...)`, extend `outcome.applied` and `outcome.skipped` from result. Then set `outcome.startup_only` and `outcome.always_live` via `_classify_startup_only_fields` and `_detect_diagnostics_live_fields`. Return a partial `ConfigReloadOutcome` with `applied`, `skipped`, `startup_only`, `always_live` populated.

#### Step 6: Simplify `apply_config_dict()`

Replace the monolithic body with sequential calls to the five extracted methods, merging their partial results into a single `ConfigReloadOutcome`. Update the method docstring to reference the new internal structure.

### Details

```python
async def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
    """Update ctx.cfg from new_cfg, sync live services, return a report.

    Replaces _apply_config_params() + all _apply_* helpers from _ConfigMixin.
    The command handler only calls this method and renders the result.

    Delegates to:
        - _apply_sections(): section-based reload for llm/rag/tool/approval/memory/mcp
        - _apply_direct_fields(): direct field updates for system_prompt_tool, allowed_tools, masked_fields
        - _handle_mcp_changes(): MCP server change classification + lifecycle cleanup
        - _sync_and_classify(): service sync + outcome classification
    """
    ctx = self._ctx
    outcome = ConfigReloadOutcome()

    # Section-based reload
    section_result = self._apply_sections(new_cfg)
    outcome.applied.extend(section_result.applied)

    # Direct field updates
    direct_result = self._apply_direct_fields(new_cfg)
    outcome.applied.extend(direct_result.applied)

    # MCP changes
    mcp_result = self._handle_mcp_changes(ctx, new_cfg)
    outcome.needs_restart.extend(mcp_result.needs_restart)

    # Service sync + classification
    sync_result = self._sync_and_classify(new_cfg, ctx)
    outcome.applied.extend(sync_result.applied)
    outcome.skipped.extend(sync_result.skipped)
    outcome.startup_only = sync_result.startup_only
    outcome.always_live = sync_result.always_live

    return outcome
```

## Compatibility considerations

- Public API (`apply_config_dict`) signature and return type unchanged
- Partial `ConfigReloadOutcome` objects merged at the end — same final result as before
- Existing callers of `apply_config_dict()` require no changes

## Security considerations

- No security-relevant behavior changes — same validation and permission checks as before
- Parameter passing preserved exactly — no new attack surface from extraction

## Rollback considerations

- If extraction breaks behavior, revert to original monolithic `apply_config_dict()` body
- Keep extracted methods private — no external contract to maintain during rollback

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| apply_config_dict() (refactored) | Unit — verify method size reduction | Manual inspection of scripts/agent/services/config_reload.py | Method spans ~10-15 lines |
| _apply_sections() | Unit — verify section-based reload works | `pytest -k "test_apply_config_dict_applies_llm_fields_via_registry"` | Tests pass |
| _apply_direct_fields() | Unit — verify direct field updates work | `pytest -k "test_apply_config_dict_applies_tool_fields_via_registry"` | Tests pass |
| _handle_mcp_changes() | Unit — verify MCP classification works | `pytest -k "TestMcpServerChangeClassification"` | Tests pass |
| _sync_and_classify() | Unit — verify service sync works | `pytest -k "TestRuntimeToolPolicyReapplication"` | Tests pass |
| Full test suite | Regression — all config_reload tests | `uv run pytest tests/agent/services/test_config_reload.py` | All 56 tests pass |
| Type checking | Static analysis | `uv run mypy scripts/agent/services/config_reload.py` | Clean |
| Linting | Style check | `uv run ruff check scripts/agent/services/config_reload.py` | Clean |

## Completion criteria

- `apply_config_dict()` reduced to approximately 10-15 lines (calling extracted methods)
- Each extracted method handles exactly one responsibility
- All existing tests pass after refactoring (56 tests, currently 14 fail)
- No behavioral changes — same inputs produce same outputs
- Docstring updated to reflect new internal structure

## Out of scope

- Changes to `config_field_registry.py`, `config_validators.py`, `config_section_reload.py`, `config_service_sync.py`, `config_outcome_classification.py`
- Adding new features or changing public APIs
- Deciding whether `ProcessSnapshotProvider` should be wired to a real caller (separate issue)

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
- **Requirement ID**: REQ-001 through REQ-005
- **Source issue**: issues/done/20260919-112313_refactor_001_refactor_config_reload_service_apply_config_dict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-114636_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-182614
- **Related target files**: scripts/agent/services/config_reload.py
