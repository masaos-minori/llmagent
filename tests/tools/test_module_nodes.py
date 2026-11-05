"""Tests for tools/module_nodes.py: measure, extract, and compare."""

from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path
from typing import Any

import pytest

from tools import module_nodes
from tools.module_nodes import _extract_lines, main, measure

SAMPLE = '''\
import os
from pathlib import Path

LIMIT = 10


def alpha():
    """Return a non-ASCII label: é."""
    return 1


class Beta:
    def method(self):
        return 2


def gamma():
    return 3
'''
SAMPLE_ASCII = SAMPLE.replace("é", "e")
ALPHA_TEXT = 'def alpha():\n    """Return a non-ASCII label: e."""\n    return 1\n'
GAMMA_TEXT = "def gamma():\n    return 3\n"


def _forbidden_run(*args: object, **kwargs: object) -> None:
    raise AssertionError("module_nodes must not run a real subprocess in tests")


@pytest.fixture(autouse=True)
def _no_real_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        module_nodes, "subprocess", types.SimpleNamespace(run=_forbidden_run)
    )


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _fake_git(
    monkeypatch: pytest.MonkeyPatch, old_source: str
) -> list[tuple[list[str], dict[str, Any]]]:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout=old_source, stderr="")

    monkeypatch.setattr(module_nodes, "subprocess", types.SimpleNamespace(run=fake_run))
    return calls


# --- measure ---


def test_measure_skips_imports_and_reports_spans(tmp_path: Path) -> None:
    src = _write(tmp_path, "m.py", SAMPLE)
    rows = measure(src, 0)
    assert [(r["name"], r["start"], r["end"], r["span"], r["kind"]) for r in rows] == [
        ("Assign", 4, 4, 1, "Assign"),
        ("alpha", 7, 9, 3, "FunctionDef"),
        ("Beta", 12, 14, 3, "ClassDef"),
        ("gamma", 17, 18, 2, "FunctionDef"),
    ]


def test_measure_counts_encoded_bytes(tmp_path: Path) -> None:
    src = _write(tmp_path, "m.py", SAMPLE)
    alpha = next(r for r in measure(src, 0) if r["name"] == "alpha")
    joined = "\n".join(SAMPLE.splitlines()[6:9])
    assert alpha["bytes"] == len(joined.encode("utf-8"))
    assert alpha["bytes"] > len(joined)


def test_measure_min_filters_small_nodes(tmp_path: Path) -> None:
    src = _write(tmp_path, "m.py", SAMPLE)
    rows = measure(src, 0)
    biggest = max(int(str(r["bytes"])) for r in rows)
    kept = measure(src, biggest)
    assert kept and all(r["bytes"] == biggest for r in kept)
    assert measure(src, biggest + 1) == []


def test_measure_json_output_matches_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = _write(tmp_path, "m.py", SAMPLE)
    assert main(["measure", str(src), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == measure(src, 0)


def test_measure_text_report_ends_with_file_total(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = _write(tmp_path, "m.py", SAMPLE)
    assert main(["measure", str(src)]) == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert out.splitlines()[-1] == f"file total: {len(SAMPLE.encode('utf-8'))}B"


def test_measure_missing_file_returns_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["measure", str(tmp_path / "nope.py")]) == 1
    assert "not found" in capsys.readouterr().err


# --- extract ---


def _extract(tmp_path: Path, *extra: str) -> tuple[Path, Path, int]:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    dest = tmp_path / "dest.py"
    rc = main(["extract", "--src", str(src), "--dest", str(dest), *extra])
    return src, dest, rc


def test_extract_by_name_moves_exact_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest, rc = _extract(tmp_path, "--name", "alpha")
    lines = SAMPLE_ASCII.splitlines(keepends=True)
    assert rc == 0
    assert dest.read_text(encoding="utf-8") == ALPHA_TEXT
    assert src.read_text(encoding="utf-8") == "".join(lines[:6] + lines[9:])
    assert f"moved 1 nodes -> {dest}" in capsys.readouterr().out


def test_extract_appends_to_an_existing_destination(tmp_path: Path) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    dest = _write(tmp_path, "dest.py", "X = 1\n")
    assert (
        main(["extract", "--src", str(src), "--dest", str(dest), "--name", "alpha"])
        == 0
    )
    assert dest.read_text(encoding="utf-8") == "X = 1\n\n\n" + ALPHA_TEXT


def test_extract_moves_several_names_in_the_requested_order(tmp_path: Path) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    kept, segments = _extract_lines(src, ["gamma", "alpha"], [], dedent=False)
    assert segments == [GAMMA_TEXT, ALPHA_TEXT]
    assert "def alpha" not in "".join(kept)
    assert "def gamma" not in "".join(kept)
    assert "class Beta" in "".join(kept)


def test_extract_range_keeps_indent_without_dedent(tmp_path: Path) -> None:
    _, dest, rc = _extract(tmp_path, "--range", "13-14")
    assert rc == 0
    assert (
        dest.read_text(encoding="utf-8") == "    def method(self):\n        return 2\n"
    )


def test_extract_range_with_dedent_removes_one_indent_level(tmp_path: Path) -> None:
    src, dest, rc = _extract(tmp_path, "--range", "13-14", "--dedent")
    assert rc == 0
    assert dest.read_text(encoding="utf-8") == "def method(self):\n    return 2\n"
    assert "def method" not in src.read_text(encoding="utf-8")


def test_extract_dedent_refuses_a_less_indented_line(tmp_path: Path) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    dest = tmp_path / "dest.py"
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "extract",
                "--src",
                str(src),
                "--dest",
                str(dest),
                "--range",
                "12-14",
                "--dedent",
            ]
        )
    assert "cannot --dedent" in str(excinfo.value.code)
    assert not dest.exists()
    assert src.read_text(encoding="utf-8") == SAMPLE_ASCII


def test_extract_unknown_name_exits_with_an_error(tmp_path: Path) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    dest = tmp_path / "dest.py"
    with pytest.raises(SystemExit) as excinfo:
        main(["extract", "--src", str(src), "--dest", str(dest), "--name", "nothere"])
    assert "not top-level nodes" in str(excinfo.value.code)
    assert "nothere" in str(excinfo.value.code)
    assert not dest.exists()


def test_extract_without_a_selector_exits_with_an_error(tmp_path: Path) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    with pytest.raises(SystemExit) as excinfo:
        main(["extract", "--src", str(src), "--dest", str(tmp_path / "dest.py")])
    assert "pass at least one" in str(excinfo.value.code)


@pytest.mark.parametrize(
    ("raw", "message"), [("5-2", "invalid --range"), ("abc", "expects START-END")]
)
def test_extract_rejects_a_bad_range(tmp_path: Path, raw: str, message: str) -> None:
    src = _write(tmp_path, "src.py", SAMPLE_ASCII)
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "extract",
                "--src",
                str(src),
                "--dest",
                str(tmp_path / "d.py"),
                "--range",
                raw,
            ]
        )
    assert message in str(excinfo.value.code)


# --- compare ---


def _compare(
    tmp_path: Path, new_source: str, *extra: str, old_src: str = "svc.py"
) -> int:
    new = _write(tmp_path, "new.py", new_source)
    return main(
        [
            "compare",
            "--old-src",
            old_src,
            "--new-src",
            str(new),
            "--name",
            "helper",
            *extra,
        ]
    )


OLD_METHOD = "class Svc:\n    def _helper(self, x):\n        return x + 1\n"


def test_compare_identical_move_returns_0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _fake_git(monkeypatch, OLD_METHOD)
    rc = _compare(tmp_path, "def helper(x):\n    return x + 1\n")
    out = capsys.readouterr().out
    assert rc == 0
    assert "identical" in out
    assert "moved functions compared: 1, differing: 0" in out
    assert calls[0][0] == ["git", "show", "HEAD:svc.py"]
    assert calls[0][1]["check"] is True


def test_compare_uses_the_given_old_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _fake_git(monkeypatch, OLD_METHOD)
    _compare(tmp_path, "def helper(x):\n    return x + 1\n", "--old-rev", "abc123")
    assert calls[0][0] == ["git", "show", "abc123:svc.py"]


def test_compare_changed_body_returns_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fake_git(monkeypatch, OLD_METHOD)
    rc = _compare(tmp_path, "def helper(x):\n    return x + 2\n")
    out = capsys.readouterr().out
    assert rc == 1
    assert "DIFFERS" in out
    assert "  old:" in out
    assert "  new:" in out
    assert "differing: 1" in out


def test_compare_missing_function_returns_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fake_git(monkeypatch, OLD_METHOD)
    rc = _compare(tmp_path, "def other(x):\n    return x\n")
    out = capsys.readouterr().out
    assert rc == 1
    assert "MISSING (old=True, new=False)" in out


def test_compare_param_option_ignores_the_injected_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = "class Svc:\n    def helper(self, data):\n        return self._send(data)\n"
    new = "def helper(data, timeout):\n    return send(data, timeout)\n"
    _fake_git(monkeypatch, old)
    assert _compare(tmp_path, new, "--old-class", "Svc") == 1
    assert _compare(tmp_path, new, "--old-class", "Svc", "--param", "timeout") == 0


def test_the_autouse_guard_blocks_unfaked_git(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="must not run a real subprocess"):
        _compare(tmp_path, "def helper(x):\n    return x\n")
