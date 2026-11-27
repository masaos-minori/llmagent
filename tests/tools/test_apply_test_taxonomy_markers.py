"""tests/tools/test_apply_test_taxonomy_markers.py
Tests for tools/apply_test_taxonomy_markers.py: writing the taxonomy markers a procedure names.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

TOOL = (
    Path(__file__).resolve().parent.parent.parent
    / "tools"
    / "apply_test_taxonomy_markers.py"
)


@pytest.fixture(autouse=True)
def _cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run each test from its own directory, restored afterwards so no later test inherits it."""
    monkeypatch.chdir(tmp_path)
    yield


def _module(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _records(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    path = tmp_path / "records.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def _run(records: Path, dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(TOOL), str(records)]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def test_writes_the_module_marker_and_the_recorded_test_markers(tmp_path: Path) -> None:
    module = _module(
        tmp_path,
        "test_mixed.py",
        "import pytest\n\n\nclass TestCited:\n    def test_cited(self) -> None:\n        pass\n\n\nclass TestRecorded:\n    def test_recorded(self) -> None:\n        pass\n",
    )
    records = _records(
        tmp_path,
        [{"path": "test_mixed.py", "pytestmark": "contract", "tests": [10]}],
    )

    code = _run(records)

    assert code.returncode == 0
    text = module.read_text(encoding="utf-8")
    assert text.splitlines()[2] == "pytestmark = pytest.mark.contract"
    assert text.splitlines()[11] == "    @pytest.mark.characterization"
    assert text.splitlines()[12] == "    def test_recorded(self) -> None:"


def test_add_import_places_pytest_after_the_future_import(tmp_path: Path) -> None:
    module = _module(
        tmp_path,
        "test_char.py",
        '"""Characterization tests."""\n\nfrom __future__ import annotations\n\nfrom shared.x import y\n\n\ndef test_observed() -> None:\n    assert y\n',
    )
    records = _records(
        tmp_path,
        [
            {
                "path": "test_char.py",
                "pytestmark": "characterization",
                "add_import": True,
                "tests": [],
            }
        ],
    )

    code = _run(records)

    assert code.returncode == 0
    lines = module.read_text(encoding="utf-8").splitlines()
    assert lines[4] == "import pytest"
    assert lines[7] == "pytestmark = pytest.mark.characterization"


def test_an_existing_marker_refuses_the_record(tmp_path: Path) -> None:
    module = _module(
        tmp_path,
        "test_classified.py",
        "import pytest\n\npytestmark = pytest.mark.contract\n\n\ndef test_cited() -> None:\n    pass\n",
    )
    records = _records(
        tmp_path,
        [{"path": "test_classified.py", "pytestmark": "contract", "tests": []}],
    )

    code = _run(records)

    assert code.returncode == 1
    assert "already carries" in code.stderr
    assert "pytestmark = pytest.mark.characterization" not in module.read_text(
        encoding="utf-8"
    )


def test_a_recorded_line_that_is_not_a_test_definition_refuses(tmp_path: Path) -> None:
    module = _module(
        tmp_path,
        "test_drift.py",
        "import pytest\n\n\nclass TestCited:\n    def helper(self) -> None:\n        pass\n",
    )
    records = _records(
        tmp_path,
        [{"path": "test_drift.py", "pytestmark": "contract", "tests": [5]}],
    )

    code = _run(records)

    assert code.returncode == 1
    assert "not a test function definition" in code.stderr
    assert "pytest.mark" not in module.read_text(encoding="utf-8")


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = _module(
        tmp_path,
        "test_dry.py",
        "import pytest\n\n\ndef test_cited() -> None:\n    pass\n",
    )
    records = _records(
        tmp_path, [{"path": "test_dry.py", "pytestmark": "contract", "tests": []}]
    )

    code = _run(records, dry_run=True)

    assert code.returncode == 0
    assert "pytestmark" not in module.read_text(encoding="utf-8")
    assert "-" in code.stdout


def test_a_malformed_records_file_exits_2(tmp_path: Path) -> None:
    records = tmp_path / "records.json"
    records.write_text("{}", encoding="utf-8")

    code = _run(records)

    assert code.returncode == 2
    assert "expected a non-empty array" in code.stderr
