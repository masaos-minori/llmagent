## Goal

Rewrite the required-tool-presence tests in `tests/agent/services/test_mcp_tool_discovery.py` to the required-capability model (`REQ-005`, `AC-3`) and drop every `McpServerConfig(..., tool_names=[...])` construction (`REQ-003`, removed by row 5). The `_check_tool_definitions` drift-mock tests stay functionally valid (the discovery service still calls the row-6–rewritten `_check_tool_definitions`).

## Scope
**Release unit**: `tool_names` removal and required-capability model (Phases 2/4/5)

## Assumptions
- Three `tool_names=[...]` kwargs exist in the file: line 1086 (`test_disabled_server_with_required_flag_still_skipped`), line 2166 and line 2217 (`TestRequiredToolPresenceCheck`). All reference the removed `McpServerConfig.tool_names` field.
- The required-tool check (`_check_required_tools`) becomes a required-capability check (row 7): each `required` server declares a required capability in the manifest, and a missing capability is FATAL (`AC-3`).
- The 9 `monkeypatch.setattr("agent.services.mcp_tool_discovery._check_tool_definitions", ...)` stubs remain valid: discovery still imports and calls `_check_tool_definitions` (rewritten in row 6), so stubbing it is unchanged.

## Design decisions
- Rewrite `TestRequiredToolPresenceCheck` and the required-flag skip test to drive the required-capability check: supply a required capability (via the manifest fixture or a manifest-shaped input the service reads) instead of a tool-name list, and assert missing-capability → FATAL / present-capability → no-FATAL.
- Delete the `tool_names=[...]` kwargs from all three `McpServerConfig(...)` constructions; keep `required=True`.
- Leave the `_check_tool_definitions` drift-mock tests untouched except optionally renaming their docstrings (cosmetic).

## Alternatives considered
- Keep `tool_names=` and only stop asserting on it: rejected by `REQ-003`, which removes the field so the kwarg raises at construction.

## Implementation
### Target file
`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure
Convert the required-tool tests to required-capability tests and remove all `tool_names=` kwargs.

### Method
- In `TestRequiredToolPresenceCheck.test_missing_required_tool_name_produces_fatal`: replace `tool_names=["grep", "nonexistent_tool"]` with a required-capability declaration whose capability no discovered tool provides; assert the missing-capability finding is FATAL (`AC-3`) in place of the "not found in discovery results" tool-name finding.
- In `TestRequiredToolPresenceCheck.test_all_required_tools_present_no_fatal`: replace `tool_names=["grep"]` with a required capability a discovered tool provides; assert no FATAL.
- In `test_disabled_server_with_required_flag_still_skipped`: replace `tool_names=["grep"]` with a required capability; adjust the "required tool" message filter (line 1101) to the required-capability finding message.
- Remove the `tool_names=[...]` kwargs from all three `McpServerConfig(...)` constructions.

### Details
- Confirm no other `tool_names=` kwarg or `McpServerConfig.tool_names` attribute access remains in the file.
- Preserve the `_check_tool_definitions` AsyncMock stubs; they are unaffected by the required-capability conversion.
- Align the required-capability fixture with `cliplc008`'s schema (row 9 manifest) so the test exercises the same field the production check reads.

## Compatibility considerations
Test-only change. Aligns the discovery required-check tests with the removed `McpServerConfig.tool_names` (row 5) and the new required-capability model (row 7).

## Security considerations
N/A: test-only. The required-capability check stays fail-closed (`AC-3`): a required server that cannot prove its declared capability reports FATAL.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `TestRequiredToolPresenceCheck` and `test_disabled_server_with_required_flag_still_skipped`; assert missing capability → FATAL, present capability → no FATAL, and that no `tool_names=` kwarg remains. Run the full `test_mcp_tool_discovery.py` to confirm the `_check_tool_definitions` drift-mock tests still pass.

## Completion criteria
No `tool_names=[...]` kwarg or `McpServerConfig.tool_names` reference remains; the required-capability tests assert FATAL on missing capability and no-FATAL when present.

## Out of Scope
The `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the required-capability check implementation (`mcp_tool_discovery.py`, row 7), the manifest (`config/tool_catalog.toml`, row 9), and the drift-check rewrite (`tool_validation.py`, row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers shift as edits proceed; identify tests by method name. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Editing existing required-tool tests; no new tests required. |
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
- **Requirement ID**: `REQ-003`, `REQ-005`, `AC-3`, `AC-4`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`
