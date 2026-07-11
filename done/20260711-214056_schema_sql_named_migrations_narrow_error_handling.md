# Implementation Procedure: schema_sql.py — named migrations + narrowed error handling

Source plan: `plans/20260711-173032_plan.md` — Design §2 / Implementation step 2

## Goal

Stop `apply_workflow_migrations()` from silently swallowing every `sqlite3.OperationalError` (masking genuinely broken migration statements) and give each migration a stable, loggable ID instead of an anonymous string in a bare list.

## Scope

**In:**
- `scripts/db/schema_sql.py`: convert `_WORKFLOW_MIGRATIONS` from `list[str]` to `list[tuple[str, str]]` (migration_id, SQL statement); narrow `apply_workflow_migrations()`'s `except sqlite3.OperationalError` to only swallow errors whose message contains `"duplicate column name"`, re-raising everything else; add `import logging` and a module-level `logger = logging.getLogger(__name__)` (confirmed absent today).

**Out:**
- No new `workflow_schema_migrations` tracking table — explicitly out of scope per the plan's Out-of-Scope section (lighter-weight named-tuple approach chosen instead).
- No change to the DDL in `workflow_schema_version`'s `CREATE TABLE` statement — columns already correct (plan Assumption 5).

## Assumptions

1. Confirmed via the plan's Assumption 3: `_WORKFLOW_MIGRATIONS` (schema_sql.py lines 241-247) is currently a bare `list[str]` of `ALTER TABLE` statements with no IDs, and `apply_workflow_migrations()` (lines 255-262) does `except sqlite3.OperationalError: pass  # column already exists` unconditionally.
2. SQLite's duplicate-column error text is the stable, standard-library message `"duplicate column name: <col>"` — safe to match via substring (`"duplicate column name" in str(exc)`), per the plan's Risk analysis (stable across SQLite versions bundled with the stdlib `sqlite3` module).
3. `schema_sql.py` has no existing `logging` import or module logger — confirmed by the plan's Design §2 ("Requires adding a module-level `logger`... confirmed absent today via full-file read"). Re-verify with a direct read at implementation time before adding a duplicate.
4. No existing repo convention for `migration_id` naming was found (`grep -rn "migration_id\|MIGRATION_ID"` returned nothing per the plan) — use a simple, descriptive, date-prefixed slug (e.g. `2026_add_attempts_error_kind`), consistent with the plan's Design §2 example. This is metadata only, with no schema/behavioral significance — safe to adjust later without touching logic.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. Add near the top of the file (if not already present): `import logging` and `logger = logging.getLogger(__name__)`.
2. Locate `_WORKFLOW_MIGRATIONS` and convert it to a list of `(migration_id, sql_statement)` tuples, one tuple per existing statement, preserving the exact SQL text and order. Suggested IDs (adjust to match any existing statements' actual column names found at implementation time):
   - `"2026_add_attempts_error_kind"` → `ALTER TABLE attempts ADD COLUMN error_kind TEXT`
   - `"2026_add_attempts_error_detail"` → `ALTER TABLE attempts ADD COLUMN error_detail TEXT`
   - `"2026_add_artifacts_workflow_id"` → `ALTER TABLE artifacts ADD COLUMN workflow_id TEXT`
   - `"2026_add_artifacts_attempt_number"` → `ALTER TABLE artifacts ADD COLUMN attempt_number INTEGER`
   - `"2026_add_processed_events_workflow_id"` → `ALTER TABLE processed_events ADD COLUMN workflow_id TEXT`
3. Update the type annotation to `_WORKFLOW_MIGRATIONS: list[tuple[str, str]] = [...]`.
4. Rewrite `apply_workflow_migrations(conn: sqlite3.Connection) -> None` to iterate `for migration_id, stmt in _WORKFLOW_MIGRATIONS:`, catch `sqlite3.OperationalError as exc`, and:
   - if `"duplicate column name" in str(exc)`: log at `logger.debug("Migration %s already applied: %s", migration_id, exc)` and `continue`.
   - else: `raise` (re-raise unchanged).
5. Keep the trailing `conn.commit()` after the loop, unchanged.
6. Update the function's docstring per the plan's Design §2 code block (documents the narrowed catch behavior explicitly).

### Method

In-place rewrite of one list literal (adding tuple structure) and one function body (narrowing an except clause and adding one conditional branch). No new public symbols; `apply_workflow_migrations()`'s signature (`conn: sqlite3.Connection -> None`) is unchanged, so no caller-side changes are needed beyond what plan item 3 (`create_schema.py`) already covers.

### Details

- Do not change the SQL statement text of any existing migration — only wrap each in a `(id, sql)` tuple.
- The `continue`/`raise` branch must be inside the `except` block, not duplicated per-statement logic — keep the loop body minimal.
- Verify no other caller destructures `_WORKFLOW_MIGRATIONS` as a flat `list[str]` before changing its shape (`grep -rn "_WORKFLOW_MIGRATIONS" scripts/ tests/`) — the plan's own grep found only `apply_workflow_migrations()` and `tests/test_workflow_stage_persistence.py` referencing related symbols; re-confirm at implementation time.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/schema_sql.py` | 0 errors |
| Type check | `uv run mypy scripts/db/` | No new errors |
| Tests | `uv run pytest tests/test_create_schema.py tests/test_workflow_stage_persistence.py -v` | All pass, including new non-duplicate-column re-raise test (see companion test doc) |
| Regression | `uv run pytest tests/ -k "schema or workflow" -q` | No new failures |
| Manual sanity | `uv run python -c "from db.create_schema import create_workflow_schema; create_workflow_schema()"` against a scratch DB path, run twice | Second run idempotent, no exception |
