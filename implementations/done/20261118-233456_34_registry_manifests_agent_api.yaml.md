## Goal

Refresh the generated Agent API manifest so it no longer publishes the removed orphan approval-event
signature and reflects the changed docstrings (REQ-011).

## Scope
**Release unit**: approval-event-cleanup and boundary-and-adr-record (Phase 6 regeneration serves both)

## Assumptions
- `registry/manifests/agent_api.yaml:548-549` publishes the `log_approval_decision` signature removed by
  Plan row 04.
- The manifest is produced by the same generator run as the API reference document (row 33).

## Design decisions
N/A: regeneration only; hand-editing a manifest is prohibited.

## Alternatives considered
Deprecating the manifest entry instead of removing it — rejected; DT-04 Option A deletes the symbol.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`
### Procedure
Run `uv run python tools/generate_reference_table.py --manifests` in the same commit as Plan rows
04/05/06/07 and commit the regenerated manifest unchanged.
### Method
Generator invocation only.
### Details
N/A: no hand edits.

## Compatibility considerations
Any downstream consumer of the manifest entry must be confirmed absent before Phase 4 (Plan UNK-08); the
compat-shim checker (row 19's companion) keeps tracking the name.

## Security considerations
N/A: generated manifest.

## Rollback considerations
Revert the whole unit commit; re-run the generator after any revert.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` (manifest-vs-source direction)

## Completion criteria
No `log_approval_decision` entry remains and the manifest matches the source with zero drift (AC-011).

## Out of Scope
The API reference document (row 33), the source symbols (rows 04/05/06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator and commit the regenerated manifest | Completed | 20261119-081802 | 20261119-081802 | Same generator run as row 33: `log_approval_decision` entry (and the removed `ToolExecutionResult`-adjacent orphan) deleted from `agent_api.yaml`; `RepositoryGateway` summary now shows the row 07 reworded docstring; manifest count of the removed symbol is 0; no hand edits |
| 3 | Run the drift gate and the full validation sequence | Completed | 20261119-081802 | 20261119-081802 | `generate_reference_table.py --check`: no drift (manifest-vs-source direction included) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-011` (generated artifacts reflect the change)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `registry/manifests/agent_api.yaml`
