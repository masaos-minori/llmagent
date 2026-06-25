# Implementation: tests/test_sqlite_helper.py

## Goal

Add 3 regression tests to `test_sqlite_helper.py` verifying that passing a `DbTarget` enum value to `SQLiteHelper` produces the same `_default_load_vec` and `_db_path` as passing the equivalent string.

## Scope

- Target: `tests/test_sqlite_helper.py`
- Add `test_dbtarget_rag_enum_default_load_vec`
- Add `test_dbtarget_session_enum_default_load_vec`
- Add `test_dbtarget_rag_enum_db_path`

## Assumptions

1. Existing `_patch_config()` context manager patches `build_db_config()` to return a mock `DbConfig` without hitting disk.
2. `DbTarget` is importable from `db.helper` or `db.schema_sql`.
3. `SQLiteHelper._default_load_vec` and `SQLiteHelper.DB_PATH` (or `_db_path`) are accessible attributes.

## Implementation

### Target file
`tests/test_sqlite_helper.py`

### Procedure
1. Import `DbTarget` from the appropriate module.
2. Add the 3 test methods, using the existing `_patch_config()` pattern.

### Method

```python
from db.helper import SQLiteHelper, DbTarget  # adjust import path as needed

def test_dbtarget_rag_enum_default_load_vec() -> None:
    with _patch_config():
        db = SQLiteHelper(DbTarget.RAG)
    assert db._default_load_vec is True

def test_dbtarget_session_enum_default_load_vec() -> None:
    with _patch_config():
        db = SQLiteHelper(DbTarget.SESSION)
    assert db._default_load_vec is False

def test_dbtarget_rag_enum_db_path() -> None:
    with _patch_config():
        db = SQLiteHelper(DbTarget.RAG)
    assert db.DB_PATH == "/opt/llm/db/rag.sqlite"  # use _db_path if DB_PATH property absent
```

### Details
- If `DB_PATH` is a property, use it. If only `_db_path` exists, access `db._db_path`.
- Tests must not open a real SQLite file — ensure `_patch_config()` prevents `build_db_config()` from hitting disk.
- Locate the correct import for `DbTarget` by checking `scripts/db/helper.py` or `scripts/db/schema_sql.py`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_sqlite_helper.py -q` | all pass incl. new tests |
| Regression | all existing `test_sqlite_helper.py` tests | still pass |
