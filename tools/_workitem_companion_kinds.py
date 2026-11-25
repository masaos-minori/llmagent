"""tools/_workitem_companion_kinds.py — Companion work-item kinds for the checker.

`issue-to-plan` Step 6 files Unknown and Risk follow-ups as
`issues/{timestamp}[_{seq}]_unknowns.md` and `issues/{timestamp}[_{seq}]_risks.md`
(written by `tools/generate_workitem.py --kind unknowns|risks`). They are generated
from `templates/unknowns-issue.md` and `templates/risks-issue.md`, not from
`templates/issue.md`, so `tools/check_workitem_structure.py` resolves them to their
own kinds here and judges them against their own template headings.

`{seq}` is the unvalidated `--seq` string of the generator, digits being its
documented form. An ordinary Issue id always contains a letter, so the digits-only
segment cannot collide with `{timestamp}_{id}_{slug}.md`.
"""

from __future__ import annotations

import re
from pathlib import Path

# kind -> template path relative to the repository root
COMPANION_TEMPLATES: dict[str, str] = {
    "unknowns": "templates/unknowns-issue.md",
    "risks": "templates/risks-issue.md",
}

_COMPANION_NAME_RE = re.compile(r"^\d{8}-\d{6}(?:_\d+)?_(unknowns|risks)\.md$")


def companion_kind(rel_path: Path) -> str | None:
    """Return `unknowns` or `risks` for a companion document path, else None.

    `rel_path` is repository-relative. Only `issues/<name>` and
    `issues/done/<name>` qualify, so a same-named file elsewhere keeps its kind.
    """
    parts = rel_path.parts
    if parts[:1] != ("issues",) or len(parts) not in (2, 3):
        return None
    if len(parts) == 3 and parts[1] != "done":
        return None
    match = _COMPANION_NAME_RE.match(parts[-1])
    return match.group(1) if match else None
