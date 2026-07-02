# Implementation: test_create_schema.py - DDL-only schema creation tests

## Goal

Remove all migration-helper references from `tests/test_create_schema.py` and align the patched
test DDL constants (`_RAG_SCHEMA_NO_VEC0`, `_SESSION_SCHEMA_NO_VEC0`) with the canonical DDL in
`scripts/db/schema_sql.py` so that schema creation tests validate only latest DDL creation and
idempotent `CREATE ... IF NOT EXISTS` behavior.

## Scope

**In scope** (`tests/test_create_schema.py` only):
- Replace the module docstring comment mentioning migration helpers with a DDL-only description
- Add `chunk_type TEXT NOT NULL DEFAULT 'text'` to the `chunks` table in `_RAG_SCHEMA_NO_VEC0`
- Add `source_file TEXT NOT NULL DEFAULT ''` to the `chunks` table in `_RAG_SCHEMA_NO_VEC0`
- Add `undone INTEGER NOT NULL DEFAULT 0` to `tool_results` in `_SESSION_SCHEMA_NO_VEC0`
- Add the `session_diagnostics` table DDL to `_SESSION_SCHEMA_NO_VEC0`
- Extend column assertions in `TestCreateRagSchema.test_chunks_columns` to include `chunk_type` and `source_file`
- Add `TestCreateSessionSchema.test_tool_results_has_undone` assertion method

**Out of scope**:
- `scripts/db/create_schema.py` — migration helpers remain untouched
- `scripts/db/schema_sql.py` — canonical DDL not modified
- Adding `chunk_type` / `source_file` to canonical `_RAG_SCHEMA_TEMPLATE` (separate task)
- Testing `ALTER TABLE` or old DB upgrade paths

## Assumptions

1. The canonical DDL in `scripts/db/schema_sql.py` is ground truth; `_RAG_SCHEMA_NO_VEC0` and
   `_SESSION_SCHEMA_NO_VEC0` are intentional subsets (vec0 virtual tables removed for test environment).
2. `chunk_type TEXT NOT NULL DEFAULT 'text'` and `source_file TEXT NOT NULL DEFAULT ''` are
   required columns in the `chunks` table per the requirement. They are currently absent from both
   canonical DDL and the test patch.
3. `undone INTEGER NOT NULL DEFAULT 0` is already present in canonical `_SESSION_SCHEMA_TEMPLATE`
   (`tool_results` table) but absent from `_SESSION_SCHEMA_NO_VEC0`.
4. `session_diagnostics` exists in canonical `_SESSION_SCHEMA_TEMPLATE` and is referenced in
   `TestTimestampDefaults.test_session_schema_timestamps` (line 565), but is absent from
   `_SESSION_SCHEMA_NO_VEC0`. Adding it to the patched constant resolves the test failure.
5. All test commands are run with `uv run pytest`.

## Implementation

### Target file

- `tests/test_create_schema.py`

### Procedure

1. **Phase 1**: Replace the migration-related comment at lines 8–10 in the module docstring.
2. **Phase 2**: Add two columns to `_RAG_SCHEMA_NO_VEC0` inside the `chunks` table DDL.
3. **Phase 3**: Add `undone` column and `session_diagnostics` table to `_SESSION_SCHEMA_NO_VEC0`.
4. **Phase 4**: Extend column-presence assertions in existing and new test methods.

### Method

- Use direct file editing (Edit tool) with exact string matching.
- Read the current file first to confirm exact whitespace and ordering before each edit.
- Each phase is independently testable; run `uv run pytest tests/test_create_schema.py -v` after
  each phase before proceeding to the next.

### Details

#### Phase 1: Replace module docstring migration comment

Locate the comment block at lines 8–10 (currently mentions `_migrate_rag_schema()`,
`_migrate_session_schema()`, and "backward-compatible schema additions"). Replace with:

```python
# These tests validate DDL-only creation and `CREATE ... IF NOT EXISTS` idempotency.
# Migration helpers are out of scope.
```

#### Phase 2: Update `_RAG_SCHEMA_NO_VEC0` — add columns to `chunks` table

Find the `chunks` table definition inside `_RAG_SCHEMA_NO_VEC0`. After the last existing column
(currently `content TEXT NOT NULL` or whichever is last before the closing `)`), insert:

```sql
    chunk_type  TEXT    NOT NULL DEFAULT 'text',
    source_file TEXT    NOT NULL DEFAULT '',
```

Confirm insertion position by reading the constant and matching indentation exactly.

Add a sync comment immediately before the constant or in a docstring:

```python
# Mirror of canonical DDL in scripts/db/schema_sql.py; keep in sync.
```

#### Phase 3: Update `_SESSION_SCHEMA_NO_VEC0`

**3a. Add `undone` column to `tool_results`**

Locate `tool_results` table inside `_SESSION_SCHEMA_NO_VEC0`. Insert after the `is_error` column
line:

```sql
    undone      INTEGER NOT NULL DEFAULT 0,
```

**3b. Add `session_diagnostics` table**

Append the following table DDL to `_SESSION_SCHEMA_NO_VEC0` after the last existing table, using
the same DDL as in canonical `_SESSION_SCHEMA_TEMPLATE`. Read `scripts/db/schema_sql.py` to copy
the exact definition before editing. Example structure:

```sql
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    -- ... remaining columns matching canonical DDL ...
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
```

Copy the exact DDL from `scripts/db/schema_sql.py` (`_SESSION_SCHEMA_TEMPLATE`) — do not
paraphrase it.

#### Phase 4: Update column-presence assertions

**4a. Extend `TestCreateRagSchema.test_chunks_columns`**

Find the expected column set inside `test_chunks_columns`. Add `"chunk_type"` and `"source_file"`
to the set literal:

```python
assert {
    ...,          # existing columns
    "chunk_type",
    "source_file",
} <= cols
```

**4b. Add `TestCreateSessionSchema.test_tool_results_has_undone`**

Add a new test method to the `TestCreateSessionSchema` class:

```python
def test_tool_results_has_undone(self) -> None:
    """tool_results table has the undone column."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(<session_schema_constant_or_fixture_call>)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tool_results)").fetchall()}
        assert "undone" in cols
    finally:
        conn.close()
```

Confirm the fixture / in-memory schema setup pattern by reading existing `TestCreateSessionSchema`
methods before writing. Reuse the exact same setup pattern (fixture or explicit `executescript`
call) as used in sibling test methods of that class.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Phase 1 verification | `uv run pytest tests/test_create_schema.py -v` | All tests pass; no migration-comment-related failures |
| Phase 2 verification | `uv run pytest tests/test_create_schema.py::TestCreateRagSchema -v` | All RAG schema tests pass including chunk_type / source_file columns |
| Phase 3 verification | `uv run pytest tests/test_create_schema.py::TestCreateSessionSchema -v` and `::TestTimestampDefaults` | All session and timestamp tests pass |
| Phase 4 verification | `uv run pytest tests/test_create_schema.py -v` | All tests pass including new `test_tool_results_has_undone` |
| Full suite regression | `uv run pytest` | All tests pass, no new failures |
| Lint | `ruff check tests/test_create_schema.py` | 0 errors |
| Type check | `mypy tests/test_create_schema.py` | No new errors |
