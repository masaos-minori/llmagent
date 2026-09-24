"""Tests for tools/check_chunks_fts_invariant.py."""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_SCRIPT = REPO_ROOT / "tools" / "check_chunks_fts_invariant.py"


@pytest.fixture
def tmp_violation_file(tmp_path: Path) -> Path:
    """Create a synthetic file with a chunks_fts violation."""
    f = tmp_path / "violation.py"
    f.write_text('db.execute("INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)")\n')
    return f


def test_detects_unsanctioned_violation(
    tmp_violation_file: Path, tmp_path: Path
) -> None:
    """Lint script should report a violation on synthetic file."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "chunks_fts" in result.stdout


def test_sanctioned_paths_pass(tmp_path: Path) -> None:
    """Sanctioned write paths should produce zero findings."""
    sanctioned_files = [
        ("schema_sql.py", "scripts/db/"),
    ]
    for name, subpath in sanctioned_files:
        src = REPO_ROOT / subpath / name
        if src.exists():
            dst = tmp_path / subpath / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No violations found." in result.stdout


@pytest.fixture
def tmp_mdq_file(tmp_path: Path) -> Path:
    """Create a synthetic MDQ-style file with chunks_fts reference."""
    f = tmp_path / "mdq" / "search.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('db.execute("INSERT INTO chunks_fts(rowid, normalized_content)"\n')
    return f


def test_excludes_mdq_directory(tmp_mdq_file: Path, tmp_path: Path) -> None:
    """MDQ directory should be excluded from detection."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No violations found." in result.stdout


def test_cli_argument_path(tmp_path: Path) -> None:
    """CLI --path argument should work."""
    f = tmp_path / "test.py"
    f.write_text('x = "INSERT INTO chunks_fts"\n')

    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "test.py" in result.stdout


@pytest.fixture
def tmp_update_violation(tmp_path: Path) -> Path:
    """Create a synthetic file with an UPDATE chunks_fts violation."""
    f = tmp_path / "update_violation.py"
    f.write_text('db.execute("UPDATE chunks_fts SET content=? WHERE rowid=?")\n')
    return f


def test_detects_update_violation(tmp_update_violation: Path, tmp_path: Path) -> None:
    """Lint script should detect UPDATE chunks_fts violations too."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "chunks_fts" in result.stdout
