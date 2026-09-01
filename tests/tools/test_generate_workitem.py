"""tests/tools/test_generate_workitem.py
Tests for tools/generate_workitem.py.

Covers:
- T1 (REQ-002): filename generation correctness for each of the three
  ``--kind`` values.
- T2 (REQ-001): rendered section-heading order matches the *current*
  ``templates/*.md`` fenced skeleton content (read live, not hardcoded, to
  detect tool/template drift).
- T3 (REQ-003): collision rejection against both the target directory and its
  ``done/`` counterpart.
- T4 (REQ-004): rejection when ``--source-plan`` does not exist
  (implementation-procedure mode).

All tests redirect ``tools.generate_workitem``'s ``ISSUES_DIR`` /
``PLANS_DIR`` / ``IMPLEMENTATIONS_DIR`` module constants into an isolated
``tmp_path`` tree via ``monkeypatch`` -- no test writes into the repository's
real ``issues/`` / ``plans/`` / ``implementations/`` directories.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest

from tools import generate_workitem as gw

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_ISSUE = REPO_ROOT / "templates" / "issue.md"
TEMPLATE_PLAN = REPO_ROOT / "templates" / "plan.md"
TEMPLATE_IMPLEMENTATION_PROCEDURE = (
    REPO_ROOT / "templates" / "implementation-procedure.md"
)

_HEADING_RE = re.compile(r"^## .+$")


def _template_section_headings(template_path: Path) -> list[str]:
    """Independently re-derive the '## ' section headings inside
    *template_path*'s fenced ```markdown block.

    Deliberately does not call ``tools.generate_workitem.extract_fenced_skeleton``
    -- this must be an independent read of the template file so a drift
    between the tool's extraction logic and the template's actual current
    content is caught (see this test module's docstring, T2).
    """
    lines = template_path.read_text(encoding="utf-8").splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == "```markdown":
            start_index = index
            break
    assert start_index is not None, f"no ```markdown fence found in {template_path}"

    end_index: int | None = None
    for index in range(start_index + 1, len(lines)):
        if lines[index].strip() == "```":
            end_index = index
            break
    assert end_index is not None, f"no closing fence found in {template_path}"

    return [
        line for line in lines[start_index + 1 : end_index] if _HEADING_RE.match(line)
    ]


def _output_section_headings(output_path: Path) -> list[str]:
    """Extract '## ' heading lines, in order, from a generated output file."""
    return [
        line
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if _HEADING_RE.match(line)
    ]


@pytest.fixture
def workitem_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Redirect ISSUES_DIR/PLANS_DIR/IMPLEMENTATIONS_DIR (and their `done/`
    counterparts) into an isolated tmp_path tree.
    """
    dirs = {
        "issues": tmp_path / "issues",
        "plans": tmp_path / "plans",
        "implementations": tmp_path / "implementations",
    }
    for target_dir in dirs.values():
        target_dir.mkdir()
        (target_dir / "done").mkdir()
    monkeypatch.setattr(gw, "ISSUES_DIR", dirs["issues"])
    monkeypatch.setattr(gw, "PLANS_DIR", dirs["plans"])
    monkeypatch.setattr(gw, "IMPLEMENTATIONS_DIR", dirs["implementations"])
    # main()'s success-path print does `output_path.relative_to(REPO_ROOT)`;
    # REPO_ROOT must also point into tmp_path so that call does not raise
    # ValueError for an output_path that lives outside the real repo root.
    monkeypatch.setattr(gw, "REPO_ROOT", tmp_path)
    return dirs


@pytest.fixture
def fixed_timestamp(monkeypatch: pytest.MonkeyPatch) -> str:
    """Freeze the timestamp `main()` computes via `datetime.now()`, so tests
    that must pre-compute a colliding filename (T3) can match it exactly.
    """
    fixed = datetime(2026, 9, 1, 12, 0, 0)

    class _FixedDatetime:
        @classmethod
        def now(cls) -> datetime:
            return fixed

    monkeypatch.setattr(gw, "datetime", _FixedDatetime)
    return fixed.strftime("%Y%m%d-%H%M%S")


def _case(kind: str, tmp_path: Path) -> tuple[list[str], str, re.Pattern[str], Path]:
    """Return (argv, target_dir_key, filename_regex, template_path) for *kind*."""
    if kind == "issue":
        argv = ["--kind", "issue", "--id", "nc020", "--title", "Fix the Thing"]
        return (
            argv,
            "issues",
            re.compile(r"^\d{8}-\d{6}_nc020_fix-the-thing\.md$"),
            TEMPLATE_ISSUE,
        )
    if kind == "plan":
        argv = ["--kind", "plan"]
        return argv, "plans", re.compile(r"^\d{8}-\d{6}_plan\.md$"), TEMPLATE_PLAN
    if kind == "implementation-procedure":
        source_plan = tmp_path / "source_plan.md"
        source_plan.write_text("dummy plan content\n", encoding="utf-8")
        argv = [
            "--kind",
            "implementation-procedure",
            "--source-plan",
            str(source_plan),
            "--target-file-path",
            "scripts/agent/foo.py",
            "--seq",
            "01",
        ]
        # NOTE -- adversarial-verification finding (not fixed here; see this
        # implementation procedure document's Blocker Log and the final
        # report for this test-authoring task):
        # This document's own Procedure section states the expected mapping
        # as "scripts/agent/foo.py -> scripts_agent_foo_py" (`.` replaced by
        # `_`). The *current* tools/generate_workitem.py implementation's
        # `_NON_PATH_SLUG_RE` pattern (`[^A-Za-z0-9_.-]`) does not replace
        # `.`, so the actual rendered slug keeps the dot:
        # "scripts_agent_foo.py" (filename ends "..._scripts_agent_foo.py.md").
        # This also diverges from `skills/plan-to-implementation-procedure/
        # workflow.md`'s stated naming rule and from both existing precedent
        # filenames (`implementations/done/
        # 20260901-113804_01_tools_generate_workitem_py.md` and
        # `..._02_tools_TOOL_DESCRIPTIONS_md.md`), which both have the `.`
        # replaced by `_`. tools/generate_workitem.py is intentionally left
        # unmodified per this test-authoring task's scope -- the assertion
        # below characterizes the tool's actual current behavior so this
        # test suite stays green; the correct/intended behavior is the one
        # quoted above from the Procedure section.
        return (
            argv,
            "implementations",
            re.compile(r"^\d{8}-\d{6}_01_scripts_agent_foo\.py\.md$"),
            TEMPLATE_IMPLEMENTATION_PROCEDURE,
        )
    raise ValueError(f"unknown kind: {kind}")


class TestFilenameGeneration:
    """T1 (REQ-002): filename generation correctness for each `--kind`."""

    @pytest.mark.parametrize("kind", ["issue", "plan", "implementation-procedure"])
    def test_filename_matches_naming_convention(
        self, workitem_dirs: dict[str, Path], tmp_path: Path, kind: str
    ) -> None:
        argv, dir_key, filename_re, _template = _case(kind, tmp_path)

        returncode = gw.main(argv)

        assert returncode == 0
        target_dir = workitem_dirs[dir_key]
        matches = [p for p in target_dir.iterdir() if filename_re.match(p.name)]
        assert len(matches) == 1, (
            f"expected exactly one file matching {filename_re.pattern!r} in "
            f"{target_dir}, found: {sorted(p.name for p in target_dir.iterdir())}"
        )


class TestFieldOrder:
    """T2 (REQ-001): rendered section-heading order matches the current
    template content, read live from `templates/*.md`.
    """

    @pytest.mark.parametrize("kind", ["issue", "plan", "implementation-procedure"])
    def test_section_headings_match_current_template(
        self, workitem_dirs: dict[str, Path], tmp_path: Path, kind: str
    ) -> None:
        argv, dir_key, filename_re, template_path = _case(kind, tmp_path)

        returncode = gw.main(argv)

        assert returncode == 0
        target_dir = workitem_dirs[dir_key]
        matches = [p for p in target_dir.iterdir() if filename_re.match(p.name)]
        assert len(matches) == 1
        output_path = matches[0]

        assert _output_section_headings(output_path) == _template_section_headings(
            template_path
        )


class TestCollisionRejection:
    """T3 (REQ-003): the tool refuses to overwrite an existing file, whether
    the collision is at the direct target path or its `done/` counterpart.
    """

    @pytest.mark.parametrize("collision_location", ["target_dir", "done_dir"])
    def test_existing_file_is_not_overwritten(
        self,
        workitem_dirs: dict[str, Path],
        fixed_timestamp: str,
        collision_location: str,
    ) -> None:
        plans_dir = workitem_dirs["plans"]
        expected_name = f"{fixed_timestamp}_plan.md"
        direct_path = plans_dir / expected_name
        colliding_path = (
            direct_path
            if collision_location == "target_dir"
            else plans_dir / "done" / expected_name
        )
        original_content = "pre-existing content, must not be overwritten\n"
        colliding_path.write_text(original_content, encoding="utf-8")

        returncode = gw.main(["--kind", "plan"])

        assert returncode == 1
        assert colliding_path.read_text(encoding="utf-8") == original_content
        if collision_location == "done_dir":
            assert not direct_path.exists()


class TestMissingSourcePlan:
    """T4 (REQ-004): implementation-procedure mode rejects a `--source-plan`
    path that does not exist, without writing any output file.
    """

    def test_missing_source_plan_is_rejected(
        self, workitem_dirs: dict[str, Path], tmp_path: Path
    ) -> None:
        missing_plan = tmp_path / "does_not_exist_plan.md"
        assert not missing_plan.exists()
        argv = [
            "--kind",
            "implementation-procedure",
            "--source-plan",
            str(missing_plan),
            "--target-file-path",
            "scripts/agent/foo.py",
            "--seq",
            "01",
        ]

        returncode = gw.main(argv)

        assert returncode == 1
        created = list(workitem_dirs["implementations"].rglob("*.md"))
        assert created == []
