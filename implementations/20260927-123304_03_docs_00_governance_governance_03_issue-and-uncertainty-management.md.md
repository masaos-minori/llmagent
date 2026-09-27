## Goal

Remove EVENTBUS-005 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once the publish client (rows 1-2) is implemented and verified (REQ-004).

## Scope

In scope: removing the EVENTBUS-005 entry and updating any adjacent cross-reference count/list. Out of scope: any other entry in this document.

## Assumptions

- Rows 1-2 of this Plan (the client and its tests) are fully implemented and validated before this row is executed — this removal is the final step, not independent of the others.

## Design decisions

- Remove the entry outright rather than marking it "resolved" inline, per this document's own Consolidation Note and Lifecycle rule: "An item is removed from this active inventory once it is resolved... it is not retained here with a closed-out status."

## Alternatives considered

- Marking the entry `Status: resolved` instead of removing it: rejected — contradicts this document's own explicit Lifecycle rule for Known Issues.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm EVENTBUS-005's exact current line range immediately before editing (this file is frequently edited by concurrent governance work).
2. Remove the entire EVENTBUS-005 entry block.
3. Check whether any other entry's `Related` field cites `EVENTBUS-005` and update per this document's own "Removal-placeholder-reference policy" (a citation to a removed ID needs a removal-placeholder paragraph, or it becomes a dangling reference).

### Method

Single-entry removal, following the document's own established Lifecycle/Consolidation-Note conventions.

### Details

- EVENTBUS-005 was confirmed present at lines 133-151 as of this Plan's investigation — re-confirm exact current lines before editing, since this file changes frequently.
- EVENTBUS-006 and EVENTBUS-007 each list EVENTBUS-005 in their own `Related` field — if either is still present when this row executes, their `Related` field should drop the now-removed ID (or, if EVENTBUS-006/007 have also been resolved by their own Plans by this point, no action is needed here).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry text.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | EVENTBUS-005 no longer present; no dangling `Related` reference to it remains |

## Completion criteria

- EVENTBUS-005 no longer appears in the Active Items list (AC-4).
- No other entry has a dangling `Related` reference to EVENTBUS-005.

## Out of scope

- Any other Known Issue or Needs Confirmation entry in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute only after rows 1-2 are implemented and validated |
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
- **Source issue**: issues/done/20260927-115602_eventbus005_implement-agent-to-eventbus-publish-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120356_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123304
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
