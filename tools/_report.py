"""tools/_report.py

Shared, non-CLI helper (same role as tools/_docs_consistency_lib.py): one finding
record that carries both the `file`/`line_no`/`severity` and the `code`/`location`
styles, key profiles that reproduce each checker's current output keys and order,
deterministic text, JSON, and CSV renderers, and the `--format` option helper.
Standard library plus orjson only; renderers return strings and never print.
"""

from __future__ import annotations

import argparse
import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import orjson


@dataclass(frozen=True)
class ReportFinding:
    message: str
    file: str = ""
    line_no: int = 0
    severity: str = ""
    code: str = ""
    location: str = ""


@dataclass(frozen=True)
class ReportProfile:
    """Output keys as `(output_key, record_field)` pairs, plus ordering rules."""

    fields: tuple[tuple[str, str], ...]
    sort_key: tuple[str, ...] | None = None
    sort_output_keys: bool = False


PROFILE_ISSUE = ReportProfile(
    fields=(
        ("file", "file"),
        ("line_no", "line_no"),
        ("severity", "severity"),
        ("message", "message"),
    ),
    sort_key=("file", "line_no"),
)
PROFILE_AUTHORITY = ReportProfile(
    fields=(("code", "code"), ("location", "location"), ("message", "message")),
    sort_key=("code", "location", "message"),
)
PROFILE_WORKITEM = ReportProfile(
    fields=(("category", "code"), ("file", "file"), ("detail", "message")),
    sort_output_keys=True,
)


class _IssueLike(Protocol):
    @property
    def file(self) -> str: ...
    @property
    def line_no(self) -> int: ...
    @property
    def severity(self) -> str: ...
    @property
    def message(self) -> str: ...


class _AuthorityLike(Protocol):
    @property
    def code(self) -> str: ...
    @property
    def location(self) -> str: ...
    @property
    def message(self) -> str: ...


def from_issue(issue: _IssueLike) -> ReportFinding:
    return ReportFinding(
        message=issue.message,
        file=issue.file,
        line_no=issue.line_no,
        severity=issue.severity,
    )


def from_authority_finding(finding: _AuthorityLike) -> ReportFinding:
    return ReportFinding(
        message=finding.message, code=finding.code, location=finding.location
    )


def _ordered(
    findings: Sequence[ReportFinding], profile: ReportProfile
) -> list[ReportFinding]:
    if profile.sort_key is None:
        return list(findings)
    key = profile.sort_key
    return sorted(findings, key=lambda f: tuple(getattr(f, name) for name in key))


def _rows(
    findings: Sequence[ReportFinding], profile: ReportProfile
) -> list[dict[str, object]]:
    return [
        {out: getattr(f, field) for out, field in profile.fields}
        for f in _ordered(findings, profile)
    ]


def render_json(findings: Sequence[ReportFinding], profile: ReportProfile) -> str:
    option = orjson.OPT_INDENT_2
    if profile.sort_output_keys:
        option |= orjson.OPT_SORT_KEYS
    return orjson.dumps(_rows(findings, profile), option=option).decode()


def render_csv(findings: Sequence[ReportFinding], profile: ReportProfile) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[out for out, _ in profile.fields])
    writer.writeheader()
    writer.writerows(_rows(findings, profile))
    return buffer.getvalue()


def render_text(findings: Sequence[ReportFinding]) -> str:
    """Findings grouped by `code` in first-seen order, one indented line each."""
    if not findings:
        return "No findings.\n"
    lines: list[str] = []
    for code in dict.fromkeys(f.code for f in findings):
        group = [f for f in findings if f.code == code]
        lines.append(f"[{code}] ({len(group)})")
        for finding in group:
            lines.append(f"  {finding.file}: {finding.message}")
    lines.append(f"\n{len(findings)} finding(s) total.")
    return "\n".join(lines) + "\n"


def add_format_argument(
    parser: argparse.ArgumentParser, choices: Sequence[str], default: str | None
) -> None:
    parser.add_argument(
        "--format",
        choices=list(choices),
        default=default,
        help="Machine-readable output format (default: human-readable text)",
    )
