"""tests/test_db_consistency_detail.py
Verifies that _db_consistency() includes numeric counts in its output.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import patch

from db.models import RagConsistencyReport
from db.rag_consistency import summarize_issues


def _make_report(
    chunks=10, fts=10, vec=10, fts_gap=0, orphan_vec_count=0, fts_orphan_count=0
):
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


@dataclass(frozen=True)
class RagConsistencyResult:
    is_consistent: bool
    issues: list[str]
    report: RagConsistencyReport


@contextmanager
def _patch_rag_consistency(report):
    """Patch RagMaintenanceService.consistency() in cmd_db module."""
    issues = [] if report.chunks == report.fts else [f"FTS gap: {report.fts_gap}"]
    result = RagConsistencyResult(
        is_consistent=report.chunks == report.fts,
        issues=issues,
        report=report,
    )
    with patch("agent.commands.db_rag_ops.RagMaintenanceService") as mock_svc:
        mock_svc.return_value.consistency.return_value = result
        yield


def _make_db_command():
    from agent.commands.cmd_db import _DbMixin
    from agent.commands.db_rag_ops import DbRagOps

    cmd = _DbMixin.__new__(_DbMixin)
    cmd._out = FakeOut()
    cmd._rag_ops = DbRagOps(ctx=None, out=cmd._out)
    return cmd


def test_consistent_shows_numeric_line():
    """Consistent DB -> numeric line written + OK line."""
    report = _make_report(chunks=10, fts=10, vec=10)
    cmd = _make_db_command()

    with _patch_rag_consistency(report):
        cmd._rag_ops.consistency()

    all_lines = cmd._out.lines + cmd._out.success_lines
    numeric_lines = [
        line for line in all_lines if "chunks:" in line and "fts_gap:" in line
    ]
    assert len(numeric_lines) == 1
    assert "10" in numeric_lines[0]
    assert any("OK" in line for line in cmd._out.success_lines)


def test_inconsistent_shows_numeric_line_and_errors():
    """Inconsistent DB -> numeric line written + error line per issue."""
    report = _make_report(chunks=10, fts=7, vec=10, fts_gap=3)
    cmd = _make_db_command()

    with _patch_rag_consistency(report):
        cmd._rag_ops.consistency()

    all_lines = cmd._out.lines
    numeric_lines = [line for line in all_lines if "fts_gap:" in line]
    assert len(numeric_lines) == 1
    assert "3" in numeric_lines[0]
    assert len(cmd._out.error_lines) >= 1


def test_inconsistent_shows_affected_identifiers_in_issue():
    """Inconsistent DB -> issue lines contain affected identifiers from summarize_issues()."""
    report_with_ids = RagConsistencyReport(
        chunks=10,
        fts=7,
        vec=10,
        fts_gap=3,
        orphan_vec_count=0,
        fts_orphan_count=0,
        affected_chunk_ids=(101, 102),
        affected_doc_ids=(5, 6),
    )
    cmd = _make_db_command()

    with patch("agent.commands.db_rag_ops.RagMaintenanceService") as mock_svc:
        result = RagConsistencyResult(
            is_consistent=False,
            issues=summarize_issues(report_with_ids),
            report=report_with_ids,
        )
        mock_svc.return_value.consistency.return_value = result
        cmd._rag_ops.consistency()

    error_lines = cmd._out.error_lines
    assert len(error_lines) >= 1
    combined_errors = "".join(error_lines)
    assert (
        "Affected doc_ids" in combined_errors
        or "/db rag rebuild-fts" in combined_errors
    )
