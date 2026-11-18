## Goal
List the new ADR structure checks in the check documentation (fallout of REQ-009 and REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit
- `### 10. ADR Structure Check` only.

## Assumptions
- Fallout file: it is outside the Issue's Target Files list and is reported to the owner as a scope amendment.
- `### 18. ADR Section Header Compliance` covers headings only and needs no change.

## Design decisions
- Two bullets in the existing list style; no GV rule row exists for this checker.

## Alternatives considered
N/A: single list addition.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
Add two bullets: the ADR `## Status` value must be in the set the policy governance document defines (Error); each `Current Decision Approval (pending)` bullet must cite an ADR approval ledger ID that resolves (Error).
### Method
Edit in place after the existing four bullets.
### Details
- Mirror the wording of row 16's checks; do not copy the allowed values (name the policy document instead).

## Compatibility considerations
N/A: wording-only.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- `### 10. ADR Structure Check` lists the Status and pending-form checks.

## Out of Scope
- Adding a GV rule row.
- Editing `### 18. ADR Section Header Compliance`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the checker procedure (row 16) is done | Pending | — | — | Stop if not |
| 2 | Add the two bullets | Pending | — | — |  |
| 3 | Run the documentation checkers listed in Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-009`: Status value check; `REQ-010`: pending-form check (documentation sync)
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
