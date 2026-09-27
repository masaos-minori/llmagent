## Goal

Remove GV-007, GV-009, and GV-015 entries from the "Follow-up Work Needed" ordered list in `docs/00_governance/governance_04_documentation-checks.md`, reconciling the derived list with the authoritative Governance Verification Matrix. Renumber the remaining ordered list so numbering is contiguous with no gaps.

## Scope

Editing the "Follow-up Work Needed" ordered list section only in `docs/00_governance/governance_04_documentation-checks.md`. No changes to the Governance Verification Matrix itself; no changes to any other governance document.

## Assumptions

- The Governance Verification Matrix is the authoritative record of each rule's tooling status and follow-up state.
- The matrix rows for GV-007, GV-009, and GV-015 accurately reflect their current implementation status.
- The "Follow-up Work Needed" header states its inclusion criterion ("Missing" or "Partial"), so every listed rule must match that criterion.

## Design decisions

- Delete-only approach: remove entries whose matrix row reads `Status=Existing` / `Follow-up=None`; do not add or modify any entry.
- Renumber sequentially after deletions to maintain contiguous ordering.

## Alternatives considered

- Leave the list unchanged and update the matrix instead: rejected — the matrix is authoritative and is what the list is reconciled against.
- Add a note explaining why certain entries remain despite being marked complete: rejected — the list's own header defines its contract; adding exceptions would violate that contract.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Read the Governance Verification Matrix table to confirm the `Status` and `Follow-up` columns for GV-007, GV-009, and GV-015.
2. Locate the "Follow-up Work Needed" ordered list section below the matrix.
3. Identify all list items whose corresponding matrix row has `Status=Existing` / `Follow-up=None`.
4. Delete those list items.
5. Renumber the remaining ordered list so numbering starts at 1 and increments by 1 with no gaps.
6. Verify that every remaining list item corresponds to a matrix row with `Status=Missing` or `Status=Partial`.

### Method

Edit — targeted deletion of list items followed by sequential renumbering.

### Details

**Step 1: Confirm matrix rows**

Read the Governance Verification Matrix table (approximately lines 291-313). Verify:
- GV-007: `Status=Existing`, `Follow-up=None` (line 298)
- GV-009: `Status=Existing`, `Follow-up=None` (line 300)
- GV-015: `Status=Existing`, `Follow-up=None` (line 305)

**Step 2: Locate the "Follow-up Work Needed" list**

Read the ordered list section below the matrix (approximately lines 315-360). The list currently starts at item 4 (GV-007) and continues through item 14 (GV-020).

**Step 3: Identify entries to delete**

Cross-reference each list item against the matrix:
- Item 4 (GV-007): `Status=Existing` / `Follow-up=None` — delete
- Item 6 (GV-009): `Status=Existing` / `Follow-up=None` — delete
- Item 10 (GV-015): `Status=Existing` / `Follow-up=None` — delete

Also scan for any additional violations beyond these three.

**Step 4: Delete entries**

Delete the following sections:
- Item 4 (GV-007): line 319
- Item 6 (GV-009): line 321
- Item 10 (GV-015): lines 331-335

**Step 5: Renumber**

Renumber the remaining ordered list items sequentially starting from 1:
- Original item 5 (GV-008) → new item 1
- Original item 7 (GV-011, GV-012) → new item 2
- Original item 8 (GV-013) → new item 3
- Original item 9 (GV-014) → new item 4
- Original item 11 (GV-016) → new item 5
- Original item 12 (GV-018) → new item 6
- Original item 13 (GV-019) → new item 7
- Original item 14 (GV-020) → new item 8

**Step 6: Verify**

Confirm that every remaining list item corresponds to a matrix row with `Status=Missing` or `Status=Partial`:
- GV-008: `Status=Existing`, `Follow-up=Implement` — keep (has pending follow-up work)
- GV-011: `Status=Missing` — keep
- GV-012: `Status=Missing` — keep
- GV-013: `Status=Partial` — keep
- GV-014: `Status=Existing`, `Follow-up=Optional...` — keep (optional scope remains)
- GV-016: `Status=Missing` — keep
- GV-018: `Status=Missing` — keep
- GV-019: `Status=Missing` — keep
- GV-020: `Status=Partial` — keep

Note: GV-008 and GV-014 have `Status=Existing` but non-empty `Follow-up` values, so they correctly belong in the list per the header's stated criterion.

## Compatibility considerations

This change affects only the ordering list under "Follow-up Work Needed". No downstream artifact consumes this list programmatically — it is human-reviewed documentation. No backward compatibility impact.

## Security considerations

None. This is a documentation-only edit with no code or configuration changes.

## Rollback considerations

Rollback is straightforward: restore the original list items (4. GV-007, 6. GV-009, 10. GV-015) and revert the renumbering. A single `git checkout -- docs/00_governance/governance_04_documentation-checks.md` reverses the entire change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Governance Verification Matrix | Read both sections side-by-side | No entry in Follow-up Work Needed lists a rule with Status=Existing/Follow-up=None; all Missing/Partial rules are present |
| docs/00_governance/governance_04_documentation-checks.md | Optional structural check | `uv run python tools/check_docs_structure.py docs/00_governance/*.md` | No new structural findings |

## Completion criteria

- No entry in "Follow-up Work Needed" names a rule whose matrix row reads `Status=Existing` / `Follow-up=None`.
- Every rule with `Status=Missing` or `Status=Partial` in the matrix appears exactly once in the list.
- The ordered list numbering is contiguous with no gaps or duplicates.

## Out of scope

- Any change to the Governance Verification Matrix itself.
- Changing GV-007, GV-009, or GV-015 tooling, scope, or status.
- Editing any other governance document.
- Adding or removing list items beyond those identified above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove GV-007, GV-009, GV-015 entries from "Follow-up Work Needed" list | Completed | — | — | REQ-001, REQ-002, REQ-003 |
| 2 | Renumber the ordered list so numbering is contiguous | Completed | — | — | REQ-004 |
| 3 | Verify remaining list items correspond to Missing/Partial matrix rows | Completed | — | — | REQ-005 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260926-172320_gd001_reconcile-governance_04-follow-up-work-needed-list-with-governance-verification-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-185358_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-060329
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md