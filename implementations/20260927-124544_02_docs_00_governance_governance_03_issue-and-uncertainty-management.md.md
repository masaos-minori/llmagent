## Goal

Remove NC-025 from the Needs Confirmation inventory's Active Items once its resolution (row 1) is applied (REQ-002).

## Scope

In scope: removing the NC-025 entry block and updating the closing ID enumeration. Out of scope: any other NC entry.

## Assumptions

- Row 1 is applied before this row executes.

## Design decisions

Remove the entry outright, per this document's Lifecycle rule.

## Alternatives considered

Marking `Status: resolved` instead of removing: rejected — contradicts the document's own Lifecycle rule.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm NC-025's exact current line range (confirmed present, unchanged, at lines 477-499 as of this cycle) immediately before editing.
2. Remove the entire NC-025 entry block.
3. Update the closing "No other active items exist outside the set listed here: ..." sentence to remove `NC-025`.

### Method

Single-entry removal plus a one-item edit to the closing enumeration.

### Details

- Confirmed current NC-025 entry (re-verified this cycle, lines 477-499).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry and ID-list reference.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | Pass; NC-025 no longer present or listed in the closing enumeration |

## Completion criteria

- NC-025 no longer appears in the Active Items list or the closing ID enumeration (AC-2).

## Out of scope

- Any other NC entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-155959 | 20260927-155959 | Row 1 applied first (owner decision: dedicated map needed, follow-up work). Re-confirmed at Step 4a: entry unchanged at lines 364-386 (line drift from cited 477-499 due to unrelated concurrent NC removals earlier in the same doc). Removed entry block and updated the closing NC-id enumeration |
| 2 | Add or update tests per Validation plan | Completed | 20260927-155959 | 20260927-155959 | N/A: documentation-only, manual + automated per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-155959 | 20260927-155959 | N/A: documentation-only; `check_needs_confirmation_inventory.py` run instead — exit 0, no NC-025 finding |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-155959 | 20260927-155959 | N/A: this document's own target file IS the documentation being updated |

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
- **Source issue**: issues/done/20260927-115841_nc025_decide-whether-a-configuration-ownership-map-or-api-consumer-map-is-needed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121503_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124544
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
