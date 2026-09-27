## Goal

Remove NC-037 from the Needs Confirmation inventory's Active Items once its resolution (row 1) is applied (REQ-003).

## Scope

In scope: removing the NC-037 entry block and updating the closing ID enumeration. Out of scope: any other NC entry.

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

1. Re-confirm NC-037's exact current line range (confirmed present, unchanged, at lines 645-659 as of this cycle) immediately before editing.
2. Remove the entire NC-037 entry block.
3. Update the closing "No other active items exist outside the set listed here: ..." sentence to remove `NC-037`.

### Method

Single-entry removal plus a one-item edit to the closing enumeration.

### Details

- Confirmed current NC-037 entry (re-verified this cycle, lines 645-659) — note its own `Evidence` field cites a stale constant name (`HEALTH_CHECK_RETRY_DELAY_SEC`), already corrected in this Plan's Background/Problem; the removal itself is unaffected by that staleness.
- CORRECTION (Step 4a re-verification, this cycle): `stale_detector.py` reported `line_out_of_bounds` (cited line 659 > current file length 653/654) — the file has shrunk from earlier batches in this same NC-cleanup effort (NC-023/024/025/031 removed above this entry), not from any change to NC-037 itself. Re-confirmed via Read: NC-037's entry, content unchanged, now sits at lines 483-498. User confirmed proceeding on this basis (content independently re-verified, not merely assumed).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry and ID-list reference.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | Pass; NC-037 no longer present or listed in the closing enumeration |

## Completion criteria

- NC-037 no longer appears in the Active Items list or the closing ID enumeration (AC-2).

## Out of scope

- Any other NC entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-161958 | 20260927-161958 | Row 1 applied first (owner ruling: no-retry is confirmed intentional policy). stale_detector line_out_of_bounds correction recorded above (Step 4b) — proceeded with user confirmation after independent Read re-verification. Removed entry block and updated the closing NC-id enumeration |
| 2 | Add or update tests per Validation plan | Completed | 20260927-161958 | 20260927-161958 | N/A: documentation-only, manual + automated per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-161958 | 20260927-161958 | N/A: documentation-only; `check_needs_confirmation_inventory.py` run instead — exit 0, no NC-037 finding |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-161958 | 20260927-161958 | N/A: this document's own target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `stale_detector.py` reported `line_out_of_bounds` for the cited NC-037 line range (659 > current file length) — cumulative drift from other batches' earlier removals in the same file, not a content change | Yes — content re-verified unchanged via Read; user confirmed proceeding | 20260927-161958 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260927-115931_nc037_confirm-whether-a-configurable-mcp-health-check-retry-policy-was-intended.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121645_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124733
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
