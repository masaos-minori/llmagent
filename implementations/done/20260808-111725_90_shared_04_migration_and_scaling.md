# Implementation Procedure: Shared — DB Migration and Scaling Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed migration names, ALTER TABLE details, and other implementation specifics while preserving critical operational guidance on schema initialization/migration policy, why rag/session/eventbus have no compatibility migrations, why only workflow.sqlite has incremental migrations, why mdq.sqlite has a separate legacy schema detection mechanism, criteria for schema changes, data loss risk during DB recreation, single-node SQLite scaling limits, that numeric thresholds are estimates requiring environment-specific validation, and migration warning checklist.

## Scope

**In-Scope:**
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` — compress internal migration list names, ALTER TABLE details, implementation details like catching duplicate column name errors, RAG consistency function internal judgment expressions, AI reference tables, overly detailed canonical source lists, deterministic-as-stated numeric thresholds; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for migration/scaling/schema change policy decisions
- Numeric thresholds are estimates requiring environment-specific validation
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full migration lists, ALTER TABLE details, and verbose processing explanations but keep references to where they live (`scripts/db/rag_consistency.py`, `scripts/db/helper.py`, etc.)
- **Preserve schema initialization/migration policy**: Keep explicit note of schema initialization/migration policy
- **Preserve rag/session/eventbus no compatibility migration**: Keep explicit note that these have no compatibility migrations
- **Preserve workflow.sqlite incremental-only**: Keep explicit note that only workflow.sqlite has incremental migrations
- **Preserve mdq.sqlite legacy schema detection**: Keep explicit note of mdq.sqlite's separate legacy schema detection mechanism
- **Preserve schema change criteria**: Keep explicit statement of criteria for when to apply schema changes
- **Preserve data loss risk during DB recreation**: Keep explicit note of data loss risk
- **Preserve single-node SQLite scaling limits**: Keep explicit note of scaling limits
- **Preserve numeric thresholds as estimates**: Keep explicit note that thresholds are estimates requiring environment-specific validation
- **Preserve migration warning checklist**: Keep explicit note of migration warning checklist

## Alternatives Considered

1. **Full deletion of migration lists** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` | Compress migration names, ALTER TABLE details, duplicate column error handling, RAG consistency expressions, AI reference tables, canonical source lists, deterministic thresholds; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (schema initialization/migration policy, rag/session/eventbus no compatibility migration, workflow.sqlite incremental-only, mdq.sqlite legacy schema detection, schema change criteria, data loss risk, single-node SQLite scaling limits, numeric thresholds as estimates, migration warning checklist)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `migration`, `ALTER TABLE`, `rag_consistency`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/rag_consistency.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`**
- Internal migration list names: Replace with prose summary referencing `scripts/db/helper.py`
- ALTER TABLE details: Replace with prose summary
- Duplicate column name error handling: Replace with prose summary
- RAG consistency function internal judgment expressions: Replace with prose summary referencing `scripts/db/rag_consistency.py`
- AI reference tables: Replace with prose summary
- Overly detailed canonical source lists: Replace with prose summary
- Deterministic-as-stated numeric thresholds: Replace with prose summary, frame as estimates

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/rag_consistency.py`, `scripts/db/helper.py`, and related modules must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about migration vs recreation criteria, data loss warnings, and threshold estimates
- Known issue note about caching duplication must be preserved
- Migration vs recreation criteria must be verified as clear
- Data loss warnings must be verified as clear
- Numeric thresholds must be verified as estimates

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| Migration vs recreation criteria preserved | Manual | Explicitly stated |
| Data-loss warnings preserved | Manual | Explicitly stated |
| Thresholds as estimates | Manual | Explicitly framed as estimates |
| Cross-references valid | Manual | All removed details point to `scripts/db/rag_consistency.py` / related modules |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full migration lists/ALTER TABLE details remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-215106_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
