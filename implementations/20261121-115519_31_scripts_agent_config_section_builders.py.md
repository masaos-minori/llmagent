## Goal

Remove the builders for the removed fields and the dry-run tool validation (REQ-005, REQ-009, REQ-011; AC-05).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- No builder is retained to preserve a value that can be derived from a declared field.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`
### Procedure
- Delete the builders that populate the removed fields, remove `_validate_dry_run_tools()`, and remove its call from the approval-section builder.
### Method
- Keep the builders for the remaining fields and the existing unknown-key handling.
### Details
- Verified 2026-11-21: `_validate_dry_run_tools()` builds its supported set from the removed constants and is called from the approval-section builder; both the function and its supported-set read disappear with this row.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The config-build path produces no value for a removed field, and the removed validator is not called from anywhere.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 5; release unit: config-removal-and-tests |
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
- **Requirement ID**: REQ-005, REQ-009, REQ-011
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/config_section_builders.py`
