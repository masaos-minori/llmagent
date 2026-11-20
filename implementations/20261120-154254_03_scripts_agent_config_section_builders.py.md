## Goal

Remove the `tool_definitions` section builder line from `scripts/agent/config_section_builders.py` (`REQ-002`).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The builder is a single keyword line at line 219 (`tool_definitions=_get_or_default(cfg, "tool_definitions", _get_list, [])`); verified against current source. If `agentcfg001` adds builder lines to the same `ToolConfig(...)` call, the line number shifts and must be re-verified.
- Removing this keyword does not affect the other keywords in the same `ToolConfig(...)` call.

## Design decisions
- Delete only the `tool_definitions=` keyword line; leave the surrounding keywords (`tool_results_turn_max_chars`, `system_prompts`) intact.

## Alternatives considered
- Leave the builder and rely on the dataclass field removal alone: rejected because the builder would re-populate a removed field's key from config, keeping the drift surface alive.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
Delete the `tool_definitions=` keyword line (line 219) from the `ToolConfig(...)` builder.

### Method
Remove the single line; confirm the `ToolConfig(...)` call still has balanced parentheses.

### Details
- Delete line 219 (`tool_definitions=_get_or_default(cfg, "tool_definitions", _get_list, []),`).
- Grep the module for any other `tool_definitions` reference and remove if present.

## Compatibility considerations
Backward incompatible by design (`REQ-002`): the builder no longer reads `tool_definitions` from config.

## Security considerations
Removes a config-driven path that could re-introduce a static tool catalog into `ToolConfig`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Build `AgentConfig` from raw config and assert the `tool_definitions` key is no longer consumed; run the config-builder tests.

## Completion criteria
The `ToolConfig(...)` builder no longer contains a `tool_definitions=` keyword and the module parses.

## Out of Scope
The dataclass field (`config_dataclasses.py`), the config-field-registry row (`config_field_registry.py`), the TOML blocks (`config/agent.toml`), tests, and docs.

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
- **Related target files**: `scripts/agent/config_section_builders.py`
