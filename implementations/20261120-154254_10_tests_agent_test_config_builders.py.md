## Goal

Drop the `tool_definitions` fixture entries and builder assertions from `tests/agent/test_config_builders.py` (`REQ-002`). The `ToolConfig.tool_definitions` field is removed by row 2, so any test that sets or asserts it breaks (`getattr(cfg, "tool_definitions")` raises `AttributeError`).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- The two references are verified against current source: `_TOOL_DEFAULTS["tool_definitions"] = []` at line 166 and `overrides["tool_definitions"] = [{"name": "x"}]` at line 197. If `agentcfg001` adds fields to `ToolConfig` first, these line numbers shift and must be re-verified.
- The `getattr(cfg, key)` loops (lines 174-175, 202-203) iterate over every dict key and assert `getattr(cfg, key) == value`; removing the `tool_definitions` key from both dicts keeps these loops valid for the remaining fields.

## Design decisions
- Delete only the `tool_definitions` entries from `_TOOL_DEFAULTS` and the overrides dict; leave every other default/override intact so the field-by-field loop tests still cover the surviving `ToolConfig` fields.

## Alternatives considered
- Leave the entries and update the loops to skip `tool_definitions`: rejected because the field no longer exists, so the cleanest correct state is their absence from the fixtures.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
Remove the `tool_definitions` keys from the tool-config fixture and override dict.

### Method
Edit the two dict literals; confirm the `getattr(cfg, key)` loop tests still pass for the remaining keys.

### Details
- Delete `"tool_definitions": [],` from `_TOOL_DEFAULTS` (line 166).
- Delete `"tool_definitions": [{"name": "x"}],` from the overrides dict (line 197).
- Confirm no other `tool_definitions` reference remains in the file.
- Run `TestBuildToolConfig` (and any test iterating `_TOOL_DEFAULTS`) to confirm the field-by-field assertions still hold.

## Compatibility considerations
Test-only change. Removing the fixture key aligns the test with the removed `ToolConfig.tool_definitions` field (row 2); no production compatibility impact.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `tests/agent/test_config_builders.py::TestBuildToolConfig`; assert the defaults and override loops pass with `tool_definitions` absent and every other field still asserted.

## Completion criteria
`test_config_builders.py` contains no `tool_definitions` fixture key or assertion, and the tool-config builder loop tests pass.

## Out of Scope
The `ToolConfig.tool_definitions` field removal (`config_dataclasses.py`, row 2), the section builder (row 3), the config-field-registry row (row 4), and the `agent.toml` blocks (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Mostly editing existing tests; no new tests required. |
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
- **Related target files**: `tests/agent/test_config_builders.py`
