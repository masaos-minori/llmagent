# Implementation: test_db_consistency_detail.py

## Goal
Create `tests/test_db_consistency_detail.py` to verify that `_db_consistency()` in
`cmd_db.py` includes numeric fields (`chunks`, `fts`, `vec`, `fts_gap`, `orphan_vec_count`)
in its output, both when consistent and when inconsistent.

## Scope
- New file: `tests/test_db_consistency_detail.py`
- Mock `check_rag_consistency` and `SQLiteHelper` to avoid real SQLite
- Tests for: numeric line written, OK written on consistent, errors written on inconsistent

## Assumptions
- `DbCommand` (or `IngestCommand` / the class owning `_db_consistency()`) can be constructed
  with a mock `_out` that records `write()`, `write_success()`, and `write_error()` calls
- `check_rag_consistency` is patched at `agent.commands.cmd_db.check_rag_consistency`
- `RagConsistencyReport` can be constructed directly with known field values
- `SQLiteHelper` is patched to avoid actual file open

## Implementation

### Target file
`tests/test_db_consistency_detail.py`

### Procedure
Write 2 test cases: one for consistent DB, one for inconsistent DB.

### Method
New test file. Use `unittest.mock.patch` + `MagicMock`.

### Details

```python
"""tests/test_db_consistency_detail.py
Verifies that _db_consistency() includes numeric counts in its output.
"""
from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from db.maintenance import RagConsistencyReport


def _make_report(chunks=10, fts=10, vec=10, fts_gap=0,
                 orphan_vec_count=0, fts_orphan_count=0):
    return RagConsistencyReport(
        chunks=chunks,
        fts=fts,
        vec=vec,
        fts_gap=fts_gap,
        orphan_vec_count=orphan_vec_count,
        fts_orphan_count=fts_orphan_count,
    )


class FakeOut:
    def __init__(self):
        self.lines: list[str] = []
        self.success_lines: list[str] = []
        self.error_lines: list[str] = []

    def write(self, msg: str) -> None:
        self.lines.append(msg)

    def write_success(self, msg: str) -> None:
        self.success_lines.append(msg)

    def write_error(self, msg: str) -> None:
        self.error_lines.append(msg)


@contextmanager
def _patch_rag_consistency(report):
    """Patch check_rag_consistency and SQLiteHelper in cmd_db module."""
    ctx_mgr = MagicMock()
    ctx_mgr.__enter__ = MagicMock(return_value=MagicMock())
    ctx_mgr.__exit__ = MagicMock(return_value=False)
    with (
        patch("agent.commands.cmd_db.check_rag_consistency", return_value=report),
        patch("agent.commands.cmd_db.SQLiteHelper") as mock_helper,
    ):
        mock_helper.return_value.open.return_value = ctx_mgr
        yield


def _make_db_command():
    from agent.commands.cmd_db import DbCommand  # adjust import as needed
    cmd = DbCommand.__new__(DbCommand)
    cmd._out = FakeOut()
    return cmd


def test_consistent_shows_numeric_line():
    """Consistent DB → numeric line written + OK line."""
    report = _make_report(chunks=10, fts=10, vec=10)
    cmd = _make_db_command()

    with _patch_rag_consistency(report):
        cmd._db_consistency()

    all_lines = cmd._out.lines + cmd._out.success_lines
    numeric_lines = [l for l in all_lines if "chunks:" in l and "fts_gap:" in l]
    assert len(numeric_lines) == 1
    assert "10" in numeric_lines[0]
    assert any("OK" in l for l in cmd._out.success_lines)


def test_inconsistent_shows_numeric_line_and_errors():
    """Inconsistent DB → numeric line written + error line per issue."""
    report = _make_report(chunks=10, fts=7, vec=10, fts_gap=3)
    cmd = _make_db_command()

    with _patch_rag_consistency(report):
        cmd._db_consistency()

    all_lines = cmd._out.lines
    numeric_lines = [l for l in all_lines if "fts_gap:" in l]
    assert len(numeric_lines) == 1
    assert "3" in numeric_lines[0]
    assert len(cmd._out.error_lines) >= 1
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 2 tests pass | `uv run pytest tests/test_db_consistency_detail.py -v` | 2 passed |
| Lint | `uv run ruff check tests/test_db_consistency_detail.py` | 0 errors |
| Type check | `uv run mypy tests/test_db_consistency_detail.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
