## Goal

Remove EVENTBUS-007 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once rows 1-6 are implemented and verified (REQ-006).

## Scope

In scope: removing the EVENTBUS-007 entry. Out of scope: any other entry in this document.

## Assumptions

- Rows 1-6 (endpoint, auth wiring, client, both test files) are fully implemented and validated before this row executes — **this row cannot execute until row 3's Blocker is resolved and rows 1-2, 5 unblock as a consequence.**

## Design decisions

- Remove the entry outright, per this document's Lifecycle rule (same convention as the EVENTBUS-005/006 procedures' equivalent rows).

## Alternatives considered

- Marking `Status: resolved` instead of removing: rejected — contradicts this document's explicit Lifecycle rule.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Confirm rows 1-6 are all Completed (not merely Pending) before starting this row.
2. Re-confirm EVENTBUS-007's exact current line range immediately before editing.
3. Remove the entire EVENTBUS-007 entry block.
4. Check whether EVENTBUS-005's or EVENTBUS-006's `Related` field cites `EVENTBUS-007` and update per the "Removal-placeholder-reference policy" if either is still present.

### Method

Single-entry removal, same convention as the EVENTBUS-005/006 procedures' equivalent rows.

### Details

- EVENTBUS-007 was confirmed present at lines 173-191 as of this Plan's investigation — re-confirm exact current lines before editing.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry text.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | EVENTBUS-007 no longer present |

## Completion criteria

- EVENTBUS-007 no longer appears in the Active Items list (AC-6), and only once rows 1-6 are genuinely Completed.

## Out of scope

- Any other Known Issue or Needs Confirmation entry in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Cannot execute until rows 1-6 are Completed, which requires row 3's Blocker to resolve first |
| 2 | Add or update tests per Validation plan | Blocked | — | — | N/A: documentation-only, manual + automated per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | N/A: documentation-only; `check_needs_confirmation_inventory.py` run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Blocked | — | — | N/A: this document's own target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Transitively blocked by row 3 (`scripts/eventbus/auth.py`)'s unresolved enforcement-model question | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
