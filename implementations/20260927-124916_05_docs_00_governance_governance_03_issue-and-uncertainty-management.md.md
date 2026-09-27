## Goal

Remove NC-039 from the Needs Confirmation inventory's Active Items once its resolution (rows 1-4) is applied (REQ-004).

## Scope

In scope: removing the NC-039 entry block and updating the closing ID enumeration. Out of scope: any other NC entry.

## Assumptions

- Rows 1-4 are applied (or row 1 alone, if the owner ruled "intentional" with no code change) before this row executes.

## Design decisions

Remove the entry outright, per this document's Lifecycle rule.

## Alternatives considered

Marking `Status: resolved` instead of removing: rejected — contradicts the document's own Lifecycle rule.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm NC-039's exact current line range (confirmed present, unchanged, at lines 662-676 as of this cycle) immediately before editing.
2. Remove the entire NC-039 entry block.
3. Update the closing "No other active items exist outside the set listed here: ..." sentence to remove `NC-039` — re-confirm its exact current wording at implementation time, since other Plans in this same batch (NC-023, NC-024, NC-025, NC-031, NC-037) may have already removed their own IDs from the same sentence by the time this row executes, in an order not controlled by this document.

### Method

Single-entry removal plus a one-item edit to the closing enumeration.

### Details

- Confirmed current NC-039 entry (re-verified this cycle, lines 662-676).
- Confirmed current closing sentence (re-verified this cycle): "No other active items exist outside the set listed here: NC-021, NC-023, NC-024, NC-025, NC-027, NC-028, NC-029, NC-031, NC-033, NC-034, NC-035, NC-036, NC-037, and NC-039." — this is NC-039's own procedure and may run before or after sibling removals from this same issue-conversion batch; only remove `NC-039` from whatever the list's actual current content is at execution time, not from this snapshot.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry and ID-list reference.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | Pass; NC-039 no longer present or listed in the closing enumeration |

## Completion criteria

- NC-039 no longer appears in the Active Items list or the closing ID enumeration (AC-3).

## Out of scope

- Any other NC entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after rows 1-4 |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260927-120057_nc039_decide-whether-rag-ingestion-scripts-should-adopt-structured-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124916
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
