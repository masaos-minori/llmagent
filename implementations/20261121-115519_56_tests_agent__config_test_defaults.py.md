## Goal

Remove the shared fixture mirrors of the removed maps (REQ-005, REQ-013 / T-05).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The mirror relationship documented in this file's docstring is the reason the fixtures must be removed together with the shipped config.

## Design decisions
- The fixture keeps the operational exception values the plan keeps, so the minimal-config helper still satisfies the validator's non-empty requirements.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/agent/_config_test_defaults.py`
### Procedure
- Delete `ALL_APPROVAL_RISK_RULES`, `ALL_TOOL_SAFETY_TIERS` and the removed-map entries, and update the docstring paragraph that describes the mirror.
### Method
- Keep `PERMISSIVE_ALLOWED_ROOT`, `PERMISSIVE_SQLITE_VEC_SO` and the protected-path mirror.
### Details
- Verified 2026-11-21: 5 direct references; the file is used by the config contract test group.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py tests/agent/test_config_dataclasses.py -v`

## Completion criteria
- The fixture defines no value for a removed concept, and no test imports the removed names.

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
- **Requirement ID**: REQ-005, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/agent/_config_test_defaults.py`
