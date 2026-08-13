# Implementation Procedure: Shared — DB Maintenance and Rotation Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed function signatures, dataclass definitions, and other implementation specifics while preserving critical operational guidance on operational purpose of maintenance functions, distinction between STRICT/BEST_EFFORT, caution around WAL checkpoint/VACUUM/purge/prune, that RAG consistency checks are read-only only.

## Scope

**In-Scope:**
- `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` — compress full maintenance function signatures, MaintenanceResult dataclass definitions, verbose processing explanations of purge/prune, rotation function lists, complete field lists of RagConsistencyReport, usage example code; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for maintenance/rotation/consistency decisions
- Maintenance operation boundary judgments are important and must maintain accuracy
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full signatures, dataclass definitions, and verbose processing explanations but keep references to where they live (`scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/db/rag_consistency.py`, etc.)
- **Preserve maintenance function operational purpose**: Keep explicit note of operational purpose of maintenance functions
- **Preserve STRICT vs BEST_EFFORT meaning**: Keep explicit statement of distinction between STRICT and BEST_EFFORT
- **Preserve BEST_EFFORT result.success always-check necessity**: Keep explicit note of need to always check result.success under BEST_EFFORT
- **Preserve WAL checkpoint/VACUUM/purge/prune operational notes**: Keep explicit note of operational considerations for these operations
- **Preserve DB rotation for backup/archive**: Keep explicit note that DB rotation is for backup/archive purposes
- **Preserve SQLite online backup API maintains WAL consistency**: Keep explicit note of WAL consistency maintained by SQLite online backup API
- **Preserve RAG consistency check read-only-only**: Keep explicit note that RAG consistency checks don't repair
- **Preserve operational judgment when FTS/vec inconsistency found**: Keep explicit note of operational judgment when FTS/vec inconsistency discovered
- **Preserve embed_failed caller-provided information**: Keep explicit note that embed_failed is caller-provided information

## Alternatives Considered

1. **Full deletion of function signatures** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` | Compress maintenance function signatures, MaintenanceResult dataclass, purge/prune explanations, rotation functions, RagConsistencyReport fields, usage examples; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (maintenance function operational purpose, STRICT vs BEST_EFFORT meaning, BEST_EFFORT result.success always-check necessity, WAL checkpoint/VACUUM/purge/prune operational notes, DB rotation for backup/archive, SQLite online backup API maintains WAL consistency, RAG consistency check read-only-only, operational judgment when FTS/vec inconsistency found, embed_failed caller-provided information)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `MaintenanceResult`, `purge`, `prune`, `RagConsistencyReport`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/maintenance.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`**
- Full maintenance function signatures: Replace with prose summary referencing `scripts/db/maintenance.py`
- MaintenanceResult dataclass definitions: Replace with prose summary
- Verbose processing explanations of purge/prune: Replace with prose summary
- Rotation function lists: Replace with prose summary referencing `scripts/db/rotation.py`
- Complete field lists of RagConsistencyReport: Replace with prose summary referencing `scripts/db/rag_consistency.py`
- Usage example code: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/maintenance.py`, `scripts/db/rotation.py`, and `scripts/db/rag_consistency.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about BEST_EFFORT result-checking requirement and RAG consistency check read-only statement
- Known issue note about caching duplication must be preserved
- BEST_EFFORT result-checking requirement must be verified as clear
- RAG consistency check read-only statement must be verified as clear

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| BEST_EFFORT result-checking requirement preserved | Manual | Explicitly stated |
| RAG consistency check read-only statement preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/maintenance.py` / `rotation.py` / `rag_consistency.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full function signatures/dataclass definitions remain | Manual | Scanning for remaining verbose definitions |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-220158_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
