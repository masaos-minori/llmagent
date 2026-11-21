## Goal

Remove the builder and validator cases for the removed fields (REQ-005, REQ-009, REQ-013 / T-05).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The build path is asserted through `_MIN_CFG`; the removed keys become unknown-key cases rather than field cases.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/agent/test_config_builders.py`
### Procedure
- Remove `TestValidateDryRunTools` and the removed-map cases in `TestBuildApprovalConfig`, and add the case that a config containing a removed key is rejected as an unknown key.
### Method
- Keep `TestBuildToolConfig`, `TestBuildLLMConfig` and the other groups unchanged.
### Details
- Verified 2026-11-21: 18 direct references; this file is named by rows 28, 31 and 32, so it keeps its own document.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v`

## Completion criteria
- The config-build tests assert the operational exceptions still load and the removed keys are rejected.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-200133 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests TestValidateDryRunTools deleted; TestBuildApprovalConfig rebuilt on kept fields with removed-map-field-absence and unknown-key rejection cases; TestBusinessRuleValidations tier-map cases deleted |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-200133 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue parametrized unknown-key rejection covers all four removed map keys via ProductionConfigValidator |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-200133 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue 71 passed; ruff check/format clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue docs owned by rows 62-67. |

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
- **Requirement ID**: REQ-005, REQ-009, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/agent/test_config_builders.py`