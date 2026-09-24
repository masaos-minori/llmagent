"""Regression tests for tools/check_chunks_fts_invariant.py."""

import subprocess
from pathlib import Path

import pytest

LINT_SCRIPT = Path("tools/check_chunks_fts_invariant.py")
REPO_ROOT = Path(__file__).resolve().parent.parent


def test_violation_detected(tmp_path: Path) -> None:
    """Verify the lint script detects an unsanctioned chunks_fts INSERT."""
    # Create a synthetic file with an unsanctioned write
    bad_file = tmp_path / "bad_script.py"
    bad_file.write_text(
        'db.execute("INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)")\n'
    )

    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
    assert "bad_script.py" in result.stdout, (
        f"Expected violation report in output: {result.stdout}"
    )


def test_zero_findings_on_sanctioned_path() -> None:
    """Verify the lint script produces zero findings on sanctioned write paths.

    Scans the repo root where all chunks_fts writes reside in sanctioned paths
    (scripts/agent/services/rag_maintenance_service.py::rebuild_fts and
    scripts/db/schema_sql.py).
    """
    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    assert "No violations found." in result.stdout, (
        f"Expected no violations, got: {result.stdout}"
    )


def test_zero_findings_on_mdq_files() -> None:
    """Verify the lint script produces zero findings on MDQ files.

    The MDQ directory is excluded by the lint script (targets /opt/llm/db/mdq.sqlite).
    """
    mdq_dir = REPO_ROOT / "scripts" / "mcp_servers" / "mdq"
    if not mdq_dir.exists():
        pytest.skip(f"MDQ directory not found: {mdq_dir}")

    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT), "--path", str(mdq_dir)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    assert "No violations found." in result.stdout, (
        f"Expected no violations, got: {result.stdout}"
    )
