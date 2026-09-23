## Goal

Delete all resolved-item removal-placeholder paragraphs from Parts 1 and 2 of `docs/00_governance_03_issue-and-uncertainty-management.md`.

## Scope

- **In-Scope**: Delete resolved-item removal-placeholder paragraphs from Parts 1 and 2 of `docs/00_governance_03_issue-and-uncertainty-management.md`; clean up resulting blank lines and orphaned headings
- **Out-of-Scope**: Creating a "Resolved Items" section; updating cross-references in ADR files or other documents that cite resolved items; modifying the Known Issue template or Status values; adding new issues or needs confirmation items

## Assumptions

- The issue's list of resolved items is complete and accurate
- No additional resolved items exist beyond those listed in the issue
- The identified phrases ("was resolved", "resolved and removed", "Its absence from the active list") reliably mark resolved-item paragraphs

## Design decisions

- Use phrase-based detection rather than heading-based deletion because some resolved items lack `#### ID` headings and appear as inline bold text within existing sections
- Do NOT create a "Resolved Items" section — the policy explicitly states resolved items are removed, not retained

## Alternatives considered

- Heading-based deletion only: rejected because several resolved items (RAG-005, DESIGN-1, EVENTBUS-001, EVENTBUS-002, CI-002, CI-003, CI-007, REQ-001, REQ-002) have no `#### ID` heading
- Retaining resolved items with a different status marker: rejected because the Current-Specification-Only Policy requires physical removal

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Scan the document for all phrases indicating resolved items: "was resolved", "resolved and removed", "Its absence from the active list", "**Resolved.**"
2. For each matched paragraph, delete the entire paragraph including its heading (if present), ensuring the deletion covers the full scope of the resolution claim
3. Clean up resulting blank lines and orphaned headings
4. Verify remaining open items retain their original formatting and ordering

### Method

**Phase 1: Preparation**
- Search for all phrases indicating resolved items to confirm completeness against the issue's list of 17 Known Issues + 3 Needs Confirmation items
- Note: some resolved items use bold text without `#### ID` headings (e.g., RAG-005, DESIGN-1, EVENTBUS-001, EVENTBUS-002, CI-003, CI-007, REQ-001, REQ-002); others have `#### ID` headings but contain resolved-item content (e.g., RAG-003, RAG-004, EVENTBUS-008, SHARED-001, CI-001, CI-002, CI-004, CI-005, CI-006)

**Phase 2: Deletion**
- Delete Part 1 resolved Known Issues (REQ-001): RAG-003, RAG-004, RAG-005, DESIGN-1, EVENTBUS-001, EVENTBUS-002, EVENTBUS-008, SHARED-001, CI-001, CI-002, CI-003, CI-004, CI-005, CI-006, CI-007, REQ-001, REQ-002
- Delete Part 2 resolved Needs Confirmation items (REQ-002): NC-022, NC-030, NC-038
- Clean up blank lines and orphaned headings after each deletion block

**Phase 3: Verification**
- Verify no resolved-item content remains in Active Items lists
- Verify remaining open items retain original formatting and ordering

### Details

**Part 1 resolved Known Issues to delete:**

1. RAG-003 (line ~107): Has `#### RAG-003` heading; content says "was resolved and removed from this active inventory 2026-09-14"
2. RAG-004 (line ~111): Has `#### RAG-004` heading; content says "was resolved and removed from this active inventory 2026-09-14"
3. RAG-005 (no heading): Bold text "**RAG-005**: Resolved." followed by resolution details
4. DESIGN-1 (no heading): Plain text "DESIGN-1 ... was resolved and removed from this active inventory 2026-09-14"
5. EVENTBUS-001 (no heading): Bold text "**EVENTBUS-001**: Resolved." followed by resolution details
6. EVENTBUS-002 (no heading): Bold text "**EVENTBUS-002**: Resolved." followed by resolution details
7. EVENTBUS-008 (line ~225): Has `#### EVENTBUS-008` heading; content says "was resolved 2026-09-14 and removed from this active inventory"
8. SHARED-001 (line ~229): Has `#### SHARED-001` heading; content says "was fully resolved this cycle"
9. CI-001 (line ~233): Has `#### CI-001` heading; content says "was resolved and removed from this active inventory 2026-09-15"
10. CI-002 (no heading): Plain text "CI-002 ... was resolved and removed from this active inventory 2026-09-09"
11. CI-003 (no heading): Bold text "**CI-003**: Resolved." followed by resolution details
12. CI-004 (line ~241): Has `#### CI-004` heading; content says "was resolved and removed from this active inventory 2026-09-14"
13. CI-005 (line ~247): Has `#### CI-005` heading; content says "was resolved and removed from this active inventory 2026-09-14"
14. CI-006 (line ~253): Has `#### CI-006` heading; content says "was resolved and removed from this active inventory 2026-09-14"
15. CI-007 (no heading): Plain text "CI-007 ... was resolved 2026-09-20"
16. REQ-001 (no heading): Plain text "REQ-001 ... was resolved 2026-09-20"
17. REQ-002 (no heading): Plain text "REQ-002 ... was resolved 2026-09-20"

**Part 2 resolved Needs Confirmation items to delete:**

1. NC-022 (line ~579): Has `#### NC-022` heading; content says "was resolved by owner review 2026-09-14"
2. NC-030 (line ~707): Has `#### NC-030` heading; content says "was resolved by owner review 2026-09-14"
3. NC-038 (line ~821): Has `#### NC-038` heading; `- **Status**: resolved` (note: Evidence field contains contradictory statement about being "genuinely unresolved" — verify before deletion)

**Cleanup actions:**
- Remove any resulting blank lines between remaining entries
- Ensure no orphaned headings remain where resolved-item paragraphs were deleted
- Maintain the existing ordering convention: entries grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group in ascending numeric order

## Compatibility considerations

- The Current-Specification-Only Policy requires physical removal of resolved items, not retention with a closed-out status — creating a "Resolved Items" section would violate this policy
- Existing cross-references in ADR files or other documents that cite resolved items are valid historical citations and must NOT be modified
- The Known Issue template and Status values must NOT be modified

## Security considerations

N/A: documentation-only task with no behavioral impact on security controls.

## Rollback considerations

- If deletions remove too many items, revert via git history — the original file can be restored from the last commit before changes
- If deletions miss items, re-scan for "was resolved"/"resolved and removed" phrases after initial implementation
- The primary risk is deleting an open item — mitigate by verifying each deletion against the issue's explicit list before removing

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual review | Read file and verify no "was resolved"/"resolved and removed" phrases remain in Active Items lists | No resolved-item content in Active Items |

## Completion criteria

- All 17 resolved Known Issues are physically deleted from the Active Items list in Part 1
- All 3 resolved Needs Confirmation items are physically deleted from the Active Items list in Part 2
- No "Resolved Items" section exists anywhere in the document
- Remaining open items retain their original formatting and ordering
- No blank lines or orphaned headings remain from deletions

## Out of scope

- Updating cross-references in ADR files or other documents that cite resolved items (those are valid historical citations)
- Modifying the Known Issue template or Status values
- Adding new issues or needs confirmation items
- Creating a "Resolved Items" section (policy prohibits retention of resolved items)

## Execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — scan for all resolved-item indicators | Pending | — | — | |
| 2 | Phase 2: Delete 17 resolved Known Issues from Part 1 | Pending | — | — | |
| 3 | Phase 2: Delete 3 resolved Needs Confirmation items from Part 2 | Pending | — | — | |
| 4 | Phase 2: Clean up blank lines and orphaned headings | Pending | — | — | |
| 5 | Phase 3: Verify no resolved-item content remains | Pending | — | — | |
| 6 | Phase 3: Verify remaining items retain formatting and ordering | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20260923-173936_doc-cleanup_remove-resolved-items-from-issue-and-uncertainty-management.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-184926_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-190432
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
