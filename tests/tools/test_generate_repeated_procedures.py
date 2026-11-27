"""tests/tools/test_generate_repeated_procedures.py
Unit tests for tools/generate_repeated_procedures.py with a synthetic Plan.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import tools.generate_repeated_procedures as grp
import tools.generate_workitem as gw

REAL_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_NAME = "20261127-000000_demo_plan.md"
ISSUE = "issues/20261127-000000_demo_issue.md"

TEMPLATE = """## Goal
- Add key x to {path} ({name}), step {seq}, pass {timestamp}.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

## Design decisions

## Alternatives considered

## Implementation
### Target file
`{path}`
### Procedure
### Method
### Details

## Compatibility considerations

## Security considerations

## Rollback considerations

## Validation plan

## Completion criteria

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the key | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
"""


def _plan_text(rows: list[tuple[str, str]]) -> str:
    table = "".join(
        f"| `{path}` | {resp} | r | REQ-00{i % 3 + 1} | e | t | V |\n"
        for i, (path, resp) in enumerate(rows)
    )
    return (
        "## Goal\n- demo\n\n## Implementation Target Files\n\n"
        "| File Path | Change Responsibility | Reason | Req | Evidence | Tests | S |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{table}\n## Reference Files\n\n## Traceability\n"
        f"- **Source issue**: {ISSUE}\n"
    )


def _ten_rows() -> list[tuple[str, str]]:
    return [
        (f"config/a{n:02d}.toml", f"Add key x to config/a{n:02d}.toml")
        for n in range(10)
    ]


class StructureStub:
    """Replaces the structure check: the real checker rejects files outside the repo."""

    def __init__(self) -> None:
        self.checked: list[str] = []
        self.exit_code = 0

    def __call__(self, root: Path, doc: Path) -> int:
        self.checked.append(doc.name)
        print(f"{doc.name}: stub structure check exit {self.exit_code}")
        return self.exit_code


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> StructureStub:
    stub = StructureStub()
    monkeypatch.setattr(grp, "_structure_check", stub)
    return stub


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stub: StructureStub) -> Path:
    (tmp_path / "implementations").mkdir()
    (tmp_path / "plans").mkdir()
    monkeypatch.setattr(gw, "IMPLEMENTATIONS_DIR", tmp_path / "implementations")
    monkeypatch.setattr(gw, "REPO_ROOT", tmp_path)
    return tmp_path


def _write(
    env: Path, rows: list[tuple[str, str]], template: str = TEMPLATE
) -> tuple[Path, Path]:
    plan = env / "plans" / PLAN_NAME
    plan.write_text(_plan_text(rows), encoding="utf-8")
    tpl = env / "body.md"
    tpl.write_text(template, encoding="utf-8")
    return plan, tpl


def _run(env: Path, plan: Path, tpl: Path, rows: list[str], *extra: str) -> int:
    return grp.main(
        [
            str(plan),
            "--rows",
            *rows,
            "--body-template",
            str(tpl),
            "--root",
            str(env),
            *extra,
        ]
    )


def _outputs(env: Path) -> list[str]:
    return sorted(p.name for p in (env / "implementations").glob("*.md"))


def test_ten_identical_rows_produce_ten_valid_documents(
    env: Path, stub: StructureStub, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = _ten_rows()
    plan, tpl = _write(env, rows)
    assert _run(env, plan, tpl, [p for p, _ in rows]) == 0
    names = _outputs(env)
    assert len(names) == 10
    assert sorted(stub.checked) == names
    assert names[0].endswith("_01_config_a00.toml.md")
    assert names[9].endswith("_10_config_a09.toml.md")
    assert "created 10 document(s)" in capsys.readouterr().out


def test_filenames_equal_those_of_generate_workitem_all_rows(env: Path) -> None:
    rows = _ten_rows()
    plan, tpl = _write(env, rows)
    assert _run(env, plan, tpl, [p for p, _ in rows]) == 0
    ours = _outputs(env)
    for doc in (env / "implementations").glob("*.md"):
        doc.unlink()
    args = argparse.Namespace(source_plan=str(plan), dry_run=False)
    assert gw.generate_all_rows(args, "20990101-000000") == 0
    assert _outputs(env) == ours


def test_documents_carry_the_traceability_block(env: Path) -> None:
    rows = _ten_rows()[:3]
    plan, tpl = _write(env, rows)
    assert _run(env, plan, tpl, [p for p, _ in rows]) == 0
    first = sorted((env / "implementations").glob("*.md"))[0].read_text(
        encoding="utf-8"
    )
    assert "- **Requirement ID**: REQ-001" in first
    assert f"- **Source issue**: {ISSUE}" in first
    assert f"- **Source plan**: plans/{PLAN_NAME}" in first
    assert "- **Related target files**: `config/a00.toml`" in first
    assert "Add key x to config/a00.toml (a00.toml), step 01" in first


def _assert_refused(env: Path, plan: Path, before: bytes) -> None:
    assert _outputs(env) == []
    assert plan.read_bytes() == before


def test_a_different_change_responsibility_is_refused(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = _ten_rows()[:3]
    rows[1] = (rows[1][0], "Rewrite the whole loader")
    plan, tpl = _write(env, rows)
    before = plan.read_bytes()
    assert _run(env, plan, tpl, [p for p, _ in rows]) == 1
    assert "Change Responsibility of config/a01.toml differs" in capsys.readouterr().err
    _assert_refused(env, plan, before)


def test_unknown_duplicate_and_template_problems_are_refused(env: Path) -> None:
    rows = _ten_rows()[:2]
    plan, tpl = _write(env, rows)
    before = plan.read_bytes()
    assert _run(env, plan, tpl, ["config/a00.toml", "config/nope.toml"]) == 1
    assert _run(env, plan, tpl, ["config/a00.toml", "config/a00.toml"]) == 1
    tpl.write_text(TEMPLATE + "\n## Traceability\n", encoding="utf-8")
    assert _run(env, plan, tpl, ["config/a00.toml"]) == 1
    tpl.write_text(TEMPLATE + "\n{other}\n", encoding="utf-8")
    assert _run(env, plan, tpl, ["config/a00.toml"]) == 1
    _assert_refused(env, plan, before)


def test_existing_outputs_are_refused_including_done(env: Path) -> None:
    rows = _ten_rows()[:2]
    plan, tpl = _write(env, rows)
    assert _run(env, plan, tpl, ["config/a00.toml"]) == 0
    existing = _outputs(env)
    assert _run(env, plan, tpl, ["config/a00.toml", "config/a01.toml"]) == 1
    assert _outputs(env) == existing
    done = env / "implementations" / "done"
    done.mkdir()
    (done / existing[0]).write_text((env / "implementations" / existing[0]).read_text())
    (env / "implementations" / existing[0]).unlink()
    assert _run(env, plan, tpl, ["config/a00.toml"]) == 1
    assert _outputs(env) == []


def test_normalize_change_substitutes_path_and_base_name() -> None:
    a = grp.normalize_change("Add  key to config/a.toml (a.toml)", "config/a.toml")
    b = grp.normalize_change("Add key to config/b.toml (b.toml)", "config/b.toml")
    assert a == b == "Add key to {path} ({name})"
    c = grp.normalize_change("Add key to config/c.toml and more", "config/c.toml")
    assert c != a


def test_failing_structure_check_gives_exit_one(
    env: Path, stub: StructureStub, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = _ten_rows()[:2]
    plan, tpl = _write(env, rows)
    stub.exit_code = 1
    assert _run(env, plan, tpl, [p for p, _ in rows]) == 1
    out = capsys.readouterr().out
    assert "stub structure check exit 1" in out
    assert len(stub.checked) == 2


def test_dry_run_writes_nothing(env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rows = _ten_rows()[:2]
    plan, tpl = _write(env, rows)
    before = plan.read_bytes()
    assert (
        _run(env, plan, tpl, ["config/a00.toml", "config/a01.toml"], "--dry-run") == 0
    )
    assert "would create" in capsys.readouterr().out
    _assert_refused(env, plan, before)


def test_missing_inputs_are_usage_errors(env: Path) -> None:
    plan, tpl = _write(env, _ten_rows()[:1])
    assert (
        grp.main([str(env / "absent.md"), "--rows", "x", "--body-template", str(tpl)])
        == 2
    )
    assert (
        grp.main([str(plan), "--rows", "x", "--body-template", str(env / "absent.md")])
        == 2
    )
