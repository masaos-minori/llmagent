## Goal

Remove the `tool_definitions_strict`, `routing_drift_strict` and `security_profile` entries from the reloadable-field registry so they are no longer known config fields (REQ-001 strict-only, REQ-007 no profile key).

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/services/config_field_registry.py` only; the registry-versus-dataclass consistency is exercised by `tests/agent/test_config_builders.py` (own Plan row).

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- After the removal the `"mcp"` section has no registry entry; `scripts/agent/services/config_reload.py` still lists `"mcp"` in its direct sections and `scripts/agent/services/config_section_reload.py` loops over `registry_for(section_path)`, which returns an empty list. Neither is a target; `tests/agent/services/test_config_reload.py` (own Plan row) must keep passing.

## Design decisions

- Delete the three `ConfigFieldRegistry(...)` entries and the `# MCP section` comment that only labelled the removed entry; the `CONFIG_FIELD_REGISTRY` dict and `registry_for` are unchanged.
- Only delete; the field must disappear from `config_dataclasses.py` in the same release unit or a registry/dataclass consistency test fails.

## Alternatives considered

N/A: removal is dictated by the Plan; no alternative keeps a dead reloadable field.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
1. Delete `ConfigFieldRegistry("tool_definitions_strict", "tool", True)` (line 75).
2. Delete `ConfigFieldRegistry("routing_drift_strict", "tool", False)` (line 81).
3. Delete the `# MCP section` comment and `ConfigFieldRegistry("security_profile", "mcp", True)` (lines 99-100).

### Method
- Edit by symbol; `rg -n "strict|security_profile" scripts/agent/services/config_field_registry.py` must return nothing.

### Details
- No other registry entry changes; do not renumber or reorder.

## Compatibility considerations

Reload of a config that still carries the removed keys is rejected elsewhere as unknown; the registry itself has no external consumer of those names.

## Security considerations

N/A: removes configuration surface only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py tests/agent/services/test_config_reload.py -v`.
- `uv run ruff format scripts/agent/services/config_field_registry.py`, `uv run ruff check` on it.

## Completion criteria

- The three entries are gone and no test or module references them from the registry.

## Out of Scope

- `config_reload.py` section list; dataclass and builder edits (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the three registry entries and the orphan comment | Pending | — | — | REQ-001, REQ-007 |
| 2 | Run ruff and the builder/reload tests (after the dataclass row lands) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001`, `REQ-007`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/services/config_field_registry.py`
