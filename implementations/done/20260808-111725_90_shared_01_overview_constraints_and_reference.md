# Implementation Procedure: Shared — Overview Constraints & Reference Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed constraint value tables, question tables, and verbose processing explanations while preserving critical operational guidance on import direction constraints, enforcement by import-linter, persistent DB overall picture, cross-cutting constraints (JSON/orjson, httpx, English-only logging, SQLite WAL), and SecurityProfile/ProductionConfigValidator operational meaning.

## Scope

**In-Scope:**
- `docs/90_shared_01_03_overview-constraints-and-reference.md` — compress overly fine-grained constraint value table, AI reference guide question table, mechanical DB table enumeration, duplicate Related Documents/Keywords; preserve design rationales

**Out-of-Scope:**
- Other shared/overview-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for import constraints and cross-cutting constraints decisions
- import-direction rule is a hard architecture boundary enforced by lint-imports and must remain clear
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full constraint value tables, question tables, and verbose processing explanations but keep references to where they live (`scripts/shared/`, `scripts/db/`)
- **Preserve import direction constraints**: Keep explanation of import direction constraints
- **Preserve import-linter enforcement**: Keep explicit note that import-linter enforces import-direction rules
- **Preserve persistent DB overall picture**: Keep explicit note of persistent DB overall picture
- **Preserve cross-cutting constraints**: Keep explicit statement of JSON/orjson, httpx, English-only logging, SQLite WAL
- **Preserve SecurityProfile/ProductionConfigValidator operational meaning**: Keep explicit note of SecurityProfile/ProductionConfigValidator operational meaning

## Alternatives Considered

1. **Full deletion of constraint value tables** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_01_03_overview-constraints-and-reference.md` | Compress constraint value table, AI reference questions, DB table enumeration, duplicate Related Documents/Keywords; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (import direction constraints, import-linter enforcement, persistent DB overall picture, cross-cutting constraints, SecurityProfile/ProductionConfigValidator operational meaning)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `constraint`, `import`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/shared/`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_01_03_overview-constraints-and-reference.md`**
- Overly fine-grained constraint value table: Replace table with prose summary referencing `scripts/shared/` and `scripts/db/`
- AI reference guide question table: Replace question table with prose summary
- Mechanical DB table enumeration: Replace table enumeration with prose summary
- Duplicate Related Documents/Keywords: Remove duplicates, keep single canonical entry

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/shared/` and `scripts/db/` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about import direction constraints and import-linter enforcement
- Known issue note about caching duplication must be preserved
- Import direction constraints must be verified as clear
- lint-imports enforcement must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Import-direction constraints preserved | Manual | Explicitly stated |
| lint-imports enforcement preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/shared/` / `scripts/db/` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full constraint value tables/question tables remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared/overview chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-214024_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_01_03_overview-constraints-and-reference.md
