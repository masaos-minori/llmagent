# Implementation Procedure: create_schema.py — dedupe migration loop via shared function

Source plan: `plans/20260711-173032_plan.md` — Design §3 / Implementation step 3

## Goal

Remove the duplicated, unnarrowed inline migration-apply loop in `create_workflow_schema()` and route it through the shared `schema_sql.apply_workflow_migrations()` function instead, so the error-handling fix (Design §2 / companion doc `20260711-214056_schema_sql_named_migrations_narrow_error_handling.md`) applies uniformly to both call paths.

## Scope

**In:**
- `scripts/db/create_schema.py::create_workflow_schema()`: replace the inline `for stmt in _WORKFLOW_MIGRATIONS: try: ... except sqlite3.OperationalError: pass` loop with a call to `apply_workflow_migrations()`.
- Update the module-level docstring's `create_workflow_schema()` line to mention `workflow_schema_version` explicitly.

**Out:**
- No change to `build_workflow_schema_sql()` or the `executescript()` call preceding the migration step.
- No change to `_record_workflow_schema_version(db)` or the final `db.commit()`.

## Assumptions

1. Confirmed via the plan's Assumption 4: `create_schema.py:80-84` currently re-implements the identical swallow-all-errors loop inline instead of calling `schema_sql.apply_workflow_migrations()`. `apply_workflow_migrations()` today is called only from `tests/test_workflow_stage_persistence.py`, never from production code — this item is what wires it into the real creation path.
2. This item depends on Design §2 (companion doc `20260711-214056_schema_sql_named_migrations_narrow_error_handling.md`) having been implemented first — `apply_workflow_migrations()` must already take `conn: sqlite3.Connection` and have its narrowed error handling in place before this call site is wired up, otherwise the duplicate inline loop is simply replaced with an equally-unnarrowed call.
3. The exact attribute name for `SQLiteHelper`'s underlying `sqlite3.Connection` (used as `db._conn` in the plan's Design §3 sketch) must be confirmed against `scripts/db/helper.py`'s actual implementation at implementation time — the plan itself flags this as unconfirmed ("to be confirmed against `db/helper.py`'s actual attribute name at implementation time").
4. No test currently patches `create_schema.py`'s inline loop directly — confirmed via `grep -rn "_WORKFLOW_MIGRATIONS|apply_workflow_migrations"` in the plan's Risk analysis, only `tests/test_workflow_stage_persistence.py` references these symbols and it already imports/calls `apply_workflow_migrations()` — so this refactor has no test-mocking fallout to account for.

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Read `scripts/db/helper.py`'s `SQLiteHelper` class to confirm the actual attribute name exposing the underlying `sqlite3.Connection` (the plan's sketch uses `db._conn`; confirm this is correct, not a guess).
2. In `create_workflow_schema()`, remove the inline `for stmt in _WORKFLOW_MIGRATIONS: try: db.execute(stmt) except sqlite3.OperationalError: pass` block.
3. Replace it with a single call: `apply_workflow_migrations(db.<confirmed_conn_attr>)`, placed at the same point in the function body (after the `executescript()` call, before `_record_workflow_schema_version(db)`).
4. Ensure `schema_sql.apply_workflow_migrations` is imported at the top of `create_schema.py` (add the import if not already present; remove any now-unused import that only existed to support the deleted inline loop, e.g. a direct `sqlite3` import if it becomes unused — verify with `ruff check --select F401` before removing).
5. Update the module-level docstring's line describing `create_workflow_schema()` (line ~12) to explicitly mention it creates/verifies `workflow_schema_version` alongside the other five tables.

### Method

Straight-line control-flow simplification: delete one inline loop, add one function call plus its import. No new branching logic introduced in this file — narrowing happens entirely inside `apply_workflow_migrations()` (Design §2), keeping this file's own error handling delegated, not duplicated.

### Details

- Preserve the existing `try/except (sqlite3.OperationalError, sqlite3.DatabaseError)` wrapping the `executescript()` call (per the plan's Design §3 code sketch) — that is a separate, already-correct error path for the initial DDL execution, not part of this change.
- Confirm the `db._conn`-vs-actual-attribute question with a direct read before writing code — do not assume the sketch's placeholder name is correct.
- After removing the inline loop, `_WORKFLOW_MIGRATIONS` should no longer be imported/referenced directly in `create_schema.py` — only `apply_workflow_migrations` needs to be imported (it already reads `_WORKFLOW_MIGRATIONS` internally from `schema_sql.py`).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/create_schema.py` | 0 errors (confirms no unused import left behind) |
| Type check | `uv run mypy scripts/db/` | No new errors |
| Tests | `uv run pytest tests/test_create_schema.py tests/test_workflow_stage_persistence.py -v` | All pass, including the idempotent-double-run test (see companion test doc) |
| Regression | `uv run pytest tests/ -k "schema or workflow" -q` | No new failures |
| Manual sanity | `uv run python -c "from db.create_schema import create_workflow_schema; create_workflow_schema()"` against a scratch DB path, run twice | Second run idempotent, no exception |
