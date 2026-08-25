"""tests/tools/test_rename_modules.py
Tests for tools/rename_modules.py.
"""

from __future__ import annotations

import pathlib
import sys
from io import StringIO
from unittest.mock import patch

import pytest

# Import the module under test — must be importable via sys.path manipulation
# because the script uses relative paths from its own location.


class TestBaseResolution:
    """BASE must resolve correctly regardless of working directory."""

    def test_base_resolves_from_script_location(self) -> None:
        import tools.rename_modules as mod

        assert mod.BASE.is_dir(), f"BASE should point to a directory, got {mod.BASE}"

    @pytest.mark.parametrize("subpath", ["scripts", "tests", "tools"])
    def test_base_contains_expected_subdirectories(self, subpath: str) -> None:
        import tools.rename_modules as mod

        assert (mod.BASE / subpath).is_dir(), f"Expected {mod.BASE / subpath} to exist"


# ---------------------------------------------------------------------------
# Fail-loud behavior
# ---------------------------------------------------------------------------


class TestFailLoudOnMissingBase:
    """main() must exit non-zero when BASE does not exist."""

    def test_exits_nonzero_when_base_missing(self, tmp_path: pathlib.Path) -> None:
        import tools.rename_modules as mod

        fake_base = tmp_path / "nonexistent"
        assert not fake_base.exists()

        old_base = mod.BASE
        try:
            mod.BASE = fake_base
            stderr_capture = StringIO()
            with patch.object(sys, "stderr", stderr_capture):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()
            assert exc_info.value.code == 1
            assert "repository root not found" in stderr_capture.getvalue()
        finally:
            mod.BASE = old_base

    def test_exits_nonzero_when_subdir_missing(self, tmp_path: pathlib.Path) -> None:
        import tools.rename_modules as mod

        fake_base = tmp_path / "fake_repo"
        fake_base.mkdir(parents=True)
        (fake_base / "scripts").mkdir()
        # tests, mutants, implementations, plans, requires are intentionally missing

        old_base = mod.BASE
        try:
            mod.BASE = fake_base
            stderr_capture = StringIO()
            with patch.object(sys, "stderr", stderr_capture):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()
            assert exc_info.value.code == 1
            assert "expected directory not found" in stderr_capture.getvalue()
        finally:
            mod.BASE = old_base


# ---------------------------------------------------------------------------
# Dead-code removal: process_file() must not exist anymore
# ---------------------------------------------------------------------------


class TestDeadCodeRemoved:
    """process_file() was dead code and must have been removed."""

    def test_process_file_not_in_module_namespace(self) -> None:
        import tools.rename_modules as mod

        assert not hasattr(mod, "process_file"), (
            "process_file() should have been removed"
        )

    def test_main_runs_without_process_file(self) -> None:
        import tools.rename_modules as mod

        try:
            mod.main()
        except SystemExit:
            pass
