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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-195800 | 20261120-195800 | Deleted the `tool_definitions=_get_or_default(cfg, "tool_definitions", _get_list, []),` builder keyword (line 219) from the `ToolConfig(...)` call in `scripts/agent/config_section_builders.py`, between `tool_results_turn_max_chars` and `system_prompts`. Re-verified current line number (219). Module parses (`ast.parse` OK) and imports cleanly; grep for `tool_definitions` in the module returns none. Other keywords in the same `ToolConfig(...)` call untouched; parentheses balanced. |
| 2 | Add or update tests per Validation plan | Completed | 20261120-195800 | 20261120-195800 | Validation plan is parse/build-only (builder no longer consumes `tool_definitions`; module parses) — verified via `ast.parse` + import + grep. The 2 remaining `tests/agent/test_config_builders.py::TestBuildToolConfig` failures (`AttributeError: 'ToolConfig' object has no attribute 'tool_definitions'`) are test-side: the test iterates a hardcoded ToolConfig field-name list and calls `getattr(cfg, key)` for each key, so the removed field name raises. This is owned by `154254_10_tests_agent_test_config_builders.py.md`, later in dependency order. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-195800 | 20261120-195800 | Builder no longer references `tool_definitions` (grep clean); module parses. The 2 failing `TestBuildToolConfig` cases are the removed-field-name iteration, owned by `_10`. Final committed state (single uncommitted batch) is internally consistent once `_06`/`_10` land. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-195800 | 20261120-195800 | N/A: documentation is explicitly out of scope for this static-catalog-removal procedure. |

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
