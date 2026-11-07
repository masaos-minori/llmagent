"""tests/tools/test_module_nodes_extract_atomic.py
`module_nodes.py extract`: output identical on success, `--dry-run` writes nothing, and
a failure at any point never loses moved code.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from tools import _atomic_write, module_nodes

SRC = "import os\n\n\ndef alpha():\n    return 1\n\n\ndef gamma():\n    return 3\n"
DEST_OLD = "def old():\n    return 0\n"
SRC_AFTER = "import os\n\n\n\n\ndef gamma():\n    return 3\n"
SRC_DECORATED = (
    "@decorator\n\n\ndef alpha():\n    return 1\n\n\ndef gamma():\n    return 3\n"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(tmp_path: Path, dest_text: str | None) -> tuple[Path, Path]:
    src = tmp_path / "src.py"
    dest = tmp_path / "dest.py"
    src.write_text(SRC, encoding="utf-8")
    if dest_text is not None:
        dest.write_text(dest_text, encoding="utf-8")
    return src, dest


def _extract(src: Path, dest: Path, *extra: str) -> int:
    return module_nodes.main(
        ["extract", "--src", str(src), "--dest", str(dest), "--name", "alpha", *extra]
    )


def _leftovers(tmp_path: Path) -> list[str]:
    return sorted(p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp"))


def _fail_nth_replace(monkeypatch: pytest.MonkeyPatch, nth: int) -> list[int]:
    calls: list[int] = []
    real = _atomic_write.os.replace

    def fake(a: Any, b: Any) -> None:
        calls.append(1)
        if len(calls) == nth:
            raise OSError("replace failed")
        real(a, b)

    monkeypatch.setattr(_atomic_write.os, "replace", fake)
    return calls


def test_success_with_a_new_destination_is_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest = _files(tmp_path, None)

    assert _extract(src, dest) == 0

    out = capsys.readouterr().out.replace(str(tmp_path), "<T>")
    assert out == (
        "moved 1 nodes -> <T>/dest.py\n  alpha\n"
        "<T>/src.py: 7 lines, 40 B\n<T>/dest.py: 2 lines, 26 B\n"
    )
    assert src.read_text(encoding="utf-8") == SRC_AFTER
    assert dest.read_text(encoding="utf-8") == "def alpha():\n    return 1\n"
    assert _leftovers(tmp_path) == []


def test_success_with_an_existing_destination_is_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest = _files(tmp_path, DEST_OLD)

    assert _extract(src, dest) == 0

    out = capsys.readouterr().out.replace(str(tmp_path), "<T>")
    assert out.endswith("<T>/src.py: 7 lines, 40 B\n<T>/dest.py: 6 lines, 52 B\n")
    assert dest.read_text(encoding="utf-8") == (
        "def old():\n    return 0\n\n\ndef alpha():\n    return 1\n"
    )


@pytest.mark.parametrize("dest_text", [None, DEST_OLD])
def test_dry_run_writes_nothing_and_returns_zero(
    tmp_path: Path, dest_text: str | None, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest = _files(tmp_path, dest_text)
    before = (_sha(src), _sha(dest) if dest.exists() else None)

    assert _extract(src, dest, "--dry-run") == 0

    assert (_sha(src), _sha(dest) if dest.exists() else None) == before
    assert "+def alpha" in capsys.readouterr().out
    assert _leftovers(tmp_path) == []


def test_failure_while_staging_leaves_both_files_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src, dest = _files(tmp_path, DEST_OLD)
    before = (_sha(src), _sha(dest))
    real = _atomic_write.tempfile.mkstemp
    count: list[int] = []

    def fake(*args: Any, **kwargs: Any) -> tuple[int, str]:
        count.append(1)
        if len(count) == 2:
            raise OSError("no space")
        return real(*args, **kwargs)

    monkeypatch.setattr(_atomic_write.tempfile, "mkstemp", fake)

    assert _extract(src, dest) == 1
    assert (_sha(src), _sha(dest)) == before
    assert _leftovers(tmp_path) == []


def test_failure_of_the_first_replace_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src, dest = _files(tmp_path, DEST_OLD)
    before = (_sha(src), _sha(dest))
    _fail_nth_replace(monkeypatch, 1)

    assert _extract(src, dest) == 1
    assert (_sha(src), _sha(dest)) == before
    assert _leftovers(tmp_path) == []


def test_failed_source_replace_restores_an_existing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest = _files(tmp_path, DEST_OLD)
    src_before = _sha(src)
    _fail_nth_replace(monkeypatch, 2)

    assert _extract(src, dest) == 1

    assert dest.read_text(encoding="utf-8") == DEST_OLD
    assert _sha(src) == src_before
    assert "replace failed" in capsys.readouterr().err
    assert _leftovers(tmp_path) == []


def test_failed_source_replace_removes_a_destination_it_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src, dest = _files(tmp_path, None)
    src_before = _sha(src)
    _fail_nth_replace(monkeypatch, 2)

    assert _extract(src, dest) == 1

    assert not dest.exists()
    assert _sha(src) == src_before


def test_failed_restore_reports_both_paths_and_keeps_the_moved_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest = _files(tmp_path, DEST_OLD)
    _fail_nth_replace(monkeypatch, 2)

    def failing_restore(*_: object, **__: object) -> None:
        raise OSError("restore failed")

    monkeypatch.setattr(module_nodes, "atomic_write_text", failing_restore)

    assert _extract(src, dest) == 1

    err = capsys.readouterr().err
    assert str(src) in err
    assert str(dest) in err
    assert "both" in err
    assert "def alpha" in src.read_text(encoding="utf-8")
    assert "def alpha" in dest.read_text(encoding="utf-8")


def test_decorated_node_moves_with_decorator_atomically(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "src.py"
    dest = tmp_path / "dest.py"
    src.write_text(SRC_DECORATED, encoding="utf-8")

    assert (
        module_nodes.main(
            ["extract", "--src", str(src), "--dest", str(dest), "--name", "alpha"]
        )
        == 0
    )

    dest_text = dest.read_text(encoding="utf-8")
    src_text = src.read_text(encoding="utf-8")
    assert "@decorator" in dest_text
    assert "def alpha()" in dest_text
    assert "@decorator" not in src_text
    assert _leftovers(tmp_path) == []
