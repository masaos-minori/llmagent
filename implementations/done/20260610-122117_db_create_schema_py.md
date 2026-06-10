# Implementation: db/create_schema.py — remove all migration code and schema_version

## Goal

Strip `create_schema.py` down to a pure "create latest schema" module:
- Delete all migration infrastructure (`_SAFE_MIGRATION_ERRORS`, `_RAG_MIGRATE_SQL`,
  `_SESSION_MIGRATE_SQL`, `_run_migrations()`).
- Remove `schema_version` table from both schema templates.
- Remove `_get_schema_log_path()` fallback `except Exception` block (fail-fast).
- Remove `assert db.conn is not None` (redundant after `db.execute` guards).
- Remove the post-migration `tool_call_id` column verification (was migration guard only).

## Scope

- `scripts/db/create_schema.py` — primary target
- `tests/test_create_schema.py` — remove migration-related tests; keep schema creation tests

## Assumptions

1. Production DB already has all columns from the deleted migrations applied.
   Fresh installs use the schema templates directly (no migration needed).
2. `IF NOT EXISTS` on `CREATE TABLE` / `CREATE VIRTUAL TABLE` / `CREATE INDEX` / `CREATE TRIGGER`
   is kept — it allows `create_schema()` to be called idempotently on an existing DB.
3. `DIMS` placeholder in schema templates is still replaced via `str.replace()`; this is kept.
4. `get_embedding_dims()` call in `create_rag_schema` / `create_session_schema` stays.
   If it raises (due to config error), that is now the intended fail-fast behaviour.
5. `_get_schema_log_path()` fallback path `/opt/llm/logs/create_schema.log` is the
   hardcoded default. After removing the try/except, `ConfigLoader().load()` failure raises.
   This is acceptable — if config is missing at schema-creation time, the operator must fix it.

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Delete `_SAFE_MIGRATION_ERRORS` tuple.
2. Delete `_RAG_MIGRATE_SQL` list.
3. Delete `_SESSION_MIGRATE_SQL` list.
4. Delete `_run_migrations()` function.
5. In `_get_schema_log_path()`: remove the `try/except Exception` wrapper;
   let `ConfigLoader().load()` raise on failure.
6. In `_RAG_SCHEMA_TEMPLATE`: remove the `CREATE TABLE IF NOT EXISTS schema_version` block.
7. In `_SESSION_SCHEMA_TEMPLATE`: remove the `CREATE TABLE IF NOT EXISTS schema_version` block.
8. In `create_rag_schema()`: remove `assert db.conn is not None` and remove
   `_run_migrations(db, _RAG_MIGRATE_SQL)` call.
9. In `create_session_schema()`: remove `assert db.conn is not None`, remove
   `_run_migrations(db, _SESSION_MIGRATE_SQL)` call, and remove the
   `tool_call_id` column post-check block.

### Method

Direct textual edit.

### Details

`_get_schema_log_path()` after change:
```python
def _get_schema_log_path() -> str:
    from shared.config_loader import ConfigLoader  # noqa: PLC0415
    cfg = ConfigLoader().load("common.toml")
    log_dir = cfg.get("log_dir", "/opt/llm/logs")
    return f"{log_dir}/create_schema.log"
```

`create_rag_schema()` after change:
```python
def create_rag_schema() -> None:
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        try:
            db.conn.executescript(_build_rag_schema_sql(dims))
        except Exception as e:
            logger.error(f"Failed to execute RAG schema DDL: {e}")
            raise
    logger.info("RAG schema created successfully.")
```

`create_session_schema()` after change:
```python
def create_session_schema() -> None:
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True) as db:
        try:
            db.conn.executescript(_build_session_schema_sql(dims))
        except Exception as e:
            logger.error(f"Failed to execute session schema DDL: {e}")
            raise
    logger.info("Session schema created successfully.")
```

Note: `db.conn` is used directly because `executescript()` is not available via `db.execute()`.
This is the one legitimate use of `db.conn` access.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/create_schema.py` | 0 errors |
| Type | `uv run mypy scripts/db/create_schema.py` | no new errors |
| Tests | `uv run pytest tests/test_create_schema.py -x -v` | all pass |
| No migration | `grep -n "_run_migrations\|_MIGRATE_SQL\|_SAFE_MIGRATION" scripts/db/create_schema.py` | 0 hits |
| No schema_version | `grep -n "schema_version" scripts/db/create_schema.py` | 0 hits |
