## Goal

Update the startup failure text and the tier-check path to follow the removed maps (REQ-002, REQ-007; AC-02, AC-10).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The tier check becomes a drift report; the startup consequence it currently states as fatal is the wording owned by ADR-002 and is not restated here.
- A missing required field is reported through the fail-closed registration path, not through a tier-map check.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/startup_validation.py`
### Procedure
- Remove the pipeline stage that reads the configuration tier map and reword the message that refers to it; keep the drift report as a non-decision finding.
### Method
- Remove the `check_routing_safety_tiers` call and the stage name recorded in the result; the report content comes from the changed drift path (row 37).
- Keep the broad-catch shape so an exception in a report path does not change startup behaviour.
### Details
- Verified 2026-11-21: the current message text names the tier map, and the check is invoked inside a broad catch.
### Companion test files
- `tests/agent/shared/test_startup_validation_pipeline.py`
  - Procedure: Update the pipeline stage names and the patched tier check at lines 310 and 322 to the drift-report shape (T-09).
  - Validation: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- No startup stage reads a removed configuration map; a disagreement is reported as a finding.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Stage renamed routing_safety_tiers -> routing_drift; remediation text no longer names [tool_safety_tiers]; broad catch kept. Coupled drift wrapper implemented early per row 37 Method (call site kept). |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_startup_validation_pipeline.py drift-shape tests (lines 310/322 group); test_startup_validation.py 2 allowed reds fixed here (row 27 owned). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203304 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue ruff/format/lint-imports green 2026-11-21; 47 targeted tests passed. mypy: only pre-existing test-file errors (also at HEAD), out of scope. unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue docs update owned by row 67 ADR scope. |

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
- **Requirement ID**: REQ-002, REQ-007
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/shared/test_startup_validation_pipeline.py`