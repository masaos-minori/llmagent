# Implementation Procedure: Shared — DB Overview and Config Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed directory structures, field definitions, and other implementation specifics while preserving critical operational guidance on reason for DB file splitting, role of SQLiteHelper, why sqlite-vec is used only for RAG, operational meaning of WAL/busy_timeout/foreign_keys, that db_path override is needed, and Event Bus runtime is out of scope of this document.

## Scope

**In-Scope:**
- `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` — compress db/ directory structure, full DbConfig field definitions, SQLiteHelper constructor details, full open() argument explanations, PRAGMA enumeration, begin_immediate/begin_exclusive implementation details; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for DB overall structure and SQLiteHelper decisions
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full directory structures, field definitions, and verbose processing explanations but keep references to where they live (`scripts/db/config.py`, `scripts/db/helper.py`, etc.)
- **Preserve DB layer purpose**: Keep explicit note of DB layer's purpose
- **Preserve DB file split rationale**: Keep explicit statement of reason for DB file splitting
- **Preserve rag/session/workflow/eventbus responsibility boundary**: Keep explicit note of responsibility boundaries between these databases
- **Preserve SQLiteHelper role**: Keep explicit note of SQLiteHelper's role
- **Preserve target-based DB switching policy**: Keep explicit note of DB switching policy by target
- **Preserve sqlite-vec only for RAG**: Keep explicit note that sqlite-vec is used only for RAG
- **Preserve WAL/busy_timeout/foreign_keys operational meaning**: Keep explicit note of operational meaning of these settings
- **Preserve db_path override necessity**: Keep explicit note of why db_path override is needed
- **Preserve Event Bus runtime out of scope**: Keep explicit note that Event Bus runtime is out of scope

## Alternatives Considered

1. **Full deletion of directory structures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` | Compress directory structure, DbConfig fields, SQLiteHelper constructors, open() arguments, PRAGMA lists, begin_immediate/begin_exclusive details; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (DB layer purpose, DB file split rationale, rag/session/workflow/eventbus responsibility boundary, SQLiteHelper role, target-based DB switching policy, sqlite-vec only for RAG, WAL/busy_timeout/foreign_keys operational meaning, db_path override necessity, Event Bus runtime out of scope)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `DbConfig`, `PRAGMA`, `sqlite-vec`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/config.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`**
- db/ directory structure: Replace with prose summary referencing `scripts/db/`
- Full DbConfig field definitions: Replace with prose summary referencing `scripts/db/config.py`
- SQLiteHelper constructor details: Replace with prose summary referencing `scripts/db/helper.py`
- Full open() argument explanations: Replace with prose summary
- PRAGMA enumeration: Replace with prose summary
- begin_immediate/begin_exclusive implementation details: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/config.py` and `scripts/db/helper.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about DB file split rationale and sqlite-vec-only-for-RAG constraint
- Known issue note about caching duplication must be preserved
- DB file split rationale must be verified as clear
- sqlite-vec-only-for-RAG constraint must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| DB file split rationale preserved | Manual | Explicitly stated |
| sqlite-vec-only-for-RAG constraint preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/config.py` / `helper.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full directory structures/field definitions remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215326_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md
