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
        "eventbus_db_path",
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
        "print(cfg.rag_db_path, cfg.workflow_db_path, cfg.eventbus_db_path)\n"
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
