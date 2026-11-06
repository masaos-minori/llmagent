"""tests/tools/test_report.py
Tests for tools/_report.py: the finding record, key profiles, text, JSON, and CSV
renderers, and the `--format` option helper.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pytest

from tools._report import (
    PROFILE_AUTHORITY,
    PROFILE_ISSUE,
    PROFILE_WORKITEM,
    ReportFinding,
    ReportProfile,
    add_format_argument,
    from_authority_finding,
    from_issue,
    render_csv,
    render_json,
    render_text,
)

ISSUES = [
    ReportFinding(message="m3", file="b.md", line_no=3, severity="WARNING"),
    ReportFinding(message="m10", file="a.md", line_no=10, severity="ERROR"),
    ReportFinding(message="m2", file="a.md", line_no=2, severity="ERROR"),
]
WORKITEMS = [
    ReportFinding(message="d2", file="f2.md", code="zeta"),
    ReportFinding(message="d1", file="f1.md", code="alpha"),
    ReportFinding(message="d3", file="f3.md", code="zeta"),
]


def test_issue_profile_sorts_by_file_then_numeric_line() -> None:
    payload = json.loads(render_json(ISSUES, PROFILE_ISSUE))

    assert [(e["file"], e["line_no"]) for e in payload] == [
        ("a.md", 2),
        ("a.md", 10),
        ("b.md", 3),
    ]
    assert list(payload[0]) == ["file", "line_no", "severity", "message"]


def test_authority_profile_sorts_by_code_location_message() -> None:
    findings = [
        ReportFinding(message="x", code="B", location="l"),
        ReportFinding(message="b", code="A", location="z"),
        ReportFinding(message="a", code="A", location="z"),
    ]

    payload = json.loads(render_json(findings, PROFILE_AUTHORITY))

    assert [(e["code"], e["location"], e["message"]) for e in payload] == [
        ("A", "z", "a"),
        ("A", "z", "b"),
        ("B", "l", "x"),
    ]
    assert list(payload[0]) == ["code", "location", "message"]


def test_workitem_profile_keeps_input_order_and_sorts_output_keys() -> None:
    text = render_json(WORKITEMS, PROFILE_WORKITEM)
    payload = json.loads(text)

    assert [e["file"] for e in payload] == ["f2.md", "f1.md", "f3.md"]
    assert list(payload[0]) == ["category", "detail", "file"]


def test_empty_input_in_every_format() -> None:
    assert render_json([], PROFILE_ISSUE) == "[]"
    assert render_csv([], PROFILE_WORKITEM) == "category,file,detail\r\n"
    assert render_text([]) == "No findings.\n"


def test_unicode_is_written_unescaped() -> None:
    finding = ReportFinding(message="ünï 日本", file="f.md", code="c")

    assert "ünï 日本" in render_json([finding], PROFILE_WORKITEM)
    assert "ünï 日本" in render_csv([finding], PROFILE_WORKITEM)


def test_csv_uses_profile_header_and_crlf() -> None:
    assert render_csv(WORKITEMS[:1], PROFILE_WORKITEM) == (
        "category,file,detail\r\nzeta,f2.md,d2\r\n"
    )


def test_text_groups_by_first_seen_code() -> None:
    assert render_text(WORKITEMS) == (
        "[zeta] (2)\n  f2.md: d2\n  f3.md: d3\n[alpha] (1)\n  f1.md: d1\n"
        "\n3 finding(s) total.\n"
    )


def test_custom_profile_without_sort_key_keeps_input_order() -> None:
    profile = ReportProfile(fields=(("m", "message"),))

    payload = json.loads(render_json(ISSUES, profile))

    assert [e["m"] for e in payload] == ["m3", "m10", "m2"]


@pytest.mark.parametrize("render", [render_json, render_csv])
def test_rendering_is_deterministic(
    render: Callable[[Sequence[ReportFinding], ReportProfile], str],
) -> None:
    first = render(WORKITEMS, PROFILE_WORKITEM)
    second = render(WORKITEMS, PROFILE_WORKITEM)

    assert first == second


def test_render_does_not_mutate_the_input_order() -> None:
    before = list(ISSUES)

    render_json(ISSUES, PROFILE_ISSUE)

    assert ISSUES == before


def test_format_option_offers_only_the_given_choices_and_keeps_the_default() -> None:
    parser = argparse.ArgumentParser()
    add_format_argument(parser, choices=("json", "csv"), default=None)

    assert parser.parse_args([]).format is None
    assert parser.parse_args(["--format", "csv"]).format == "csv"
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--format", "xml"])
    assert excinfo.value.code == 2


def test_json_only_option_rejects_csv() -> None:
    parser = argparse.ArgumentParser()
    add_format_argument(parser, choices=("json",), default=None)

    with pytest.raises(SystemExit):
        parser.parse_args(["--format", "csv"])


@dataclass(frozen=True)
class _Issue:
    file: str
    line_no: int
    severity: str
    message: str


@dataclass(frozen=True)
class _Core:
    code: str
    location: str
    message: str


def test_converters_accept_duck_typed_findings() -> None:
    issue = from_issue(_Issue("f.md", 4, "ERROR", "boom"))
    core = from_authority_finding(_Core("C", "loc", "msg"))

    assert (issue.file, issue.line_no, issue.severity, issue.message) == (
        "f.md",
        4,
        "ERROR",
        "boom",
    )
    assert (core.code, core.location, core.message) == ("C", "loc", "msg")
