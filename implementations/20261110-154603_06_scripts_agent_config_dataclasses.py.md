## Goal

Delete the `tool_definitions_strict` and `routing_drift_strict` fields from `ToolConfig` and the `security_profile` field with its coercion from `MCPConfig` (REQ-001, REQ-007); update the dataclass tests.

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/config_dataclasses.py` and its companion `tests/agent/test_config_dataclasses.py`.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- The strict fields (Phase 1) and `security_profile` (Phase 3) are in the same file and are deleted in one edit; order across the Plan phases does not matter provided the builder, registry, validator and display rows land in the same change (Release unit `strict-only-startup`).
- `ApprovalConfig.allowed_root` and `ToolConfig.allowed_tools` keep their `""` / `[]` dataclass defaults: the rejection is at load (builder/validator) and at runtime (`tool_policy.py`), not in the dataclass, so test fixtures that construct `ApprovalConfig()` directly stay valid.

## Design decisions

- After the edit `MCPConfig` is a plain dataclass holding `mcp_servers` with no `__post_init__`.
- The comment block above the strict fields (`# Compare tool_definitions against /v1/tools at startup`, `# Treat config/registry routing drift as fatal ...`) is deleted with them.

## Alternatives considered

Keeping `security_profile` as an ignored attribute was rejected: the key must fail as unknown at load.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Change the import (line 25) to `from shared.mcp_config import McpServerConfig`.
2. In `ToolConfig` delete `tool_definitions_strict` (line 164), `routing_drift_strict` (line 166) and their comments (lines 163, 165).
3. In `MCPConfig` (line 267) delete the `security_profile` field, its comment (lines 271-272) and `__post_init__` (lines 275-278).

### Method
- Edit by symbol; `rg -n "strict|SecurityProfile|security_profile" scripts/agent/config_dataclasses.py` should show only unrelated `strict` hits (none expected).
- Check no other module reads `cfg.tool.*_strict` or `cfg.mcp.security_profile`: `rg -n "cfg\.(tool\.(tool_definitions|routing_drift)_strict|mcp\.security_profile)" scripts` must be empty once the other Plan rows land.

### Details
- Keep the `tool_definitions` field comment that cites `_check_tool_definitions` in the `tool_validation` module; it is unrelated to the removed fields.

### Companion test files
- `tests/agent/test_config_dataclasses.py`
  - Procedure: Delete the strict-field default cases and the two `MCPConfig` security-profile cases (lines 292-301 and the local `SecurityProfile` imports); add one case asserting `MCPConfig()` has no `security_profile` attribute and `ToolConfig()` has neither strict attribute (`hasattr` is False).
  - Validation: `uv run pytest tests/agent/test_config_dataclasses.py -v`

## Compatibility considerations

Attribute access to the removed fields now raises `AttributeError`; all in-repo readers are Plan rows. `dataclasses.replace(...)` reload paths no longer see the fields.

## Security considerations

N/A: removes optionality; no authorization behavior changes.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_dataclasses.py tests/agent/test_config_builders.py -v`.
- `uv run ruff format`/`ruff check` on both files; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- The three fields are gone; the companion test asserts their absence; no `SecurityProfile` import remains in either file.

## Out of Scope

- Builder, validator, registry, display edits (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the two strict fields, the `security_profile` field and `__post_init__`, and fix the import | Pending | — | — | REQ-001, REQ-007 |
| 2 | Update the companion test file (remove default/coercion cases, add absence cases) | Pending | — | — | REQ-001, REQ-007 |
| 3 | Run ruff, mypy, lint-imports and the dataclass tests | Pending | — | — |  |

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
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_dataclasses.py`
