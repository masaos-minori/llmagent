# Implementation: schema version check in `check_workflow_schema()`

## Goal

Extend `scripts/agent/repl_health.py::check_workflow_schema()` to compare the DB's recorded `workflow_schema_version` against the expected `WORKFLOW_SCHEMA_VERSION` constant, raising a clear error on mismatch or absence.

## Scope

**In:**
- `scripts/agent/repl_health.py`: extend `check_workflow_schema()` (lines ~455-484) with a version-row query and comparison, after its existing table/column checks

**Out:**
- No weakening of the existing table/column validation already in `check_workflow_schema()`
- No change to `REQUIRED_WORKFLOW_TABLES`

## Assumptions

1. Depends on `implementations/20260710-155420_workflow_schema_version_table_and_recording.md` (the `workflow_schema_version` table and `WORKFLOW_SCHEMA_VERSION` constant) being implemented first.
2. `check_workflow_schema()` already has a `db` connection/cursor object in scope with a `.fetchone(query, params)`-style helper (per its existing table/column loop) — the version check reuses the same access pattern.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Add the import at the top of the file (alongside existing `db.*` imports):
   ```python
   from db.schema_sql import WORKFLOW_SCHEMA_VERSION
   ```
2. At the end of `check_workflow_schema()`, after the existing required-tables/columns loop, add:
   ```python
   row = db.fetchone(
       "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1", ()
   )
   actual_version = row[0] if row else None
   if actual_version != WORKFLOW_SCHEMA_VERSION:
       raise RuntimeError(
           f"Workflow schema version mismatch: expected {WORKFLOW_SCHEMA_VERSION!r}, "
           f"found {actual_version!r}. Run create_workflow_schema() to migrate."
       )
   ```
3. Add/update a unit test in the corresponding test file for `repl_health.py` asserting:
   - `check_workflow_schema()` raises `RuntimeError` when `workflow_schema_version` has no rows.
   - `check_workflow_schema()` raises `RuntimeError` when the latest row's version differs from `WORKFLOW_SCHEMA_VERSION`.
   - `check_workflow_schema()` passes (no exception) when the latest row matches `WORKFLOW_SCHEMA_VERSION` and all required tables/columns are present.

### Method

Direct extension of an existing, already-tested function — one new query plus one new comparison/raise, appended after the existing checks (so the existing table/column validation always runs first and is not bypassed).

### Details

- `actual_version` is `None` (not a missing-table error) when the table exists but has zero rows — this is the expected state for any pre-existing `workflow.sqlite` created before this change, and is deliberately treated as a mismatch (not a separate error class), matching the plan's accepted-risk note that old DBs must be re-migrated.

## Validation plan

```bash
uv run ruff check scripts/agent/repl_health.py
uv run mypy scripts/agent/repl_health.py
PYTHONPATH=scripts uv run lint-imports
uv run pytest tests/ -k "repl_health" -v
```

Expected outcome: existing `check_workflow_schema()` tests still pass; new tests confirming version-mismatch and version-absent cases both raise `RuntimeError` with a message naming both the expected and found versions; a DB with matching version and complete tables/columns passes with no exception.
