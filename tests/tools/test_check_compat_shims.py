"""tests/tools/test_check_compat_shims.py
Tests for tools/check_compat_shims.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from tools.check_compat_shims import (
    ADR_PROHIBITED_PATTERNS,
    COMPAT_PATTERNS,
    ROOT_DIR,
    check_adr_prohibited_patterns,
    check_all,
    check_compat_patterns,
    check_removed_name_reintroduction,
    main,
)


class TestRootDirResolution:
    """ROOT_DIR must resolve to the actual repository root.

    Regression test for a bug where an extra `.parent` made ROOT_DIR resolve
    one directory too high, causing main()'s default scan to silently see
    zero files (dirs_to_scan entries all failed their exists() guard).
    """

    def test_root_dir_resolves_to_repository_root(self) -> None:
        assert (ROOT_DIR / "scripts").exists()
        assert (ROOT_DIR / "docs").exists()
        assert (ROOT_DIR / "tests").exists()
        assert (ROOT_DIR / "tools").exists()


class TestPatternDetection:
    """Each new pattern is detected in synthetic input."""

    @pytest.mark.parametrize(
        "phrase",
        [
            "re-export stub",
            "compatibility shim",
            "existing imports continue to work",
            "backward-compatible",
            "_cast_enums",
        ],
    )
    def test_new_pattern_detected_in_synthetic_string(
        self, phrase: str, tmp_path: Path
    ) -> None:
        synthetic = tmp_path / "synthetic_test.py"
        synthetic.write_text(f"# {phrase}\n")
        content = synthetic.read_text()
        matched = any(re.search(pat, content) for pat in COMPAT_PATTERNS.values())
        assert matched, f"Pattern for '{phrase}' was not detected"

    def test_clean_file_has_no_matches(self, tmp_path: Path) -> None:
        clean = tmp_path / "clean.py"
        clean.write_text("# This file has no compat patterns\n")
        issues = check_compat_patterns(clean.read_text(), clean, set())
        assert issues == []

    def test_allowlisted_file_skipped(self, tmp_path: Path) -> None:
        dirty = tmp_path / "allowlisted.py"
        dirty.write_text("# re-export stub for compatibility\n")
        issues = check_compat_patterns(dirty.read_text(), dirty, {dirty})
        assert issues == []


class TestAdrProhibitedPatterns:
    """The ADR-scoped check (REQ-002) fires on a seeded pattern and is
    silent otherwise; distinct from COMPAT_PATTERNS's own detection."""

    def test_seeded_pattern_detected_in_synthetic_code(self, tmp_path: Path) -> None:
        dirty = tmp_path / "synthetic.py"
        dirty.write_text("if disable_workflow:\n    pass\n")
        issues = check_adr_prohibited_patterns(dirty.read_text(), dirty, set())
        assert len(issues) == 1
        assert "ADR-001" in issues[0]

    def test_clean_file_has_no_adr_pattern_matches(self, tmp_path: Path) -> None:
        clean = tmp_path / "clean.py"
        clean.write_text("if some_other_flag:\n    pass\n")
        issues = check_adr_prohibited_patterns(clean.read_text(), clean, set())
        assert issues == []

    def test_allowlisted_file_skipped(self, tmp_path: Path) -> None:
        dirty = tmp_path / "allowlisted.py"
        dirty.write_text("if disable_workflow:\n    pass\n")
        issues = check_adr_prohibited_patterns(dirty.read_text(), dirty, {dirty})
        assert issues == []

    def test_adr001_prose_in_docs_is_not_matched(self, tmp_path: Path) -> None:
        """The Japanese ADR-001 prohibition prose must not self-trigger this
        identifier-shaped check."""
        doc = tmp_path / "adr_prose.md"
        doc.write_text(
            "Workflow無効化モードを設けない。Workflowを迂回する直接実行経路を設けない。\n"
        )
        issues = check_adr_prohibited_patterns(doc.read_text(), doc, set())
        assert issues == []

    def test_every_pattern_maps_to_a_real_adr_id(self) -> None:
        for name, (adr_id, pattern) in ADR_PROHIBITED_PATTERNS.items():
            assert re.match(r"^ADR-\d{3}$", adr_id), (
                f"'{name}' maps to malformed ADR id {adr_id!r}"
            )


class TestDirectoryPositionalArgument:
    """A directory passed as a positional file argument must be expanded into its
    contained files (mirroring the no-args scan), not crash with IsADirectoryError.
    """

    def test_directory_with_violation_is_expanded_and_flagged(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "dirty.py").write_text("# re-export stub for compatibility\n")
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", str(tmp_path)])

        exit_code = main()

        assert exit_code == 1
        assert "dirty.py" in capsys.readouterr().err

    def test_directory_with_no_violations_returns_clean_without_crashing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", str(tmp_path)])

        exit_code = main()

        assert exit_code == 0

    def test_relative_directory_argument_does_not_crash(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regression test: expanded glob results must be resolved to absolute
        paths, or filepath.relative_to(ROOT_DIR) raises ValueError for any
        relative directory argument that yields a match or allowlist check."""
        (tmp_path / "clean.py").write_text("# nothing to see here\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["check_compat_shims", "."])

        exit_code = main()

        assert exit_code == 0


def _check(content: str) -> list[str]:
    return check_compat_patterns(content, Path("scripts/test.py"), set())


class TestWorkflowEnforcementPatterns:
    """Each workflow enforcement pattern is detected in synthetic input."""

    def test_detects_workflow_mode_field_reference(self) -> None:
        assert any(
            "workflow_mode field reference" in i
            for i in _check("workflow_mode: str = 'auto'")
        )

    def test_detects_allow_startup_fallback(self) -> None:
        assert any(
            "allow_startup_fallback" in i
            for i in _check("if self.allow_startup_fallback():")
        )

    def test_detects_is_workflow_enabled(self) -> None:
        assert any(
            "is_workflow_enabled" in i
            for i in _check("if not policy.is_workflow_enabled():")
        )

    def test_detects_requires_startup_definition(self) -> None:
        assert any(
            "requires_startup_definition" in i
            for i in _check("policy.requires_startup_definition()")
        )

    def test_detects_allow_turn_fallback(self) -> None:
        assert any(
            "allow_turn_fallback" in i
            for i in _check("if policy.allow_turn_fallback():")
        )

    def test_detects_workflow_mode_disabled_string(self) -> None:
        assert any(
            "workflow_mode=disabled" in i for i in _check('workflow_mode="disabled"')
        )

    def test_detects_workflow_mode_auto_string(self) -> None:
        assert any("workflow_mode=auto" in i for i in _check('workflow_mode="auto"'))

    def test_detects_workflow_mode_disabled_log(self) -> None:
        assert any(
            "Workflow mode=disabled" in i
            for i in _check('logger.info("Workflow mode=disabled")')
        )

    def test_detects_direct_llm_path_phrase(self) -> None:
        assert any("direct LLM path" in i for i in _check("# direct LLM path fallback"))

    def test_detects_direct_execution_fallback_phrase(self) -> None:
        assert any(
            "direct-execution fallback" in i
            for i in _check("# direct-execution fallback")
        )

    def test_detects_workflow_execution_policy_import(self) -> None:
        assert any(
            "WorkflowExecutionPolicy import" in i
            for i in _check(
                "from agent.workflow_execution_policy import WorkflowExecutionPolicy"
            )
        )

    def test_detects_workflow_execution_policy_module_import(self) -> None:
        assert any(
            "workflow_execution_policy module import" in i
            for i in _check("import workflow_execution_policy")
        )

    def test_allowlisted_file_not_flagged(self) -> None:
        issues = check_compat_patterns(
            "workflow_mode: str = 'auto'",
            Path("scripts/test.py"),
            {Path("scripts/test.py")},
        )
        assert issues == []

    def test_unrelated_mode_assignment_not_flagged(self) -> None:
        issues = _check('display_mode = "compact"')
        assert not any("workflow_mode field reference" in i for i in issues)


class TestRemovedNameReintroduction:
    """check_removed_name_reintroduction() — compatterms REQ-003's
    simple-absence case: `_update_null_fill` and the ToolRouteResolver+
    server_configs co-occurrence, both scoped to docs/*.md only, both
    exempted inside historical/resolved context."""

    def test_update_null_fill_flagged_outside_historical_context(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert len(issues) == 1
        assert "_update_null_fill" in issues[0]

    def test_update_null_fill_exempted_in_historical_context(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "**Status**: resolved\n\n"
            "This entry records that `_update_null_fill()` was removed.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    def test_non_markdown_file_is_not_checked(self, tmp_path: Path) -> None:
        py_file = tmp_path / "example.py"
        py_file.write_text("# _update_null_fill() is current\n")
        issues = check_removed_name_reintroduction(py_file.read_text(), py_file)
        assert issues == []

    def test_tool_route_resolver_server_configs_flagged_same_section(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolRouteResolver\n\n"
            "- **Configuration:** accepts `server_configs` for backward "
            "compatibility.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert len(issues) == 1
        assert "ToolRouteResolver+server_configs" in issues[0]

    def test_tool_route_resolver_server_configs_exempted_in_historical_section(
        self, tmp_path: Path
    ) -> None:
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolRouteResolver (historical)\n\n"
            "- **Removed:** previously accepted `server_configs`.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []

    def test_server_configs_alone_without_class_name_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """server_configs unrelated to ToolRouteResolver (e.g. ToolExecutor's
        own, still-current field) must not be flagged."""
        doc = tmp_path / "example.md"
        doc.write_text(
            "## ToolExecutor\n\n"
            "- **Configuration:** `server_configs` is the active MCP "
            "execution configuration.\n"
        )
        issues = check_removed_name_reintroduction(doc.read_text(), doc)
        assert issues == []


class TestCheckAllRemovedNamesGating:
    """check_all()'s `include_removed_names` defaults to False so the
    existing .pre-commit-config.yaml wiring (a bare invocation with no
    flags) is unaffected by this new, currently-non-compliant check."""

    def test_default_does_not_include_removed_names_check(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_all(doc.read_text(), doc, allowlist=set())
        assert issues == []

    def test_opt_in_includes_removed_names_check(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        doc.write_text("`_update_null_fill()` is the current fallback path.\n")
        issues = check_all(
            doc.read_text(), doc, allowlist=set(), include_removed_names=True
        )
        assert len(issues) == 1
