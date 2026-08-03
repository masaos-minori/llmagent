"""tests/test_check_agent_docs_consistency.py

Unit tests for tools/check_agent_docs_consistency.py — synthetic doc content
and synthetic source snippets, not references to real doc/source files.
"""

from __future__ import annotations

from pathlib import Path

from check_agent_docs_consistency import (
    DocFile,
    check_broken_internal_links,
    check_command_drift,
    check_removed_file_references,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _mk_file(rel: str, lines: list[str]) -> DocFile:
    return DocFile(path=Path(f"/fake/{rel}"), rel_path=rel, lines=lines)


# ── check_broken_internal_links ──────────────────────────────────────────────


class TestCheckBrokenInternalLinks:
    def test_link_to_existing_file_no_issue(self, tmp_path: Path) -> None:
        (tmp_path / "05_agent_01_a.md").write_text("target")
        doc = _mk_file("05_agent_00_b.md", ["see [a](05_agent_01_a.md)"])
        issues = check_broken_internal_links(tmp_path, [doc])
        assert issues == []

    def test_link_to_missing_file_is_error(self, tmp_path: Path) -> None:
        doc = _mk_file("05_agent_00_b.md", ["see [a](05_agent_99_missing.md)"])
        issues = check_broken_internal_links(tmp_path, [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "05_agent_99_missing.md" in issues[0].message

    def test_external_link_skipped(self, tmp_path: Path) -> None:
        doc = _mk_file("05_agent_00_b.md", ["see [x](https://example.com/x.md)"])
        issues = check_broken_internal_links(tmp_path, [doc])
        assert issues == []

    def test_anchor_only_link_skipped(self, tmp_path: Path) -> None:
        doc = _mk_file("05_agent_00_b.md", ["see [x](#section)"])
        issues = check_broken_internal_links(tmp_path, [doc])
        assert issues == []

    def test_link_with_anchor_to_existing_file_no_issue(self, tmp_path: Path) -> None:
        (tmp_path / "05_agent_01_a.md").write_text("target")
        doc = _mk_file("05_agent_00_b.md", ["see [a](05_agent_01_a.md#some-heading)"])
        issues = check_broken_internal_links(tmp_path, [doc])
        assert issues == []


# ── check_removed_file_references ────────────────────────────────────────────


class TestCheckRemovedFileReferences:
    def test_reference_to_missing_file_is_error(self, tmp_path: Path) -> None:
        doc = _mk_file("05_agent_00_b.md", ["see `05_agent_99_missing.md`"])
        issues = check_removed_file_references(tmp_path, [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_reference_to_existing_file_no_issue(self, tmp_path: Path) -> None:
        (tmp_path / "05_agent_01_a.md").write_text("target")
        doc = _mk_file("05_agent_00_b.md", ["see `05_agent_01_a.md`"])
        issues = check_removed_file_references(tmp_path, [doc])
        assert issues == []

    def test_historical_marker_line_skipped(self, tmp_path: Path) -> None:
        doc = _mk_file(
            "05_agent_00_b.md",
            ["削除済みの`05_agent_99_missing.md`は統合された"],
        )
        issues = check_removed_file_references(tmp_path, [doc])
        assert issues == []


# ── check_command_drift ───────────────────────────────────────────────────────


class TestCheckCommandDrift:
    def test_registered_command_no_issue(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        (repo_root / "scripts" / "agent" / "commands").mkdir(parents=True)
        (
            repo_root / "scripts" / "agent" / "commands" / "command_defs_list.py"
        ).write_text('CommandDef("/help", False, False, "_cmd_help", "help")')
        doc = _mk_file("05_agent_00_b.md", ["run /help to see commands"])
        issues = check_command_drift(tmp_path, [doc], repo_root)
        assert issues == []

    def test_unregistered_command_is_warning(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        (repo_root / "scripts" / "agent" / "commands").mkdir(parents=True)
        (
            repo_root / "scripts" / "agent" / "commands" / "command_defs_list.py"
        ).write_text('CommandDef("/help", False, False, "_cmd_help", "help")')
        doc = _mk_file("05_agent_00_b.md", ["run /db rag stats"])
        issues = check_command_drift(tmp_path, [doc], repo_root)
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "/db" in issues[0].message

    def test_historical_marker_line_skipped(self, tmp_path: Path) -> None:
        repo_root = tmp_path
        (repo_root / "scripts" / "agent" / "commands").mkdir(parents=True)
        (
            repo_root / "scripts" / "agent" / "commands" / "command_defs_list.py"
        ).write_text('CommandDef("/help", False, False, "_cmd_help", "help")')
        doc = _mk_file("05_agent_00_b.md", ["/db removed entirely"])
        issues = check_command_drift(tmp_path, [doc], repo_root)
        assert issues == []

    def test_missing_source_file_returns_no_issues(self, tmp_path: Path) -> None:
        doc = _mk_file("05_agent_00_b.md", ["run /db rag stats"])
        issues = check_command_drift(tmp_path, [doc], tmp_path)
        assert issues == []
