# Implementation: H-9 — Remove tool_results assertions from test_create_schema.py

## Goal

Remove the `tool_results` table DDL from the test-local `_SESSION_SCHEMA_NO_VEC0` fixture
constant, and remove/update the test methods that assert `tool_results` exists in a freshly
created schema, matching the companion `db/schema_sql.py` DDL removal.

## Scope

**Target**: `tests/test_create_schema.py`

**Depends on**: `scripts/db/schema_sql.py`'s H-9 change already applied (or applied together
with this doc).

**Out of scope**: `test_no_session_tables_in_rag_db` (asserts `tool_results` is ABSENT from the
RAG database, which remains true and requires no change), every other test in this file covering
`sessions`, `messages`, `memories`, `session_diagnostics`, RAG tables, workflow tables, and
eventbus tables — all unaffected.

## Assumptions

1. `_SESSION_SCHEMA_NO_VEC0` (a module-level test fixture constant, lines ~52-120) duplicates
   the real `_SESSION_SCHEMA_TEMPLATE` from `db/schema_sql.py` minus vec0 virtual tables, for
   tests that need a working schema without the sqlite-vec extension loaded — it independently
   contains its own copy of the `tool_results` DDL that must be removed in sync with the real
   template.
2. `test_creates_tool_results_table` and `test_tool_results_has_undone` test ONLY
   `tool_results`-specific behavior and have no other assertions worth preserving under a
   different name (unlike, say, the `undo_service.py` rewrite, where other assertions in the
   same test were worth keeping) — full deletion is appropriate for both.

## Implementation

### Target file

`tests/test_create_schema.py`

### Procedure

#### Step 1: Remove the `tool_results` DDL from `_SESSION_SCHEMA_NO_VEC0`

Current (within the `_SESSION_SCHEMA_NO_VEC0` string, lines ~67-80):

```sql
     CREATE TABLE IF NOT EXISTS tool_results (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        turn       INTEGER NOT NULL,
        tool_name  TEXT    NOT NULL,
        args_masked  TEXT,
        full_text  TEXT    NOT NULL,
        summary    TEXT,
     is_error   INTEGER NOT NULL DEFAULT 0,
        undone     INTEGER NOT NULL DEFAULT 0,
        created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
     );
     CREATE INDEX IF NOT EXISTS idx_tool_results_session
        ON tool_results(session_id);
```

Remove this block entirely from the string (the `messages` table's closing `);` and the
`memories` table's opening `CREATE TABLE IF NOT EXISTS memories (` become adjacent).

#### Step 2: Delete `test_creates_tool_results_table`

Current (in `TestCreateSessionSchema`):

```python
    def test_creates_tool_results_table(
        self, session_tmp_db: sqlite3.Connection
    ) -> None:
        assert "tool_results" in _table_names(session_tmp_db)
```

Remove this method entirely.

#### Step 3: Delete `test_tool_results_has_undone`

Current (in `TestCreateSessionSchema`):

```python
    def test_tool_results_has_undone(self, session_tmp_db: sqlite3.Connection) -> None:
        """tool_results table has the undone column."""
        cols = {
            row[1] for row in session_tmp_db.execute("PRAGMA table_info(tool_results)")
        }
        assert "undone" in cols
```

Remove this method entirely.

#### Step 4: Update `test_session_schema_timestamps`'s table tuple

Current (inside the method, lines ~588-594):

```python
        for table in (
            "sessions",
            "messages",
            "tool_results",
            "memories",
            "session_diagnostics",
        ):
```

Replace with:

```python
        for table in (
            "sessions",
            "messages",
            "memories",
            "session_diagnostics",
        ):
```

### Method

- One DDL-string edit, two full test-method deletions, one tuple-element removal — no other
  test logic changes.
- `test_no_session_tables_in_rag_db`'s `assert "tool_results" not in table_names` line is left
  completely untouched — it is not asserting anything about the session schema, and remains a
  valid (if now slightly redundant, since the table no longer exists anywhere) regression guard
  that RAG and session schemas stay independent.

### Details

- `_table_names()` helper (used throughout this file) is unaffected — it is a generic table-name
  lister with no `tool_results`-specific logic.
- `session_tmp_db` fixture (used by the deleted tests) has other consumers throughout
  `TestCreateSessionSchema` and stays defined.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_create_schema.py` | 0 errors |
| Type check | `mypy tests/test_create_schema.py` | no new errors |
| Grep (DDL and tests removed) | `grep -n "tool_results" tests/test_create_schema.py` | only the `test_no_session_tables_in_rag_db` line remains (`assert "tool_results" not in table_names`) |
| Tests (targeted) | `uv run pytest tests/test_create_schema.py -v` | all remaining tests pass |
| Tests (full) | `uv run pytest -v` | no new failures once the companion `db/schema_sql.py` doc is applied together |
| Pre-commit | `pre-commit run --all-files` | pass |
