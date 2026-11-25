#!/usr/bin/env python3
"""tools/set_step_status_batch.py - Applies a batch of Execution Status row updates.

Recording one implementation cycle's rows is the same `manage_workitem_stage.py
set-step-status` operation for every row, so the rows are described once in a JSON file and
applied here. Each record is the operation that command performs; nothing is verified beyond
what it verifies (the file exists and the row parses), so `close_procedures_batch.py` stays
the tool that gates an archive on the rows.

Usage:
    python tools/set_step_status_batch.py RECORDS.json

Record format (JSON array of objects):
    {"path": "implementations/....md", "kind": "implementation-procedure",
     "step": 3, "status": "In Progress", "notes": "..."}

- `kind` defaults to `implementation-procedure`; `step` selects one row, or `description`
  selects the first row whose Description contains the text.
- Timestamps are stamped by status: `In Progress` sets
  Started, `Completed` sets Completed and Started when Started is unset. A record may name an
  explicit `started` or `completed` value instead, which overrides the stamp.
- Rows are never completed implicitly: a record must name the status it wants.

Exit codes: 0 when every record applied, 1 when any record failed (each failure is reported
and the others are still attempted), 2 when the records file is missing, unreadable, or not a
JSON array.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._workitem_status_table import update_execution_status


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def _text(record: dict[str, object], key: str) -> str | None:
    """A record field as text, or None when it is absent."""
    value = record.get(key)
    return None if value is None else str(value)


def _apply(record: dict[str, object]) -> bool:
    source = Path(str(record.get("path", "")))
    if not source.is_file():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return False

    step_number = record.get("step")
    if step_number is not None and not isinstance(step_number, int):
        print(
            f"ERROR: record step must be an integer: {step_number!r}", file=sys.stderr
        )
        return False

    status = str(record.get("status", ""))
    now = _ts()
    started = _text(record, "started")
    completed = _text(record, "completed")
    if status == "In Progress":
        started = started or now
    elif status == "Completed":
        completed = completed or now
        started = started or now

    description = _text(record, "description")
    label = f"step={step_number}" if step_number is not None else f"'{description}'"
    modified = update_execution_status(
        source=source,
        kind=str(record.get("kind", "implementation-procedure")),
        step_number=step_number,
        description_match=description,
        new_status=status,
        new_notes=_text(record, "notes"),
        new_started=started,
        new_completed=completed,
    )
    if not modified:
        print(f"ERROR: no row updated: {source} {label}", file=sys.stderr)
        return False
    print(f"OK: updated {label} to '{status}' in {source}")
    return True


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(
            "Usage: python tools/set_step_status_batch.py RECORDS.json", file=sys.stderr
        )
        return 2

    records_path = Path(argv[0])
    try:
        records = json.loads(records_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: records file {records_path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(records, list):
        print("ERROR: the records file must contain a JSON array", file=sys.stderr)
        return 2

    failed = 0
    for record in records:
        if not isinstance(record, dict):
            print(f"ERROR: record is not an object: {record!r}", file=sys.stderr)
            failed += 1
            continue
        if not _apply(record):
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
