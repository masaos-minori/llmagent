# Implementation Procedure: Shared — DB Schema Reference Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed DDL text, column lists, and other implementation specifics while preserving critical operational guidance on why db/schema_sql.py is the canonical source of schema truth, meaning of rag.sqlite/session.sqlite/workflow.sqlite, why session_diagnostics is separated from messages, workflow_schema_version-based version management, FATAL-on-mismatch policy, timestamp format unification policy, RAG FTS auto-sync trigger operational notes, and prohibition of chunks_fts manual sync.

## Scope

**In-Scope:**
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md` — compress full DDL text, table-by-table column lists, FTS5 virtual table definitions, vec virtual table definitions, SQL-equivalent trigger explanations, workflow table column lists, schema version table column lists; preserve design rationales
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` — same compression targets

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for DB canonical source and schema policy decisions
- Schema version mismatch handling and FTS sync rules are important for accuracy and must NOT be weakened
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full DDL text, column lists, and verbose processing explanations but keep references to where they live (`scripts/db/schema_sql.py`, etc.)
- **Preserve db/schema_sql.py as canonical source**: Keep explicit note that this module is the canonical source of schema truth
- **Preserve rag.sqlite/session.sqlite/workflow.sqlite meaning**: Keep explicit note of what each database represents
- **Preserve session_diagnostics separation from messages**: Keep explicit note of why session_diagnostics is separated
- **Preserve workflow_schema_version-based version management**: Keep explicit statement of version management approach
- **Preserve FATAL-on-mismatch policy**: Keep explicit note of FATAL-on-mismatch policy
- **Preserve timestamp format unification policy**: Keep explicit note of timestamp format unification
- **Preserve RAG FTS auto-sync trigger operational notes**: Keep explicit note of operational considerations for auto-sync triggers
- **Preserve chunks_fts manual sync prohibition**: Keep explicit note of prohibition of manual chunks_fts sync

## Alternatives Considered

1. **Full deletion of DDL text** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target Files

| File | Action |
|------|--------|
| `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md` | Compress DDL text, column lists, FTS5/vec definitions, trigger explanations, workflow table columns, schema version table columns; preserve design rationales |
| `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` | Same compression targets |

### Procedure

1. Read both target files to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (db/schema_sql.py as canonical source, rag.sqlite/session.sqlite/workflow.sqlite meaning, session_diagnostics separation, workflow_schema_version-based version management, FATAL-on-mismatch policy, timestamp format unification, RAG FTS auto-sync trigger operational notes, chunks_fts manual sync prohibition)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `CREATE TABLE`, `schema_sql.py`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/schema_sql.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`**
- Full DDL text: Replace with prose summary referencing `scripts/db/schema_sql.py`
- Table-by-table column lists: Replace with prose summary
- FTS5 virtual table definitions: Replace with prose summary
- vec virtual table definitions: Replace with prose summary
- SQL-equivalent trigger explanations: Replace with prose summary
- Workflow table column lists: Replace with prose summary
- Schema version table column lists: Replace with prose summary

**File: `90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md`**
- Same compression targets as part1

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/schema_sql.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about FATAL-on-mismatch policy and manual-FTS-sync prohibition
- Known issue note about caching duplication must be preserved
- FATAL-on-mismatch policy must be verified as clear
- manual-FTS-sync prohibition must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| FATAL-on-mismatch policy preserved | Manual | Explicitly stated |
| Manual-FTS-sync prohibition preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/schema_sql.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full DDL text/column lists remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the two target files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215218_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md, docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md
