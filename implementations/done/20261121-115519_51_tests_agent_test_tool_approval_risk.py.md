## Goal

Assert risk levels read from declared metadata (REQ-004, REQ-013 / T-04).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The risk-fallback cases in `TestClassifyRisk` move from the removed rule map to the declared tier's mapped risk.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/agent/test_tool_approval_risk.py`
### Procedure
- Change `_make_cfg()` so it no longer supplies the removed maps, and move `TestClassifyRisk` and `TestClassifyOperationType` to declared metadata.
### Method
- Keep `TestBuildPreview` as the check that the preview shape is unchanged.
### Details
- Verified 2026-11-21: 14 direct references to the removed maps in this file.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_risk.py -v`

## Completion criteria
- No test in this file supplies a removed configuration map.

## Out of Scope
- The preview decision rules (preview work item).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-195133 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests _make_cfg drops the removed maps; TestClassifyRisk/TestClassifyOperationType read declared metadata via make_producer_registry; stale-map validator rejection added |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-195134 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue declared-tier risk cases (write_file none, delete_file medium, github branch-key absence pin, UNKNOWN fail-closed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-195134 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue 36 passed; ruff check/format clean |
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
- **Requirement ID**: REQ-004, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/agent/test_tool_approval_risk.py`