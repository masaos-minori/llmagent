# Implementation Procedure: Shared DB — Architecture Overview & Config Documentation Restructuring

## Goal

Restructure shared/DB design documentation chapter to remove overly detailed directory structures, field definitions, and PRAGMA enumerations while preserving critical operational guidance on why DB files are split, SQLiteHelper role, sqlite-vec usage limited to RAG, WAL/busy_timeout/foreign_keys operational meaning, and Event Bus runtime being out of scope.

## Scope

**In-Scope:**
- `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` — compress db/ directory structure, DbConfig full field definition, SQLiteHelper constructor details, open() argument explanations, mechanical PRAGMA enumeration, begin_immediate/begin_exclusive implementation details; preserve design rationales

**Out-of-Scope:**
- Other shared/DB-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/db/config.py` or `scripts/db/helper.py`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for DB architecture decisions
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision
- Event Bus runtime is explicitly out of scope for this document

## Design Decisions

- **Compress over delete**: Remove full directory structures, field lists, and PRAGMA enumerations but keep references to where they live (`scripts/db/config.py`, `scripts/db/helper.py`)
- **Preserve DB file split rationale**: Keep explanation of why DB files are split into rag/session/workflow/eventbus responsibility boundaries
- **Preserve SQLiteHelper role**: Keep explanation of SQLiteHelper as the central connection management component
- **Preserve sqlite-vec constraint**: Keep explicit note that sqlite-vec is used only for RAG
- **Preserve PRAGMA operational meaning**: Keep explanations for WAL mode, busy_timeout, foreign_keys enforcement
- **Preserve db_path override necessity**: Keep explanation of why db_path override is needed
- **Preserve Event Bus exclusion**: Keep note that Event Bus runtime is out of scope for this document

## Alternatives Considered

1. **Full deletion of directory structures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` | Compress db/ directory structure, DbConfig fields, SQLiteHelper constructor, open() args, PRAGMA enum, begin_immediate/exclusive details; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (DB file split rationale, SQLiteHelper role, sqlite-vec constraint, PRAGMA meanings, db_path override necessity)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `DbConfig`, `SQLiteHelper`, `open()`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/config.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`**
- db/ directory structure: Replace tree diagram with prose summary noting rag/session/workflow/eventbus boundary separation
- DbConfig: Replace full field definition with prose summary referencing `scripts/db/config.py`
- SQLiteHelper constructor: Replace constructor details with prose summary referencing `scripts/db/helper.py`
- open() arguments: Replace complete argument explanations with prose summary
- PRAGMA enumeration: Replace mechanical PRAGMA list with prose summary noting WAL/busy_timeout/foreign_keys operational meaning
- begin_immediate/begin_exclusive: Replace implementation details with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/config.py` and `scripts/db/helper.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about DB file split rationale and sqlite-vec constraint
- Known issue note about caching duplication must be preserved

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| DB file split rationale preserved | Manual | Rag/session/workflow/eventbus boundaries explicitly stated |
| sqlite-vec constraint preserved | Manual | RAG-only usage explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/config.py` / `scripts/db/helper.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full field definitions/PRAGMA lists remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/db/config.py` or `scripts/db/helper.py`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared/DB chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-211418_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md
