"""tools/_workitem_status_check.py

Status value rule shared by tools/check_workitem_structure.py: decides which rows of a
plan or procedure document's `### Execution Status` table hold a Status value outside
the shared vocabulary of tools/_workitem_status_table.py. Not a CLI; it judges one
document's contents and returns finding dicts shaped like the checker's own rules.
"""

from __future__ import annotations

from tools._workitem_status_table import STATUS_VOCABULARY, parse_execution_status_rows


def find_status_value_findings(content: str, rel_path: str) -> list[dict[str, str]]:
    """Report rows whose Status is outside the vocabulary, as one finding per file.

    Returns an empty list when the document has no Execution Status table (the parser
    returns None: a missing table is a section-gate problem, not a value problem).
    Matching is exact after trimming cell whitespace — no case folding — so a row whose
    cell is empty or reads `N/A: reason` is reported.
    """
    rows = parse_execution_status_rows(content)
    if rows is None:
        return []
    offenders = [
        (row.get("Step", "").strip() or "?", row.get("Status", "").strip())
        for row in rows
        if row.get("Status", "").strip() not in STATUS_VOCABULARY
    ]
    if not offenders:
        return []
    named = ", ".join(f"step {step} has status '{value}'" for step, value in offenders)
    return [
        {
            "category": "status-value",
            "file": rel_path,
            "detail": f"Execution Status row outside the vocabulary: {named}",
        }
    ]
