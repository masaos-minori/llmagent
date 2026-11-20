## Goal

Remove `ToolConfig.tool_definitions` (field plus its doc comment at lines 204-213) from `scripts/agent/config_dataclasses.py` (`REQ-002`). The field has no active runtime consumer outside the target files; the drift-check input moves to the new registry manifest.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The field and its comment occupy lines 204-213 of the current `config_dataclasses.py` (verified); if `agentcfg001` adds fields to `ToolConfig` first, these line numbers shift and must be re-verified.
- Removing the field does not change `ToolConfig`'s constructor positionality for callers: it is a keyword-only dataclass field with a default, so positional construction is unaffected.

## Design decisions
- Delete the whole comment block (lines 204-212) together with the field (line 213) so no dangling reference to a removed field remains.

## Alternatives considered
- Keep the field but stop using it: rejected by `REQ-002`, which requires the field itself gone so a stray `[[tool_definitions]]` cannot silently re-enter the dataclass.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
Delete `ToolConfig.tool_definitions` and its doc comment (lines 204-213).

### Method
Remove the 9-line comment (204-212) and the field declaration (213); leave the surrounding fields (`tool_results_turn_max_chars`, `system_prompts`) intact.

### Details
- Delete lines 204-213 (comment + `tool_definitions: list[dict] = field(default_factory=list)`).
- Confirm no other symbol in the module references `tool_definitions`; grep the module and the drift-check caller (`tool_validation.py`) for residual references.

## Compatibility considerations
Backward incompatible by design (`REQ-002`): any code path that read `ToolConfig.tool_definitions` now fails. The only prior consumers were the drift check (replaced, `REQ-004`) and test-fixture shape templates (migrated, `REQ-009`).

## Security considerations
Removing the field closes a drift surface; no runtime path can fall back to a static catalog after removal.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Import `config_dataclasses` and assert `ToolConfig` has no `tool_definitions` attribute; run the affected config-builder tests.

## Completion criteria
`ToolConfig` exposes no `tool_definitions` field, the stale comment is gone, and no in-module or drift-check reference to it remains.

## Out of Scope
The section builder (`config_section_builders.py`), the config-field-registry row (`config_field_registry.py`), the TOML blocks (`config/agent.toml`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/config_dataclasses.py`
