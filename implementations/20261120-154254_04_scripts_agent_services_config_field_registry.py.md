## Goal

Remove the `tool_definitions` config-field-registry row from `scripts/agent/services/config_field_registry.py` (`REQ-002`). Removing the row also makes a reintroduced `tool_definitions` key fail the unknown-key check (`REQ-008`).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The row is a single entry at line 82 (`ConfigFieldRegistry("tool_definitions", "tool", True)`); verified against current source.
- The registry drives the unknown-key rejection, so removing this row is what makes a reintroduced `tool_definitions` key fail (`REQ-008`).

## Design decisions
- Delete only the `tool_definitions` row; leave the neighboring `tool`-section rows intact.

## Alternatives considered
- Keep the row but mark it deprecated: rejected by `REQ-002`, which requires the registry entry gone so the key is unrecognized.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
Delete the `ConfigFieldRegistry("tool_definitions", "tool", True)` row (line 82).

### Method
Remove the single line; confirm the registry list still parses.

### Details
- Delete line 82.
- Confirm no other module references the `"tool_definitions"` registry key in a way that now breaks (the drift-check caller is replaced in `REQ-004`).

## Compatibility considerations
Backward incompatible by design (`REQ-002`, `REQ-008`): a `tool_definitions` key is now an unrecognized key and is rejected at parse time.

## Security considerations
Removes a recognized config key from the allowlist, reinforcing the fail-closed unknown-key policy.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Parse an `agent.toml` containing a reintroduced `tool_definitions` key and assert it is rejected; run the config-field-registry tests.

## Completion criteria
The registry list contains no `"tool_definitions"` entry and the module parses.

## Out of Scope
The dataclass field (`config_dataclasses.py`), the section builder (`config_section_builders.py`), the TOML blocks (`config/agent.toml`), tests, and docs.

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
- **Requirement ID**: `REQ-002`, `REQ-008`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/services/config_field_registry.py`
