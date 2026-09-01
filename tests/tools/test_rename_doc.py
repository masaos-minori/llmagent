"""tests/tools/test_rename_doc.py
Tests for tools/rename_doc.py.
"""

from __future__ import annotations

from pathlib import Path

import git
import pytest

from tools.rename_doc import (
    PlannedRewrite,
    apply_rewrites_to_content,
    build_plan,
    git_mv,
    main,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _init_git_repo(root: Path) -> git.Repo:
    """Initialize a git repository at `root` with a fixture-only identity."""
    repo = git.Repo.init(root)
    with repo.config_writer() as writer:
        writer.set_value("user", "name", "Test User")
        writer.set_value("user", "email", "test@example.com")
    return repo


def _commit_file(repo: git.Repo, path: Path, content: str) -> None:
    """Write `content` to `path` and commit it (`git mv` needs a tracked file)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    repo.index.add([str(path)])
    repo.index.commit(f"add {path.name}")


# ---------------------------------------------------------------------------
# T1 (REQ-001, REQ-002): multi-file rename, both link conventions preserved
# ---------------------------------------------------------------------------


def test_t1_multi_file_rename_preserves_link_styles(tmp_path: Path) -> None:
    """Renaming a file with `--apply` rewrites every referencing link to the
    new path in its own original style: bare filename for a same-directory
    reference, `../<filename>` for a parent-hop reference (the two
    conventions confirmed in `docs/adr/ADR-005-...`/`docs/adr/ADR-012-...`),
    and the move itself happens via `git mv`.
    """
    repo = _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"

    old_path = docs_root / "old_name.md"
    new_path = docs_root / "new_name.md"
    bare_ref = docs_root / "ref_bare.md"
    dotdot_ref = docs_root / "adr" / "ref_dotdot.md"

    _commit_file(repo, old_path, "# Old Doc\n\nContent.\n")
    _commit_file(repo, bare_ref, "See [Old Doc](old_name.md) for background.\n")
    _commit_file(repo, dotdot_ref, "See [Old Doc](../old_name.md) for background.\n")

    plan = build_plan(docs_root, old_path, new_path, None, None)

    assert set(plan.rewrites_by_file) == {bare_ref, dotdot_ref}
    assert plan.rewrites_by_file[bare_ref][0].new_snippet == "[Old Doc](new_name.md)"
    assert (
        plan.rewrites_by_file[dotdot_ref][0].new_snippet == "[Old Doc](../new_name.md)"
    )
    assert plan.unresolved_links == []
    assert plan.prose_findings == []

    git_mv(old_path, new_path, tmp_path)
    for target_file, rewrites in plan.rewrites_by_file.items():
        content = target_file.read_text(encoding="utf-8")
        target_file.write_text(
            apply_rewrites_to_content(content, rewrites), encoding="utf-8"
        )

    assert not old_path.exists()
    assert new_path.exists()
    assert "[Old Doc](new_name.md)" in bare_ref.read_text(encoding="utf-8")
    assert "[Old Doc](../new_name.md)" in dotdot_ref.read_text(encoding="utf-8")

    status = repo.git.status("--porcelain")
    assert "old_name.md" in status
    assert "new_name.md" in status


# ---------------------------------------------------------------------------
# T2 (REQ-003): opt-in title-rewrite flag
# ---------------------------------------------------------------------------


def test_t2_title_rewrite_flag_is_opt_in(tmp_path: Path) -> None:
    """`--old-title`/`--new-title` rewrites the adjacent link text only when
    both are supplied; without them the link text is left untouched while
    the link path is still rewritten to the new target.
    """
    repo = _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    old_path = docs_root / "old_name.md"
    new_path = docs_root / "new_name.md"
    ref = docs_root / "ref.md"

    _commit_file(repo, old_path, "# Old Title\n")
    _commit_file(repo, ref, "See [Old Title](old_name.md) for details.\n")

    plan_with_title = build_plan(
        docs_root, old_path, new_path, "Old Title", "New Title"
    )
    rewrite_with_title = plan_with_title.rewrites_by_file[ref][0]
    assert rewrite_with_title.new_snippet == "[New Title](new_name.md)"

    rewritten_content = apply_rewrites_to_content(
        ref.read_text(encoding="utf-8"), [rewrite_with_title]
    )
    assert "[New Title](new_name.md)" in rewritten_content
    assert "Old Title" not in rewritten_content

    plan_without_title = build_plan(docs_root, old_path, new_path, None, None)
    rewrite_without_title = plan_without_title.rewrites_by_file[ref][0]
    assert rewrite_without_title.new_snippet == "[Old Title](new_name.md)"


# ---------------------------------------------------------------------------
# T3 (REQ-004): non-link prose mention is reported, never rewritten
# ---------------------------------------------------------------------------


def test_t3_non_link_prose_is_reported_not_rewritten(tmp_path: Path) -> None:
    """A plain-prose mention of the old filename outside any `[text](path)`
    span is surfaced as a `ProseFinding` but never enters `rewrites_by_file`,
    so applying the plan's rewrites (mirroring `main()`'s apply loop, which
    only touches files present in `rewrites_by_file`) leaves the prose text
    byte-for-byte unchanged.
    """
    repo = _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    old_path = docs_root / "old_name.md"
    new_path = docs_root / "new_name.md"
    prose_file = docs_root / "prose.md"

    prose_line = "See old_name.md in the repository for background.\n"
    _commit_file(repo, old_path, "# Old Doc\n")
    _commit_file(repo, prose_file, prose_line)

    plan = build_plan(docs_root, old_path, new_path, None, None)

    assert prose_file not in plan.rewrites_by_file
    assert len(plan.prose_findings) == 1
    finding = plan.prose_findings[0]
    assert finding.file == prose_file
    assert finding.line_no == 1
    assert "old_name.md" in finding.snippet

    content_before = prose_file.read_text(encoding="utf-8")
    rewrites_for_prose_file = plan.rewrites_by_file.get(prose_file, [])
    content_after = apply_rewrites_to_content(content_before, rewrites_for_prose_file)
    assert content_after == content_before == prose_line


# ---------------------------------------------------------------------------
# T4 (REQ-005): dry-run vs. apply parity
# ---------------------------------------------------------------------------


def _build_t4_fixture(
    root: Path,
) -> tuple[git.Repo, Path, Path, Path, Path]:
    """Build an identical old/new/ref fixture tree under `root`."""
    repo = _init_git_repo(root)
    docs_root = root / "docs"
    old_path = docs_root / "old_name.md"
    new_path = docs_root / "new_name.md"
    ref = docs_root / "ref.md"
    _commit_file(repo, old_path, "# Old Doc\n")
    _commit_file(repo, ref, "See [Old Doc](old_name.md) for details.\n")
    return repo, docs_root, old_path, new_path, ref


def test_t4_dry_run_matches_apply_without_writing(tmp_path: Path) -> None:
    """The plan a dry-run would report (no `git mv`, no file write) is
    identical to the plan `--apply` acts on, when computed from two
    independent, identically-seeded fixture copies -- `main()` builds this
    same plan before either mode diverges on whether to write it.
    """
    dry_root = tmp_path / "dry"
    apply_root = tmp_path / "apply"
    dry_root.mkdir()
    apply_root.mkdir()

    _, dry_docs_root, dry_old, dry_new, dry_ref = _build_t4_fixture(dry_root)
    (
        _,
        apply_docs_root,
        apply_old,
        apply_new,
        apply_ref,
    ) = _build_t4_fixture(apply_root)

    dry_plan = build_plan(dry_docs_root, dry_old, dry_new, None, None)
    apply_plan = build_plan(apply_docs_root, apply_old, apply_new, None, None)

    # Dry-run mode never calls git_mv()/write_text() -- assert the fixture
    # this plan was computed from is untouched.
    assert dry_old.exists()
    assert not dry_new.exists()
    original_ref_content = "See [Old Doc](old_name.md) for details.\n"
    assert dry_ref.read_text(encoding="utf-8") == original_ref_content

    def _relative_snippets(
        plan_rewrites: dict[Path, list[PlannedRewrite]], docs_root: Path
    ) -> dict[Path, list[tuple[int, str, str]]]:
        return {
            file.relative_to(docs_root): [
                (r.line_no, r.old_snippet, r.new_snippet) for r in rewrites
            ]
            for file, rewrites in plan_rewrites.items()
        }

    assert _relative_snippets(
        dry_plan.rewrites_by_file, dry_docs_root
    ) == _relative_snippets(apply_plan.rewrites_by_file, apply_docs_root)

    git_mv(apply_old, apply_new, apply_root)
    for target_file, rewrites in apply_plan.rewrites_by_file.items():
        content = target_file.read_text(encoding="utf-8")
        target_file.write_text(
            apply_rewrites_to_content(content, rewrites), encoding="utf-8"
        )

    assert not apply_old.exists()
    assert apply_new.exists()
    assert "[Old Doc](new_name.md)" in apply_ref.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T5 (REQ-006): docs/-containment enforcement
# ---------------------------------------------------------------------------


def test_t5_containment_escape_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `new-path` (or `old-path`) argument that escapes `docs/` via a `..`
    traversal is rejected by `main()` with a non-zero return and no write
    occurs anywhere, including outside the fixture root.
    """
    repo = _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    old_path = docs_root / "old_name.md"
    _commit_file(repo, old_path, "# Old Doc\n")

    monkeypatch.chdir(tmp_path)

    escape_target = tmp_path.parent / "escaped.md"
    assert not escape_target.exists()

    exit_code = main(["docs/old_name.md", "../escaped.md"])

    assert exit_code != 0
    assert not escape_target.exists()
    assert old_path.exists()
    assert not (docs_root / "new_name.md").exists()

    escape_source_target = tmp_path.parent / "old_name.md"
    exit_code_old_escape = main(["../old_name.md", "docs/new_name.md"])

    assert exit_code_old_escape != 0
    assert not escape_source_target.exists()
    assert old_path.exists()
    assert not (docs_root / "new_name.md").exists()
