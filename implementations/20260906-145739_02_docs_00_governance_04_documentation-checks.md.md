## Goal
Remove Manual Check 9's numbered list item 2 ("The most recently reviewed document
is authoritative among conflicting documents") and replace it with a reference to
seq 01's new "Recency Is Not Authority" subsection (REQ-001, REQ-005).

## Scope
- In scope: item 2 only, within "### 9. Canonical Source Verification" (currently
  line 185).
- Out of scope: item 1 (`M-01-02`'s scope, tracked in that Plan's own procedure
  documents, already generated this session under
  `implementations/20260906-145512_02_docs_00_governance_04_documentation-checks.md.md`)
  and item 3 (area document-guide, unrelated).

## Assumptions
- This row depends on seq 01 (`docs/00_governance_01_documentation-policy.md`'s new
  "Recency Is Not Authority" subsection) landing first, so the replacement reference
  points to an existing subsection, not a forward reference to unwritten content.
- **Cross-Plan note**: `M-01-02`'s own row for this exact file
  (`implementations/20260906-145512_02_docs_00_governance_04_documentation-checks.md.md`)
  edits item 1 in the same numbered list this row edits item 2 in — if both Plans'
  implementations execute close together, re-read the current numbered list before
  editing to apply this row's change on top of (not instead of) that Plan's item-1
  edit.

## Design decisions
- Replace item 2's text with a one-line reference (e.g. "Recency
  (review/modification/commit date) never determines canonical authority — see
  `00_governance_01_documentation-policy.md`'s Recency Is Not Authority
  subsection"), matching the reference-not-restate pattern seq 01 of `M-01-02`'s
  procedure already applies to item 1.

## Alternatives considered
- Delete item 2 entirely with no replacement: rejected — Design section (this Plan)
  explicitly calls for a cross-reference, not silent removal, so a reader checking
  Manual Check 9 still finds a pointer to where recency's role IS defined.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Confirm seq 01 has landed (the "Recency Is Not Authority" subsection exists in
   `docs/00_governance_01_documentation-policy.md`) before editing this row.
2. Re-read the current numbered list under "### 9. Canonical Source Verification" —
   confirm item 2's current wording and number (may have shifted if `M-01-02`'s item-1
   edit already landed and changed surrounding content).
3. Replace item 2 with the cross-reference sentence; leave items 1 and 3 as they are
   at the time of this edit (whatever `M-01-02`'s own row has made of item 1).

### Method
Confirmed this cycle (2026-09-06) via direct read: item 2 at line 185 reads exactly
"The most recently reviewed document is authoritative among conflicting documents" —
no drift from the Plan's citation. Item 1 (line 184, `M-01-02`'s scope) confirmed
still in its original unmodified form as of this cycle (that Plan's own procedure
document, seq 02, has not yet been executed as code).

### Details
No change to item 3 or any other Manual Check.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py` flags an
issue, or if this row's edit conflicts with `M-01-02`'s concurrent item-1 edit to the
same numbered list (reconcile by re-reading current content, not by force-applying).

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md`
- `rg -i "most recent|latest reviewed" docs/` — confirm no remaining match.

## Completion criteria
- Item 2 no longer asserts recency-based authority; it references the new "Recency
  Is Not Authority" subsection instead.

## Out of scope
- Item 1 — `M-01-02`'s scope (separate Plan, procedure already generated).
- Item 3 — unrelated.
- `docs/00_governance_01_documentation-policy.md` — tracked in seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on seq 01 landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20260903-103026_m0103_remove-document-recency-as-canonical-authority-rule.md
- **Source plan**: plans/20260905-165006_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145739
- **Related target files**: docs/00_governance_04_documentation-checks.md
