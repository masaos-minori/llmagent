## Goal

Read the declared capability flag and remove `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (REQ-004, REQ-009; AC-04, AC-08).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The decision rules about what the preview shows stay with the preview work item; this row only changes where the capability value comes from.

## Design decisions
- The preflight asks the declared flag for the entry it already resolves; the local tool-name set has no remaining reader once the configuration map is removed.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/tool_approval.py`
### Procedure
- Replace the local set and the `approval_dry_run_tools` read with the declared capability flag on the registry entry.
### Method
- Remove `_KNOWN_DRY_RUN_CAPABLE_TOOLS` and the configuration-map lookup; keep the preflight order and the prompt behaviour unchanged.
### Details
- Verified 2026-11-21: `_KNOWN_DRY_RUN_CAPABLE_TOOLS` is a module-level set and `approval_dry_run_tools` is read in the same module; both readers disappear with this change.
### Companion test files
- `tests/agent/test_tool_approval_preflight.py`
  - Procedure: Replace the config-map and local-set fixtures in `TestCheckApprovalDryRun` with an entry that declares the capability flag (T-04, T-07).
  - Validation: `uv run pytest tests/agent/test_tool_approval_preflight.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- `_KNOWN_DRY_RUN_CAPABLE_TOOLS` is gone, and the preflight's capability decision comes only from the declared flag.

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
- **Requirement ID**: REQ-004, REQ-009
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/tool_approval.py`, `tests/agent/test_tool_approval_preflight.py`
