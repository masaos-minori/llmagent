"""tools/_workitem_citation_check.py

Plain path citation rule shared by tools/check_workitem_structure.py (the finding) and
tools/backtick_plan_related_tests.py (the repair). Not a CLI.

tools/close_procedures_batch.py reads the `File Path` column of `Implementation Target
Files` and the `Implementation steps` through a backtick regular expression, and
tools/check_workitem_traceability.py reads the `Related Tests` column the same way, so a
path written without backticks in those three places is silently ignored. This module
finds those plain paths and wraps them; it never reads any other table or section, and a
cell that is not a bare path (trailing text, a command, `N/A: ...`) is left alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_PATH_CELL_RE = re.compile(r"^[\w.-]+(?:/[\w.-]+)+$")
_TEST_PATH_RE = re.compile(r"(?<![\w/.-])tests/[\w./-]+\.py(?![\w/-]|\.\w)")
_CODE_SPAN_RE = re.compile(r"`[^`]*`")

KIND_FILE_PATH = "File Path"
KIND_RELATED_TESTS = "Related Tests"
KIND_STEPS = "Implementation steps"


@dataclass(frozen=True)
class PlainCitation:
    """One plain path: `line_index` is 0-based into `text.split("\\n")`; offsets are in that line."""

    kind: str
    line_index: int
    start: int
    end: int
    path: str


def _blank_code_spans(line: str) -> str:
    """Replace each backtick span by spaces of equal length, so offsets stay valid."""
    return _CODE_SPAN_RE.sub(lambda match: " " * len(match.group()), line)


def _section_range(lines: list[str], name: str) -> tuple[int, int]:
    """Body line range of `## name`, or (0, 0) when the section is absent."""
    heading = f"## {name}"
    for start, line in enumerate(lines):
        if line.rstrip() == heading:
            end = next(
                (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
                len(lines),
            )
            return start + 1, end
    return 0, 0


def _split_cells(line: str) -> list[tuple[str, int]]:
    """Cells of a table row as (text, offset of the text in the line)."""
    parts = line.split("|")
    cells: list[tuple[str, int]] = []
    offset = len(parts[0]) + 1
    for part in parts[1:-1]:
        cells.append((part, offset))
        offset += len(part) + 1
    return cells


def _table_rows(
    lines: list[str],
) -> tuple[list[tuple[int, list[tuple[str, int]]]], int | None]:
    """Data rows of the target table and the index of its `Related Tests` column."""
    start, end = _section_range(lines, "Implementation Target Files")
    for i in range(start, end):
        if not lines[i].startswith("| File Path |"):
            continue
        header = [text.strip() for text, _ in _split_cells(lines[i])]
        related = header.index("Related Tests") if "Related Tests" in header else None
        rows: list[tuple[int, list[tuple[str, int]]]] = []
        j = i + 2
        while j < end and lines[j].startswith("|"):
            rows.append((j, _split_cells(lines[j])))
            j += 1
        return rows, related
    return [], None


def _target_paths_and_file_cells(
    rows: list[tuple[int, list[tuple[str, int]]]],
) -> tuple[list[str], list[PlainCitation]]:
    paths: list[str] = []
    plain: list[PlainCitation] = []
    for line_index, cells in rows:
        if not cells:
            continue
        text, offset = cells[0]
        stripped = text.strip()
        if _PATH_CELL_RE.match(stripped):
            start = offset + len(text) - len(text.lstrip())
            plain.append(
                PlainCitation(
                    KIND_FILE_PATH, line_index, start, start + len(stripped), stripped
                )
            )
            paths.append(stripped)
        elif (
            stripped.startswith("`")
            and stripped.endswith("`")
            and _PATH_CELL_RE.match(stripped[1:-1])
        ):
            paths.append(stripped[1:-1])
    return paths, plain


def find_plain_citations(text: str) -> list[PlainCitation]:
    """Plain paths in the target table's `File Path` and `Related Tests` cells and the steps."""
    lines = text.split("\n")
    rows, related_index = _table_rows(lines)
    paths, found = _target_paths_and_file_cells(rows)
    if related_index is not None:
        for line_index, cells in rows:
            if related_index >= len(cells):
                continue
            cell, offset = cells[related_index]
            for match in _TEST_PATH_RE.finditer(_blank_code_spans(cell)):
                start = offset + match.start()
                found.append(
                    PlainCitation(
                        KIND_RELATED_TESTS,
                        line_index,
                        start,
                        offset + match.end(),
                        match.group(),
                    )
                )
    patterns = [
        (path, re.compile(r"(?<![\w/.-])" + re.escape(path) + r"(?![\w/-]|\.\w)"))
        for path in sorted(set(paths), key=len, reverse=True)
    ]
    steps_start, steps_end = _section_range(lines, "Implementation steps")
    for line_index in range(steps_start, steps_end):
        blanked = _blank_code_spans(lines[line_index])
        taken: list[tuple[int, int]] = []
        for path, pattern in patterns:
            for match in pattern.finditer(blanked):
                if any(match.start() < b and a < match.end() for a, b in taken):
                    continue
                taken.append((match.start(), match.end()))
                found.append(
                    PlainCitation(
                        KIND_STEPS, line_index, match.start(), match.end(), path
                    )
                )
    return sorted(found, key=lambda c: (c.line_index, c.start))


def wrap_plain_citations(text: str) -> str:
    """Wrap every plain citation in backticks; the identity when there is none."""
    citations = find_plain_citations(text)
    if not citations:
        return text
    lines = text.split("\n")
    for citation in sorted(
        citations, key=lambda c: (c.line_index, c.start), reverse=True
    ):
        line = lines[citation.line_index]
        lines[citation.line_index] = (
            f"{line[: citation.start]}`{line[citation.start : citation.end]}`{line[citation.end :]}"
        )
    return "\n".join(lines)


def find_plan_citation_findings(doc_path: Path, root: Path) -> list[dict[str, str]]:
    """One `plain-path-citation` finding per plain citation of the Plan at `doc_path`."""
    rel_path = doc_path.resolve().relative_to(root.resolve()).as_posix()
    text = doc_path.read_text(encoding="utf-8")
    return [
        {
            "category": "plain-path-citation",
            "file": rel_path,
            "detail": (
                f"{citation.kind}: {citation.path} is not in backticks (line {citation.line_index + 1}); "
                f"run uv run python tools/backtick_plan_related_tests.py {rel_path}"
            ),
        }
        for citation in find_plain_citations(text)
    ]
