## Goal

Remove the ledger entries AAL-001, AAL-031, AAL-033, AAL-034, AAL-035, and AAL-036 from the ADR Approval Ledger, as a revert of the pending Non-Blocking changes.

## Scope
**Release unit**: N/A: not part of a release unit

One governance file. Run this procedure after the procedures that create the tests it cites (earlier `seq` values 01 to 06); it cites test node ids that must exist and pass. Run it with procedures 07 to 10 so no ADR bullet points to a removed entry.

## Assumptions

- Entries at lines 366 (AAL-001) and 627-680 (AAL-031 to AAL-036); AAL-032 stays (read in Step 3a).
- Part 5 rules: an entry is removed once the pending change is reverted; an implementer never writes approval text.

## Design decisions

- Delete each entry block (heading through its last field) and leave the others untouched; write no replacement text.

## Alternatives considered

Keep the entries with a withdrawn mark: rejected, the Part 5 rules call for removal (Plan UNK-03).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Delete the six entry blocks.
2. Check the surrounding headings and blank lines.
3. Run the checkers.

### Method
- Edit by exact block text; confirm AAL-032 and AAL-030 remain.

### Details
- The count of remaining entries drops by six; no text elsewhere cites the number (rg in Step 3a).

## Compatibility considerations

N/A: documentation only; the Verification table and index must keep agreeing (`tools/check_adr_invariant_matrix.py`).

## Security considerations

N/A: documentation only; no approval text, approver, or date is written, since an entry is removed as a revert.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` (ledger ids match pending bullets)
- `uv run python tools/check_adr_reference.py`

## Completion criteria

- The six entries are gone and AAL-032 remains.
- `check_adr_structure.py` reports no finding.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (restore Blocking rows and close the ledger entries)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
