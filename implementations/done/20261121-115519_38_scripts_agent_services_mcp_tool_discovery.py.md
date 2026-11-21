## Goal

Compare declared write classification with the reference sets only as a drift report (REQ-007; AC-10).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The existing ADR-003 INV-03 report keeps its shape; its wording states that the declared value is the authority and the reference sets are comparison data.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`
### Procedure
- Change `_build_write_classification_findings()` to read the declared field and keep the comparison with the reference sets as a finding only.
### Method
- Keep the security-posture gate and the existing finding aggregation unchanged.
### Details
- Verified 2026-11-21: the current finding text describes a disagreement between the runtime flag and the static tool sets; with the priority inverted, the declared value is the reference and the static set is the comparison.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The finding reports disagreement without changing any decision, and the phrase that presents the static sets as the authority is removed.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-192145 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Consumer wording and finding label updated to declared-authority semantics (Declared write classification drift:); unowned ripple test files fixed directly: test_mcp_tool_discovery.py migrated to schema-2.1 via tools/fill_schema21_test_entries.py, posture-gate fixtures, test_mcp_status_display drift-label assertions |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-192145 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_mcp_tool_discovery.py 93 passed including the new parametrized missing-required-field test and round-trip assertions; posture-gate and mcp_status_display green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261121-192145 | 20261121-203306 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue targeted pytest plus ruff/format/mypy/lint-imports green for the row files; full suite runs at release-unit end unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`