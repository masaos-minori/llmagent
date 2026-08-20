# Implementation Procedure: Restructure NC Inventory — Add Archive Section and Fix NC-005 Duplicate Field

## Goal
Restructure `docs/00_governance_07_needs-confirmation-inventory.md`:
1. Add "Archived (Resolved) Items" section after existing "Inventory Items" section
2. Move all 17 `Status: resolved` NC entries verbatim to the archive section
3. Leave "Inventory Items" explicitly empty with a note
4. Fix NC-005's duplicate `Last Reviewed` field (keep only the more recent 2026-07-29)

## Scope
- Target file: `docs/00_governance_07_needs-confirmation-inventory.md`
- Add archive section, move 17 entries, fix NC-005

## Assumptions
- All 17 current entries have `Status: resolved` (confirmed by grep)
- NC-005 has two `**Last Reviewed**:` lines (2026-07-29 and 2026-07-22); keep the more recent (2026-07-29)
- Single document approach (not separate file) per plan's "whichever keeps the existing doc's structure simplest"

## Design decisions
- Add "Archived (Resolved) Items" section after "Inventory Items" section
- Cut-paste (not rewrite) all 17 `### NC-00N` blocks to preserve content exactly
- Leave "Inventory Items" with explicit sentence: "No active (open/investigating/deferred) items as of {date} — all 17 originally tracked items have been resolved; see Archived (Resolved) Items below."
- Fix NC-005 by deleting the stale `**Last Reviewed**: 2026-07-22` line

## Implementation
### Target file
`docs/00_governance_07_needs-confirmation-inventory.md`

### Procedure
1. Read the file
2. Add "Archived (Resolved) Items" section after "Inventory Items" section (around line 322)
3. Cut all 17 `### NC-00N` blocks from "Inventory Items" and paste under archive heading in same order
4. Replace "Inventory Items" content with empty-state note
4. Fix NC-005: delete the second `**Last Reviewed**: 2026-07-22` line

### Method
Direct Markdown editing with structural cut-paste

### Details
**After "Inventory Items" section (around line 322), add:**
```markdown
## Archived (Resolved) Items

### NC-001
... (verbatim paste of NC-001 block)

### NC-002
... (verbatim paste of NC-002 block)

...
### NC-017
... (verbatim paste of NC-017 block)
```

**Replace "Inventory Items" section content with:**
```markdown
## Inventory Items

No active (open/investigating/deferred) items as of 2026-08-20 — all 17 originally tracked items have been resolved; see Archived (Resolved) Items below.
```

**NC-005 fix (in archived section):**
```markdown
### NC-005
...
- **Resolution**: Resolved — confirmed zero production callers via full-repo grep and git history back to initial commit. Both classes removed from `scripts/rag/models_audit.py`. See implementations/done/20260728-174511_models_audit.py.md.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29
```
(Delete the second `**Last Reviewed**: 2026-07-22` line that currently follows the first)

## Compatibility considerations
- Documentation-only change
- No content lost — all 17 entries preserved verbatim in archive
- NC-005 keeps the more recent review date

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file

## Validation plan
- `git diff docs/00_governance_07_needs-confirmation-inventory.md` — confirm:
  - All 17 NC IDs present exactly once each (not duplicated, not missing)
  - NC-005 has exactly one `Last Reviewed` line (2026-07-29)
  - Archive section contains all 17 entries in order
  - "Inventory Items" shows empty-state note

## Out of scope
- Resolving/closing any NC items
- Adding new NC entries (separate procedure)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134121
- Related target files: docs/00_governance_07_needs-confirmation-inventory.md