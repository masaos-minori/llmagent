"""tests/tools/test_check_suppression_justification.py
Tests for tools/check_suppression_justification.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_suppression_justification import check_suppression_justification


class TestSuppressionKindJustification:
    """Bare / code-only / code+em-dash matrix for each suppression kind."""

    @pytest.mark.parametrize(
        ("line", "expect_issue"),
        [
            pytest.param("value = 1  # noqa", True, id="noqa-bare"),
            pytest.param("value = 1  # noqa: E501", True, id="noqa-code-no-dash"),
            pytest.param(
                "value = 1  # noqa: E501 — line kept long for readability",
                False,
                id="noqa-code-with-dash",
            ),
            pytest.param("value = 1  # type: ignore", True, id="type-ignore-bare"),
            pytest.param(
                "value = 1  # type: ignore[arg-type]",
                True,
                id="type-ignore-code-no-dash",
            ),
            pytest.param(
                "value = 1  # type: ignore[arg-type] — upstream stub is incomplete",
                False,
                id="type-ignore-code-with-dash",
            ),
            pytest.param(
                "result = subprocess.run(cmd)  # nosec", True, id="nosec-bare"
            ),
            pytest.param(
                "result = subprocess.run(cmd)  # nosec B603",
                True,
                id="nosec-code-no-dash",
            ),
            pytest.param(
                "result = subprocess.run(cmd)  # nosec B603 — cmd is a validated static list",
                False,
                id="nosec-code-with-dash",
            ),
        ],
    )
    def test_suppression_matrix(
        self, line: str, expect_issue: bool, tmp_path: Path
    ) -> None:
        synthetic = tmp_path / "synthetic_test.py"
        synthetic.write_text(line + "\n")
        content = synthetic.read_text()
        issues = check_suppression_justification(content, synthetic, set())
        assert bool(issues) is expect_issue, issues


class TestAllowlistPassThrough:
    """A file present in the allowlist is skipped even if it would otherwise fail."""

    def test_allowlisted_file_skipped(self, tmp_path: Path) -> None:
        dirty = tmp_path / "allowlisted.py"
        dirty.write_text("value = 1  # noqa\n")
        issues = check_suppression_justification(dirty.read_text(), dirty, {dirty})
        assert issues == []


class TestMultiLineImportFixture:
    """Multi-line/parenthesized-import noqa style is flagged, not silently ignored."""

    def test_multiline_parenthesized_import_is_flagged(self, tmp_path: Path) -> None:
        synthetic = tmp_path / "multiline_import.py"
        synthetic.write_text(
            "from shared.config_loader import (  # noqa: PLC0415\n"
            "    _BASE_CONFIG_FILES,\n"
            "    ConfigLoader,\n"
            ")\n"
        )
        content = synthetic.read_text()
        issues = check_suppression_justification(content, synthetic, set())
        assert len(issues) == 1
        assert "noqa" in issues[0]
