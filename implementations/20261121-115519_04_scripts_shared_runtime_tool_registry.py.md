## Goal

Stop applying a configuration-derived safety tier in `apply_policy()` (REQ-004, REQ-005; AC-04).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The change to ADR-003 Decision 9 needs a maintainer approval record (UNK-04); if it is not given, this row keeps its current behaviour and is re-scoped.

## Design decisions
- The tier a tool carries is the declared value, so `apply_policy()` no longer has a policy-derived tier to overwrite; the single-assignment install behaviour stays as ADR-003 Decision 9 describes.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`
### Procedure
- Remove the tier-map argument and the tier overwrite from `apply_policy()`; keep the complete-replacement-and-single-assignment behaviour.
### Method
- Drop the `tier_map` parameter and the per-tool tier lookup; the mapping is built from the registered entries as they already are.
### Details
- Verified 2026-11-21: `apply_policy()` is called with `ctx.cfg.approval.tool_safety_tiers` from `scripts/agent/services/config_service_sync.py`, so removing the field here also removes the caller's argument (row 35).

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- After a policy application, the tier a lookup returns is the tier the entry was declared with, and no configuration source is read.

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/runtime_tool_registry.py`
