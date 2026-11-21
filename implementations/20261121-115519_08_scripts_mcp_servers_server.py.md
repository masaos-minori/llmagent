## Goal

Extend the per-tool required field set that a `/v1/tools` response must carry (REQ-003; AC-03).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- `MCP_TOOL_SCHEMA_VERSION` stays at its current value: only the required field set grows, so the envelope contract tests are not affected.
- The field-set version is imported from `scripts/shared/tool_metadata.py` so it is recorded in one place; this module does not define a second copy.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/mcp_servers/server.py`
### Procedure
- Add the new fields to `TOOL_SCHEMA_V2_FIELDS` and read the version constant from the vocabulary module.
### Method
- Keep the existing four schema-2.0 field names unchanged and append the new required names.
- Keep validation behaviour: an entry missing a required field is reported, not defaulted.
### Details
- Verified 2026-11-21: `TOOL_SCHEMA_V2_FIELDS` lists the four required keys and `MCP_TOOL_SCHEMA_VERSION` is the envelope value.

## Compatibility considerations
- This is the contract the 13 producer files must satisfy, so the row lands in the same release unit.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- Every producer entry that declares the extended set passes validation; an entry that omits a field is rejected.
- The envelope version value is unchanged from the current one.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 3; release unit: contract-and-producers |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/mcp_servers/server.py`
