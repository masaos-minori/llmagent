## Goal

Remove EVENTBUS-006 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once the subscriber (rows 1-2) is implemented and verified (REQ-005).

## Scope

In scope: removing the EVENTBUS-006 entry and updating any adjacent cross-reference. Out of scope: any other entry in this document.

## Assumptions

- Rows 1-2 of this Plan (the subscriber and its tests) are fully implemented and validated before this row is executed.

## Design decisions

- Remove the entry outright, per this document's Lifecycle rule (same convention as the EVENTBUS-005 procedure's equivalent row).

## Alternatives considered

- Marking `Status: resolved` instead of removing: rejected — contradicts this document's explicit Lifecycle rule.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm EVENTBUS-006's exact current line range immediately before editing.
2. Remove the entire EVENTBUS-006 entry block.
3. Check whether EVENTBUS-005's or EVENTBUS-007's `Related` field cites `EVENTBUS-006` and update per the "Removal-placeholder-reference policy" if either is still present at this point.

### Method

Single-entry removal, same convention as the EVENTBUS-005 procedure's equivalent row.

### Details

- EVENTBUS-006 was confirmed present at lines 153-171 as of this Plan's investigation — re-confirm exact current lines before editing.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the removed entry text.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual + automated | `uv run python tools/check_needs_confirmation_inventory.py`, Read the Active Items list | EVENTBUS-006 no longer present; no dangling `Related` reference to it remains |

## Completion criteria

- EVENTBUS-006 no longer appears in the Active Items list (AC-5).

## Out of scope

- Any other Known Issue or Needs Confirmation entry in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-141518 | 20260927-141518 | Execute only after rows 1-2 are implemented and validated |
| 2 | Add or update tests per Validation plan | Completed | 20260927-141518 | 20260927-141518 | N/A: documentation-only, manual + automated per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-141518 | 20260927-141518 | N/A: documentation-only; `check_needs_confirmation_inventory.py` run instead check_needs_confirmation_inventory.py: N/A, same pre-existing tool/filename mismatch as prior cycles. check_docs_quality.py/check_docs_structure.py: same 3 pre-existing Lifecycle-similarity warnings + file-size finding as prior cycles, unrelated. EVENTBUS-006 fully removed, EVENTBUS-007's Related field updated to None (its only remaining reference) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-141518 | 20260927-141518 | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260927-115629_eventbus006_implement-agent-eventbus-sse-subscribe-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-120532_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123444
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md