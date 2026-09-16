## Goal

Move `CONFIG_FIELD_REGISTRY` and `ConfigFieldRegistry` to `config_field_registry.py`; add `registry_for(section_path: str) -> Iterator[ConfigFieldRegistry]`.

## Scope

- Create `config_field_registry.py` that houses `CONFIG_FIELD_REGISTRY` (46 entries) + `ConfigFieldRegistry` + `registry_for()`
- No other files are modified in this row

## Assumptions

- The existing `CONFIG_FIELD_REGISTRY` definition in `config_reload.py` contains 46 entries across 6 sections (llm=14, rag=6, tool=10, approval=10, memory=4, mcp=2), confirmed by direct count against the source.
- Moving the registry verbatim preserves all field definitions; only the accessor function `registry_for()` is new.
- The parent directory `scripts/agent/services/` exists (confirmed).

## Design decisions

- Adding `registry_for(section_path: str) -> Iterator[ConfigFieldRegistry]` as a convenience accessor rather than exposing the raw dict directly: callers can iterate over fields for a specific section without filtering manually.
- Keeping `CONFIG_FIELD_REGISTRY` as a module-level constant (not a class attribute): this matches the existing pattern in `config_reload.py` and avoids changing the dataclass structure.

## Alternatives considered

- Making `registry_for()` return a list instead of an iterator — rejected: iterators are more memory-efficient for large registries and match the existing iteration patterns in `config_reload.py`.

## Implementation

### Target file

`scripts/agent/services/config_field_registry.py` (new file)

### Procedure

Create `config_field_registry.py` with `CONFIG_FIELD_REGISTRY`, `ConfigFieldRegistry`, and `registry_for()`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): Confirmed non-existent (`ls scripts/agent/services/` — absent); parent dir exists.
2. Create `config_field_registry.py` with the following contents:
   - Import statements for `ConfigFieldRegistry` and `CONFIG_FIELD_REGISTRY` from the original location
   - Move `ConfigFieldRegistry` class definition verbatim
   - Move `CONFIG_FIELD_REGISTRY` dictionary definition verbatim
   - Add `registry_for(section_path: str) -> Iterator[ConfigFieldRegistry]` function

### Details

```python
"""Configuration field registry — shared schema definition for config reload."""

from __future__ import annotations

import dataclasses
from typing import Iterator

# Moved verbatim from agent/services/config_reload.py:
@dataclasses.dataclass(frozen=True)
class ConfigFieldRegistry:
    """A single entry in CONFIG_FIELD_REGISTRY."""
    name: str
    section_path: str
    validator: object | None = None  # Callable[[Any, str, Any], None]

# Moved verbatim from agent/services/config_reload.py:
CONFIG_FIELD_REGISTRY: dict[str, ConfigFieldRegistry] = {
    # llm section (14 entries)
    "llm.model": ConfigFieldRegistry("model", "llm"),
    "llm.api_key": ConfigFieldRegistry("api_key", "llm"),
    # ... (all 46 entries moved verbatim)
    # rag section (6 entries)
    "rag.chunk_size": ConfigFieldRegistry("chunk_size", "rag"),
    # ... (remaining entries)
    # tool section (10 entries)
    "tool.max_iterations": ConfigFieldRegistry("max_iterations", "tool"),
    # ... (remaining entries)
    # approval section (10 entries)
    "approval.mode": ConfigFieldRegistry("mode", "approval"),
    # ... (remaining entries)
    # memory section (4 entries)
    "memory.type": ConfigFieldRegistry("type", "memory"),
    # ... (remaining entries)
    # mcp section (2 entries)
    "mcp.servers": ConfigFieldRegistry("servers", "mcp"),
    # ... (remaining entries)
}

def registry_for(section_path: str) -> Iterator[ConfigFieldRegistry]:
    """Yield ConfigFieldRegistry entries for a given section path.
    
    Args:
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        
    Yields:
        ConfigFieldRegistry entries whose section_path matches the argument.
    """
    for entry in CONFIG_FIELD_REGISTRY.values():
        if entry.section_path == section_path:
            yield entry
```

## Compatibility considerations

- Both the class definition and the registry dictionary are moved verbatim — no behavioral changes.
- The new `registry_for()` accessor is backward compatible: callers that previously iterated over `CONFIG_FIELD_REGISTRY.values()` and filtered by `section_path` can now use `registry_for(section_path)` directly.

## Security considerations

- No security impact. This is moving existing code into a separate module without changing behavior.

## Rollback considerations

- Reverting this change restores the original monolithic `config_reload.py` with all code in one file. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_field_registry.py -q` to confirm `registry_for()` returns correct per-section entries.
- Static analysis: `uv run ruff check scripts/agent/services/config_field_registry.py`, `uv run mypy scripts/agent/services/config_field_registry.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `CONFIG_FIELD_REGISTRY` and `ConfigFieldRegistry` live in `config_field_registry.py` with a working `registry_for()` (REQ-001).
- All 46 entries across 6 sections are preserved verbatim.
- New unit test exists for `registry_for()` (REQ-008).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_reload.py` — covered by separate row (REQ-001–REQ-007).
- Changes to `scripts/agent/services/config_section_reload.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/services/config_service_sync.py` — covered by separate row (REQ-003).
- Changes to `scripts/agent/services/config_outcome_classification.py` — covered by separate row (REQ-004, REQ-005).
- Repointing mock-patch sites in `tests/agent/services/test_config_reload.py` — covered by separate row (REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create config_field_registry.py | Pending | — | — | |
| 2 | Move ConfigFieldRegistry class verbatim | Pending | — | — | |
| 3 | Move CONFIG_FIELD_REGISTRY dict verbatim | Pending | — | — | |
| 4 | Add registry_for() accessor function | Pending | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: scripts/agent/services/config_field_registry.py
