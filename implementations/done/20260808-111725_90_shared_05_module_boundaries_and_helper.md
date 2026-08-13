# Implementation Procedure: Shared — DB Module Boundaries and Helper Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed method tables, constructor signatures, and other implementation details while preserving critical operational guidance on why db.store is the public API surface, why store_protocols/store_impl are internal boundaries, responsibility split during DB store extension, SQLiteHelper's operational role, special nature of pragma application to raw sqlite3 connections, purpose of transaction helpers, and treatment of VACUUM/DDL as exclusive operations.

## Scope

**In-Scope:**
- `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` — compress SQLiteHelper full method table, mechanical explanations of execute/fetchall/commit/close, full constructor signatures, open() argument tables, typical usage example code, apply_connection_pragmas caller site lists; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for DB API boundary decisions
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full method tables, constructor signatures, and verbose processing explanations but keep references to where they live (`scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/helper.py`)
- **Preserve db.store public API surface**: Keep explicit note that db.store is the public API surface
- **Preserve store_protocols/store_impl internal boundary**: Keep explicit note that these are internal boundaries
- **Preserve caller import destination**: Keep explicit note of where callers import from
- **Preserve responsibility split during DB store extension**: Keep explicit statement of responsibility split
- **Preserve SQLiteHelper operational role**: Keep explicit note of SQLiteHelper's operational role
- **Preserve pragma application to raw sqlite3 connection**: Keep explicit note of special nature of pragma application
- **Preserve transaction helper purpose**: Keep explicit note of transaction helper purpose
- **Preserve VACUUM/DDL as exclusive operation**: Keep explicit note of VACUUM/DDL treated as exclusive operations

## Alternatives Considered

1. **Full deletion of method tables** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` | Compress SQLiteHelper method table, execute/fetchall/commit/close explanations, constructor signatures, open() argument tables, usage examples, pragma caller lists; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (db.store public API surface, store_protocols/store_impl internal boundary, caller import destination, responsibility split during DB store extension, SQLiteHelper operational role, pragma application special nature, transaction helper purpose, VACUUM/DDL exclusive operation treatment)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `SQLiteHelper`, `execute`, `fetchall`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/helper.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`**
- SQLiteHelper full method table: Replace table with prose summary referencing `scripts/db/helper.py`
- Mechanical explanations of execute/fetchall/commit/close: Replace with prose summary
- Full constructor signatures: Replace with prose summary
- open() argument tables: Replace with prose summary
- Typical usage example code: Replace with prose summary
- apply_connection_pragmas caller site list: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, and `scripts/db/helper.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about db.store public API surface and store_protocols/store_impl internal boundaries
- Known issue note about caching duplication must be preserved
- db.store public API surface must be verified as clear
- store_protocols/store_impl internal boundary must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| db.store public API surface preserved | Manual | Explicitly stated |
| store_protocols/store_impl internal boundary preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/store.py` / `store_protocols.py` / `store_impl.py` / `helper.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full method tables/constructor signatures remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215003_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
