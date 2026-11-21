## Goal

Read the retry class from the declared `retry_policy` instead of from `RETRYABLE_TOOLS` (REQ-004, REQ-007; AC-04, AC-09).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The declared value is the authority; the reference set remains for the drift comparison owned by row 05.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/tool_runner.py`
### Procedure
- Change `_classify_retry_class()` to read the entry's declared `retry_policy` and pass the classification to `scripts/shared/mcp_dedup.py`.
### Method
- Remove the membership test against `RETRYABLE_TOOLS`; map the declared value to the existing classification the dedup path expects.
- Keep the existing retry limits and the existing reconciliation handling unchanged.
### Details
- Verified 2026-11-21: the current function names `RETRYABLE_TOOLS` as the single source of truth and credits ADR-008; the ownership statement moves with the ADR row.
### Companion test files
- `tests/agent/test_tool_runner.py`
  - Procedure: Replace the `RETRYABLE_TOOLS` membership assertions at lines 2534-2555 with the declared retry policy, and keep the reconciliation classification cases (T-04, T-08).
  - Validation: `uv run pytest tests/agent/test_tool_runner.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The classification applied to a call comes from the declared policy, and no membership test against a static set remains in this module.

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
- **Requirement ID**: REQ-004, REQ-007
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/tool_runner.py`, `tests/agent/test_tool_runner.py`
