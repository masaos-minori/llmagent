"""Tests that the test run is isolated from production state under /opt/llm.

Every probe that could create a production file uses a directory that does not
exist under /opt/llm: if the guard were missing, SQLite or the file handler would
fail to open instead of creating anything.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader
from shared.logger import Logger

_PROBE = "/opt/llm/__guard_probe__/x"
_PRODUCTION = "/opt/llm"


def _root() -> Path:
    return Path(os.environ["LLMAGENT_CONFIG_DIR"]).parent


def test_temporary_root_is_outside_production() -> None:
    root = _root()
    assert root.is_dir()
    assert not str(root).startswith(_PRODUCTION)


def test_config_loader_paths_are_redirected() -> None:
    cfg = ConfigLoader().load("agent.toml")
    root = str(_root())
    checked = 0
    for key in (
        "rag_db_path",
        "session_db_path",
        "workflow_db_path",
        "sqlite_archive_dir",
    ):
        if key in cfg:
            assert cfg[key].startswith(root), f"{key} = {cfg[key]}"
            checked += 1
    assert checked >= 2
    assert cfg["memory_jsonl_dir"].startswith(root)
    assert cfg["sqlite_vec_so"] == "/opt/llm/sqlite-vec/vec0.so"


def test_session_helper_resolves_under_temporary_root() -> None:
    assert SQLiteHelper("session").DB_PATH.startswith(str(_root()))


def test_logger_path_is_redirected() -> None:
    logger = Logger(f"isolation-{uuid.uuid4().hex}", "/opt/llm/logs/probe-dir/x.log")
    handler = next(
        h for h in logger._logger.handlers if isinstance(h, logging.FileHandler)
    )
    try:
        log_dir = Path(os.environ["LLMAGENT_LOG_DIR"])
        assert Path(handler.baseFilename) == log_dir / "probe-dir" / "x.log"
    finally:
        logger._logger.removeHandler(handler)
        handler.close()


def test_guard_rejects_production_sqlite_connect() -> None:
    with pytest.raises(AssertionError, match="/opt/llm"):
        sqlite3.connect(_PROBE + ".sqlite")


def test_guard_rejects_production_file_handler() -> None:
    with pytest.raises(AssertionError, match="/opt/llm"):
        logging.FileHandler(_PROBE + ".log")


@pytest.mark.production_paths_allowed
def test_opt_out_marker_skips_guard() -> None:
    with pytest.raises(sqlite3.OperationalError):
        sqlite3.connect(_PROBE + ".sqlite")


def test_cleanup_removes_the_root(tmp_path: Path) -> None:
    from tests.conftest import _cleanup_isolated_root

    root = tmp_path / "root"
    (root / "nested").mkdir(parents=True)
    _cleanup_isolated_root(root)
    assert not root.exists()


def test_collection_check_flags_production_handler(tmp_path: Path) -> None:
    from tests.conftest import _production_file_handlers

    assert _production_file_handlers() == []
    handler = logging.FileHandler(tmp_path / "h.log")
    handler.baseFilename = "/opt/llm/logs/fake.log"
    logger = logging.getLogger(f"isolation-check-{uuid.uuid4().hex}")
    logger.addHandler(handler)
    try:
        assert handler in _production_file_handlers()
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_conftest_imports_on_host_without_production_db_dir() -> None:
    """The isolation setup must not need /opt/llm/db to exist (CI runner case).

    Runs conftest in a child process with only that directory hidden from
    Path.exists, so DbConfig's parent-directory check sees what a runner sees.
    """
    repo = Path(__file__).resolve().parent.parent
    code = (
        "import os, pathlib, runpy\n"
        "orig = pathlib.Path.exists\n"
        "pathlib.Path.exists = lambda self, *a, **k: (\n"
        "    False if str(self) == '/opt/llm/db' else orig(self, *a, **k)\n"
        ")\n"
        "os.environ.pop('LLMAGENT_TEST_ROOT', None)\n"
        "runpy.run_path('tests/conftest.py', run_name='conftest_probe')\n"
        "from db.config import DbConfig\n"
        "cfg = DbConfig(rag_db_path='/opt/llm/db/rag.sqlite', session_db_path='/tmp/s')\n"
        "print(cfg.rag_db_path, cfg.workflow_db_path)\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-800:]
    # A DbConfig built directly with production defaults is redirected as well.
    assert "/opt/llm" not in result.stdout, result.stdout


def test_xdist_worker_builds_its_own_root_and_children_reuse_it() -> None:
    """A worker builds its own root; a process it spawns reuses it (REQ-003).

    Inject a worker id that does not match the parent's recorded owner, so the
    child must build a fresh root rather than reuse the parent's. The child then
    records itself as owner and its grandchild, inheriting both variables, reuses
    the child's root.
    """
    repo = Path(__file__).resolve().parent.parent
    # xdist names workers gw0..gw(N-1); "gw999" can never equal a real parent
    # owner for any realistic worker count, so the child's owner mismatch is
    # deterministic and the test is not flaky on an 8-CPU host.
    FOREIGN_WORKER = "gw999"
    grandchild_code = (
        "import os, runpy\n"
        "runpy.run_path('tests/conftest.py', run_name='grandchild_probe')\n"
        "print(os.environ['LLMAGENT_TEST_ROOT'])\n"
    )
    code = (
        "import os, runpy, subprocess, sys\n"
        "runpy.run_path('tests/conftest.py', run_name='conftest_probe')\n"
        "print(os.environ['LLMAGENT_TEST_ROOT'])\n"
        f"gc = {grandchild_code!r}\n"
        "r = subprocess.run([sys.executable, '-I', '-c', gc], env=os.environ, "
        "capture_output=True, text=True, timeout=120)\n"
        "print(r.stdout.strip())\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=repo,
        env={
            **os.environ,
            "PYTEST_XDIST_WORKER": FOREIGN_WORKER,
            "LLMAGENT_TEST_ROOT": str(_root()),
        },
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-800:]
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    assert len(lines) == 2, result.stdout
    child_root = Path(lines[0])
    grandchild_root = Path(lines[1])
    parent_root = _root()
    # The parent itself runs inside an isolation root created by mkdtemp.
    assert Path(parent_root).name.startswith("llmagent-test-")
    # The child's worker id does not match the parent's owner, so it builds
    # a fresh root distinct from the parent's.
    assert child_root != parent_root
    assert Path(child_root).name.startswith("llmagent-test-")
    assert not str(child_root).startswith(_PRODUCTION)
    # The grandchild inherits owner == worker_id and reuses the child's root.
    assert grandchild_root == child_root
    assert not str(grandchild_root).startswith(_PRODUCTION)


def _stand_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the session check at a temporary directory holding two stand-in files."""
    from tests import conftest as conftest_module

    directory = tmp_path / "db"
    directory.mkdir()
    (directory / "a.sqlite").write_bytes(b"main-v1")
    (directory / "a.sqlite-wal").write_bytes(b"wal-v1")
    monkeypatch.setattr(conftest_module, "_PRODUCTION_DB_DIR", directory)
    monkeypatch.setattr(conftest_module, "_db_baseline", None)
    conftest_module._refresh_db_baseline()
    return directory


def test_unchanged_directory_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    _stand_in(tmp_path, monkeypatch)
    conftest_module._assert_production_db_unchanged()


def test_changed_file_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    directory = _stand_in(tmp_path, monkeypatch)
    (directory / "a.sqlite").write_bytes(b"main-v2")
    with pytest.raises(pytest.fail.Exception, match=r"a\.sqlite \(changed\)"):
        conftest_module._assert_production_db_unchanged()


def test_sidecar_only_change_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    directory = _stand_in(tmp_path, monkeypatch)
    (directory / "a.sqlite-wal").write_bytes(b"wal-v2")
    with pytest.raises(pytest.fail.Exception, match=r"a\.sqlite-wal \(changed\)"):
        conftest_module._assert_production_db_unchanged()


def test_added_file_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    directory = _stand_in(tmp_path, monkeypatch)
    (directory / "a.sqlite-shm").write_bytes(b"shm")
    with pytest.raises(pytest.fail.Exception, match=r"a\.sqlite-shm \(added\)"):
        conftest_module._assert_production_db_unchanged()


def test_removed_file_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    directory = _stand_in(tmp_path, monkeypatch)
    (directory / "a.sqlite-wal").unlink()
    with pytest.raises(pytest.fail.Exception, match=r"a\.sqlite-wal \(removed\)"):
        conftest_module._assert_production_db_unchanged()


def test_absent_directory_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    monkeypatch.setattr(conftest_module, "_PRODUCTION_DB_DIR", tmp_path / "missing")
    monkeypatch.setattr(conftest_module, "_db_baseline", {"x": (1, 1, "h")})
    conftest_module._refresh_db_baseline()
    assert conftest_module._db_baseline is None
    conftest_module._assert_production_db_unchanged()


def test_refresh_accepts_prior_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest as conftest_module

    directory = _stand_in(tmp_path, monkeypatch)
    (directory / "a.sqlite").write_bytes(b"main-v2")
    conftest_module._refresh_db_baseline()
    conftest_module._assert_production_db_unchanged()


def test_fingerprint_does_not_create_sidecars(tmp_path: Path) -> None:
    from tests import conftest as conftest_module

    directory = tmp_path / "db"
    directory.mkdir()
    conn = sqlite3.connect(directory / "real.sqlite")
    try:
        conn.execute("CREATE TABLE t (x)")
        conn.commit()
    finally:
        conn.close()
    before = sorted(p.name for p in directory.iterdir())
    fingerprint = conftest_module._fingerprint_directory(directory)
    assert sorted(fingerprint) == before
    assert sorted(p.name for p in directory.iterdir()) == before


_CHILD_TEST = (
    "from pathlib import Path\n"
    "import pytest\n"
    "from tests import conftest as c\n"
    "\n"
    "c._PRODUCTION_DB_DIR = Path({stand_in!r})\n"
    "{marker}\n"
    "def test_touch() -> None:\n"
    "    (c._PRODUCTION_DB_DIR / 'victim.sqlite').write_bytes(b'changed')\n"
)


def _run_child_session(tmp_path: Path, marker: str) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parent.parent
    stand_in = tmp_path / "standin"
    stand_in.mkdir()
    (stand_in / "victim.sqlite").write_bytes(b"original")
    test_file = tmp_path / "test_child_touch.py"
    test_file.write_text(
        _CHILD_TEST.format(stand_in=str(stand_in), marker=marker), encoding="utf-8"
    )
    env = {**os.environ, "PYTHONPATH": str(repo)}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.conftest",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            "-p",
            "no:testmon",
            str(test_file),
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_session_fails_when_standin_changes(tmp_path: Path) -> None:
    result = _run_child_session(tmp_path, "")
    output = result.stdout + result.stderr
    assert result.returncode != 0, output[-1500:]
    assert "session changed production database files" in output, output[-1500:]
    assert "victim.sqlite (changed)" in output, output[-1500:]


def test_opt_out_marker_does_not_fail_session(tmp_path: Path) -> None:
    result = _run_child_session(tmp_path, "@pytest.mark.production_paths_allowed")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output[-1500:]
