## Goal

Assert the extended per-tool field set for every producer module (REQ-003, REQ-013 / T-03).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The producers in rows 08 to 21 and row 68 must land in the same release unit.

## Design decisions
- The contract test stays the single check over all producers; the envelope-version assertion is added only as a check that the value is unchanged.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/mcp_servers/test_tool_schema_contract.py`
### Procedure
- Extend the field set `test_all_tools_pass_schema_v2_contract()` checks, and change `test_side_effect_parity_matches_canonical()` to compare the declared class with the reference sets as a cross-check.
### Method
- Keep `_TOOL_LIST_MODULES` unchanged (13 producer modules) and keep the tool-name coverage test as the check that no producer entry is missing.
### Details
- Verified 2026-11-21: this file is named by rows 08 and 68, so it keeps its own document.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v`

## Completion criteria
- Every producer entry declares the extended set, and no field is supplied by a default.

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
- **Requirement ID**: REQ-003, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/mcp_servers/test_tool_schema_contract.py`
