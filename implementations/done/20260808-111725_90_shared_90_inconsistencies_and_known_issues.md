# Implementation Procedure: Shared DB — Known Issues & Inconsistencies Documentation Restructuring

## Goal

Restructure shared/DB design documentation chapter to remove overly detailed metadata field templates while preserving critical operational guidance on each known issue's meaning, why it matters, operational notes, and fix decision criteria. Explicitly preserve SHARED-001 (recover_corruption propagating exceptions during actual page corruption) and its unresolved status.

## Scope

**In-Scope:**
- `docs/90_shared_90_inconsistencies_and_known_issues.md` — compress complete 17-field error template, unverified metadata fields (Owner / First Found / Target / Related), migration notes (where applicable), detailed implementation file/test names, mechanical documentation gap classification; preserve design rationales

**Out-of-Scope:**
- Other shared/DB-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/db/recovery.py` or related modules
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for known issue decisions
- `rules/coding.md` "Current behavior" classification table is valid and entries must be verified against current code before deletion
- SHARED-001 impact and unresolved statement must NOT be weakened
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full error templates, metadata field lists, and verbose processing explanations but keep references to where they live (`scripts/db/recovery.py`)
- **Preserve each known issue's meaning**: Keep explanation of what each known issue represents
- **Preserve why each issue matters**: Keep explicit note of operational impact
- **Preserve operational notes**: Keep operational guidance for each issue
- **Preserve fix decision criteria**: Keep explicit note of when/how to fix each issue
- **Preserve SHARED-001 impact**: Keep explicit statement that recover_corruption does not propagate exceptions during actual page corruption
- **Preserve SHARED-001 unresolved status**: Keep explicit note that SHARED-001 remains unresolved
- **Apply five-way classification**: Classify each entry per `rules/coding.md` §「Current behavior」table

## Alternatives Considered

1. **Full deletion of error templates** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_90_inconsistencies_and_known_issues.md` | Compress error templates, metadata fields, migration notes, file/test names, gap classifications; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (each known issue's meaning, why it matters, operational notes, fix decision criteria, SHARED-001 impact and unresolved status)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `RecoveryResult`, `recover_corruption`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/recovery.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_90_inconsistencies_and_known_issues.md`**
- Complete 17-field error template: Replace full template with prose summary referencing `scripts/db/recovery.py`
- Unverified metadata fields: Replace field enumeration with prose summary
- Migration notes: Replace migration notes with prose summary (where applicable)
- Detailed implementation file/test names: Replace file/test enumeration with prose summary
- Mechanical documentation gap classification: Replace gap classification with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/recovery.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about SHARED-001 impact and unresolved status
- Known issue note about caching duplication must be preserved
- Five-way classification must be applied consistently across all entries

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| SHARED-001 impact and unresolved status preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/recovery.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| Five-way classification applied | Manual | Each entry classified per `rules/coding.md` |
| No full error templates/metadata fields remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/db/recovery.py` or related modules
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared/DB chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-213056_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_90_inconsistencies_and_known_issues.md
