# Implementation: scripts/db/create_schema.py — Remove _migrate_* Functions and Update Docstring

**Plan source:** `plans/20260702-201024_plan.md` (Phase 3)
**Target file:** `scripts/db/create_schema.py`

---

## Goal

Remove all four `_migrate_*` private functions and their call sites from `create_schema.py`, eliminating the obsolete migration helper layer and leaving the module focused solely on DDL execution.

---

## Scope

**In:**
- Remove `_migrate_rag_schema()` function body and definition
- Remove `_migrate_add_undone_column()` function body and definition
- Remove `_migrate_session_schema()` function body and definition
- Remove `_migrate_workflow_schema()` function body and definition
- Remove the four `_migrate_*` call sites inside `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()`
- Remove `db.conn` direct-access references and `# type: ignore[arg-type]` annotations associated with migration calls
- Update module docstring: remove "互換性修復（_migrate_*）を適用する" references; state DDL-only schema creation policy; note that `schema_sql.py` is the canonical DDL source

**Out:**
- Changes to `schema_sql.py`, `helper.py`, or `store_protocols.py`
- Changes to the public API (`create_schema()`, `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()`)
- Changes to `tests/test_create_schema.py` (migration tests use idempotency path, not direct `_migrate_*` calls)

---

## Assumptions

1. `schema_sql.py` DDL already includes `chunk_type`, `source_file`, `undone`, the FK on `tool_results.session_id`, and `workflow_id` — confirmed prerequisite from Phase 2.
2. All production databases have had migrations applied; `_migrate_*` are dead paths.
3. `sqlite3` and `sys` imports remain necessary after removal (`sqlite3` for exception types, `sys` for `sys.exit`).
4. No external callers reference `_migrate_*` functions (confirmed by grep in Phase 1).

---

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Run `grep -rn "_migrate_" /home/masaos/llmagent/scripts/` to confirm no external callers.
2. Read the file to identify exact line ranges of each `_migrate_*` function.
3. Remove `_migrate_rag_schema()` function (lines ~33–39).
4. Remove `_migrate_add_undone_column()` function (lines ~42–52).
5. Remove `_migrate_session_schema()` function (lines ~54–82).
6. Remove `_migrate_workflow_schema()` function (lines ~111–115).
7. Remove the 4 `_migrate_*` call sites in their respective `create_*_schema()` functions (including `db.conn` refs and `type: ignore` comments).
8. Update module docstring: remove migration references, add "DDL-only schema creation" policy statement, note `schema_sql.py` as canonical source.
9. Run `ruff check scripts/db/create_schema.py` — confirm 0 errors.

### Method

Edit tool for targeted removal of function blocks and call sites. Single docstring update with Edit.

### Details

The module docstring should state:
- `create_schema()` uses `IF NOT EXISTS` — idempotent and non-destructive
- No migration helpers; schema changes require DB recreation using `rotate_all_dbs()` + `create_schema()`
- `schema_sql.py` is the canonical DDL source for all schemas

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| External caller check | `grep -rn "_migrate_" scripts/` | No callers outside `create_schema.py` (0 matches after removal) |
| Lint | `ruff check scripts/db/create_schema.py` | 0 errors, 0 unused imports |
| Unit tests | `uv run pytest tests/test_create_schema.py -v` | All tests pass |
| Full suite | `uv run pytest` | No regressions |
| Type check | `mypy scripts/db/` | No new type errors |
