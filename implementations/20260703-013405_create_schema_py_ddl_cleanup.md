# Implementation: scripts/db/create_schema.py — DDL-Only Cleanup (Remove _migrate_* Functions)

**Plan source:** `plans/20260702-202728_plan.md` (Phase 2)
**Target file:** `scripts/db/create_schema.py`

---

## Goal

Remove all `_migrate_*` helpers and `db.conn` direct-access patterns from `scripts/db/create_schema.py` after confirming schema DDL completeness, leaving the file focused solely on DDL execution.

---

## Scope

**In:**
- Prerequisite (Phase 1): Read `scripts/db/schema_sql.py` and confirm `build_rag_schema_sql` includes `chunk_type` and `source_file`; `build_session_schema_sql` includes `undone` and FK on `tool_results.session_id`; `build_workflow_schema_sql` includes `workflow_id`.
- Remove `_migrate_rag_schema()` function (lines ~33–39)
- Remove `_migrate_add_undone_column()` function (lines ~42–52)
- Remove `_migrate_session_schema()` function (lines ~54–82)
- Remove `_migrate_workflow_schema()` function (lines ~111–115)
- Remove all `db.conn` direct access and their `# type: ignore[arg-type]` annotations
- Remove stale comments referencing migration behavior from module docstring
- Update module docstring to reflect DDL-only behavior

**Out:**
- Changes to `db/helper.py`, `db/schema_sql.py`, or `db/store_protocols.py`
- Changes to `tests/test_create_schema.py`
- Changes to other modules that import `create_schema`

---

## Assumptions

1. If any column is missing from DDL in Phase 1 verification, it must be added to `schema_sql.py` before removing the migration helper.
2. `sqlite3` and `sys` imports remain necessary after removal.
3. `db.store_protocols.get_embedding_dims` and `db.helper.SQLiteHelper` imports remain necessary.

---

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. **Phase 1 prerequisite:** Read `scripts/db/schema_sql.py`. Confirm:
   - `build_rag_schema_sql` → `chunks` table has `chunk_type TEXT` and `source_file TEXT`
   - `build_session_schema_sql` → `tool_results` has `undone INTEGER NOT NULL DEFAULT 0` and `REFERENCES sessions(session_id)`
   - `build_workflow_schema_sql` → `tasks` has `workflow_id TEXT`
   - If any column missing: add to `schema_sql.py` as separate commit first.
2. Remove `_migrate_rag_schema()` function.
3. Remove `_migrate_add_undone_column()` function.
4. Remove `_migrate_session_schema()` function.
5. Remove `_migrate_workflow_schema()` function.
6. Remove the 4 call sites and associated `db.conn` references and `type: ignore` comments.
7. Update module docstring: remove "限定的な互換性修復（_migrate_*）を適用する" line.
8. Run `ruff check scripts/db/create_schema.py` — confirm 0 errors.

### Method

Edit tool for each function removal. Single docstring Edit.

### Details

After removal, `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()` should each contain only the schema creation logic with no `_migrate_*` calls and no `db.conn` access.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| DDL completeness | Read `scripts/db/schema_sql.py` | All columns present before deletion |
| Lint | `ruff check scripts/db/create_schema.py` | 0 errors, 0 unused imports |
| Unit tests | `uv run pytest tests/test_create_schema.py -v` | All tests pass |
| Full suite | `uv run pytest` | No new failures |
