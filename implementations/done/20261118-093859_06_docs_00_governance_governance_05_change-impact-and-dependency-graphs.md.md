## Goal
Map each Required Reviewer name used in ADRs to a RACI role (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
- A subsection after the RACI table in `## RACI Model`.

## Assumptions
- Confirm that the maintainer decision this document needs (D1 to D4 and UNK-01 to UNK-03 of the Source plan) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Write no approval text.
- UNK-03: the proposal maps only where a RACI role of the same function exists and records the gap otherwise; the maintainer fills the gap at the sign-off.

## Design decisions
- Proposed mapping: Architecture Owner to `@architect`; Affected Component Owner to the `<area-lead>` of the ADR's area; Ops Reviewer and Operations Reviewer (both spellings occur in ADRs) to `@devops`; Data Owner to `@db-admin` (DB) or `@data-eng` (RAG); Documentation Governance Owner (used by three ADRs, found in Step 3a) to `@governance-lead`; Security Reviewer: no RACI role of the same function (gap, not invented).

## Alternatives considered
N/A: the roles come from the existing RACI Model.

## Implementation
### Target file
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
### Procedure
Add a `### Required Reviewer Roles` subsection with a two-column table (reviewer name, RACI role or recorded gap) and one sentence that ADR Required Reviewers sections use these names.
### Method
Edit in place after the RACI table; keep `@lead` as accountable.
### Details
- Do not edit the ADR Required Reviewers sections.

## Compatibility considerations
N/A: additive.

## Security considerations
N/A: documentation-only change; no role is invented.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- Every reviewer name used in the ADRs appears in the mapping, with a role or a recorded gap.

## Out of Scope
- Defining a new RACI role.
- Editing ADR Approval sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer sign-off for D4 and UNK-03 | Completed | 20261118-103727 | 20261118-103727 | Maintainer sign-off D4 (Security Reviewer left as a recorded gap) recorded in session 2026-11-18 |
| 2 | Add the reviewer mapping subsection | Completed | 20261118-103727 | 20261118-103727 | Required Reviewer Roles table added after the RACI table; Step 3a found Documentation Governance Owner (three ADRs) missing from the procedure and mapped it to @governance-lead; procedure corrected |
| 3 | Run the documentation checkers listed in Validation plan | Completed | 20261118-103727 | 20261118-103727 | docs checkers: pass |

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
- **Requirement ID**: `REQ-007`: reviewer to RACI mapping
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
