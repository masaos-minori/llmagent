# Implementation Procedure: Shared — Doc Guide Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed file indexes and AI query routing tables while preserving critical operational guidance on navigation guide role, doc set purpose, high-level chapter navigation, Canonical Source Rule, Known Issues handling, and a subset of operational/design decisions for safe AI usage.

## Scope

**In-Scope:**
- `docs/90_shared_00_document-guide.md` — compress overly detailed File Index, overly fine-grained AI Query Routing Table, keyword enumeration, mechanical full file name list, duplicate safety memos close to implementation details; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be maintained as a navigation guide (NOT an alternative to design documents)
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full file indexes, AI query routing tables, and verbose processing explanations but keep references to where they live (`scripts/shared/`, `scripts/db/`)
- **Preserve navigation guide role**: Keep explanation of navigation guide role
- **Preserve doc set purpose**: Keep explicit note of doc set purpose
- **Preserve high-level chapter navigation**: Keep explicit statement of high-level chapter navigation
- **Preserve Canonical Source Rule**: Keep explicit note of Canonical Source Rule
- **Preserve Known Issues handling**: Keep explicit note of Known Issues handling
- **Preserve safe AI usage subset**: Keep explicit note of subset of operational/design decisions for safe AI usage

## Alternatives Considered

1. **Full deletion of file indexes** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_00_document-guide.md` | Compress File Index, AI Query Routing Table, keyword enumeration, file name lists, duplicate safety memos; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (navigation guide role, doc set purpose, high-level chapter navigation, Canonical Source Rule, Known Issues handling, safe AI usage subset)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `File Index`, `AI Query Routing`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_00_document-guide.md`**
- Overly detailed File Index: Replace index with prose summary referencing `scripts/shared/` and `scripts/db/`
- Overly fine-grained AI Query Routing Table: Replace table with prose summary
- Keyword enumeration: Replace enumeration with prose summary
- Mechanical full file name list: Replace list with prose summary
- Duplicate safety memos close to implementation details: Replace duplicates with single canonical entry

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/` and `scripts/db/` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about navigation guide role and Canonical Source Rule
- Known issue note about caching duplication must be preserved
- Navigation guide role must be verified as clear
- Canonical Source Rule must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Navigation-guide role preserved | Manual | Explicitly stated |
| Canonical Source Rule preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/` / `scripts/db/` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full file indexes/AI query routing tables remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-214752_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_00_document-guide.md
