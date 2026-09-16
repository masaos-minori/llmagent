## Goal

Reduce `scripts/agent/services/config_reload.py` to a thin orchestrator: remove extracted registry/section-reload/sync/classification code, delegate to new modules, keep `ConfigReloadService`/`ConfigReloadOutcome`/`ConfigReloadValidationError` in place.

## Scope

- Reduce `config_reload.py` to a thin orchestrator that delegates to the four new modules
- Keep `ConfigReloadService`, `ConfigReloadOutcome`, `ConfigReloadValidationError` in place
- No other files are modified in this row

## Assumptions

- The four new modules (`config_field_registry.py`, `config_section_reload.py`, `config_service_sync.py`, `config_outcome_classification.py`) have been created in Phase 1/Phase 2 before this step.
- `ConfigReloadService.__init__(ctx: AgentContext)` already matches the Issue's "accept only `AgentContext`" acceptance criterion (already true in current source — no code change required for this item; verify it stays true after the split).
- The public API (`ConfigReloadService.apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome`) is unchanged.

## Design decisions

- Keeping `ConfigReloadService` as a thin orchestrator rather than making it fully stateless: the frozen public constructor signature prohibits changing the constructor, so `self._ctx` must remain.
- Delegating section handling to `reload_validated_section()`/`reload_direct_fields()` preserves the existing two distinct section-reload algorithms (dataclasses.replace() + validator for llm/rag/tool vs. direct setattr for approval/memory/mcp).

## Alternatives considered

- Making `ConfigReloadService` fully stateless — rejected: the frozen public constructor signature prohibits changing the constructor, so `self._ctx` must remain.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

Reduce `config_reload.py` to a thin orchestrator by removing extracted code and delegating to new modules.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/services/config_reload.py` full file read; 481 lines, `apply_config_dict()` at L215 (radon C18), `_sync_services` at L310, `_classify_mcp_server_changes` at L357 (already takes explicit `ctx`), `_reload_section_fields` at L392, `_classify_startup_only_fields` at L434, `_detect_diagnostics_live_fields` at L457.
2. Remove `CONFIG_FIELD_REGISTRY` definition (moved to `config_field_registry.py`).
3. Remove `ConfigFieldRegistry` class definition (moved to `config_field_registry.py`).
4. Replace `apply_config_dict()`'s inline section iteration with delegation to `reload_validated_section()`/`reload_direct_fields()`.
5. Replace `_sync_services()`'s scalar-parameter passing with `ServiceSyncer` class (moved to `config_service_sync.py`).
6. Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` as standalone functions (moved to `config_outcome_classification.py`).
7. Import the four new modules at module level.

### Details

```python
# config_reload.py: reduce to thin orchestrator:
# Before: 481 lines, mixing schema definition, section-reload control flow, service-instance sync, and outcome classification

# After: ~150 lines, thin orchestrator:

"""Config reload service — thin orchestrator over extracted sub-modules."""

from __future__ import annotations

import logging
from typing import Any

from agent.config_dataclasses import ConfigReloadRequest
from agent.services.config_field_registry import registry_for
from agent.services.config_section_reload import reload_validated_section, reload_direct_fields
from agent.services.config_service_sync import ServiceSyncer
from agent.services.config_outcome_classification import (
    classify_mcp_server_changes,
    classify_startup_only_fields,
    detect_diagnostics_live_fields,
)
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadOutcome
from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)

class ConfigReloadService:
    """Orchestrates config reload: validate → apply → sync → report."""

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    # --- public entry points (unchanged) ---

    def apply_config(self, req: ConfigReloadRequest) -> ConfigReloadOutcome:
        """Update ctx.cfg from req, sync live services, return a report."""
        new_cfg = self._req_to_dict(req)
        return self.apply_config_dict(new_cfg)

    def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
        """Update ctx.cfg from new_cfg, sync live services, return a report.

        Delegates section handling to reload_validated_section/reload_direct_fields.
        """
        ctx = self._ctx
        outcome = ConfigReloadOutcome()

        # Delegate validated section handling (llm/rag/tool)
        for section_path in ("llm", "rag", "tool"):
            cfg = getattr(ctx.cfg, section_path)
            changed_fields: dict[str, Any] = {}
            for field_entry in registry_for(section_path):
                value = new_cfg.get(field_entry.name)
                if value is None or value == getattr(cfg, field_entry.name):
                    continue
                changed_fields[field_entry.name] = value
            if changed_fields:
                try:
                    replaced = dataclasses.replace(cfg, **changed_fields)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e
                for field_entry in registry_for(section_path):
                    if field_entry.name in changed_fields:
                        validator = field_entry.validator
                        if validator is not None:
                            validator(replaced, field_entry.name, changed_fields[field_entry.name])
                setattr(ctx.cfg, section_path, replaced)
                outcome.applied.append(section_path)

        # Delegate direct field handling (approval/memory/mcp)
        for section_path in ("approval", "memory", "mcp"):
            cfg = getattr(ctx.cfg, section_path)
            changed_fields = reload_direct_fields(ctx, new_cfg, section_path)
            if changed_fields:
                setattr(ctx.cfg, section_path, cfg)
                outcome.applied.append(section_path)

        # Sync live services via ServiceSyncer
        syncer = ServiceSyncer(ctx)
        sync_result = syncer.sync_all(ctx.cfg.llm, ctx.cfg.rag, ctx.cfg.tool)
        outcome.applied.extend(sync_result.applied)
        outcome.skipped.extend(sync_result.skipped)

        # Classify outcomes via standalone functions
        mcp_servers = _build_mcp_servers(ctx.cfg.mcp.servers) if ctx.cfg.mcp.servers else {}
        outcome.mcp_server_changes = classify_mcp_server_changes(mcp_servers)
        outcome.startup_only_fields = classify_startup_only_fields(ctx)
        outcome.diagnostics_live_fields = detect_diagnostics_live_fields(ctx)

        return outcome

    # --- internal helpers (minimal, delegated) ---

    def _req_to_dict(self, req: ConfigReloadRequest) -> dict[str, Any]:
        """Convert ConfigReloadRequest to a flat dict keyed by section.field."""
        ...

    def _validate_masked_fields(self, masked_fields: list[str] | None) -> list[str]:
        """Validate and normalize masked_fields input."""
        ...

# --- remaining private helpers (unchanged, minimal) ---

def _build_mcp_servers(...) -> Mapping[str, McpServerConfig]:
    ...

def _diff_mcp_server_config(...) -> list[dict[str, str]]:
    ...
```

## Compatibility considerations

- The public API (`ConfigReloadService.apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome`) is unchanged.
- One real importer (`agent/commands/cmd_config.py`, function-local import) relies on the public API — blast radius on that caller is nil.

## Security considerations

- No security impact. This is a refactoring that moves code into separate modules without changing behavior.

## Rollback considerations

- Reverting this change restores the original monolithic `config_reload.py` with all code in one file. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_reload*.py tests/agent/commands/test_agent_cmd_config.py -q` to confirm no failures introduced, including the 11 tests dependent on the repointed patches (REQ-006, REQ-007).
- Static analysis: `uv run ruff check scripts/agent/services/config_reload.py`, `uv run mypy scripts/agent/services/config_reload.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `config_reload.py` is reduced to a thin orchestrator (~150 lines) that delegates to the four new modules.
- `ConfigReloadService`, `ConfigReloadOutcome`, `ConfigReloadValidationError` remain in place.
- All existing tests in `tests/agent/services/test_config_reload*.py` and `tests/agent/commands/test_agent_cmd_config.py` pass without modification (REQ-006, REQ-007).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_field_registry.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/services/config_section_reload.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/services/config_service_sync.py` — covered by separate row (REQ-003).
- Changes to `scripts/agent/services/config_outcome_classification.py` — covered by separate row (REQ-004, REQ-005).
- Repointing mock-patch sites in `tests/agent/services/test_config_reload.py` — covered by separate row (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove CONFIG_FIELD_REGISTRY / ConfigFieldRegistry definitions | Pending | — | — | |
| 2 | Add imports for the four new modules | Pending | — | — | |
| 3 | Replace apply_config_dict() with delegation calls | Pending | — | — | |
| 4 | Replace _sync_services() with ServiceSyncer | Pending | — | — | |
| 5 | Replace classification helpers with standalone functions | Pending | — | — | |
| 6 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001–REQ-007
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: scripts/agent/services/config_reload.py
