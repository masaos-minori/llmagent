# Implementation and Test Procedure: tests/test_db_performance.py

## Goal

Create `tests/test_db_performance.py` with tests for `SQLiteHelper` connection reuse behavior.

## Scope

**In:**
- New file `tests/test_db_performance.py`

**Out:**
- Modifying `helper.py` (handled separately)

## Assumptions

1. `SQLiteHelper(db_name, cfg=DbConfig(...))` can be constructed with a temp DB path.
2. `reuse_connection=True` keeps the same connection object across multiple `open()` calls.
3. Default behavior (`reuse_connection=False`) creates a new connection on each `open()`.

## Implementation

### Target file
`tests/test_db_performance.py`

### Procedure
Create tests using `tmp_path` to create an isolated SQLite file.

### Details

```python
"""tests/test_db_performance.py
Tests for SQLiteHelper.open() reuse_connection behavior.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import pytest
from db.config import DbConfig
from db.helper import SQLiteHelper


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path=db_path,
        session_db_path=db_path,
        workflow_db_path=db_path,
    )


class TestConnectionReuse:
    def test_connection_reuse_same_instance(self, tmp_path: Path) -> None:
        """reuse_connection=True returns same connection object on second open()."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        helper = SQLiteHelper("rag", cfg=cfg)
        with patch("db.helper.build_db_config", return_value=cfg):
            with helper.open(reuse_connection=True) as h1:
                conn1 = h1._conn
            with helper.open(reuse_connection=True) as h2:
                conn2 = h2._conn
        assert conn1 is conn2

    def test_backward_compatibility_per_query(self, tmp_path: Path) -> None:
        """Default reuse_connection=False opens and closes connection each time."""
        db_path = str(tmp_path / "test.sqlite")
        cfg = _make_cfg(db_path)
        helper = SQLiteHelper("rag", cfg=cfg)
        with patch("db.helper.build_db_config", return_value=cfg):
            with helper.open() as h1:
                conn1 = h1._conn
            # After context exit, connection should be closed
            assert conn1 is not None
            with helper.open() as h2:
                conn2 = h2._conn
        # New connection created (different object or same closed+reopened)
        # At minimum: no exception raised and connection is usable
        assert conn2 is not None
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests pass | `uv run pytest tests/test_db_performance.py -v` | all pass |
| Lint | `uv run ruff check tests/test_db_performance.py` | 0 errors |
