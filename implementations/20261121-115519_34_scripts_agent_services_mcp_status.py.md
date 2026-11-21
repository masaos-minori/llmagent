## Goal

Derive a server's risk level from the declared tiers instead of the configuration map (REQ-004; AC-04).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The display value is still the highest risk among the server's tools; only its source becomes the declared field.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`
### Procedure
- Change `_tier_for_server()` and the probe path to read the declared tier on each registered entry.
### Method
- Remove the `tool_safety_tiers` argument and the dictionary read; iterate the registry entries the server owns.
- Keep the `McpTier` output shape so the `/mcp` status display is unchanged.
### Details
- Verified 2026-11-21: the current code reads `ctx.cfg.approval.tool_safety_tiers` and the highest-risk helper over that map.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- A server's displayed level comes from the declared tiers, and no configuration map is read.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/services/mcp_status.py`
