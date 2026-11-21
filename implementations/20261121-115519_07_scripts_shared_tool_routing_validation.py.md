## Goal

Make the tier checks drift reports rather than decision inputs (REQ-007; AC-10).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The checks compare declared metadata with the reference data and return findings; nothing that reads the result changes a decision.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/tool_routing_validation.py`
### Procedure
- Change `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` to compare declared tiers with the reference data, and remove the configuration-map argument.
### Method
- Read the registry's declared tiers instead of `cfg.approval.tool_safety_tiers`; keep the message shape so the callers' report paths do not change.
- Keep the startup consequence owned by ADR-004 as it is written today, and do not restate it here.
### Details
- Verified 2026-11-21: both functions are called from `scripts/agent/services/routing_drift.py`, which is updated by row 37; `test_tool_routing_validation.py` is not a row of this plan.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- A disagreement is reported as a finding, and no caller uses the result to classify a tool.

## Out of Scope
- The test file that exercises these functions through fixtures only (covered by the follow-up test-audit work item).

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/tool_routing_validation.py`
