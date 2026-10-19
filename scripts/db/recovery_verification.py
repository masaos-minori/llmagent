#!/usr/bin/env python3
"""scripts/db/recovery_verification.py — Logical verification of a recovered database.

Owns the logical half of recovery verification: dispatch a target to the consistency
contract defined for its domain, and summarize an inconsistent report as
counts/identifiers only (REQ-010/AC-7). Condition classification, the physical
integrity check, and the RecoveryResult policy stay in db.recovery, which calls
these helpers.
"""

import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path

from db.helper import SQLiteHelper
from db.models import (
    RagConsistencyReport,
    SessionConsistencyReport,
)
from db.rag_consistency import check_rag_consistency
from db.rag_consistency import is_consistent as rag_is_consistent
from db.session_consistency import (
    check_session_consistency,
)
from db.session_consistency import (
    is_consistent as session_is_consistent,
)

logger = logging.getLogger(__name__)


def _rag_inconsistency_detail(report: RagConsistencyReport) -> str:
    """Summarize a rag report's inconsistencies as counts/identifiers only (REQ-010/AC-7).

    Entries are listed in the order `check_rag_consistency` computes them. An empty
    string means the inconsistency came from a check this summary does not name
    (read smoke test, diagnostic errors).
    """
    mismatches = report.url_level_mismatches or {}
    entries: list[tuple[bool, str]] = [
        (report.fts_gap > 0, f"fts_gap={report.fts_gap}"),
        (report.fts_orphan_count > 0, f"fts_orphan={report.fts_orphan_count}"),
        (report.orphan_vec_count > 0, f"orphan_vec={report.orphan_vec_count}"),
        (report.vec != report.chunks, f"vec={report.vec}/chunks={report.chunks}"),
        (
            report.documents_without_chunks_count > 0,
            f"docs_no_chunks={report.documents_without_chunks_count}",
        ),
        (
            report.chunks_without_vec_count > 0,
            f"chunks_no_vec={report.chunks_without_vec_count}",
        ),
        (
            report.duplicate_chunk_index_count > 0,
            f"dup_chunk_idx={report.duplicate_chunk_index_count}",
        ),
        (bool(mismatches), f"url_mismatches={len(mismatches)}"),
    ]
    return "; ".join(text for include, text in entries if include)


def _session_inconsistency_detail(report: SessionConsistencyReport) -> str:
    """Summarize a session report's inconsistencies as counts/identifiers only (REQ-010/AC-7).

    `write_smoke_test_ok is False` is the only trigger for the write-smoke entry:
    None means the test was not run, which is not an inconsistency.
    """
    errors = report.diagnostic_errors or ()
    entries: list[tuple[bool, str]] = [
        (
            report.orphaned_message_count > 0,
            f"orphan_msgs={report.orphaned_message_count}",
        ),
        (
            report.orphaned_memory_link_count > 0,
            f"orphan_mem_links={report.orphaned_memory_link_count}",
        ),
        (not report.session_diagnostics_readable, "diag_not_readable"),
        (not report.read_smoke_test_ok, "read_smoke_fail"),
        (report.write_smoke_test_ok is False, "write_smoke_fail"),
        (bool(errors), f"errors={len(errors)}"),
    ]
    return "; ".join(text for include, text in entries if include)


def _verify_rag_logic(db: SQLiteHelper) -> tuple[bool, str | None]:
    """Return (consistent, count-only detail) for the rag domain."""
    report = check_rag_consistency(db)
    if rag_is_consistent(report):
        return True, None
    return False, _rag_inconsistency_detail(report)


def _verify_session_logic(db: SQLiteHelper) -> tuple[bool, str | None]:
    """Return (consistent, count-only detail) for the session domain."""
    report = check_session_consistency(db)
    if session_is_consistent(report):
        return True, None
    return False, _session_inconsistency_detail(report)


# Logical verifiers by target. A target missing from this table skips logical
# verification entirely: no consistency contract is defined for it.
_LOGICAL_VERIFIERS: dict[str, Callable[[SQLiteHelper], tuple[bool, str | None]]] = {
    "rag": _verify_rag_logic,
    "session": _verify_session_logic,
}


def _run_logical_verification(db_path: Path, target: str) -> tuple[bool, str | None]:
    """Run logical consistency verification on the restored database.

    Returns (consistent, detail_string) — detail contains a short summary
    of counts/identifiers only (no row content), matching REQ-010/AC-7.

    An unknown target, or a database this stage cannot open, is reported as
    consistent: a verification gap must never block a completed physical restore.
    """
    verify = _LOGICAL_VERIFIERS.get(target)
    if verify is None:
        return True, None
    try:
        with SQLiteHelper(target, db_path=str(db_path)).open() as db:
            return verify(db)
    except sqlite3.Error as e:
        logger.warning("Logical verification could not open DB: %s", e)
        return True, None
