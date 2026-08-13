# Implementation Procedure: Shared — DB Recovery and Reference Documentation Restructuring

## Goal

Restructure shared design documentation chapter to remove overly detailed caller site code examples, dataclass definitions, and other implementation specifics while preserving critical operational guidance on intended scope of recover_corruption, known limitations when workflow/eventbus is passed, known issue of DatabaseError propagation during physical corruption, that DB recreation does not migrate existing data, that archive is needed before recreation, schema initialization is idempotent but doesn't convert existing data, and verification plan maintained as high-level quality gate.

## Scope

**In-Scope:**
- `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` — compress recover_corruption caller site code examples, RecoveryResult dataclass definitions, complete error behavior correspondence tables, DB recreation procedure shell command details, test command lists, AI reference tables; preserve design rationales

**Out-of-Scope:**
- Other shared-related chapters (`docs/90_shared_*.md`)
- Source code changes to `scripts/shared/` or `scripts/db/`
- Test modifications

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be the authoritative reference for recovery/recreation/verification decisions
- Recovery operation boundary judgments are important and must maintain accuracy
- Existing internal links and cross-references must remain valid after edits
- Compression preserves the "why" behind each design decision

## Design Decisions

- **Compress over delete**: Remove full caller site examples, dataclass definitions, and verbose processing explanations but keep references to where they live (`scripts/db/recovery.py`, etc.)
- **Preserve recover_corruption target limited to rag/session**: Keep explicit note that recover_corruption's targets should be limited to rag/session
- **Preserve known limitation when workflow/eventbus passed**: Keep explicit note of mismatch between displayed path and actual connection when workflow/eventbus is passed
- **Preserve known issue of DatabaseError propagation during physical corruption**: Keep explicit note of known issue with DatabaseError propagation
- **Preserve DB recreation doesn't migrate data**: Keep explicit statement that DB recreation does not migrate data
- **Preserve archive needed before recreation**: Keep explicit note that archive is needed before recreation
- **Preserve schema initialization idempotent but doesn't convert existing data**: Keep explicit note of schema initialization behavior
- **Preserve verification plan as high-level quality gate**: Keep explicit note of verification plan as high-level quality gate

## Alternatives Considered

1. **Full deletion of caller site examples** — Rejected: loses traceability to source implementations
2. **Move to appendix** — Rejected: fragments the document unnecessarily
3. **Inline cross-references only** — Chosen: balances brevity with traceability

## Implementation

### Target File

| File | Action |
|------|--------|
| `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` | Compress recover_corruption callers, RecoveryResult dataclass, error behavior tables, DB recreation commands, test commands, AI reference tables; preserve design rationales |

### Procedure

1. Read target file to understand current structure
2. For each section containing overly detailed definitions, replace with prose summary that references source files
3. Preserve all design rationale paragraphs (recover_corruption target limited to rag/session, known limitation when workflow/eventbus passed, known issue of DatabaseError propagation during physical corruption, DB recreation doesn't migrate data, archive needed before recreation, schema initialization idempotent but doesn't convert existing data, verification plan as high-level quality gate)
4. Verify all internal Markdown links remain valid after edits
5. Confirm each design decision's "why" is explicitly stated
6. Coordinate cleanup task SHARED-001 from `docs/90_shared_90_inconsistencies_and_known_issues.md`

### Method

For each target section:
1. Locate the section containing the full definition (grep for key identifiers like `recover_corruption`, `RecoveryResult`, `DatabaseError`, etc.)
2. Read the surrounding context (5-10 lines before/after) to preserve relationships
3. Replace the definition block with a summary paragraph:
   - State what the component represents (1 sentence)
   - Note its purpose in the DB architecture
   - Reference where the full definition lives (e.g., `scripts/db/recovery.py`)
4. Leave any design rationale paragraphs untouched

### Details

**File: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`**
- recover_corruption caller site code examples: Replace with prose summary referencing `scripts/db/recovery.py`
- RecoveryResult dataclass definitions: Replace with prose summary
- Complete error behavior correspondence tables: Replace with prose summary
- DB recreation procedure shell command details: Replace with prose summary
- Test command lists: Replace with prose summary
- AI reference tables: Replace with prose summary

## Compatibility Considerations

- All compression targets are documentation-only; no API contract changes
- Internal cross-references to `scripts/db/recovery.py` must remain accurate
- Any downstream consumers of these docs (e.g., AI agent prompts) should still receive sufficient information about recover_corruption scope limitation and physical corruption exception propagation known issue
- Known issue note about caching duplication must be preserved
- recover_corruption scope limitation must be verified as clear
- Physical corruption exception propagation known issue must be verified as clear
- Coordination with SHARED-001 cleanup task required

## Security Considerations

N/A — documentation restructuring only; no security-sensitive content involved.

## Rollback Considerations

- Before making changes, commit current state: `git add docs/ && git commit -m "pre-restructure snapshot"`
- After edits, verify with `git diff --stat` to confirm only documentation changed
- If internal links break, revert to pre-change state and adjust compression strategy

## Validation Plan

| Check | Tool | Target |
|-------|------|--------|
| recover_corruption scope limitation preserved | Manual | Explicitly stated |
| Physical corruption exception propagation known issue preserved | Manual | Explicitly stated |
| Cross-references valid | Manual | All removed details point to `scripts/db/recovery.py` |
| Internal links valid | Manual | All Markdown links resolve correctly |
| Template compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |
| No full caller site examples/dataclass definitions remain | Manual | Scanning for remaining verbose definitions |
| Coordination with SHARED-001 | Manual | Verified against `docs/90_shared_90_inconsistencies_and_known_issues.md` |

## Out of Scope

- Modifying source type definitions in `scripts/shared/` or `scripts/db/`
- Adding new types or changing existing ones
- Updating test coverage for type definitions
- Changes to other shared chapters beyond the one target file

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-220038_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-111725
- Related target files: docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md
