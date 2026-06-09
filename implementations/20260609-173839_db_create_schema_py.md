# Implementation: db/create_schema.py — add RENAME COLUMN migration + update schema definition

## Goal

Add a migration statement to rename the `args_json` column to `args_masked` in the `tool_results` table, and update the schema template definition to use the new column name so that fresh DB creation and migration both produce the same schema.

## Scope

- `scripts/db/create_schema.py`
  - Update `_SESSION_SCHEMA_TEMPLATE`: rename `args_json` → `args_masked` in the `CREATE TABLE tool_results` block
  - Append `ALTER TABLE tool_results RENAME COLUMN args_json TO args_masked` to `_SESSION_MIGRATE_SQL`
- `tests/test_create_schema.py` — update the inline schema definition to use `args_masked`

## Assumptions

1. SQLite version is 3.46.1 (`RENAME COLUMN` supported since 3.25).
2. The migration is idempotent: if the column is already named `args_masked` (i.e., fresh install), `_SAFE_MIGRATION_ERRORS` catches the "no such column" error.
   - Verify: test `_SAFE_MIGRATION_ERRORS` covers "no such column". If not, add it.
3. `create_session_schema()` is called at deploy time; it applies the migration automatically.

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Read the current file.
2. Update `_SESSION_SCHEMA_TEMPLATE` (column definition).
3. Append migration statement to `_SESSION_MIGRATE_SQL`.
4. Update `_SAFE_MIGRATION_ERRORS` if "no such column" is not already covered.
5. Update `tests/test_create_schema.py`.
6. Run `uv run ruff check scripts/db/create_schema.py --fix` and `uv run mypy scripts/db/create_schema.py`.

### Method

Targeted string substitution in two locations within `create_schema.py`, plus one line in the test.

### Details

**`_SESSION_SCHEMA_TEMPLATE` — column rename in CREATE TABLE:**
```python
# BEFORE (inside the tool_results CREATE TABLE block)
    CREATE TABLE IF NOT EXISTS tool_results (
        ...
        args_json  TEXT,
        ...
    );

# AFTER
    CREATE TABLE IF NOT EXISTS tool_results (
        ...
        args_masked  TEXT,
        ...
    );
```

**`_SESSION_MIGRATE_SQL` — append migration at end of list:**
```python
# BEFORE (last element of _SESSION_MIGRATE_SQL)
    "CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0("
    "memory_id TEXT PRIMARY KEY, embedding float[384])",
]

# AFTER
    "CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0("
    "memory_id TEXT PRIMARY KEY, embedding float[384])",
    "ALTER TABLE tool_results RENAME COLUMN args_json TO args_masked",
]
```

**`_SAFE_MIGRATION_ERRORS` — add "no such column" guard:**

Check if `"no such column"` is already in `_SAFE_MIGRATION_ERRORS`. If not:
```python
_SAFE_MIGRATION_ERRORS: tuple[str, ...] = (
    "duplicate column name",
    "already exists",
    "no such column",  # RENAME COLUMN on already-renamed column in fresh DB
)
```

**`tests/test_create_schema.py:78` — schema definition update:**
```python
# BEFORE
    args_json  TEXT,

# AFTER
    args_masked  TEXT,
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/create_schema.py` | 0 errors |
| Type | `uv run mypy scripts/db/create_schema.py` | no new errors |
| Unit tests | `uv run pytest tests/test_create_schema.py -v` | all pass |
| Migration idempotency | Run `create_session_schema()` twice against in-memory DB | no error on second run |
