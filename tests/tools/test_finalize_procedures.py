"""tests/tools/test_finalize_procedures.py
Unit tests for tools/finalize_procedures.py with synthetic Plans and procedures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.finalize_procedures as fp
from tools.stale_detector import StaleResult

PLAN_NAME = "20261127-000000_demo_plan.md"

HEADINGS = (
    "## Goal\n\n## Scope\n\n## Assumptions\n\n## Design decisions\n\n"
    "## Alternatives considered\n\n"
)


def _procedure(body: str, plan: str = f"plans/{PLAN_NAME}") -> str:
    return (
        f"{HEADINGS}## Implementation\n### Target file\n### Procedure\n{body}\n"
        "## Compatibility considerations\n\n## Traceability\n"
        f"- **Source plan**: {plan}\n"
    )


def _plan(rows: int = 2) -> str:
    table = "".join(
        f"| `tools/f{i}.py` | Create | r | REQ-001 | e | t | V |\n" for i in range(rows)
    )
    return (
        "## Implementation Target Files\n\n"
        "| File Path | Change | Reason | Req | Evidence | Tests | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{table}\n## Reference Files\n"
    )


@pytest.mark.parametrize(
    ("body", "name", "expected"),
    [
        (
            "- constants: `HIGH_SHARE = 0.70` and `HIGH_SHARE` is used",
            "HIGH_SHARE",
            fp.CREATED,
        ),
        ("- fields: `dedup_key: str`", "dedup_key", fp.CREATED),
        ("- Create the field `dedup_key` on the record", "dedup_key", fp.CREATED),
        (
            "- Add a function `deploy_impact(path, deploy_text)`",
            "deploy_text",
            fp.CREATED,
        ),
        (
            "- Add a function `deploy_impact(path, deploy_text)`",
            "deploy_impact",
            fp.CREATED,
        ),
        (
            "- The call `deploy_impact(path, deploy_text)` returns text",
            "deploy_text",
            fp.AMBIGUOUS,
        ),
        ("- read `result.is_stale` first", "is_stale", fp.NOT_SYMBOL),
        ('- the literal `"value_name"` is printed', "value_name", fp.NOT_SYMBOL),
        ("- pass `mode=value_name` to it", "value_name", fp.NOT_SYMBOL),
        ("- the helper `mystery_name` appears", "mystery_name", fp.AMBIGUOUS),
        ("- `x.some_name` and a plain `some_name`", "some_name", fp.AMBIGUOUS),
    ],
)
def test_classify_symbol(body: str, name: str, expected: str) -> None:
    assert fp.classify_symbol(_procedure(body), name) == expected


def test_classify_ignores_text_outside_the_implementation_section() -> None:
    text = _procedure("- nothing here").replace(
        "## Goal\n", "## Goal\n- `OUTSIDE_NAME = 1`\n", 1
    )
    assert fp.classify_symbol(text, "OUTSIDE_NAME") == fp.AMBIGUOUS


def test_parse_missing_symbols_separates_other_findings() -> None:
    output = (
        "Sibling resolution: order rule = earlier\n"
        "Stale: 3 mismatch(es) detected.\n"
        "  - symbol_missing: Symbol 'alpha_name' not found in source\n"
        "  - line_ref: lines 1-2 out of range\n"
        "  - new_target_exists: Target file declared new already exists: tools/x.py\n"
    )
    names, others = fp.parse_missing_symbols(output)
    assert names == ["alpha_name"]
    assert others == [
        "- line_ref: lines 1-2 out of range",
        "- new_target_exists: Target file declared new already exists: tools/x.py",
    ]


def test_parse_pattern_matches_the_real_detector_summary() -> None:
    result = StaleResult(is_stale=True)
    result.add_mismatch("symbol_missing", "Symbol 'real_name' not found in source")
    names, _ = fp.parse_missing_symbols(result.summary)
    assert names == ["real_name"]


def test_apply_actions_marks_unbackticks_and_skips_ambiguous() -> None:
    text = "use `made_here` and `plain_value` and `unclear_name`; again `made_here`\n"
    classes = {
        "made_here": fp.CREATED,
        "plain_value": fp.NOT_SYMBOL,
        "unclear_name": fp.AMBIGUOUS,
    }
    once = fp.apply_actions(text, classes)
    assert once == (
        "use `made_here` (new) and plain_value and `unclear_name`; "
        "again `made_here` (new)\n"
    )
    assert fp.apply_actions(once, classes) == once


def test_apply_actions_leaves_a_name_inside_a_longer_span() -> None:
    text = "see `call(plain_value)` and `plain_value`\n"
    assert fp.apply_actions(text, {"plain_value": fp.NOT_SYMBOL}) == (
        "see `call(plain_value)` and plain_value\n"
    )


def test_find_procedures_matches_by_base_name_and_done_flag(tmp_path: Path) -> None:
    impl = tmp_path / "implementations"
    (impl / "done").mkdir(parents=True)
    (impl / "20_b.md").write_text(
        _procedure("x", f"plans/done/{PLAN_NAME}"), encoding="utf-8"
    )
    (impl / "10_a.md").write_text(_procedure("x"), encoding="utf-8")
    (impl / "30_other.md").write_text(
        _procedure("x", "plans/other.md"), encoding="utf-8"
    )
    (impl / "done" / "05_z.md").write_text(_procedure("x"), encoding="utf-8")
    plan = tmp_path / "plans" / PLAN_NAME
    names = [p.name for p in fp.find_procedures(plan, tmp_path, include_done=False)]
    assert names == ["10_a.md", "20_b.md"]
    names_done = [p.name for p in fp.find_procedures(plan, tmp_path, include_done=True)]
    assert names_done == ["05_z.md", "10_a.md", "20_b.md"]


def test_plan_row_count() -> None:
    assert fp.plan_row_count(_plan(3)) == 3


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "plans").mkdir()
    (tmp_path / "implementations").mkdir()
    (tmp_path / "plans" / PLAN_NAME).write_text(_plan(2), encoding="utf-8")
    for seq in ("01", "02"):
        (tmp_path / "implementations" / f"{seq}_doc.md").write_text(
            _procedure("- plain text"), encoding="utf-8"
        )
    return tmp_path


class Recorder:
    """Stub for `run_check` returning scripted exit codes and recording calls.

    With `once=True` a scripted failure is returned only for the first call of its
    key, so a re-run after `--apply` sees the fixed document.
    """

    def __init__(
        self,
        fail: dict[tuple[str, str], tuple[int, str]] | None = None,
        once: bool = False,
    ) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.fail = fail or {}
        self.once = once

    def __call__(self, root: Path, tool: str, *args: str) -> fp.CheckResult:
        self.calls.append((tool, args))
        key = (tool, args[-1])
        code, out = self.fail.get(key, (0, "No findings."))
        if self.once and self.calls.count((tool, args)) > 1:
            code, out = 0, "No findings."
        return fp.CheckResult(tool, args[-1], code, out)


def test_all_pass_prints_exactly_one_summary_line(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    rec = Recorder()
    monkeypatch.setattr(fp, "run_check", rec)
    plan = repo / "plans" / PLAN_NAME
    assert fp.main([str(plan), "--root", str(repo)]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ["OK: 2 procedure(s) checked, 2 Plan row(s), coverage exit 0"]
    assert len(rec.calls) == 5


def test_a_failure_is_one_row_and_the_other_checks_still_run(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    key = ("check_workitem_structure.py", "implementations/01_doc.md")
    rec = Recorder({key: (1, "missing required section: ## Goal\ndetail line")})
    monkeypatch.setattr(fp, "run_check", rec)
    plan = repo / "plans" / PLAN_NAME
    assert fp.main([str(plan), "--root", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "01_doc.md | check_workitem_structure.py | exit 1 | missing required" in out
    assert "OK:" not in out
    assert len(rec.calls) == 5


def test_no_procedures_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "implementations").mkdir()
    plan = tmp_path / PLAN_NAME
    plan.write_text(_plan(1), encoding="utf-8")
    assert fp.main([str(plan), "--root", str(tmp_path)]) == 1
    assert "no procedures found" in capsys.readouterr().out


def _stale_failure(name: str) -> tuple[int, str]:
    return (
        1,
        f"Stale: 1 mismatch(es) detected.\n  - symbol_missing: Symbol '{name}' not found in source",
    )


def test_apply_edits_only_with_the_flag(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = repo / "implementations" / "01_doc.md"
    doc.write_text(
        _procedure("- constants: `MADE_HERE = 1` and `MADE_HERE`"), encoding="utf-8"
    )
    before = doc.read_text(encoding="utf-8")
    key = ("stale_detector.py", "implementations/01_doc.md")
    monkeypatch.setattr(fp, "run_check", Recorder({key: _stale_failure("MADE_HERE")}))
    plan = repo / "plans" / PLAN_NAME
    assert fp.main([str(plan), "--root", str(repo)]) == 1
    assert doc.read_text(encoding="utf-8") == before
    assert "MADE_HERE -> created here; suggested: add (new)" in capsys.readouterr().out
    assert fp.main([str(plan), "--root", str(repo), "--apply", "--dry-run"]) == 1
    assert doc.read_text(encoding="utf-8") == before
    monkeypatch.setattr(
        fp, "run_check", Recorder({key: _stale_failure("MADE_HERE")}, once=True)
    )
    assert fp.main([str(plan), "--root", str(repo), "--apply"]) == 0
    assert "`MADE_HERE` (new)" in doc.read_text(encoding="utf-8")


def test_apply_never_edits_an_ambiguous_name(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = repo / "implementations" / "01_doc.md"
    doc.write_text(_procedure("- the helper `mystery_name` appears"), encoding="utf-8")
    before = doc.read_text(encoding="utf-8")
    key = ("stale_detector.py", "implementations/01_doc.md")
    monkeypatch.setattr(
        fp, "run_check", Recorder({key: _stale_failure("mystery_name")})
    )
    plan = repo / "plans" / PLAN_NAME
    assert fp.main([str(plan), "--root", str(repo), "--apply"]) == 1
    assert doc.read_text(encoding="utf-8") == before


def test_missing_plan_is_a_usage_error(tmp_path: Path) -> None:
    assert fp.main([str(tmp_path / "absent.md")]) == 2


def test_real_structure_checker_runs_on_a_synthetic_procedure(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("## Goal\n", encoding="utf-8")
    result = fp.run_check(
        fp.ROOT_DIR, "check_workitem_structure.py", "--file", str(doc)
    )
    assert result.tool == "check_workitem_structure.py"
    assert isinstance(result.exit_code, int)
