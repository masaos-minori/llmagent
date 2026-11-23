## Goal

Update the MCP-005 bullet in ADR-012 `## Known Deviations` to say the HEAD-destination check is now covered by tests while the Invariant decision stays pending (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the one MCP-005 bullet of this ADR. No Invariant, Approval Record, verification table, or index change.

## Assumptions

- Verified in this cycle: the bullet says the check has no dedicated protected-branch test and is recorded pending a maintainer decision; it cites MCP-005 in the governance inventory, which `check_known_deviation_sync.py` resolves.
- The Known Issue stays open until the maintainer decides, following the SHARED-002 precedent in ADR-008.

## Design decisions

- Replace the no-test wording with a statement that `TestHeadDestinationProtection` in `tests/mcp_servers/git/test_repository_state.py` covers the check, keep the `INV-03` limitation and the pending-decision sentence, and keep the governance citation.

## Alternatives considered

Rejected: adding an Invariant and a pending approval bullet (the maintainer's decision and it would change the index matrix and its pinned citation count).

## Implementation
### Target file
`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`

### Procedure
1. Edit only the MCP-005 bullet under `## Known Deviations`: say it is enforced in code and covered by the new test class, mandated by no Invariant (INV-03 names only checkout, pull, and push), and recorded pending a maintainer decision on an Invariant; not resolved; keep the governance inventory citation.

### Method
One Edit on the bullet; leave every other section, the verification tables, and the Approval Record unchanged.

### Details
- Run the known-deviation sync and ADR structure checkers: the Known Issue citation must still resolve.

## Compatibility considerations

N/A: no behavior change; production code is untouched.

## Security considerations

N/A: documentation or tests only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_known_deviation_sync.py`, `check_adr_structure.py`, and `check_adr_invariant_matrix.py` report no findings.

## Completion criteria

- The bullet no longer says there is no test, names the new test class, and keeps the pending-decision statement and the inventory citation; the checkers pass.

## Out of Scope

Invariants, ledger entries, the index matrix, and the Approval Record.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-112813 | 20261123-112813 | Changed: docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md (MCP-005 bullet) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-112813 | 20261123-112813 | N/A: documentation-only; known-deviation sync, ADR structure, invariant matrix checkers and gates pass |

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
- **Requirement ID**: `REQ-002` (ADR-012 MCP-005 deviation note states tests now exist)
- **Source issue**: issues/20261123-104601_gov002_git-protected-head-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-110851_gov002_git-protected-head-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-111623
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
