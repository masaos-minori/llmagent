## Goal

Read `tool_policy_mode` and `disabled_tools` from raw config in `_build_tool_config` and forward them to the `ToolConfig` constructor so the two new typed fields are populated from config (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- An absent `tool_policy_mode` key resolves to `explicit_allowlist` (the plan's fixed absent-key meaning); the builder supplies this default, so no special-casing is needed.
- `disabled_tools` defaults to `[]` (no denied tools).
- The builder already reads `allowed_tools` at line 224 via `_get_or_default`; the two new kwargs join it as siblings.

## Design decisions
- Add `tool_policy_mode=...` and `disabled_tools=...` kwargs to the existing `_build_model(ToolConfig, ...)` call in `_build_tool_config`, placed immediately after `allowed_tools=` (line 224) so the three exposure fields read as one group.
- Reuse the builder's existing `_get_or_default(cfg, "<key>", _get_str/_get_list, <default>)` helpers, matching every neighboring field.

## Alternatives considered
- Relying on the `ToolConfig` field default instead of reading raw config here: rejected because `REQ-001`/`REQ-002` require both fields to be read from raw config in `_build_tool_config`, not resolved lazily by the dataclass.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
In `_build_tool_config` (line 185), add two keyword arguments to the `_build_model(ToolConfig, ...)` call, adjacent to `allowed_tools=` (line 224).

### Method
Mirror the surrounding `_get_or_default(...)` calls that populate every other `ToolConfig` field.

### Details
- `tool_policy_mode=_get_or_default(cfg, "tool_policy_mode", _get_str, "explicit_allowlist")`
- `disabled_tools=_get_or_default(cfg, "disabled_tools", _get_list, [])`

## Compatibility considerations
Backward compatible: no existing config sets either key, and the builder supplies a safe default when the key is absent.

## Security considerations
The `explicit_allowlist` default is fail-closed and matches the current runtime, so an absent key cannot widen tool visibility.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/services/test_config_reload.py` and the startup test confirm both fields are populated from raw config.

## Completion criteria
`_build_tool_config` returns a `ToolConfig` whose `tool_policy_mode` and `disabled_tools` reflect the raw config (or the documented defaults), and the section-builder/startup test passes.

## Out of Scope
Validator logic (`config_validators.py`), registry wiring (`config_field_registry.py`), and runtime application (`tool_policy.py`, `runtime_tool_registry.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/config_section_builders.py`
