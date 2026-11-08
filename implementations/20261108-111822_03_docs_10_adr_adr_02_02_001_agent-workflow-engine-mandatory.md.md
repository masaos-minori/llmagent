## Goal
Make the ADR-001 current contract complete: define "interrupted Attempts" by lease expiry in Decision Details so INV-07 does not depend on the Amendment, mark the Amendment in force, and cite its plan by identifier only (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit
Edits `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`: Decision Details and the Amendment. Invariant text is unchanged.

## Assumptions
- Phase 1 of the Plan: independent of the owner decision.
- Verified now: the definition of "interrupted Attempts" (lease expiry; rows without a lease older than the documented age) exists only in the Amendment, and the Amendment cites a plan by path that no longer resolves.
- The marker wording follows the rule once written; until then use the plain phrase "in force" with no change-history marker.

## Design decisions
- Move the definition (not the history) into Decision Details; keep rationale in the Amendment, marked in force.
- Replace the plan path with the plan identifier (wflease001) only.

## Alternatives considered
N/A: wording move within one file

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Add a Decision Details item defining interrupted Attempts by lease expiry (owner and lease columns, stamping at attempt start, recovery only of lease-expired rows).
2. Mark the Amendment as in force: it records rationale of text now in the current sections.
3. Replace the stale plan path in the Amendment with the identifier.

### Method
Documentation edit; copy facts from the Amendment, verify them against the workflow engine source and the lease test.

### Details
- Do not change INV-07 text or the Approval section.
- No done/ paths, REQ identifiers, or dated added-annotations (active-document quality rules).

## Compatibility considerations
Documentation only; no behavior change.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_invariant_matrix.py`: no ERROR
- `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py`: pass (unchanged)

## Completion criteria
- INV-07 is fully defined by the current sections without reading the Amendment.
- The Amendment is marked in force and carries no path to a plan.

## Out of Scope
- Invariant text; other ADR-001 sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Pending | — | — |  |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-004` (complete ADR-001 current contract)
- **Source issue**: issues/20261107-050707_adrdoc001_separate-adr-current-history.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-093000_adrdoc001_separate-adr-current-history.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111822
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
