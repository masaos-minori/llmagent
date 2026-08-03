"""tests/test_db_ownership_boundaries.py
Static scan tests for DB ownership boundaries.

Enforces that agent/ code does not directly access rag.sqlite or mdq.sqlite
except through the approved maintenance exceptions.
"""

from __future__ import annotations

import pathlib

AGENT_DIR = pathlib.Path("scripts/agent")

APPROVED_RAG_FILES: set[str] = {
    "services/rag_maintenance_service.py",
}

APPROVED_MDQ_FILES: set[str] = set()


def find_direct_db_calls(root: pathlib.Path, db_name: str) -> list[tuple[str, int]]:
    """Return (relative_path, line_number) for SQLiteHelper("<db_name>") calls under root."""
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


def test_no_unauthorized_rag_db_access() -> None:
    hits = find_direct_db_calls(AGENT_DIR, "rag")
    unauthorized = [(f, ln) for f, ln in hits if f not in APPROVED_RAG_FILES]
    assert not unauthorized, (
        "Unauthorized direct rag DB access found in agent/:\n"
        + "\n".join(f"  {f}:{ln}" for f, ln in unauthorized)
    )


def test_no_unauthorized_mdq_db_access() -> None:
    hits = find_direct_db_calls(AGENT_DIR, "mdq")
    unauthorized = [(f, ln) for f, ln in hits if f not in APPROVED_MDQ_FILES]
    assert not unauthorized, (
        "Unauthorized direct mdq DB access found in agent/:\n"
        + "\n".join(f"  {f}:{ln}" for f, ln in unauthorized)
    )


def test_approved_rag_file_actually_exists() -> None:
    for approved in APPROVED_RAG_FILES:
        assert (AGENT_DIR / approved).exists(), (
            f"Approved file not found: scripts/agent/{approved} — "
            "update APPROVED_RAG_FILES if file was renamed or moved"
        )


def test_negative_forbidden_rag_pattern_detected(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "agent"
    fake_root.mkdir()
    bad_file = fake_root / "bad_module.py"
    bad_file.write_text('db = SQLiteHelper("rag")\n')
    hits = find_direct_db_calls(fake_root, "rag")
    assert len(hits) == 1
    assert hits[0][0] == "bad_module.py"
    assert hits[0][1] == 1


def test_negative_approved_file_not_flagged(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "agent"
    (fake_root / "services").mkdir(parents=True)
    approved_file = fake_root / "services" / "rag_maintenance_service.py"
    approved_file.write_text('db = SQLiteHelper("rag")\n')
    hits = find_direct_db_calls(fake_root, "rag")
    unauthorized = [f for f, _ in hits if f not in APPROVED_RAG_FILES]
    assert not unauthorized


def test_cmd_db_no_direct_rag_access() -> None:
    cmd_db_path = AGENT_DIR / "commands" / "cmd_db.py"
    if not cmd_db_path.exists():
        return
    content = cmd_db_path.read_text()
    assert 'SQLiteHelper("rag")' not in content, (
        "cmd_db.py must not directly access rag DB — use rag_maintenance_service.py"
    )


def test_cmd_mdq_no_direct_db_access() -> None:
    cmd_mdq_path = AGENT_DIR / "commands" / "cmd_mdq.py"
    if not cmd_mdq_path.exists():
        return
    content = cmd_mdq_path.read_text()
    assert 'SQLiteHelper("mdq")' not in content, (
        "cmd_mdq.py must not directly access mdq DB — use MCP tool executor"
    )
