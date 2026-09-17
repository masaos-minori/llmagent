## Goal

Extract `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` as standalone functions in `config_outcome_classification.py`, each accepting only its narrowed inputs (e.g. `mcp_servers: Mapping[str, McpServerConfig]`, not `ctx`). Import `_build_mcp_servers` at module level from `shared.mcp_config`.

## Scope

- Create `config_outcome_classification.py` that houses the three classification functions + module-level `_build_mcp_servers` import
- No other files are modified in this row

## Assumptions

- The exact composition of the stable idempotency key (e.g. `{workflow_id}:{task_id}:{turn_id}:{sequence}` vs. an alternative) is deferred to implementation time against the actual call-site data (UNK-01).
- The existing `# noqa: F401 — used by config_reload.py (lazy import)` comment on `agent/config_builders.py`'s `_build_mcp_servers` import becomes stale after this Plan but is out of this Plan's explicit scope.
- `_build_mcp_servers`'s move to a module-level import in the new classification module is safe because `shared/mcp_config.py` has zero `agent.*` imports (confirmed via `rg "^from|^import"` and a direct interpreter import test).

## Design decisions

- Making each classification function accept only its narrowed inputs rather than the whole `ctx` object: this goes one step further than the current `_classify_mcp_server_changes()` which already avoids `self._ctx` but still takes the whole `ctx`.
- Importing `_build_mcp_servers` at module level from `shared.mcp_config` directly: the historical "avoids circular import at module level" comment on the current lazy import no longer reflects a real constraint.

## Alternatives considered

- Keeping the classification functions as bound methods of `ConfigReloadService` — rejected: prevents isolated unit testing; the Issue's own Problem section confirms no unit tests exercise these helpers independently.

## Implementation

### Target file

`scripts/agent/services/config_outcome_classification.py` (new file)

### Procedure

Create `config_outcome_classification.py` with the three classification functions + module-level `_build_mcp_servers` import.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): Confirmed non-existent; source logic at `config_reload.py` L357-390, L434-481; `_build_mcp_servers` defined at `shared/mcp_config.py:244`, confirmed importable without circular-import error (`PYTHONPATH=scripts uv run python -c "from shared.mcp_config import _build_mcp_servers"` succeeded).
2. Create `config_outcome_classification.py` with the following contents:
   - Module-level import of `_build_mcp_servers` from `shared.mcp_config`
   - Create `classify_mcp_server_changes(mcp_servers: Mapping[str, McpServerConfig])` function
   - Create `classify_startup_only_fields(ctx: AgentContext)` function
   - Create `detect_diagnostics_live_fields(ctx: AgentContext)` function

### Details

```python
"""Outcome classification — standalone functions for MCP server changes, startup-only fields, diagnostics."""

from __future__ import annotations

from typing import Mapping

# Module-level import from shared.mcp_config (safe: zero agent.* imports in shared/mcp_config.py)
from shared.mcp_config import McpServerConfig, _build_mcp_servers

def classify_mcp_server_changes(
    mcp_servers: Mapping[str, McpServerConfig],
) -> list[dict[str, str]]:
    """Classify MCP server configuration changes.
    
    Args:
        mcp_servers: Mapping of server name to McpServerConfig.
        
    Returns:
        List of dicts describing changed servers.
    """
    # Moved verbatim from ConfigReloadService._classify_mcp_server_changes():
    # ... (logic unchanged, but now accepts explicit mcp_servers instead of ctx)
    ...

def classify_startup_only_fields(
    ctx: AgentContext,
) -> list[str]:
    """Classify startup-only configuration fields.
    
    Args:
        ctx: AgentContext with cfg attribute.
        
    Returns:
        List of field names that are startup-only.
    """
    # Moved verbatim from ConfigReloadService._classify_startup_only_fields():
    # ... (logic unchanged, but now accepts explicit ctx instead of self._ctx)
    ...

def detect_diagnostics_live_fields(
    ctx: AgentContext,
) -> list[str]:
    """Detect diagnostics live fields.
    
    Args:
        ctx: AgentContext with cfg attribute.
        
    Returns:
        List of diagnostic field names.
    """
    # Moved verbatim from ConfigReloadService._detect_diagnostics_live_fields():
    # ... (logic unchanged, but now accepts explicit ctx instead of self._ctx)
    ...
```

## Compatibility considerations

- Each classification function accepts only its narrowed inputs rather than the whole `ctx` object — callers must be updated to pass the specific values they need.
- The return types remain unchanged — no behavioral changes.

## Security considerations

- No security impact. This is moving existing code into a separate module without changing behavior.

## Rollback considerations

- Reverting this change restores the original monolithic `config_reload.py` with all code in one file. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_outcome_classification.py -q` to confirm each classification function returns identical results to its bound-method predecessor.
- Static analysis: `uv run ruff check scripts/agent/services/config_outcome_classification.py`, `uv run mypy scripts/agent/services/config_outcome_classification.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `_classify_mcp_server_changes()`, `_classify_startup_only_fields()`, `_detect_diagnostics_live_fields()` exist as standalone functions taking only their narrowed inputs (REQ-004).
- `_build_mcp_servers` is imported at module level in `config_outcome_classification.py` from `shared.mcp_config` (REQ-005).
- New unit test exists for each function (REQ-008).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_reload.py` — covered by separate row (REQ-001–REQ-007).
- Changes to `scripts/agent/services/config_field_registry.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/services/config_section_reload.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/services/config_service_sync.py` — covered by separate row (REQ-003).
- Repointing mock-patch sites in `tests/agent/services/test_config_reload.py` — covered by separate row (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create config_outcome_classification.py | Pending | — | — | |
| 2 | Add module-level _build_mcp_servers import | Pending | — | — | |
| 3 | Add classify_mcp_server_changes() function | Pending | — | — | |
| 4 | Add classify_startup_only_fields() function | Pending | — | — | |
| 5 | Add detect_diagnostics_live_fields() function | Pending | — | — | |
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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: scripts/agent/services/config_outcome_classification.py
