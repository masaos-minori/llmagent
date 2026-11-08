## Goal
Register the Needs confirmation items added to ADR-010 in the governance inventory (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
Adds registration entries to `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

## Assumptions
- Depends on the ADR-010 markers (seq 01); register exactly the markers added there.
- The highest-churn target of this Plan: make a single registration edit.

## Design decisions
- One entry per marker, following the inventory format defined near its registration rule.

## Alternatives considered
N/A: follows the existing inventory format

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Read the inventory format and registration rule.
2. Add one entry for each Needs confirmation marker added to ADR-010 (4xx handling, `is_error=true` classification, parse-failure handling).

### Method
Documentation edit.

### Details
- Run the inventory checker after the ADR-010 edit and after this edit.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change; no secret, permission, or input-handling behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py`: no findings
- `uv run python tools/check_known_deviation_sync.py`: no findings
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`: no findings

## Completion criteria
- Every Needs confirmation marker in ADR-010 is registered and the checker passes.

## Out of Scope
- Other inventory entries.

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
- **Requirement ID**: `REQ-007` (register open decisions)
- **Source issue**: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111044
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
