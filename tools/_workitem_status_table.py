"""tools/_workitem_status_table.py

Execution Status table logic of tools/manage_workitem_stage.py: parsing the
`### Execution Status` table of a work item, rendering its rows, and rewriting the
status of a row. Not a CLI; tools/manage_workitem_stage.py re-exports the public names.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from tools._atomic_write import atomic_write_text


def _normalize_status(raw: str) -> str:
    """Normalize a status string to its canonical form.

    Accepts camelCase / snake_case variants (e.g. ``InProgress``, ``in_progress``)
    and returns the canonical value defined in ``_VALID_STATUSES``.
    Raises ``ValueError`` when the raw value cannot be mapped.
    """
    lower = raw.lower()
    if lower in _STATUS_ALIASES:
        return _STATUS_ALIASES[lower]
    if raw in _VALID_STATUSES:
        return raw
    raise ValueError(
        f"invalid status '{raw}'; must be one of: {', '.join(sorted(_VALID_STATUSES))}"
    )


def parse_execution_status_rows(content: str) -> list[dict[str, str]] | None:
    """Parse the `### Execution Status` Markdown table's data rows.

    Returns `None` when the heading itself cannot be found, or when the table's
    header row does not include a `Status` column (both a structural problem,
    distinct from an empty table) — a renamed or missing `Status` column would
    otherwise silently disable `close-implementation`'s Pending-row block instead
    of surfacing an error. Each returned row maps the header's column names
    (`Step`, `Description`, `Status`, `Started`, `Completed`, `Notes`) to that
    row's cell values.
    """
    lines = content.splitlines()
    heading_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == EXECUTION_STATUS_HEADING),
        None,
    )
    if heading_idx is None:
        return None

    header: list[str] | None = None
    separator_seen = False
    rows: list[dict[str, str]] = []
    for line in lines[heading_idx + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            if "Status" not in header:
                return None
            continue
        if not separator_seen:
            separator_seen = True
            if all(re.fullmatch(r"-+", cell) for cell in cells):
                continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def update_execution_status(
    source: Path,
    kind: str,
    step_number: int | None = None,
    description_match: str | None = None,
    new_status: str = "",
    new_notes: str | None = None,
    new_started: str | None = None,
    new_completed: str | None = None,
) -> bool:
    """Update the Execution Status table on an implementation or plan file.

    If ``step_number`` is given, only that row's ``Status`` column is changed.
    If ``description_match`` is given, the first row whose ``Description`` contains
    the substring (case-insensitive) is updated.
    Otherwise every row's ``Status`` column is set to ``new_status``.

    When ``new_notes`` is provided, the Notes column of the matched row(s) is
    appended with the text (a single space separator is inserted before appending).

    When ``new_started`` / ``new_completed`` is provided, the matched row(s)' Started /
    Completed column is overwritten (not appended) with that value — pass the output of
    `date +%Y%m%d-%H%M%S` (per `templates/execution-status.md` Notes) to record an actual
    execution timestamp; this function does not generate one itself.

    Returns ``True`` when at least one row was modified; ``False`` when nothing
    matched or the file could not be written.
    """
    try:
        new_status = _normalize_status(new_status)
    except ValueError:
        print(
            f"ERROR: invalid status '{new_status}', must be one of: "
            f"{', '.join(sorted(_VALID_STATUSES))}",
            file=sys.stderr,
        )
        return False

    content = source.read_text(encoding="utf-8")
    heading, header, data_rows = parse_execution_status_table(content)
    if heading is None or header is None or data_rows is None:
        print(
            f"ERROR: '{EXECUTION_STATUS_HEADING}' table missing or malformed "
            f"(no 'Status' column) in {source}",
            file=sys.stderr,
        )
        return False

    status_col_idx = header.index("Status")
    notes_col_idx = header.index("Notes")
    modified = False

    for row in data_rows:
        if step_number is not None:
            try:
                row_step = int(row[header.index("Step")])
            except (ValueError, IndexError):
                continue
            if row_step != step_number:
                continue
        elif description_match is not None:
            desc_col_idx = header.index("Description")
            row_desc = row[desc_col_idx].lower()
            if description_match.lower() not in row_desc:
                continue
        # else: update every row

        row[status_col_idx] = new_status
        modified = True

        if new_started is not None:
            row[header.index("Started")] = new_started
            modified = True

        if new_completed is not None:
            row[header.index("Completed")] = new_completed
            modified = True

        if new_notes is not None:
            existing_notes = row[notes_col_idx]
            if existing_notes.strip():
                row[notes_col_idx] = f"{existing_notes} {new_notes}"
            else:
                row[notes_col_idx] = new_notes
            modified = True

    if not modified:
        if step_number is not None:
            print(
                f"ERROR: no row with Step={step_number} found in {source}",
                file=sys.stderr,
            )
        elif description_match is not None:
            print(
                f"ERROR: no row with Description containing '{description_match}' "
                f"found in {source}",
                file=sys.stderr,
            )
        else:
            print(
                f"ERROR: no rows found in {source}",
                file=sys.stderr,
            )
        return False

    # Rebuild the entire table section from modified data_rows
    new_lines: list[str] = []
    in_table = False
    separator_appended = False
    rows_inserted = False
    for line in content.splitlines():
        if line.strip() == EXECUTION_STATUS_HEADING:
            new_lines.append(line)
            in_table = True
            continue
        if in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not separator_appended:
                # Header row, then the separator row — keep both as-is; only
                # rows seen *after* the separator are data rows to rebuild.
                new_lines.append(line)
                if all(re.fullmatch(r"-+", c) for c in cells):
                    separator_appended = True
                continue
            if len(cells) == len(header):
                # Data row — skip, will be replaced with rebuilt rows
                continue
            # Empty line or non-table line after the table — insert the
            # rebuilt rows here, right where the original data rows ended,
            # before falling through to append this non-table line.
            for dr in data_rows:
                new_lines.append(build_data_row_line(header, dr))
            rows_inserted = True
            in_table = False
        new_lines.append(line)

    # If the table ran to the end of the file (no trailing line ever
    # triggered the insertion above), append the rebuilt rows now.
    if separator_appended and not rows_inserted:
        for dr in data_rows:
            new_lines.append(build_data_row_line(header, dr))

    # Write back
    new_content = "\n".join(new_lines)
    atomic_write_text(source, new_content)
    return True


def _rows_equal(a: list[str], b: list[str], header: list[str]) -> bool:
    """Check whether two rows match on all columns except Status and Notes."""
    status_idx = header.index("Status")
    notes_idx = header.index("Notes")
    for i, col in enumerate(header):
        if i == status_idx or i == notes_idx:
            continue
        if a[i] != b[i]:
            return False
    return True


def parse_execution_status_table(
    content: str,
) -> tuple[str | None, list[str] | None, list[list[str]] | None]:
    """Parse the `### Execution Status` table into components.

    Returns (heading_line, header_cells, data_rows) where each data row is a list of
    cell strings matching the header length. Returns None for any component if parsing
    fails.
    """
    lines = content.splitlines()
    heading_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == EXECUTION_STATUS_HEADING),
        None,
    )
    if heading_idx is None:
        return None, None, None

    header: list[str] | None = None
    separator_seen = False
    data_rows: list[list[str]] = []
    for line in lines[heading_idx + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            if "Status" not in header:
                return None, None, None
            continue
        if not separator_seen:
            separator_seen = True
            if all(re.fullmatch(r"-+", cell) for cell in cells):
                continue
        if len(cells) != len(header):
            continue
        data_rows.append(cells)
    return EXECUTION_STATUS_HEADING, header, data_rows


def build_table_header_line(header: list[str]) -> str:
    """Rebuild a Markdown table header line from header cells."""
    return "| " + " | ".join(header) + " |"


def build_table_separator_line(header_len: int) -> str:
    """Rebuild a Markdown table separator line."""
    return "|" + "|".join(["------"] * header_len) + "|"


def build_data_row_line(header: list[str], cells: list[str]) -> str:
    """Rebuild a Markdown table data row line."""
    return "| " + " | ".join(cells) + " |"


EXECUTION_STATUS_HEADING = "### Execution Status"


_VALID_STATUSES = frozenset({"Pending", "In Progress", "Blocked", "Completed"})
# Alias mapping: camelCase / snake_case variants → canonical status string
_STATUS_ALIASES = {
    "inprogress": "In Progress",
    "in_progress": "In Progress",
}
