## Goal
Add the ADR approval ledger rows that the ADR-003 pending bullets cite (`REQ-006`: pending approval state of Decisions #15, #16, #17), so the ledger exists before any bullet cites it.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: three new entries at the end of `### Active Items` in `## Part 5: ADR Approval Ledger`.
- Scope amendment against the Issue's Target Files, decided by the maintainer for this Plan.

## Assumptions
- AAL-021, AAL-022, AAL-023 are the next free ids: the ledger currently ends at AAL-020 (checked in Step 3a).
- The rows record pending state only. `Approver` and `Date` stay `Not recorded`; no approval text is written (Part 5 Rules).

## Design decisions
- One entry per pending ADR-003 change: AAL-021 Decision Detail #15 severity correction, AAL-022 Decision Detail #16, AAL-023 Decision Detail #17.
- Entry shape is copied from AAL-020 (heading plus the six fields) so `tools/check_adr_structure.py` parses the ids.

## Alternatives considered
N/A: the ledger form is fixed by Part 5 Rules.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. After the `AAL-020` entry and before `## Resolution Rules`, add three `#### AAL-NNN` entries in ascending order.
2. Fill the fields as below; keep one blank line between entries.

### Method
- AAL-021: ADR `ADR-003`; Decision `Drift validation aborts startup (severity wording of Decision Detail #15 corrected)`; Scope `Decision Detail #15`.
- AAL-022: ADR `ADR-003`; Decision `Security Posture exclusion from RuntimeToolRegistry and its startup consequence`; Scope `Decision Detail #16`.
- AAL-023: ADR `ADR-003`; Decision `Dynamic health hints are advisory error metadata`; Scope `Decision Detail #17`.
- Every entry: `Approver` and `Date` are `Not recorded`.

### Details
- Use the exact field labels of AAL-020 (`**ID:**`, `**ADR:**`, `**Decision:**`, `**Approver:**`, `**Date:**`, `**Scope:**`).
- The file stays under the 32768-byte document limit (25625 bytes now; three entries add about 0.7 KB).

## Compatibility considerations
N/A: additive documentation rows; no existing entry changes.

## Security considerations
N/A: documentation only; no approval statement is written or simulated.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` (ledger parsing; ADR-003 has no pending bullet yet at this point, so no id is cited).
- `uv run python tools/check_docs_structure.py` and the other checkers `routing.md` Tools lists for a `docs/` edit.

## Completion criteria
- `#### AAL-021`, `#### AAL-022`, `#### AAL-023` exist with the six fields and `Not recorded` approver and date.
- All named checkers report no finding.

## Out of Scope
- The ADR-003 edits (procedure 07), approval text, any other Part of `governance_03`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three ledger entries (Implementation > Procedure) | Completed | 20261118-140956 | 20261118-140956 | Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md. Docs checkers pass; stale detector clean. |
| 2 | Run the documentation checkers (Validation plan) | Completed | 20261118-140956 | 20261118-140956 | — |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
