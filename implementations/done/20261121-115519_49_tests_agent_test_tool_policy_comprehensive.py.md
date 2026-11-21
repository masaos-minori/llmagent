## Goal

Assert the inverted priority in `classify_operation_type()` (REQ-007, REQ-013 / T-04, T-09).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The priority test is the one that can fail if the declared value is read after the reference sets, so it needs a case where the two disagree.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/agent/test_tool_policy_comprehensive.py`
### Procedure
- Change `TestClassifyOperationType` to read declared metadata as the authority and assert the reference sets only produce a disagreement report.
### Method
- Keep `TestEscalateForPath` and `TestEscalateForGithubBranch`, with the fixtures carrying the declared key kinds.
### Details
- Verified 2026-11-21: this file is cited by `docs/10_adr/adr_01_index.md` for the tier rule.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy_comprehensive.py -v`

## Completion criteria
- A disagreement between a declaration and the reference data changes no decision, and the declared value is what the classification returns.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-194636 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests TestClassifyOperationType reads declared side_effect_class as authority (disagreement only reported by check_write_classification); posture class rebuilt on make_producer_registry; escalate/jail/preflight fixtures carry declared key kinds; removed-map cfg keys deleted |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-194636 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue new disagreement-decides-nothing case, fail-closed UNKNOWN case, declared-tier posture sweep over all producer tools |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-194636 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue 140 passed; ruff check/format clean |
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
- **Requirement ID**: REQ-007, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/agent/test_tool_policy_comprehensive.py`