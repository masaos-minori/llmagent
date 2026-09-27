## Goal

Remove NC-023 from the Needs Confirmation inventory's Active Items once its resolution (row 1) is applied (REQ-002).

## Scope

In scope: removing the NC-023 entry block and updating the closing "No other active items beyond..." ID list. Out of scope: any other NC entry.

## Assumptions

- Row 1 (`governance_01_documentation-policy.md`'s dependency-graph update) is applied before this row executes.

## Design decisions

Remove the entry outright, per this document's Lifecycle rule for Needs Confirmation ("removed... once resolved... not retained here with a closed-out status").

## Alternatives considered

Marking `Status: resolved` instead of removing: rejected — contradicts the document's own explicit Lifecycle rule.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm NC-023's exact current line range (confirmed present, unchanged, at lines 428-447 as of this cycle) immediately before editing.
2. Remove the entire NC-023 entry block (from `#### NC-023` up to, but not including, the next `#### NC-024` heading).
3. Update the closing sentence "No other active items exist outside the set listed here: NC-021, NC-023, NC-024, ..." to remove `NC-023` from that list.

### Method

Single-entry removal plus a one-item edit to the closing enumeration, following this document's own established convention.

### Details

- Confirmed current NC-023 entry (re-verified this cycle, lines 428-447): full 15-field block as shown in the Plan's Problem section.
- The closing sentence (near the end of Part 2) lists every active NC ID by name — removing NC-023 from that list keeps it accurate; re-confirm its exact current wording before editing, since other Plans in this same batch may also be removing entries from it concurrently.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry and ID-list reference.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | Pass; NC-023 no longer present or listed in the closing enumeration |

## Completion criteria

- NC-023 no longer appears in the Active Items list or the closing ID enumeration (AC-2).

## Out of scope

- Any other NC entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after row 1 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, manual + automated per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | N/A: documentation-only; `check_needs_confirmation_inventory.py` run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260927-115727_nc023_determine-rag-implementation-relationship-for-dependency-graph.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124333
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
