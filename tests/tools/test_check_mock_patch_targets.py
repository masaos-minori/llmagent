"""tests/tools/test_check_mock_patch_targets.py
Tests for tools/check_mock_patch_targets.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_mock_patch_targets as cmpt


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    monkeypatch.setattr(cmpt, "ROOT_DIR", tmp_path)
    source_modules = cmpt.discover_source_modules()
    reverse_index = cmpt.build_reverse_import_index(source_modules)
    test_files = cmpt.discover_test_files(tmp_path / "tests")
    return cmpt.find_ineffective_patch_targets(
        test_files, reverse_index, set(source_modules)
    )


class TestIneffectivePatchTarget:
    """The exact repeatedly-found bug pattern: a test patches the symbol's
    origin module, but the module under test re-imported it at module
    level -- the patch never takes effect.
    """

    def test_origin_patch_flagged_against_module_level_reimport(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "from db.helper import SQLiteHelper\n\n\nclass DiagnosticStore:\n    pass\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            "from unittest.mock import patch\n"
            "from agent.diagnostic_store import DiagnosticStore\n\n\n"
            '@patch("db.helper.SQLiteHelper")\n'
            "def test_it(mock_helper):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert len(findings) == 1
        assert findings[0]["category"] == "ineffective-patch-target"
        assert "tests/agent/test_diagnostic_store.py" in findings[0]["file"]
        assert "agent.diagnostic_store" in findings[0]["detail"]

    def test_correct_patch_at_the_reimporting_module_is_not_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "from db.helper import SQLiteHelper\n\n\nclass DiagnosticStore:\n    pass\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            "from unittest.mock import patch\n"
            "from agent.diagnostic_store import DiagnosticStore\n\n\n"
            '@patch("agent.diagnostic_store.SQLiteHelper")\n'
            "def test_it(mock_helper):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert findings == []

    def test_function_local_import_is_not_module_level(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A deferred import inside a function body re-resolves on every
        call, so patching the origin there still works -- must not flag.
        """
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "class DiagnosticStore:\n"
            "    def load(self):\n"
            "        from db.helper import SQLiteHelper\n"
            "        return SQLiteHelper()\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            "from unittest.mock import patch\n"
            "from agent.diagnostic_store import DiagnosticStore\n\n\n"
            '@patch("db.helper.SQLiteHelper")\n'
            "def test_it(mock_helper):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert findings == []

    def test_type_checking_guarded_import_is_not_module_level(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from db.helper import SQLiteHelper\n\n\n"
            "class DiagnosticStore:\n"
            "    pass\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            "from unittest.mock import patch\n"
            "from agent.diagnostic_store import DiagnosticStore\n\n\n"
            '@patch("db.helper.SQLiteHelper")\n'
            "def test_it(mock_helper):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert findings == []

    def test_patch_object_calls_are_ignored(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`patch.object(Cls, "attr")` targets an object, not a dotted
        string -- out of scope for this string-target-only checker.
        """
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "from db.helper import SQLiteHelper\n\n\nclass DiagnosticStore:\n    pass\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            "from unittest.mock import patch\n"
            "from agent.diagnostic_store import DiagnosticStore\n\n\n"
            '@patch.object(DiagnosticStore, "load")\n'
            "def test_it(mock_load):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert findings == []

    def test_no_candidate_sut_module_is_not_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A test file that never imports any known source module has no
        candidate to compare against -- nothing to flag.
        """
        _write(
            tmp_path / "scripts" / "db" / "helper.py",
            "class SQLiteHelper:\n    pass\n",
        )
        _write(
            tmp_path / "scripts" / "agent" / "diagnostic_store.py",
            "from db.helper import SQLiteHelper\n\n\nclass DiagnosticStore:\n    pass\n",
        )
        _write(
            tmp_path / "tests" / "agent" / "test_diagnostic_store.py",
            'from unittest.mock import patch\n\n\n@patch("db.helper.SQLiteHelper")\n'
            "def test_it(mock_helper):\n"
            "    pass\n",
        )

        findings = _run(tmp_path, monkeypatch)

        assert findings == []
