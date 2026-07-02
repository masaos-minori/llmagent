"""tests/test_check_no_compat.py
Tests for scripts/checks/check_no_compat.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.checks.check_no_compat import (
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
