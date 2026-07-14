# Implementation Procedure: tests — workflow schema/migration/error-message coverage

Source plan: `plans/20260711-173032_plan.md` — Design §6 / Implementation step 6

## Goal

Add test coverage for every behavior change in this plan: the `workflow_schema_version` table-existence check (companion doc `20260711-...repl_health_workflow_schema_version_required_table.md`), the narrowed migration error handling (companion doc `20260711-214056_schema_sql_named_migrations_narrow_error_handling.md`), and the `common.toml`→`agent.toml` message fix (companion doc `20260711-214149_db_helper_common_toml_error_message_fix.md`).

## Scope

**In:**
- `tests/test_repl_health.py` (or `tests/test_startup.py`, whichever currently hosts `check_workflow_schema()` coverage — confirm exact location at implementation time): new test for missing `workflow_schema_version` table.
- `tests/test_create_schema.py`: new test for non-duplicate-column `OperationalError` re-raise; new/extended idempotency test for `create_workflow_schema()` run twice.
- `tests/test_sqlite_helper.py`: new test asserting the missing-db-path `ValueError` message mentions `agent.toml`, not `common.toml`.

**Out:**
- No change to `tests/test_workflow_stage_persistence.py` — it already tests `apply_workflow_migrations()` idempotency directly at the function level; this plan only adds the equivalent guarantee at the `create_workflow_schema()` call-site level (a different, additive test target, not a duplicate).
- No change to the existing version-mismatch test path — already covered; only confirm it still passes unchanged (a negative/regression check, not new code).

## Assumptions

1. Confirmed via the plan's Design §6: `tests/test_repl_health.py::_create_workflow_db()` test helper unconditionally creates `workflow_schema_version` (its `exclude_table` parameter only applies to the other five tables) — no existing test exercises "workflow_schema_version missing entirely." This is genuinely new coverage.
2. `tests/test_workflow_stage_persistence.py` already imports and calls `apply_workflow_migrations()` directly and already tests its idempotency — confirmed via the plan's Risk analysis grep (`_WORKFLOW_MIGRATIONS|apply_workflow_migrations`). The new `test_create_schema.py` idempotency test targets a different call path (`create_workflow_schema()` end-to-end, not the migration function in isolation).
3. This test doc depends on the three implementation docs (repl_health.py, schema_sql.py, create_schema.py, db/helper.py) having landed first — tests assert against the post-fix behavior described in those docs.

## Implementation

### Target file

`tests/test_repl_health.py` (or `tests/test_startup.py`), `tests/test_create_schema.py`, `tests/test_sqlite_helper.py`

### Procedure

**`tests/test_repl_health.py` / `tests/test_startup.py`:**
1. Confirm which file currently hosts `check_workflow_schema()`'s test coverage (`grep -rln "check_workflow_schema" tests/`).
2. Add a test that builds a workflow DB via `_create_workflow_db()` (or equivalent helper) with all required tables present EXCEPT `workflow_schema_version`, then asserts `check_workflow_schema()` raises `RuntimeError` whose message mentions `workflow_schema_version` and `"Run create_workflow_schema()"` — and does NOT raise `sqlite3.OperationalError`.
3. Confirm the existing "version mismatch: found None" test (empty `workflow_schema_version` table, no rows) still passes unchanged — run it, do not modify it unless it fails.
4. Confirm the existing stale-version-string mismatch `RuntimeError` test still passes unchanged.

**`tests/test_create_schema.py`:**
5. Add a test that monkeypatches or constructs a scenario where a migration statement raises a non-duplicate-column `OperationalError` (e.g. `ALTER TABLE nonexistent_table ADD COLUMN x TEXT`, or a temporary entry appended to `_WORKFLOW_MIGRATIONS` for the test) and asserts the exception propagates out of `apply_workflow_migrations()` / `create_workflow_schema()` rather than being swallowed.
6. Add or extend a test that calls `create_workflow_schema()` twice against the same scratch DB path and asserts the second call raises no exception (idempotent), migrations skip cleanly via the "duplicate column name" branch.

**`tests/test_sqlite_helper.py`:**
7. Add a test that triggers the missing-db-path `ValueError` (per the target file's existing pattern for constructing `SQLiteHelper` with an unconfigured target) and asserts the message contains `"agent.toml"` and does NOT contain `"common.toml"`.

### Method

Standard `pytest` unit/integration tests using existing fixtures/helpers already present in each target test file (e.g. `_create_workflow_db()`, scratch SQLite paths via `tmp_path`). No new test infrastructure needed — extend existing patterns.

### Details

- For the non-duplicate-column re-raise test, prefer a real `ALTER TABLE` against a nonexistent table/column (produces a genuine, non-"duplicate column name" `OperationalError` from SQLite itself) over mocking, to test the actual substring-matching logic in `apply_workflow_migrations()`.
- Keep each new test focused on one behavior (single assertion focus), consistent with the existing style in each target file.
- Do not modify or remove any existing, currently-passing test as part of this item — only add new tests and confirm (via running, not editing) that pre-existing coverage still passes.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these files:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_repl_health.py tests/test_startup.py tests/test_create_schema.py tests/test_sqlite_helper.py` | 0 errors |
| Tests | `uv run pytest tests/test_repl_health.py tests/test_startup.py tests/test_create_schema.py tests/test_sqlite_helper.py tests/test_workflow_stage_persistence.py -v` | All pass, including all new/updated tests |
| Regression | `uv run pytest tests/ -k "schema or workflow or sqlite" -q` | No new failures |
| Manual grep | `grep -rn "common\.toml" scripts/db/` | No matches remain |
