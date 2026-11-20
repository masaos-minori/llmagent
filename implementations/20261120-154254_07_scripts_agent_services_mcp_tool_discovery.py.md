## Goal

Convert `_check_required_tools` in `scripts/agent/services/mcp_tool_discovery.py` from a `McpServerConfig.tool_names` loop to a required-capability check driven by the new registry manifest (`REQ-005`), keep cross-server duplicate-name and drift findings fatal, and remove the stale `repl_health.py` docstring reference.

## Scope
**Release unit**: tool_names removal and required-capability model

## Assumptions
- `_check_required_tools(self, findings, registry: RuntimeToolRegistry)` currently iterates `srv_cfg.tool_names` for required servers (lines 227-250); `srv_cfg.required` stays.
- The new registry manifest (`config/tool_catalog.toml`, a separate target row) declares each required server's required capability; `cliplc008`'s required-capability schema is the canonical one and is reused unchanged.
- The manifest is loaded at startup and reachable from this service (per the Plan's Assumptions); pass it into `_check_required_tools` if it is not already in scope.
- `_check_tool_definitions_finding` still wraps `tool_validation.py::_check_tool_definitions` (row 6); the two modules change together in the same release unit.

## Design decisions
- Replace the `for tool_name in srv_cfg.tool_names` loop with a per-required-server lookup of the declared required capability in the manifest, then assert a discovered tool provides that capability; a missing capability is a FATAL finding.
- Leave the duplicate-name exclusion and the drift-findings path (`_check_tool_definitions_finding`, `_escalate_unreachable_findings`) untouched except that their input now comes from the reshaped drift check.

## Alternatives considered
- Keep checking `srv_cfg.tool_names`: rejected by `REQ-003`/`REQ-005`, which remove the field and require a required-capability model.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
Rewrite `_check_required_tools` to read required capabilities from the manifest instead of `srv_cfg.tool_names`; clean the stale docstring.

### Method
- Replace lines 234-250: for each required server, read its declared required capability from the manifest and confirm a discovered tool provides it; append a FATAL finding when the capability is absent.
- Update the method signature/docstring to describe the required-capability model.
- Delete the `repl_health.py` references in the module docstring (lines 11 and 26-30): the referenced helper does not exist in the current source; state that discovery fetches `/v1/tools` once per server and that no cross-module double fetch exists.

### Details
- If the manifest is not already available to the service, thread it through the discovery entry point so `_check_required_tools` can read it; do not reload it per server.
- Preserve the `FATAL` severity for a missing required capability (AC-3).
- Confirm duplicate-name detection (in `mcp_tool_discovery_registry.py`) still runs and stays fatal.

## Compatibility considerations
Backward incompatible by design (`REQ-005`): a required server whose manifest no longer declares a capability that a previously-listed tool provided will now report a missing-capability FATAL unless the manifest is updated to match the live tools.

## Security considerations
Fail-closed: a required server that cannot prove its declared capability is present at startup blocks startup, matching the old required-tool behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Drive `_check_required_tools` with a manifest-shaped expected capability present and missing; assert present passes and missing yields a FATAL finding. Run the affected discovery tests.

## Completion criteria
`_check_required_tools` reads no `McpServerConfig.tool_names`, derives requirements from the manifest, reports a missing required capability as FATAL, and the module docstring no longer names `repl_health.py`.

## Out of Scope
The drift-check rewrite (`tool_validation.py`), the registry manifest (`config/tool_catalog.toml`), the live-vs-registry comparison (`tool_routing_validation.py`), the required-capability schema definition (`cliplc008`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Also covered by the Step 4 drift-input reshape (static-catalog removal unit). |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`
