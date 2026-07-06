# Implementation: tests/test_db_ownership_boundaries.py — DB ownership boundary static scan tests

## Goal

CI-enforced static checks that `agent/` code does not directly access `rag.sqlite` or `mdq.sqlite` outside the approved maintenance exception.

## Scope

**In**: Static scan tests + command chain tests + negative test for forbidden pattern.

**Out**: Source file changes.

## Assumptions

1. `scripts/agent/services/rag_maintenance_service.py` is the ONLY approved direct `rag` accessor.
2. No code in `agent/` directly uses `SQLiteHelper("mdq")`.
3. Tests/scripts directories are excluded from the scan scope.
4. The scan uses simple string matching (not AST) — sufficient because `SQLiteHelper("rag")` is the canonical call pattern.
5. `/db rag urls` and `/db rag clean` call `rag_maintenance_service.py` (no raw DB access).
6. `/mdq` commands call through `cmd_mdq.py` → tool executor (no raw DB access).

## Implementation

### Target file
`tests/test_db_ownership_boundaries.py`

### Procedure
1. Implement `find_direct_db_calls()` scanner.
2. Write `test_no_unauthorized_rag_db_access()` with approved whitelist.
3. Write `test_no_unauthorized_mdq_db_access()`.
4. Write negative test: `rag_maintenance_service.py` IS in the whitelist (prevents false positives).
5. Write `test_negative_forbidden_pattern_detected()` — temp file with forbidden pattern triggers scan.

### Method

```python
import pathlib
import tempfile

AGENT_DIR = pathlib.Path("scripts/agent")
APPROVED_RAG_FILES: set[str] = {
    "services/rag_maintenance_service.py",
}
APPROVED_MDQ_FILES: set[str] = set()  # no direct mdq access is ever approved


def find_direct_db_calls(root: pathlib.Path, db_name: str) -> list[tuple[str, int]]:
    """Find SQLiteHelper("<db_name>") calls in Python source files under root.
    Returns list of (relative_path, line_number).
    """
    pattern = f'SQLiteHelper("{db_name}")'
    hits: list[tuple[str, int]] = []
    for py_file in sorted(root.rglob("*.py")):
        try:
            lines = py_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, 1):
            if pattern in line:
                hits.append((str(py_file.relative_to(root)), lineno))
    return hits


def test_no_unauthorized_rag_db_access():
    hits = find_direct_db_calls(AGENT_DIR, "rag")
    unauthorized = [
        (f, ln) for f, ln in hits
        if f not in APPROVED_RAG_FILES
    ]
    assert not unauthorized, (
        f"Unauthorized direct rag DB access found in agent/:\n"
        + "\n".join(f"  {f}:{ln}" for f, ln in unauthorized)
    )


def test_no_unauthorized_mdq_db_access():
    hits = find_direct_db_calls(AGENT_DIR, "mdq")
    unauthorized = [
        (f, ln) for f, ln in hits
        if f not in APPROVED_MDQ_FILES
    ]
    assert not unauthorized, (
        f"Unauthorized direct mdq DB access found in agent/:\n"
        + "\n".join(f"  {f}:{ln}" for f, ln in unauthorized)
    )


def test_approved_rag_file_actually_exists():
    """Whitelist sanity check: approved file must exist to prevent stale whitelist."""
    for approved in APPROVED_RAG_FILES:
        assert (AGENT_DIR / approved).exists(), (
            f"Approved file not found: scripts/agent/{approved} — "
            "update APPROVED_RAG_FILES if file was renamed or moved"
        )


def test_negative_forbidden_rag_pattern_detected(tmp_path):
    """Verify scanner detects a forbidden pattern when planted in a temp file.
    This is a meta-test: it ensures the scanner would catch violations.
    """
    fake_root = tmp_path / "agent"
    fake_root.mkdir()
    bad_file = fake_root / "bad_module.py"
    bad_file.write_text('db = SQLiteHelper("rag")\n')
    hits = find_direct_db_calls(fake_root, "rag")
    assert len(hits) == 1
    assert hits[0][0] == "bad_module.py"
    assert hits[0][1] == 1


def test_negative_approved_file_not_flagged(tmp_path):
    """Approved file with the pattern should NOT appear in unauthorized list."""
    fake_root = tmp_path / "agent"
    (fake_root / "services").mkdir(parents=True)
    approved_file = fake_root / "services" / "rag_maintenance_service.py"
    approved_file.write_text('db = SQLiteHelper("rag")\n')
    hits = find_direct_db_calls(fake_root, "rag")
    unauthorized = [f for f, _ in hits if f not in APPROVED_RAG_FILES]
    assert not unauthorized


def test_cmd_db_uses_rag_maintenance_service():
    """cmd_db.py must not import SQLiteHelper("rag") directly — it should use rag_maintenance_service."""
    cmd_db_path = AGENT_DIR / "commands" / "cmd_db.py"
    if not cmd_db_path.exists():
        return  # skip if file not found
    content = cmd_db_path.read_text()
    assert 'SQLiteHelper("rag")' not in content, (
        "cmd_db.py must not directly access rag DB — use rag_maintenance_service.py"
    )


def test_cmd_mdq_no_direct_db_access():
    """cmd_mdq.py must not import SQLiteHelper("mdq") directly."""
    cmd_mdq_path = AGENT_DIR / "commands" / "cmd_mdq.py"
    if not cmd_mdq_path.exists():
        return  # skip if file not found
    content = cmd_mdq_path.read_text()
    assert 'SQLiteHelper("mdq")' not in content, (
        "cmd_mdq.py must not directly access mdq DB — use MCP tool executor"
    )
```

## Validation plan

- `uv run pytest tests/test_db_ownership_boundaries.py -v` — all pass.
- `ruff check tests/test_db_ownership_boundaries.py` — 0 errors.
- Confirm: planting `SQLiteHelper("rag")` in a new temp agent file → `test_no_unauthorized_rag_db_access` fails.
