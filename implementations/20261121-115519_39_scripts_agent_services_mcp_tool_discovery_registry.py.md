## Goal

Build registered tools through the extended required field set (REQ-002, REQ-003; AC-02, AC-03).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field set and the vocabulary come from rows 01, 02, 08 and 68 in the same release unit.

## Design decisions
- The discovery path passes the values the producer declared; it does not supply defaults, so an entry that omits a field is rejected before registration.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery_registry.py`
### Procedure
- Pass the new required fields from the `/v1/tools` entry to `build_runtime_tool()` in `_build_runtime_tools()` and `_dedupe_and_build()`.
### Method
- Keep the duplicate detection and the single-assignment install behaviour unchanged.
- Keep the exclusion of a server whose security posture is not accepted unchanged.
### Details
- Verified 2026-11-21: the module builds `RuntimeTool` instances from the discovered definitions, so it is the path that turns a producer declaration into a registry entry.

## Compatibility considerations
- The contract test that asserts this behaviour lives in `tests/shared/test_runtime_tool_registry.py`, which is a separate document in this pass.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- An entry that omits a required field is not registered, and a complete entry is registered with the values it declared.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/services/mcp_tool_discovery_registry.py`
