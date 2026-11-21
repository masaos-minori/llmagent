## Goal

Resolve the operation type and the resource keys written to audit records from declared metadata (REQ-004, REQ-008; AC-04, AC-07).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The audit record keeps its key shape; only the source of the key names changes, from the `path_keys`/`branch_keys` configuration map to the declared key kinds.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/tool_audit.py`
### Procedure
- Change `_extract_resource_scope()` to group declared keys by kind, and remove the configuration-map union.
### Method
- Keys typed `path` are read as path values, keys typed `branch` as branch values; `non_escalating` keys are not written to the audit scope.
- Keep the behaviour for a list value (non-empty elements joined with `;`) and the existing fallback for an unknown tool name, which now has no configuration source to fall back to.
### Details
- Verified 2026-11-21: the current code unions `approval_resource_keys` `path_keys` with the declared `resource_scope_keys`, which is the double source REQ-011 removes.
### Companion test files
- `tests/agent/test_tool_audit.py`
  - Procedure: Move the operation-type and key-kind assertions in `TestAuditToolExec` to declared metadata, with a case for a `non_escalating` key not appearing in the audit scope (T-04, T-06).
  - Validation: `uv run pytest tests/agent/test_tool_audit.py -v`

## Compatibility considerations
- The ADR that cites this module's behaviour is updated by row 67; the audit record shape is not changed here.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The audit scope for a call is derived from the declared mapping only, and the recorded values are unchanged for the tools that exist today.

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
- **Requirement ID**: REQ-004, REQ-008
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/tool_audit.py`, `tests/agent/test_tool_audit.py`
