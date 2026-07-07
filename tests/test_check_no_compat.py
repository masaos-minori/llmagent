"""tests/test_check_no_compat.py
Tests for scripts/checks/check_no_compat.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools.check_no_compat import (
    COMPAT_PATTERNS,
    check_compat_patterns,
)


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
