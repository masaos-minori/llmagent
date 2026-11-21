## Goal

Drop the hot-reload contract for the removed fields (REQ-005, REQ-011, REQ-013 / T-05).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- Hot reload is asserted as accepting only the fields that remain; the policy-reapplication group keeps its behaviour without a tier map.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/agent/services/test_config_reload.py`
### Procedure
- Remove the removed-map cases from `TestApplyConfig` and `TestConfigReloadAtomicity`, update the field list asserted at lines 1167-1168, and change `TestRuntimeToolPolicyReapplication` to the reduced `apply_policy()` signature.
### Method
- Keep the field-registry coverage test as the check that no removed field is registered.
### Details
- Verified 2026-11-21: 19 direct references; this file is named by rows 29 and 35, so it keeps its own document.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -v`

## Completion criteria
- The hot-reload tests pass without supplying a removed map, and the field list they assert matches the registry.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests |
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
- **Requirement ID**: REQ-005, REQ-011, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/agent/services/test_config_reload.py`
