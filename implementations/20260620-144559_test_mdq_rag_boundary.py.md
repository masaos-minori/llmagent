# Implementation: tests/test_mdq_rag_boundary.py (new file)

## Goal

Create a lightweight pytest test that enforces MDQ/RAG data ownership boundaries by
scanning source files for forbidden cross-DB references and disallowed direct SQLite
access patterns in the agent layer.

## Scope

**In:**
- Create `tests/test_mdq_rag_boundary.py` with three assertions:
  1. `mcp/mdq/` source files contain no references to `rag.sqlite`
  2. `mcp/rag_pipeline/` source files contain no references to `mdq.sqlite`
  3. `SQLiteHelper("rag")` in the agent layer appears only in `db_maintenance_service.py`

**Out:**
- Runtime DB access tests
- Changes to production code

## Assumptions

- `Path(__file__).parent.parent / "scripts"` resolves to `scripts/` during pytest
- Source files are UTF-8 encoded Python (`*.py`)
- Comments may contain cross-DB names in passing (e.g., "not rag.sqlite"); the scan
  targets the literal string patterns used in connection paths — practical false positives
  are low given clean current state
- `SQLiteHelper("rag")` is the only allowed direct RAG DB access mechanism in the
  agent layer; `sqlite3.connect` is not used directly in that layer

## Implementation

### Target file

`tests/test_mdq_rag_boundary.py`

### Procedure

1. Create new file at `tests/test_mdq_rag_boundary.py`
2. Use `pathlib.Path.glob` to collect source files per layer
3. Read each file and scan for the forbidden patterns
4. Accumulate violations before asserting (full report on failure)

### Method

```python
"""tests/test_mdq_rag_boundary.py
Boundary enforcement: MDQ/RAG cross-DB access and agent-layer direct DB access.
"""

from __future__ import annotations

from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"


def _py_files(subdir: str) -> list[Path]:
    return list((SCRIPTS / subdir).rglob("*.py"))


class TestMdqRagBoundary:
    def test_mdq_layer_has_no_rag_sqlite_references(self) -> None:
        """mcp/mdq/ must not reference rag.sqlite."""
        violations = [
            str(p) for p in _py_files("mcp/mdq")
            if "rag.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, (
            "rag.sqlite referenced in mcp/mdq/:\n" + "\n".join(f"  {v}" for v in violations)
        )

    def test_rag_pipeline_layer_has_no_mdq_sqlite_references(self) -> None:
        """mcp/rag_pipeline/ must not reference mdq.sqlite."""
        violations = [
            str(p) for p in _py_files("mcp/rag_pipeline")
            if "mdq.sqlite" in p.read_text(encoding="utf-8")
        ]
        assert not violations, (
            "mdq.sqlite referenced in mcp/rag_pipeline/:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_agent_layer_rag_sqlite_access_only_in_maintenance_service(self) -> None:
        """SQLiteHelper("rag") in agent/ must only appear in db_maintenance_service.py."""
        ALLOWED = {"db_maintenance_service.py"}
        pattern = 'SQLiteHelper("rag")'
        violations = [
            str(p) for p in _py_files("agent")
            if pattern in p.read_text(encoding="utf-8")
            and p.name not in ALLOWED
        ]
        assert not violations, (
            f'{pattern!r} found outside allowed files:\n'
            + "\n".join(f"  {v}" for v in violations)
        )
```

### Details

- `_py_files()` uses `rglob("*.py")` to find all Python files recursively, including
  `__init__.py` and sub-packages
- The `ALLOWED` set in the third test is the single source of truth for permitted
  RAG access in the agent layer; adding a new maintenance file requires updating this set
- No mocking required — this is a static analysis test that reads source files
- Runs fast (file I/O only, no imports of production modules)
- `__pycache__` files are excluded automatically because they have `.pyc` extension,
  not `.py`

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File created | `ls tests/test_mdq_rag_boundary.py` | exists |
| All 3 tests pass | `uv run pytest tests/test_mdq_rag_boundary.py -v` | 3 passed |
| Lint | `uv run ruff check tests/test_mdq_rag_boundary.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_rag_boundary.py` | 0 errors |
| No false positives | Review test output for unexpected violations | 0 violations |
