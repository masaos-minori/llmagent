# Reduce implementation-derived detail in docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part{1,2}.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to the schema-reference chapter (both parts): keep which DB is authoritative for what and schema-change caution points; remove full DDL, column lists, and FTS/vec table definitions.

## Reason for Change
This chapter is the canonical source for DB source-of-truth and schema policy (per `memo-doc-shared-review.md` §「章間の正本ルール」: DB正本とスキーマ方針 = `90_shared_04_02_db_architecture_and_schema-schema-reference`). Per the memo's explicit 注意 for this chapter: focus on "which DB is authoritative for what" and "what to watch for on change," not column tables — but this is also correctness-critical (schema-version-mismatch handling, FTS sync rules) and must not be diluted.

## Implementation Intent
Keep this chapter focused on `db/schema_sql.py` as the schema source of truth, the meaning of rag/session/workflow DBs, why `session_diagnostics` is separated from `messages`, `workflow_schema_version`-based version management, the FATAL-on-mismatch policy, and the manual-FTS-sync prohibition.

## Target Files or Areas
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md`

## Required Changes
- Keep: that `db/schema_sql.py` is the schema source of truth, the meaning of `rag.sqlite`/`session.sqlite`/`workflow.sqlite`, why `session_diagnostics` is separated from `messages`, schema-version management via `workflow_schema_version`, that a workflow schema mismatch is treated as FATAL at startup, the policy of unifying timestamp formats, the operational caution around the RAG FTS auto-sync trigger, that `chunks_fts` must not be manually synced.
- Remove or compress: full DDL text, per-table column lists, FTS5 virtual table definitions, vec virtual table definitions, SQL-equivalent trigger explanations, workflow-table column lists, schema-version-table column lists.

## Acceptance Criteria
- Both files follow the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full DDL, column list, or virtual-table definition remains; readers are pointed to `db/schema_sql.py` for exact schema.
- The FATAL-on-schema-mismatch policy and the manual-FTS-sync prohibition remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the FATAL-on-mismatch policy and FTS-manual-sync prohibition were not weakened. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches data-integrity-critical documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- `scripts/db/schema_sql.py` itself (code, not documentation).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_04_02_db_architecture_and_schema-schema-reference」 including its 注意 note. Do not edit code. Point to `schema_sql.py` for exact column/index detail rather than transcribing it. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_04_02_db_architecture_and_schema-schema-reference」
- Generated at: 2026-08-05
