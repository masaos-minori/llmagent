"""tests/tools/test_generate_issue_batch.py
Unit tests for tools/generate_issue_batch.py.

Covers AC-1 to AC-6 of plans/20261117-125502_wftool005_workitem-batch-generate.md:
parsing and validation (exit 2, nothing written), strictly increasing allocation,
collision refusal in `issues/` and `issues/done/`, `{{issue:<id>}}` resolution,
`Generated at` rewriting, atomic writes and `--dry-run`, the mid-run write-failure
report, and the single post-write checker call with its exit-code mapping.

Like tests/tools/test_generate_workitem.py, every test redirects
`tools.generate_workitem.ISSUES_DIR` into `tmp_path` via `monkeypatch`. The
post-write checker call is stubbed because `tools/check_workitem_structure.py`
resolves every checked path against the repo root, so `tmp_path` files would
only produce `unknown-kind` findings (plan AC-6: "tests with a stubbed checker
call"). The real checker is exercised by the procedure's smoke run only.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest

from tools import generate_issue_batch as gib
from tools import generate_workitem as gw

FIXED_NOW = datetime(2026, 1, 1, 0, 0, 0)
TS_0 = "20260101-000000"
TS_1 = "20260101-000001"
TS_2 = "20260101-000002"

_BODY = (
    "Generated at: {{Generated at}}\n\n"
    "**Category**: Feature\n"
    "**Priority**: P1\n\n"
    "## Why now\n\nBatch generation avoids repeated manual calls.\n\n"
    "## Acceptance criteria\n\n- AC text\n"
)


def _spec(blocks: list[tuple[str, str, str]]) -> str:
    parts = [
        f"<!-- issue: {issue_id} {slug} -->\n{body}" for issue_id, slug, body in blocks
    ]
    return "\n\n".join(parts) + "\n"


def _write_spec(tmp_path: Path, text: str) -> Path:
    spec = tmp_path / "spec.md"
    spec.write_text(text, encoding="utf-8")
    return spec


@pytest.fixture
def issues_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "issues"
    directory.mkdir()
    monkeypatch.setattr(gw, "ISSUES_DIR", directory)
    return directory


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gib, "_now", lambda: FIXED_NOW)


@pytest.fixture
def checker_ok(monkeypatch: pytest.MonkeyPatch) -> list[list[Path]]:
    calls: list[list[Path]] = []

    def fake(paths: list[Path]) -> tuple[int, str]:
        calls.append(list(paths))
        return 0, "No findings."

    monkeypatch.setattr(gib, "_run_checker", fake)
    return calls


# AC-1, AC-2: three valid blocks parse in order; strictly increasing timestamps.
def test_three_valid_blocks_create_files_in_order(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(
        tmp_path,
        _spec(
            [
                ("alpha", "first", _BODY),
                ("beta", "second-doc", _BODY),
                ("c1", "third", _BODY),
            ]
        ),
    )
    assert gib.main([str(spec)]) == 0
    expected = [
        issues_dir / f"{ts}_{issue_id}_{slug}.md"
        for ts, (issue_id, slug) in zip(
            (TS_0, TS_1, TS_2),
            (("alpha", "first"), ("beta", "second-doc"), ("c1", "third")),
        )
    ]
    for path in expected:
        assert path.is_file()
    stamps = [re.match(r"^(\d{8}-\d{6})_", path.name) for path in expected]
    parsed = [datetime.strptime(m.group(1), "%Y%m%d-%H%M%S") for m in stamps if m]
    assert parsed == sorted(parsed)
    assert (parsed[1] - parsed[0]).total_seconds() == 1
    assert (parsed[2] - parsed[1]).total_seconds() == 1
    out = capsys.readouterr().out
    for path in expected:
        assert str(path) in out


# AC-6: the checker runs once with all created paths.
def test_checker_runs_once_with_all_created_paths(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("beta", "second", _BODY)])
    )
    assert gib.main([str(spec)]) == 0
    assert len(checker_ok) == 1
    assert checker_ok[0] == [
        issues_dir / f"{TS_0}_alpha_first.md",
        issues_dir / f"{TS_1}_beta_second.md",
    ]


# AC-1: bad ids exit 2 and create nothing.
@pytest.mark.parametrize(
    ("issue_id", "slug", "why"),
    [
        ("00123", "slug", "digits-only id"),
        ("Abc", "slug", "uppercase id"),
        ("ab_c", "slug", "underscore in id"),
    ],
)
def test_bad_ids_exit_2_writing_nothing(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
    issue_id: str,
    slug: str,
    why: str,
) -> None:
    spec = _write_spec(tmp_path, _spec([(issue_id, slug, _BODY)]))
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert checker_ok == []
    err = capsys.readouterr().err
    assert "error:" in err and issue_id in err
    assert why  # parametrization label


# AC-1: bad or over-long slugs exit 2 and create nothing.
@pytest.mark.parametrize(
    ("issue_id", "slug", "why"),
    [
        ("ok", "Slug", "uppercase slug"),
        ("ok", "one-two-three-four-five", "slug over four words"),
        ("ok", "-lead", "leading separator"),
        ("ok", "trail-", "trailing separator"),
    ],
)
def test_bad_slugs_exit_2_writing_nothing(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
    issue_id: str,
    slug: str,
    why: str,
) -> None:
    spec = _write_spec(tmp_path, _spec([(issue_id, slug, _BODY)]))
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert checker_ok == []
    assert slug in capsys.readouterr().err
    assert why  # parametrization label


# AC-1: a malformed delimiter line (not `<!-- issue: {id} {slug} -->`) exits 2.
def test_malformed_delimiter_exits_2(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(tmp_path, "<!-- issue: alpha -->\n" + _BODY + "\n")
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert "malformed issue delimiter" in capsys.readouterr().err


# AC-1: text before the first delimiter exits 2.
def test_text_before_first_block_exits_2(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
) -> None:
    spec = _write_spec(tmp_path, "intro text\n\n" + _spec([("alpha", "first", _BODY)]))
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []


# AC-1: duplicate ids exit 2.
def test_duplicate_ids_exit_2(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("alpha", "second", _BODY)])
    )
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert "duplicate" in capsys.readouterr().err


# AC-1: an empty block exits 2.
def test_empty_block_exit_2(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(
        tmp_path,
        "<!-- issue: alpha first -->\n\n<!-- issue: beta second -->\n" + _BODY + "\n",
    )
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert "empty" in capsys.readouterr().err


# AC-2: an existing path in issues/ refuses the whole run before any write.
def test_collision_in_issues_dir_refuses_before_write(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    clash = issues_dir / f"{TS_1}_beta_second.md"
    clash.write_text("pre-existing\n", encoding="utf-8")
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("beta", "second", _BODY)])
    )
    assert gib.main([str(spec)]) == 2
    assert [p.name for p in issues_dir.iterdir()] == [clash.name]
    assert "collid" in capsys.readouterr().err
    assert checker_ok == []


# AC-2: a done/ counterpart refuses the whole run before any write.
def test_collision_with_done_counterpart_refuses_before_write(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    done = issues_dir / "done"
    done.mkdir()
    clash = done / f"{TS_0}_alpha_first.md"
    clash.write_text("archived\n", encoding="utf-8")
    spec = _write_spec(tmp_path, _spec([("alpha", "first", _BODY)]))
    assert gib.main([str(spec)]) == 2
    assert sorted(p.name for p in issues_dir.iterdir()) == ["done"]


# AC-3: {{issue:<id>}} becomes issues/<allocated name> for ids in the spec.
def test_reference_tokens_resolve(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    spec = _write_spec(
        tmp_path,
        _spec(
            [
                ("alpha", "first", _BODY + "\nSee {{issue:beta}}.\n"),
                ("beta", "second", _BODY + "\nBack to {{issue:alpha}}.\n"),
            ]
        ),
    )
    assert gib.main([str(spec)]) == 0
    alpha = (issues_dir / f"{TS_0}_alpha_first.md").read_text(encoding="utf-8")
    beta = (issues_dir / f"{TS_1}_beta_second.md").read_text(encoding="utf-8")
    assert f"issues/{TS_1}_beta_second.md" in alpha
    assert f"issues/{TS_0}_alpha_first.md" in beta
    assert "{{issue:" not in alpha and "{{issue:" not in beta


# AC-3: an unknown referenced id exits 2 and creates nothing.
def test_unknown_reference_exits_2(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY + "\nSee {{issue:zeta}}.\n")])
    )
    assert gib.main([str(spec)]) == 2
    assert list(issues_dir.iterdir()) == []
    assert "zeta" in capsys.readouterr().err
    assert checker_ok == []


# AC-4: Generated at equals the filename timestamp; the rest equals the spec block.
def test_generated_at_replaced_and_rest_preserved(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("beta", "second", _BODY)])
    )
    assert gib.main([str(spec)]) == 0
    for ts, name in ((TS_0, "alpha_first"), (TS_1, "beta_second")):
        text = (issues_dir / f"{ts}_{name}.md").read_text(encoding="utf-8")
        assert (
            text
            == _BODY.strip().replace(
                "Generated at: {{Generated at}}", f"Generated at: {ts}"
            )
            + "\n"
        )


# AC-4: a block without a Generated at field gets it added with the allocated timestamp.
def test_generated_at_line_absent_is_added(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    body = _BODY.replace("Generated at: {{Generated at}}\n\n", "").strip()
    spec = _write_spec(tmp_path, _spec([("alpha", "first", body)]))
    assert gib.main([str(spec)]) == 0
    text = (issues_dir / f"{TS_0}_alpha_first.md").read_text(encoding="utf-8")
    assert text == f"Generated at: {TS_0}\n\n" + body + "\n"


# AC-5: --dry-run leaves the directory unchanged and prints every planned path.
def test_dry_run_writes_nothing(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("beta", "second", _BODY)])
    )
    assert gib.main([str(spec), "--dry-run"]) == 0
    assert list(issues_dir.iterdir()) == []
    out = capsys.readouterr().out
    assert str(issues_dir / f"{TS_0}_alpha_first.md") in out
    assert str(issues_dir / f"{TS_1}_beta_second.md") in out
    assert checker_ok == []


# AC-5: a mid-run write failure reports the created files and deletes none.
def test_write_failure_reports_created_and_deletes_none(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original = gib.atomic_write_text
    attempts: list[Path] = []

    def fail_second(path: Path, text: str, **kwargs: object) -> None:
        attempts.append(path)
        if len(attempts) == 2:
            raise OSError("disk full")
        original(path, text, **kwargs)

    monkeypatch.setattr(gib, "atomic_write_text", fail_second)
    spec = _write_spec(
        tmp_path, _spec([("alpha", "first", _BODY), ("beta", "second", _BODY)])
    )
    assert gib.main([str(spec)]) == 2
    assert (issues_dir / f"{TS_0}_alpha_first.md").is_file()
    assert not (issues_dir / f"{TS_1}_beta_second.md").exists()
    err = capsys.readouterr().err
    assert "disk full" in err
    assert str(issues_dir / f"{TS_0}_alpha_first.md") in err
    assert checker_ok == []


# AC-5 (REQ-005): atomic writes leave no temporary files in the issues directory.
def test_atomic_write_leaves_no_temp_files(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    checker_ok: list[list[Path]],
) -> None:
    spec = _write_spec(tmp_path, _spec([("alpha", "first", _BODY)]))
    assert gib.main([str(spec)]) == 0
    names = [p.name for p in issues_dir.iterdir()]
    assert names == [f"{TS_0}_alpha_first.md"]


# AC-6: checker findings give exit 1 and name the file; created files remain.
def test_checker_findings_give_exit_1(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake(paths: list[Path]) -> tuple[int, str]:
        return (
            1,
            f"{paths[0]}: template-leftover at line 1: leftover template content remains",
        )

    monkeypatch.setattr(gib, "_run_checker", fake)
    spec = _write_spec(tmp_path, _spec([("alpha", "first", _BODY)]))
    assert gib.main([str(spec)]) == 1
    assert (issues_dir / f"{TS_0}_alpha_first.md").is_file()
    assert "template-leftover" in capsys.readouterr().out


# AC-6: a checker that errors (exit other than 0/1) gives exit 2.
def test_checker_error_gives_exit_2(
    tmp_path: Path,
    issues_dir: Path,
    fixed_clock: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake(paths: list[Path]) -> tuple[int, str]:
        return 2, "checker crashed"

    monkeypatch.setattr(gib, "_run_checker", fake)
    spec = _write_spec(tmp_path, _spec([("alpha", "first", _BODY)]))
    assert gib.main([str(spec)]) == 2
    assert (issues_dir / f"{TS_0}_alpha_first.md").is_file()
    assert "checker crashed" in capsys.readouterr().out


def test_missing_spec_file_exits_2(
    tmp_path: Path,
    issues_dir: Path,
    checker_ok: list[list[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert gib.main([str(tmp_path / "nope.md")]) == 2
    assert "cannot read spec" in capsys.readouterr().err
    assert checker_ok == []
