"""tests/tools/test_compare_test_baseline.py

Tests for tools/compare_test_baseline.py: JUnit XML reading (failure, fixture error,
collection error, teardown error), baseline validation, classification and exit codes,
the explicit update and add modes, and the unusable-input cases. The XML is synthetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import compare_test_baseline as ctb

_REASON = "issues/20260101-000000_example_known.md"


def _xml(tmp_path: Path, cases: list[str], name: str = "run.xml") -> Path:
    path = tmp_path / name
    path.write_text(
        '<?xml version="1.0"?><testsuites><testsuite name="pytest">'
        + "".join(cases)
        + "</testsuite></testsuites>",
        encoding="utf-8",
    )
    return path


def _ok(classname: str, name: str) -> str:
    return f'<testcase classname="{classname}" name="{name}"/>'


def _fail(classname: str, name: str) -> str:
    return f'<testcase classname="{classname}" name="{name}"><failure message="x"/></testcase>'


def _error(classname: str, name: str) -> str:
    return f'<testcase classname="{classname}" name="{name}"><error message="x"/></testcase>'


def _skip(classname: str, name: str) -> str:
    return f'<testcase classname="{classname}" name="{name}"><skipped message="x"/></testcase>'


def _baseline(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "baseline.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run(tmp_path: Path, xml: Path, baseline: Path, *extra: str) -> int:
    return ctb.main([str(xml), "--baseline", str(baseline), *extra])


def test_read_junit_collects_failure_fixture_error_and_collection_error(
    tmp_path: Path,
) -> None:
    xml = _xml(
        tmp_path,
        [
            _ok("pkg.test_a", "test_ok"),
            _fail("pkg.test_a", "test_bad[1.5]"),
            _error("pkg.test_a", "test_fx"),
            _error("", "pkg.sub.test_nested"),
        ],
    )

    result = ctb.read_junit(xml)

    assert result.failing == frozenset(
        {"pkg.test_a::test_bad[1.5]", "pkg.test_a::test_fx", "pkg.sub.test_nested"}
    )
    assert result.passed == frozenset({"pkg.test_a::test_ok"})
    assert result.total == 4


def test_read_junit_counts_a_teardown_error_of_a_passing_test_as_failing(
    tmp_path: Path,
) -> None:
    case = '<testcase classname="pkg.t" name="test_x"><error message="teardown"/></testcase>'
    xml = _xml(tmp_path, [case, _ok("pkg.t", "test_x")])

    result = ctb.read_junit(xml)

    assert result.failing == frozenset({"pkg.t::test_x"})
    assert result.passed == frozenset()


def test_read_junit_skipped_test_is_neither_failing_nor_passed(tmp_path: Path) -> None:
    result = ctb.read_junit(_xml(tmp_path, [_skip("pkg.t", "test_s")]))

    assert result.skipped == frozenset({"pkg.t::test_s"})
    assert result.failing == frozenset()
    assert result.passed == frozenset()


@pytest.mark.parametrize(
    "content", ["", "<not xml", '<testsuites><testsuite name="p"/></testsuites>']
)
def test_read_junit_rejects_unusable_files(tmp_path: Path, content: str) -> None:
    path = tmp_path / "bad.xml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ctb.InputError):
        ctb.read_junit(path)


def test_read_junit_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ctb.InputError):
        ctb.read_junit(tmp_path / "absent.xml")


def test_load_baseline_skips_comments_and_blank_lines(tmp_path: Path) -> None:
    path = _baseline(tmp_path, ["# header", "", f"pkg.t::test_a\t{_REASON}"])

    assert ctb.load_baseline(path) == {"pkg.t::test_a": _REASON}


@pytest.mark.parametrize(
    ("line", "line_no"),
    [
        ("pkg.t::test_a", 2),
        (f"\t{_REASON}", 2),
        ("pkg.t::test_a\tno issue path here", 2),
        ("pkg.t::test_a\t", 2),
    ],
)
def test_load_baseline_rejects_an_entry_without_a_valid_reason(
    tmp_path: Path, line: str, line_no: int
) -> None:
    path = _baseline(tmp_path, ["# header", line])

    with pytest.raises(ctb.BaselineError) as exc:
        ctb.load_baseline(path)

    assert exc.value.line_no == line_no


def test_load_baseline_rejects_a_duplicate_entry(tmp_path: Path) -> None:
    path = _baseline(
        tmp_path, [f"pkg.t::test_a\t{_REASON}", f"pkg.t::test_a\t{_REASON}"]
    )

    with pytest.raises(ctb.BaselineError):
        ctb.load_baseline(path)


def test_load_baseline_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ctb.InputError):
        ctb.load_baseline(tmp_path / "absent.txt")


def test_the_shipped_baseline_parses() -> None:
    # The shipped file is no longer empty: entries are added with `--add`. What the test
    # guards is that every shipped line parses and each reason names an issue path.
    entries = ctb.load_baseline(ctb.DEFAULT_BASELINE)
    assert entries
    for test_id, reason in entries.items():
        assert test_id.strip()
        assert ctb.ISSUE_PATH_RE.search(reason)


def test_known_failures_only_exit_zero_and_report_the_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_ok"), _fail("p.t", "test_known")])
    baseline = _baseline(tmp_path, [f"p.t::test_known\t{_REASON}"])

    code = _run(tmp_path, xml, baseline)

    assert code == 0
    assert "known failures: 1" in capsys.readouterr().out


def test_a_new_failure_exits_one_and_is_named(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_fail("p.t", "test_known"), _fail("p.t", "test_new")])
    baseline = _baseline(tmp_path, [f"p.t::test_known\t{_REASON}"])

    code = _run(tmp_path, xml, baseline)

    assert code == 1
    out = capsys.readouterr().out
    assert "p.t::test_new" in out
    assert "known failures: 1" in out


def test_a_new_collection_error_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_ok"), _error("", "p.sub.test_broken")])

    code = _run(tmp_path, xml, _baseline(tmp_path, ["# none"]))

    assert code == 1
    assert "p.sub.test_broken" in capsys.readouterr().out


def test_a_fixed_entry_is_reported_for_removal_and_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_was_known")])
    baseline = _baseline(tmp_path, [f"p.t::test_was_known\t{_REASON}"])

    code = _run(tmp_path, xml, baseline)

    assert code == 0
    out = capsys.readouterr().out
    assert "fixed" in out
    assert "p.t::test_was_known" in out


def test_an_entry_that_did_not_run_is_not_counted_as_fixed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_other"), _skip("p.t", "test_skipped")])
    baseline = _baseline(
        tmp_path, [f"p.t::test_absent\t{_REASON}", f"p.t::test_skipped\t{_REASON}"]
    )

    code = _run(tmp_path, xml, baseline)

    assert code == 0
    out = capsys.readouterr().out
    assert "not run" in out
    assert "p.t::test_absent" in out
    assert "p.t::test_skipped" in out
    assert "fixed" not in out


def test_an_invalid_baseline_exits_two(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_ok")])

    assert _run(tmp_path, xml, _baseline(tmp_path, ["p.t::test_a\tno path"])) == 2


def test_an_unusable_xml_exits_two(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xml"
    bad.write_text("<not xml", encoding="utf-8")

    assert _run(tmp_path, bad, _baseline(tmp_path, ["# none"])) == 2


def test_a_plain_run_leaves_the_baseline_byte_identical(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_was_known")])
    baseline = _baseline(tmp_path, [f"p.t::test_was_known\t{_REASON}"])
    before = baseline.read_bytes()

    _run(tmp_path, xml, baseline)

    assert baseline.read_bytes() == before


def test_update_removes_only_fixed_entries_and_keeps_comments(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_fixed"), _fail("p.t", "test_still")])
    baseline = _baseline(
        tmp_path,
        [
            "# keep me",
            f"p.t::test_fixed\t{_REASON}",
            f"p.t::test_still\t{_REASON}",
            f"p.t::test_absent\t{_REASON}",
        ],
    )

    code = _run(tmp_path, xml, baseline, "--update")

    assert code == 0
    assert baseline.read_text(encoding="utf-8").splitlines() == [
        "# keep me",
        f"p.t::test_still\t{_REASON}",
        f"p.t::test_absent\t{_REASON}",
    ]


def test_add_appends_an_entry_for_a_test_that_failed(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_fail("p.t", "test_new")])
    baseline = _baseline(tmp_path, ["# header"])

    code = _run(
        tmp_path,
        xml,
        baseline,
        "--add",
        "p.t::test_new",
        "--reason",
        f"tracked in {_REASON}",
    )

    assert code == 1
    assert baseline.read_text(encoding="utf-8").splitlines() == [
        "# header",
        f"p.t::test_new\ttracked in {_REASON}",
    ]


@pytest.mark.parametrize(
    ("test_id", "reason"),
    [
        ("p.t::test_passed", _REASON),
        ("p.t::test_new", "no issue path"),
        ("p.t::test_known", _REASON),
    ],
)
def test_add_refuses_an_unfailed_id_a_reason_without_issue_and_a_duplicate(
    tmp_path: Path, test_id: str, reason: str
) -> None:
    xml = _xml(
        tmp_path,
        [
            _ok("p.t", "test_passed"),
            _fail("p.t", "test_new"),
            _fail("p.t", "test_known"),
        ],
    )
    baseline = _baseline(tmp_path, [f"p.t::test_known\t{_REASON}"])
    before = baseline.read_bytes()

    code = _run(tmp_path, xml, baseline, "--add", test_id, "--reason", reason)

    assert code == 2
    assert baseline.read_bytes() == before


def test_add_requires_a_reason(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_fail("p.t", "test_new")])

    assert (
        _run(tmp_path, xml, _baseline(tmp_path, ["# header"]), "--add", "p.t::test_new")
        == 2
    )


def test_update_and_add_cannot_be_combined(tmp_path: Path) -> None:
    xml = _xml(tmp_path, [_fail("p.t", "test_new")])

    with pytest.raises(SystemExit) as exc:
        _run(
            tmp_path,
            xml,
            _baseline(tmp_path, ["# header"]),
            "--update",
            "--add",
            "p.t::test_new",
        )

    assert exc.value.code == 2


def test_dry_run_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    xml = _xml(tmp_path, [_ok("p.t", "test_fixed")])
    baseline = _baseline(tmp_path, [f"p.t::test_fixed\t{_REASON}"])
    before = baseline.read_bytes()

    code = _run(tmp_path, xml, baseline, "--update", "--dry-run")

    assert code == 0
    assert baseline.read_bytes() == before
    assert "test_fixed" in capsys.readouterr().out
