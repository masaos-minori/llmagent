"""tools/_workitem_length_check.py

Length rule shared by tools/check_workitem_structure.py: decides whether a
documentation-only implementation procedure outgrew the "Lightweight fill for small
rows" target of templates/implementation-procedure.md. Not a CLI; it judges one
document's contents and returns finding dicts shaped like the checker's own rules.
The finding is advisory: the checker does not count it toward its exit code.
"""

from __future__ import annotations

import re

PROCEDURE_LINE_LIMIT = 60

_TARGET_FILE_RE = re.compile(r"(?m)^### Target file\s*\n\s*(?:-\s*)?`([^`]+)`")


def find_docs_procedure_length_findings(
    content: str, rel_path: str, limit: int = PROCEDURE_LINE_LIMIT
) -> list[dict[str, str]]:
    """Report a procedure whose Target file is under docs/ and exceeds `limit` lines.

    Returns an empty list when the Target file cannot be read from the document or is
    not under docs/: a code row may need the full form, so only documentation-only
    rows, the case the lightweight criteria name first, are measured.
    """
    match = _TARGET_FILE_RE.search(content)
    if match is None or not match.group(1).startswith("docs/"):
        return []
    line_count = len(content.splitlines())
    if line_count <= limit:
        return []
    return [
        {
            "category": "procedure-length",
            "file": rel_path,
            "detail": (
                f"documentation-only procedure has {line_count} lines (limit {limit}): "
                "shrink it per templates/implementation-procedure.md 'Lightweight fill "
                "for small rows', or state in the report why this row needs the full form"
            ),
        }
    ]
