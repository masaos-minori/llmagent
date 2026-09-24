"""Tests for tools/check_chunks_fts_invariant.py."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "tools" / "check_chunks_fts_invariant.py"
SCHEMA_SQL = REPO_ROOT / "scripts" / "db" / "schema_sql.py"
RAG_MAINTENANCE = REPO_ROOT / "scripts" / "agent" / "services" / "rag_maintenance_service.py"


@pytest.fixture
def tmpdir(tmp_path):
    return tmp_path


def _write_file(dir_: Path, name: str, content: str) -> None:
    (dir_ / name).write_text(textwrap.dedent(content), encoding="utf-8")


class TestViolationDetection:
    """Verify the lint script detects unsanctioned chunks_fts writes."""

    def test_detects_insert_violation(self, tmpdir: Path) -> None:
        _write_file(
            tmpdir,
            "bad.py",
            '''db.execute("INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)")''',
        )
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "bad.py" in result.stdout

    def test_detects_update_violation(self, tmpdir: Path) -> None:
        _write_file(
            tmpdir,
            "bad.py",
            '''db.execute("UPDATE chunks_fts SET content=? WHERE rowid=?")''',
        )
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "bad.py" in result.stdout

    def test_no_false_positive_on_schema_sql(self, tmpdir: Path) -> None:
        # Copy the real schema_sql.py to verify whitelist works
        src = REPO_ROOT / "scripts" / "db" / "schema_sql.py"
        dst = tmpdir / "schema_sql.py"
        dst.write_bytes(src.read_bytes())
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No violations found." in result.stdout

    def test_no_false_positive_on_rebuild_fts(self, tmpdir: Path) -> None:
        # Create a copy of rag_maintenance_service.py with only rebuild_fts content
        src = REPO_ROOT / "scripts" / "agent" / "services" / "rag_maintenance_service.py"
        dst = tmpdir / "rag_maintenance_service.py"
        dst.write_bytes(src.read_bytes())
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        # Should still detect violations because lines 106,117 are outside rebuild_fts
        assert result.returncode == 1
        assert "rag_maintenance_service.py" in result.stdout

    def test_excludes_mdq_directory(self, tmpdir: Path) -> None:
        mdq_dir = tmpdir / "mdq"
        mdq_dir.mkdir()
        _write_file(
            mdq_dir,
            "db_schema.py",
            '''INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)''',
        )
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No violations found." in result.stdout

    def test_excludes_tests_directory(self, tmpdir: Path) -> None:
        tests_dir = tmpdir / "tests"
        tests_dir.mkdir()
        _write_file(
            tests_dir,
            "test_bad.py",
            '''INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)''',
        )
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No violations found." in result.stdout

    def test_returns_zero_when_no_matches(self, tmpdir: Path) -> None:
        _write_file(tmpdir, "clean.py", 'print("hello world")')
        result = subprocess.run(
            ["uv", "run", "python", str(SCRIPT), "--path", str(tmpdir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No violations found." in result.stdout
