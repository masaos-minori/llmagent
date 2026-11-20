## Goal

- Add the ADR approval ledger entries that the pending Blocking amendments cite (`REQ-009`, pending Blocking amendment).

## Scope
**Release unit**: pending-amendments

- Plan step 10 only, gated on UNK-02. This file is outside the Issue's Target Files: its addition to the Plan is a scope amendment that the owner approves through UNK-02.
- Execute together with the ADR procedures of Plan step 11 (ADR-002, ADR-003, ADR-012): an entry without its bullet and a bullet without its entry each fail `tools/check_adr_structure.py`.

## Assumptions

- The last entry is AAL-030, so new entries continue ascending from the next free ID, read at execution time; AAL-001 (ADR-001 INV-02 verification row set to Non-Blocking) is the precedent for this kind of entry.
- One entry per pending bullet: ADR-002 INV-03, ADR-002 INV-04, ADR-003 INV-03, ADR-003 INV-04, ADR-003 INV-07, and ADR-012 INV-04 when it is `Not verified`.
- Approver and Date stay `Not recorded`; the implementer writes no approval text (Part 5 Rules).

## Design decisions

- Entry shape copies AAL-001: `ID`, `ADR`, `Decision` (for example "INV-03 verification row set to Non-Blocking"), `Approver`, `Date`, `Scope`.

## Alternatives considered

N/A: Part 5 fixes the entry fields and rules.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`
### Procedure
1. Append one `#### AAL-NNN` entry per pending bullet at the end of Part 5 `### Active Items`, in ascending order.
2. Set `Approver` and `Date` to `Not recorded` and `Scope` to the invariant's verification row.
### Method
- Direct text edit following the entry format of AAL-001.
### Details
- Entry IDs and the set of changed invariants must equal what the ADR procedures cite.

## Compatibility considerations

N/A: governance ledger addition; entries are removed when the approval is recorded or the change is reverted.

## Security considerations

- No entry may state or imply an approval.

## Rollback considerations

N/A: revert the commit together with the ADR procedures (release unit).

## Validation plan

- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- Every ledger ID cited by a pending bullet has an entry, with all six fields (AC-5).

## Out of Scope

- Approving anything, Known Issue entries, and entries for past approvals.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the ledger entries (Plan step 10) | Completed | 20261120 | 20261120 | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 11 - UNK-02 owner decision pending Owner resolved UNK-02 20261120 (incl. governance_03 scope amendment): AAL-031..036 appended after AAL-030 in ascending order |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | adr_structure/known_deviation_sync/needs_confirmation_inventory/docs checkers all exit 0; every cited AAL ID resolves |

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
- **Requirement ID**: `REQ-009` (ledger entries for the pending Blocking amendments, gated)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`