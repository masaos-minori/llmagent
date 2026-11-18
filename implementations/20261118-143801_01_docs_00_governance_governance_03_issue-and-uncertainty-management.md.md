## Goal
Add the ledger rows that the ADR-008 and ADR-006 pending bullets cite (`REQ-008`), before any bullet cites them.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: six new entries at the end of `### Active Items` in `## Part 5: ADR Approval Ledger` (scope amendment decided by the maintainer for this Plan).

## Assumptions
- The ledger ends at AAL-023 (checked in Step 3a); AAL-024 to AAL-029 are the next free ids.
- Rows record pending state only: `Approver` and `Date` are `Not recorded`.

## Design decisions
- One entry per pending decision-text change, in the form of the AAL-023 entry (heading plus the six fields).

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. After the `AAL-023` entry and before `## Resolution Rules`, add `#### AAL-024` to `#### AAL-029` in ascending order.

### Method
- AAL-024: ADR `ADR-008`; Decision `Scope widened to six databases (title, Summary, Scope, Recovery Policy Matrix)`; Scope `Title, Summary, Scope, Recovery Policy Matrix`.
- AAL-025: ADR `ADR-008`; Decision `Schema-mismatch rule: every database is archived and recreated, with per-database preconditions`; Scope `Decision Detail 22`.
- AAL-026: ADR `ADR-008`; Decision `Retention rule per database; EventBus events, consumer_delivery, and dlq_outbox growth is an accepted risk`; Scope `Decision Detail 23, INV-09`.
- AAL-027: ADR `ADR-008`; Decision `Memory canonical store: memories and memory_links canonical, memories_fts and memories_vec derived, JSONL append-only archive`; Scope `Decision Detail 24, Recovery Policy Matrix`.
- AAL-028: ADR `ADR-008`; Decision `INV-04 names the dlq_outbox durable promotion record`; Scope `INV-04`.
- AAL-029: ADR `ADR-006`; Decision `No-loss statements hold under the ADR-008 schema-mismatch rule; EventBus retention is an accepted risk`; Scope `Decision Detail 9, INV-07, Data Ownership`.

### Details
- Use the field labels of AAL-023 exactly.
- The file is about 26.3 KB now; the limit is 32768 bytes; six entries add about 1.4 KB.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` (ledger ids parse), the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- Six entries exist with the six fields and `Not recorded` approver and date; the checkers report no finding.

## Out of Scope
- The ADR edits (procedures 02 and 04), approval text, other Parts of `governance_03`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the six ledger entries (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
