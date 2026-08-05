# Reduce implementation-derived detail in docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`: keep the reasons DB files are split and per-DB responsibility boundaries; remove directory-structure listings and full config-field definitions.

## Reason for Change
This chapter is the canonical source for the DB layer's overall structure (per `memo-doc-shared-review.md` §「章間の正本ルール」: DB全体構造とSQLiteHelper = `90_shared_04_01_db_architecture_and_schema-overview-and-config`), but currently carries directory trees, `DbConfig`'s full field definition, and PRAGMA enumerations that belong to code.

## Implementation Intent
Keep this chapter focused on why DB files are split (rag/session/workflow/eventbus), `SQLiteHelper`'s role, that sqlite-vec is used only for RAG, and the operational meaning of WAL/busy_timeout/foreign_keys.

## Target Files or Areas
`docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

## Required Changes
- Keep: the DB layer's purpose, the reason DB files are split, the rag/session/workflow/eventbus responsibility boundary, `SQLiteHelper`'s role, the policy of switching DBs by target via `SQLiteHelper`, that sqlite-vec is used only for RAG, the operational meaning of WAL/busy_timeout/foreign_keys, why a `db_path` override is needed, that the Event Bus runtime is out of scope for this document.
- Remove or compress: the `db/` directory structure, `DbConfig`'s full field definition, `SQLiteHelper`'s constructor detail, `open()`'s full argument explanation, a mechanical PRAGMA enumeration, `begin_immediate`/`begin_exclusive` implementation detail.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No directory tree, full config-field definition, or PRAGMA enumeration remains.
- The DB-file-split rationale and the sqlite-vec-only-for-RAG constraint remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `config.py`, `helper.py`).
- Event Bus runtime documentation (out of scope for this doc set; covered separately under `docs/06_eventbus_*.md`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_04_01_db_architecture_and_schema-overview-and-config」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_04_01_db_architecture_and_schema-overview-and-config」
- Generated at: 2026-08-05
