## Goal

Add `reload_validated_section()` and `reload_direct_fields()` in `config_section_reload.py`, replacing the inline llm/rag/tool loop and the renamed `_reload_section_fields()` respectively.

## Scope

- Create `config_section_reload.py` that houses `reload_validated_section()` + `reload_direct_fields()`
- No other files are modified in this row

## Assumptions

- The two distinct section-reload algorithms (dataclasses.replace() + validator for llm/rag/tool vs. direct setattr for approval/memory/mcp) stay as two named functions in one file rather than being merged or split further by domain, matching the Issue's own resolved Unresolved Questions.
- Validator imports are spread across `config_validators.py` (defines), `config_dataclasses.py` (imports as `_v_*`), and `config_reload.py` (re-imports by full name) — confirmed by reading `config_reload.py`'s import block.
- The existing `# noqa: F401 — used by config_reload.py (lazy import)` comment on `agent/config_builders.py`'s `_build_mcp_servers` import becomes stale after this Plan but is out of this Plan's explicit scope.

## Design decisions

- Keeping the two distinct section-reload algorithms as separate functions (`reload_validated_section` vs. `reload_direct_fields`) rather than merging them: they have fundamentally different semantics (dataclass replacement + validation vs. direct setattr).
- Having each function accept only the specific values it needs (e.g. `ctx.cfg.llm`, not `ctx`) rather than an entire context object — going one step further than the current `_classify_mcp_server_changes()` which already avoids `self._ctx` but still takes the whole `ctx`.

## Alternatives considered

- Merging both algorithms into a single function — rejected: they have fundamentally different semantics; keeping them separate improves readability and testability.

## Implementation

### Target file

`scripts/agent/services/config_section_reload.py` (new file)

### Procedure

Create `config_section_reload.py` with `reload_validated_section()` and `reload_direct_fields()`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): Confirmed non-existent; source logic at `config_reload.py` L223-260 (validated loop), L392-432 (`_reload_section_fields`).
2. Create `config_section_reload.py` with the following contents:
   - Import statements for validators from `config_validators.py`
   - Create `reload_validated_section(ctx, section_path, new_cfg)` function
   - Create `reload_direct_fields(ctx, new_cfg, section_path, field_filter=None)` function

### Details

```python
"""Section reload logic — validated (llm/rag/tool) and direct (approval/memory/mcp) paths."""

from __future__ import annotations

import dataclasses
from typing import Any

from agent.services.config_field_registry import registry_for
from agent.services.exceptions import ConfigReloadValidationError

# Validators imported from config_validators.py (unchanged):
# from agent.services.config_validators import validate_llm_model, validate_rag_chunk_size, ...

def reload_validated_section(
    ctx: AgentContext,
    section_path: str,
    new_cfg: dict[str, Any],
) -> list[str]:
    """Reload a validated section (llm/rag/tool) using dataclasses.replace + validators.
    
    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        new_cfg: New configuration dictionary.
        
    Returns:
        List of applied section names.
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}
    
    for field_entry in registry_for(section_path):
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value
    
    if not changed_fields:
        return []
    
    try:
        replaced = dataclasses.replace(cfg, **changed_fields)
    except ValueError as e:
        raise ConfigReloadValidationError(str(e)) from e
    
    # Run validators on changed fields
    for field_entry in registry_for(section_path):
        if field_entry.name in changed_fields:
            validator = field_entry.validator
            if validator is not None:
                validator(replaced, field_entry.name, changed_fields[field_entry.name])
    
    setattr(ctx.cfg, section_path, replaced)
    return [section_path]

def reload_direct_fields(
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    section_path: str,
    field_filter: set[str] | None = None,
) -> dict[str, Any]:
    """Reload a direct section (approval/memory/mcp) using setattr.
    
    Args:
        ctx: AgentContext with cfg attribute.
        new_cfg: New configuration dictionary.
        section_path: Section identifier (e.g., "approval", "memory", "mcp").
        field_filter: Optional set of field names to process; processes all if None.
        
    Returns:
        Dict of changed fields.
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}
    
    for field_entry in registry_for(section_path):
        if field_filter is not None and field_entry.name not in field_filter:
            continue
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value
    
    if not changed_fields:
        return {}
    
    # Apply changes via setattr (preserving dict/list copy-vs-reference semantics)
    for field_name, value in changed_fields.items():
        setattr(cfg, field_name, value)
    
    return changed_fields
```

## Compatibility considerations

- Both functions accept the same inputs as their predecessors in `config_reload.py` — no behavioral changes.
- The `field_filter` parameter in `reload_direct_fields()` is optional (default `None`) so callers can process all fields without modification.

## Security considerations

- No security impact. This is moving existing code into a separate module without changing behavior.

## Rollback considerations

- Reverting this change restores the original monolithic `config_reload.py` with all code in one file. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_section_reload.py -q` to confirm validatated/direct paths behave identically to pre-split code.
- Static analysis: `uv run ruff check scripts/agent/services/config_section_reload.py`, `uv run mypy scripts/agent/services/config_section_reload.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `apply_config_dict()` in `config_reload.py` delegates section handling to `reload_validated_section()`/`reload_direct_fields()` (REQ-002).
- Validated section handling uses dataclasses.replace() + validators for llm/rag/tool.
- Direct section handling uses setattr for approval/memory/mcp.
- New unit test exists for each function (REQ-008).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_reload.py` — covered by separate row (REQ-001–REQ-007).
- Changes to `scripts/agent/services/config_field_registry.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/services/config_service_sync.py` — covered by separate row (REQ-003).
- Changes to `scripts/agent/services/config_outcome_classification.py` — covered by separate row (REQ-004, REQ-005).
- Repointing mock-patch sites in `tests/agent/services/test_config_reload.py` — covered by separate row (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create config_section_reload.py | Pending | — | — | |
| 2 | Add reload_validated_section() function | Pending | — | — | |
| 3 | Add reload_direct_fields() function | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: scripts/agent/services/config_section_reload.py
