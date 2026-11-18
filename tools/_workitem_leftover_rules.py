"""tools/_workitem_leftover_rules.py

Scaffold leftover rules for the three work item kinds, shared by
tools/check_workitem_structure.py: the verbatim issue-template line rule
(relocated from the checker, behavior unchanged) and the structural rules
for plans and procedures — a Traceability field whose whole value is a
`{...}` placeholder, a table data row whose cells are all empty, and, for a
plan only, a line equal to a bracket-wrapped placeholder line of the
`templates/plan.md` fence (the set derived at run time; no recorded list).
Not a CLI; each finder takes the document and the repository root in from
the checker and returns finding dicts shaped like the checker's own rules.
The rules never compare the Freeze paragraph or any other prose.
"""

from __future__ import annotations

import re
from pathlib import Path

_FENCE_RE = re.compile(r"```markdown\n(.*?)\n```", re.DOTALL)
_PLACEHOLDER_BRACE_RE = re.compile(r"\{[^{}]*\}")
_WHOLE_VALUE_RE = re.compile(r"^- \*\*[^*]+\*\*: \{[^{}]+\}$")
_BRACKET_LINE_RE = re.compile(r"^\[[^\]]*\]$")


def issue_template_leftover_lines(template_path: Path) -> frozenset[str]:
    """Build the verbatim leftover rule from the issue template's fenced scaffold.

    The rule is the scaffold an unfilled issue keeps verbatim: the `# <Issue
    Title>` line, the bullets holding a `{...}` placeholder, and the
    instruction lines under each `## ` heading. Section headings and table
    rows stay out — a filled document legitimately repeats them.
    """
    fence_match = _FENCE_RE.search(template_path.read_text(encoding="utf-8"))
    if fence_match is None:
        return frozenset()
    lines: list[str] = []
    for raw in fence_match.group(1).splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("##") or stripped.startswith("|"):
            continue
        if stripped.startswith("# ") or not stripped.startswith(("- ", "* ")):
            lines.append(stripped)
        elif _PLACEHOLDER_BRACE_RE.search(stripped):
            lines.append(stripped)
    return frozenset(lines)


def find_issue_leftover_findings(
    doc_path: Path, root: Path, rule: frozenset[str] | None = None
) -> list[dict[str, str]]:
    """Report an issue document that keeps canonical-template lines verbatim.

    ``rule`` lets a directory scan load the template once; pass None to read
    it from ``templates/issue.md`` on the spot.
    """
    if rule is None:
        rule = issue_template_leftover_lines(root / "templates" / "issue.md")
    if not rule:
        return []
    rel_path = doc_path.relative_to(root).as_posix()
    findings: list[dict[str, str]] = []
    for raw in doc_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped in rule:
            findings.append(
                {
                    "category": "template-leftover",
                    "file": rel_path,
                    "detail": f"verbatim issue-template leftover: {stripped}",
                }
            )
    return findings


def plan_bracket_lines(template_path: Path) -> frozenset[str]:
    """The bracket-wrapped placeholder lines of the plan template's fence.

    Derived at run time so the rule follows any change to the template;
    no line list is recorded anywhere.
    """
    fence_match = _FENCE_RE.search(template_path.read_text(encoding="utf-8"))
    if fence_match is None:
        return frozenset()
    return frozenset(
        stripped
        for stripped in (raw.strip() for raw in fence_match.group(1).splitlines())
        if _BRACKET_LINE_RE.match(stripped)
    )


def _structural_leftover_findings(
    doc_path: Path, root: Path, bracket_lines: frozenset[str] | None
) -> list[dict[str, str]]:
    """Report unfilled scaffold lines of a plan (with brackets) or procedure."""
    rel_path = doc_path.relative_to(root).as_posix()
    findings: list[dict[str, str]] = []
    for lineno, raw in enumerate(doc_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        detail = _structural_leftover_detail(stripped, bracket_lines, lineno)
        if detail is not None:
            findings.append(
                {"category": "template-leftover", "file": rel_path, "detail": detail}
            )
    return findings


def _structural_leftover_detail(
    stripped: str, bracket_lines: frozenset[str] | None, lineno: int
) -> str | None:
    """One finding detail for an unfilled structural line, None when filled."""
    if _WHOLE_VALUE_RE.match(stripped):
        return f"unfilled Traceability value (line {lineno}): {stripped}"
    if _is_all_empty_row(stripped):
        return f"all-empty table row (line {lineno}): {stripped}"
    if bracket_lines is not None and stripped in bracket_lines:
        return f"verbatim plan-template bracket line (line {lineno}): {stripped}"
    return None


def _is_all_empty_row(stripped: str) -> bool:
    """True for a table data row whose cells hold no text at all.

    Dash placeholder rows (`| — | — |`) and separator rows (`|---|`) carry
    text and stay unreported — a filled document legitimately keeps them.
    """
    if not stripped.startswith("|"):
        return False
    return all(not cell.strip() for cell in stripped.strip("|").split("|"))


def find_plan_leftover_findings(
    doc_path: Path, root: Path, bracket_lines: frozenset[str] | None = None
) -> list[dict[str, str]]:
    """Report unfilled scaffold lines of a plan document.

    ``bracket_lines`` lets a directory scan derive the set from the plan
    template once; pass None to read it on the spot.
    """
    if bracket_lines is None:
        bracket_lines = plan_bracket_lines(root / "templates" / "plan.md")
    return _structural_leftover_findings(doc_path, root, bracket_lines)


def find_procedure_leftover_findings(
    doc_path: Path, root: Path
) -> list[dict[str, str]]:
    """Report unfilled scaffold lines of a procedure document (no bracket rule)."""
    return _structural_leftover_findings(doc_path, root, None)
