"""tests/tools/test_check_conftest_integrity.py
Tests for tools/check_conftest_integrity.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_conftest_integrity as cci

REQUIRED_FIXTURES = ("_reset_tool_registry", "_reset_web_search_health_and_metrics")

_VALID_CONFTEST = (
    "import pytest\n\n\n"
    "@pytest.fixture(autouse=True)\n"
    "def _reset_tool_registry():\n"
    "    yield\n\n\n"
    "@pytest.fixture(autouse=True)\n"
    "def _reset_web_search_health_and_metrics():\n"
    "    yield\n"
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestValidConftest:
    def test_complete_conftest_reports_no_findings(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conftest_path = tmp_path / "tests" / "conftest.py"
        _write(conftest_path, _VALID_CONFTEST)
        monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)

        findings = cci.find_conftest_findings(conftest_path, REQUIRED_FIXTURES)

        assert findings == []


class TestConftestMissing:
    def test_missing_file_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conftest_path = tmp_path / "tests" / "conftest.py"
        (tmp_path / "tests").mkdir(parents=True)
        monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)

        findings = cci.find_conftest_findings(conftest_path, REQUIRED_FIXTURES)

        categories = {f["category"] for f in findings}
        assert "conftest-missing" in categories


class TestSuspiciousBackupFile:
    def test_bak_sibling_is_reported_even_when_conftest_itself_is_fine(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The historical incident: the real file was renamed to `.bak` --
        detect the suspicious sibling regardless of the real file's state.
        """
        conftest_path = tmp_path / "tests" / "conftest.py"
        _write(conftest_path, _VALID_CONFTEST)
        _write(tmp_path / "tests" / "conftest.py.bak", "# stale debris\n")
        monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)

        findings = cci.find_conftest_findings(conftest_path, REQUIRED_FIXTURES)

        assert len(findings) == 1
        assert findings[0]["category"] == "conftest-suspicious-backup-file"
        assert findings[0]["file"] == "tests/conftest.py.bak"


class TestMissingRequiredFixture:
    def test_missing_fixture_name_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conftest_path = tmp_path / "tests" / "conftest.py"
        _write(
            conftest_path,
            "import pytest\n\n\n"
            "@pytest.fixture(autouse=True)\n"
            "def _reset_tool_registry():\n"
            "    yield\n",
        )
        monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)

        findings = cci.find_conftest_findings(conftest_path, REQUIRED_FIXTURES)

        assert len(findings) == 1
        assert findings[0]["category"] == "conftest-missing-fixture"
        assert "_reset_web_search_health_and_metrics" in findings[0]["detail"]

    def test_fixture_present_but_not_autouse_is_still_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A fixture with the right name but autouse=False (or dropped
        entirely) no longer runs for every test -- same failure mode.
        """
        conftest_path = tmp_path / "tests" / "conftest.py"
        _write(
            conftest_path,
            "import pytest\n\n\n"
            "@pytest.fixture(autouse=True)\n"
            "def _reset_tool_registry():\n"
            "    yield\n\n\n"
            "@pytest.fixture(autouse=False)\n"
            "def _reset_web_search_health_and_metrics():\n"
            "    yield\n",
        )
        monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)

        findings = cci.find_conftest_findings(conftest_path, REQUIRED_FIXTURES)

        assert len(findings) == 1
        assert findings[0]["category"] == "conftest-missing-fixture"
