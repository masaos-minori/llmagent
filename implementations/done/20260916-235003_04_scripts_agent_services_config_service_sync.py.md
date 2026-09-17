## Goal

Add a `ServiceSyncer` class in `config_service_sync.py` that accepts typed config objects (`ctx.cfg.llm`, `ctx.cfg.rag`, `ctx.cfg.tool`) instead of `_sync_services()`'s current scalar-parameter signature, preserving the exact `ConfigReloadOutcome.applied` entries (`"llm"`, `"hist_mgr"`, `"runtime_tools"`).

## Scope

- Create `config_service_sync.py` that houses `ServiceSyncer`
- No other files are modified in this row

## Assumptions

- The exact public method shape of `ServiceSyncer` (single `sync_all()` vs. per-section methods) is an implementation-phase design choice, constrained only by preserving `ConfigReloadOutcome.applied` output (UNK-01).
- The three applied entries (`"llm"`, `"hist_mgr"`, `"runtime_tools"`) are preserved exactly as they were in `_sync_services()`.
- The typed config objects (`ctx.cfg.llm`, `ctx.cfg.rag`, `ctx.cfg.tool`) are passed directly rather than scalar parameters.

## Design decisions

- Using a single `sync_all()` method rather than per-section methods: this keeps the API simple and matches the existing `_sync_services()` behavior where all three sections are synced together.
- Accepting typed config objects (`ctx.cfg.llm`, etc.) rather than the whole `ctx` object: this goes one step further than the current `_classify_mcp_server_changes()` which already avoids `self._ctx` but still takes the whole `ctx`.

## Alternatives considered

- Making `ServiceSyncer` fully stateless — rejected: the frozen public constructor signature prohibits changing the constructor, so some state may need to remain.

## Implementation

### Target file

`scripts/agent/services/config_service_sync.py` (new file)

### Procedure

Create `config_service_sync.py` with `ServiceSyncer` class.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): Confirmed non-existent; source logic at `config_reload.py` L310-353 (`_sync_services`).
2. Create `config_service_sync.py` with the following contents:
   - Import statements for typed config types
   - Create `ServiceSyncer` class that accepts typed config objects
   - Implement `sync_all()` method that preserves the exact `ConfigReloadOutcome.applied` entries

### Details

```python
"""Service sync logic — propagates config changes to live service instances."""

from __future__ import annotations

from typing import NamedTuple

# Typed config imports (unchanged):
# from agent.config_dataclasses import LlmConfig, RagConfig, ToolConfig

class SyncResult(NamedTuple):
    """Result of ServiceSyncer.sync_all()."""
    applied: list[str]
    skipped: list[str]

class ServiceSyncer:
    """Propagates config changes to live service instances.
    
    Accepts typed config objects (ctx.cfg.llm, ctx.cfg.rag, ctx.cfg.tool)
    instead of _sync_services()'s current scalar-parameter signature.
    Preserves the exact ConfigReloadOutcome.applied entries.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def sync_all(
        self,
        llm_cfg: LlmConfig,
        rag_cfg: RagConfig,
        tool_cfg: ToolConfig,
    ) -> SyncResult:
        """Sync all three config sections to live services.
        
        Args:
            llm_cfg: LLM configuration object.
            rag_cfg: RAG configuration object.
            tool_cfg: Tool configuration object.
            
        Returns:
            SyncResult with applied and skipped section names.
        """
        applied: list[str] = []
        skipped: list[str] = []
        
        # Sync LLM config
        try:
            # Propagate llm config to live service instance
            # (e.g., update model, api_key, etc.)
            ...
            applied.append("llm")
        except Exception:
            skipped.append("llm")
        
        # Sync history manager config
        try:
            # Propagate hist_mgr config to live service instance
            ...
            applied.append("hist_mgr")
        except Exception:
            skipped.append("hist_mgr")
        
        # Sync runtime tools config
        try:
            # Propagate runtime_tools config to live service instance
            ...
            applied.append("runtime_tools")
        except Exception:
            skipped.append("runtime_tools")
        
        return SyncResult(applied=applied, skipped=skipped)
```

## Compatibility considerations

- The `ServiceSyncer` class replaces `_sync_services()`'s scalar-parameter signature with typed config access — the exact `ConfigReloadOutcome.applied` entries (`"llm"`, `"hist_mgr"`, `"runtime_tools"`) are preserved.
- The return type changes from `None` (void) to `SyncResult` — callers must be updated to use the returned value.

## Security considerations

- No security impact. This is moving existing code into a separate module without changing behavior.

## Rollback considerations

- Reverting this change restores the original monolithic `config_reload.py` with all code in one file. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_service_sync.py -q` to confirm `ServiceSyncer` produces the same `applied`/`skipped` entries as `_sync_services()` did.
- Static analysis: `uv run ruff check scripts/agent/services/config_service_sync.py`, `uv run mypy scripts/agent/services/config_service_sync.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `ServiceSyncer` replaces `_sync_services()`'s scalar-parameter signature with typed config access (REQ-003).
- `ConfigReloadOutcome.applied` values are preserved (`"llm"`, `"hist_mgr"`, `"runtime_tools"`).
- New unit test exists for `ServiceSyncer` (REQ-008).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_reload.py` — covered by separate row (REQ-001–REQ-007).
- Changes to `scripts/agent/services/config_field_registry.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/services/config_section_reload.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/services/config_outcome_classification.py` — covered by separate row (REQ-004, REQ-005).
- Repointing mock-patch sites in `tests/agent/services/test_config_reload.py` — covered by separate row (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create config_service_sync.py | Pending | — | — | |
| 2 | Add ServiceSyncer class | Pending | — | — | |
| 3 | Implement sync_all() method | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: scripts/agent/services/config_service_sync.py
