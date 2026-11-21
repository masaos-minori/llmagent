## Goal

Take the retry classification from the caller-supplied declared policy instead of from a static reference set (REQ-007, REQ-010; AC-09).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The `[retry_class]` mirror in `config/mcp_dedup.toml` stays as a drift comparison; its removal is decided by the open dedup configuration issue (UNK-06).
- The call-state contract itself stays with the MCP two-layer defense issues (REQ-010).
- The lease/identity contract in this module is covered by `implementations/20261121-093956_01_scripts_shared_mcp_dedup.py.md` from the earlier dedup plan; this document covers only the retry-classification input, so the two documents do not overlap.

## Design decisions
- The module receives the classification as an argument; it keeps no ownership of retry behaviour.
- The comparison against `config/mcp_dedup.toml` stays, but its result is reported as a disagreement and cannot change the classification used for a call.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`
### Procedure
- Change the classification input from the reference set to the declared policy value, and turn the existing cross-check into a drift finding.
### Method
- The caller (`scripts/agent/tool_runner.py`, row 25) supplies the declared `retry_policy`; this file does not read `RETRYABLE_TOOLS`.
- Keep the reconciliation behaviour and the existing cross-check output, and label the output as a drift finding.
### Details
- Verified 2026-11-21: the cross-check reads `config/mcp_dedup.toml` `[retry_class]` against `RETRYABLE_TOOLS`; this is the reconciliation coupling the issue describes, not `scripts/db/recovery.py`.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- A disagreement between a declaration and the mirror is reported without changing the classification applied to the call.

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
- **Requirement ID**: REQ-007, REQ-010
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/mcp_dedup.py`
