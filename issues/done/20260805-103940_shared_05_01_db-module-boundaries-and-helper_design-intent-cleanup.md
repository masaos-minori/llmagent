# Reduce implementation-derived detail in docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`: keep `db.store` as the public API boundary and the internal-vs-public split; remove full method tables and constructor signatures.

## Reason for Change
This chapter is the canonical source for the DB API boundary (per `memo-doc-shared-review.md` §「章間の正本ルール」: DB API境界 = `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper`), but currently carries `SQLiteHelper`'s full method table and constructor detail that duplicates the code.

## Implementation Intent
Keep this chapter focused on why `db.store` is the public surface, why `store_protocols`/`store_impl` are internal boundaries, and the responsibility split for extending DB store.

## Target Files or Areas
`docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`

## Required Changes
- Keep: that `db.store` is the public API surface, that `store_protocols`/`store_impl` are internal boundaries, that callers should import from `db.store` in principle, the responsibility split when extending the DB store, `SQLiteHelper`'s operational role, the special case of applying pragmas to a raw sqlite3 connection, the purpose of the transaction helper, that VACUUM/DDL must be treated as exclusive operations.
- Remove or compress: `SQLiteHelper`'s full method table, mechanical explanations of `execute`/`fetchall`/`commit`/`close`, the full constructor signature, `open()`'s argument table, typical usage code examples, a call-site list for `apply_connection_pragmas`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full method table, constructor signature, or usage-code example remains.
- The `db.store`-as-public-surface / `store_protocols`/`store_impl`-as-internal boundary remains explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `store.py`, `store_protocols.py`, `store_impl.py`, `helper.py`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_05_01_db_api_and_operations-module-boundaries-and-helper」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_05_01_db_api_and_operations-module-boundaries-and-helper」
- Generated at: 2026-08-05
