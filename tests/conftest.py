"""
Shared pytest fixtures for the llmagent test suite.
Adds scripts/ to sys.path so all project modules are importable without installation.

Isolation from production state: this host's repository configuration points at
/opt/llm, so without isolation the suite writes test data into the production
session database and logs. At import time this module builds a temporary root with a
copy of config/ and schemas/ (writable-state paths rewritten into the root) and sets
LLMAGENT_CONFIG_DIR, EVENTBUS_CONFIG_PATH, EVENTBUS_SCHEMA_PATH, and LLMAGENT_LOG_DIR
(read by shared.logger). An autouse guard fails a test that opens a SQLite database or
a FileHandler under /opt/llm unless the test carries the marker
``production_paths_allowed``.
"""

import atexit
import logging
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# scripts/ and tools/ are not installed packages; add them to sys.path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

# ── Isolation from production state under /opt/llm ──────────────────────────────
# Set at import time, not in a fixture: Logger instances and several MCP server modules
# read configuration while scripts/ modules are imported during collection.

_PRODUCTION_ROOT = "/opt/llm"
# Only writable-state paths are rewritten; read-only resources (bin, sqlite-vec, docs,
# venv) keep their real paths because tests load the real extension and validate them.
_WRITABLE_STATE_RE = re.compile(
    r"/opt/llm/(db|storage|offsets|deadletter|rag-src|logs|memory)\b"
)
_CREATED_ROOT: Path | None = None


def _cleanup_isolated_root(root: Path) -> None:
    """Remove the temporary isolation root."""
    shutil.rmtree(root, ignore_errors=True)


def _build_isolated_root() -> Path:
    """Copy config/ and schemas/ into a temporary root with state paths rewritten."""
    repo = Path(__file__).resolve().parent.parent
    root = Path(tempfile.mkdtemp(prefix="llmagent-test-"))
    shutil.copytree(repo / "config", root / "config")
    shutil.copytree(repo / "schemas", root / "schemas")
    rewritten = re.compile(
        re.escape(str(root))
        + r"/(?:db|storage|offsets|deadletter|rag-src|logs|memory)[^\s\"']*"
    )
    for toml_file in (root / "config").rglob("*.toml"):
        text = _WRITABLE_STATE_RE.sub(
            lambda m: f"{root}/{m.group(1)}", toml_file.read_text(encoding="utf-8")
        )
        toml_file.write_text(text, encoding="utf-8")
        for match in rewritten.finditer(text):
            path = Path(match.group(0))
            (path.parent if path.suffix else path).mkdir(parents=True, exist_ok=True)
    for name in ("db", "logs", "memory", "storage", "offsets", "deadletter"):
        (root / name).mkdir(exist_ok=True)
    return root


_VEC_TABLE_RE = re.compile(
    r"CREATE VIRTUAL TABLE IF NOT EXISTS \w+ USING vec0\(.*?\);", re.DOTALL
)


def _provision_databases() -> None:
    """Create empty, initialized databases in the isolation root.

    Production databases exist with their schema (deploy/init_db.sh), and many tests
    were written against that. The isolation root starts empty, so create the same
    schemas the same way. Without the sqlite-vec extension (for example on CI), the
    vec0 tables are skipped so the remaining tables still exist.
    """
    from db import create_schema
    from db.config import build_db_config
    from db.schema_sql import build_rag_schema_sql, build_session_schema_sql
    from db.store_protocols import get_embedding_dims

    create_schema.create_workflow_schema()
    create_schema.create_eventbus_schema()
    cfg = build_db_config()
    for create, build_sql, db_path in (
        (
            create_schema.create_session_schema,
            build_session_schema_sql,
            cfg.session_db_path,
        ),
        (create_schema.create_rag_schema, build_rag_schema_sql, cfg.rag_db_path),
    ):
        try:
            create()
        except (sqlite3.OperationalError, ValueError):
            # sqlite-vec is unavailable: create the schema without the vec0 tables.
            sql = _VEC_TABLE_RE.sub("", build_sql(get_embedding_dims()))
            conn = sqlite3.connect(db_path)
            try:
                conn.executescript(sql)
            finally:
                conn.close()


def _isolate_db_config(root: Path) -> None:
    """Point every production DB path that DbConfig receives into the isolation root.

    agent.toml does not set workflow_db_path (the production config validator rejects
    the key), so build_db_config() falls back to a production default in code, and
    tests build DbConfig directly with some paths left at their defaults. DbConfig
    refuses to be built when a path's parent directory is missing, which is the case
    on a host without /opt/llm/db (such as the CI runner). The rewrite therefore runs
    inside DbConfig.__post_init__, before that validation, and covers both routes.
    """
    import db.config as db_config

    production_db_dir = "/opt/llm/db/"
    isolated_db_dir = f"{root}/db/"
    original_post_init = db_config.DbConfig.__post_init__

    def post_init_isolated(self: Any) -> None:
        for field in (
            "rag_db_path",
            "session_db_path",
            "workflow_db_path",
            "eventbus_db_path",
        ):
            value = getattr(self, field)
            if isinstance(value, str) and value.startswith(production_db_dir):
                object.__setattr__(
                    self, field, isolated_db_dir + value[len(production_db_dir) :]
                )
        original_post_init(self)

    setattr(db_config.DbConfig, "__post_init__", post_init_isolated)


def _setup_isolation() -> Path:
    """Create the isolation root once per process tree and set the environment."""
    global _CREATED_ROOT
    existing = os.environ.get("LLMAGENT_TEST_ROOT")
    created = not (existing and Path(existing).is_dir())
    if created:
        root = _build_isolated_root()
        os.environ["LLMAGENT_TEST_ROOT"] = str(root)
        _CREATED_ROOT = root
        atexit.register(_cleanup_isolated_root, root)
    else:
        root = Path(str(existing))
    os.environ["LLMAGENT_CONFIG_DIR"] = str(root / "config")
    os.environ["EVENTBUS_CONFIG_PATH"] = str(root / "config" / "eventbus.toml")
    os.environ["EVENTBUS_SCHEMA_PATH"] = str(root / "schemas" / "event_envelope.json")
    os.environ["LLMAGENT_LOG_DIR"] = str(root / "logs")
    _isolate_db_config(root)
    if created:
        _provision_databases()
    return root


_ISOLATED_ROOT = _setup_isolation()


def _is_production_path(path: object) -> bool:
    """Return True when ``path`` resolves to /opt/llm or below."""
    if not isinstance(path, str | bytes | os.PathLike):
        return False
    text = os.fsdecode(path)
    if not text or text.startswith(("file:", ":memory:")):
        return False
    resolved = os.path.realpath(text)
    return resolved == _PRODUCTION_ROOT or resolved.startswith(_PRODUCTION_ROOT + "/")


def _production_file_handlers() -> list[logging.FileHandler]:
    """Return FileHandlers of registered loggers whose file is under /opt/llm."""
    loggers: list[logging.Logger] = [logging.getLogger()]
    loggers.extend(
        obj
        for obj in list(logging.Logger.manager.loggerDict.values())
        if isinstance(obj, logging.Logger)
    )
    return [
        handler
        for logger in loggers
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler)
        and _is_production_path(handler.baseFilename)
    ]


def pytest_configure(config: pytest.Config) -> None:
    """Register the opt-out marker for tests that must use a real production path."""
    config.addinivalue_line(
        "markers",
        "production_paths_allowed: skip the guard that fails a test opening a "
        "database or log file under /opt/llm",
    )


def pytest_collection_finish(session: pytest.Session) -> None:
    """Stop the run if a logger created during collection points at production."""
    offenders = _production_file_handlers()
    if offenders:
        files = ", ".join(sorted({h.baseFilename for h in offenders}))
        pytest.exit(
            f"Loggers created during collection write to production files: {files}",
            returncode=3,
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Remove the isolation root created by this process."""
    if _CREATED_ROOT is not None:
        _cleanup_isolated_root(_CREATED_ROOT)


# config/agent.toml's own [mcp.mcp_servers.*] table references the same
# ${ENV:...} pattern for every subprocess-started server's auth_token,
# resolved by build_agent_config() -> shared.mcp_config._build_single_server().
# McpServerConfig requires a non-empty auth_token (production-strict validation),
# and every MCP server module refuses to import with an empty token, so all ten
# tokens need a real (dummy) value rather than "". web_search shares its variable
# with the agent configuration, like git and cicd. Tests that call
# build_agent_config() against the real agent.toml (e.g.
# tests/agent/test_mcp_server_cmd_paths.py) need all of these set.
for _mcp_env_var in (
    "MCP_SHELL_AUTH_TOKEN",
    "MCP_FILE_DELETE_AUTH_TOKEN",
    "MCP_FILE_WRITE_AUTH_TOKEN",
    "MCP_FILE_READ_AUTH_TOKEN",
    "MCP_GITHUB_AUTH_TOKEN",
    "MCP_RAG_PIPELINE_AUTH_TOKEN",
    "MCP_MDQ_AUTH_TOKEN",
    "MCP_GIT_AUTH_TOKEN",
    "MCP_CICD_AUTH_TOKEN",
    "MCP_WEB_SEARCH_AUTH_TOKEN",
):
    os.environ.setdefault(_mcp_env_var, "test-token")

# shell-mcp builds its sandbox when mcp_servers.shell is first imported (the package
# __init__ imports shell_server, which calls build_service()), and that raises
# RuntimeError when the firejail binary is not in PATH. Hosts without firejail (the CI
# runner) therefore fail at collection, before any fixture can patch it. Report firejail
# as present only when it is really absent, so the import succeeds and no test depends
# on the host; tests that exercise the missing-binary path patch shutil.which themselves.
# Production code is unchanged, so the fail-closed startup rule (ADR-004) still holds.
if shutil.which("firejail") is None:
    _real_which = shutil.which

    def _which_with_firejail_present(cmd: str, *args: Any, **kwargs: Any) -> str | None:
        if cmd == "firejail":
            return "/usr/bin/firejail"
        return _real_which(cmd, *args, **kwargs)

    shutil.which = _which_with_firejail_present


@pytest.fixture
def firejail_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a stub firejail first in PATH so child interpreters need no host binary.

    shell-mcp only looks the binary up at import (never runs it), and the in-process
    shutil.which shim above does not reach a fresh interpreter. Tests that start a real
    shell-mcp child process opt in with `pytest.mark.usefixtures("firejail_on_path")`.
    """
    stub = tmp_path / "firejail"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")


@pytest.fixture(autouse=True)
def _reset_tool_registry() -> Generator[None]:
    """Reset the global ToolRegistry singleton before and after every test.

    Several tests across the suite register throwaway tool names (e.g.
    "tool_a") into shared.tool_registry's process-wide singleton via
    get_registry(). Without a session-wide reset, a registration left behind
    by one test file leaks into another depending on test collection order,
    causing ValueError: "Tool already registered" or stale-drift false
    positives in unrelated tests.
    """
    from shared.tool_registry import _reset_registry_for_testing

    _reset_registry_for_testing()
    yield
    _reset_registry_for_testing()


@pytest.fixture(autouse=True)
def _reset_web_search_health_and_metrics() -> Generator[None]:
    """Reset web-search-mcp's in-process health/metrics singletons per test.

    mcp_servers.web_search.health and mcp_servers.web_search.metrics track
    state (e.g. consecutive_failures) in module-level singletons by design
    (single-worker process, no persistence). Without a session-wide reset,
    a failure recorded by one test file leaks into unrelated tests depending
    on test collection order, e.g. flipping web_search's /health to 503 in
    an unrelated test.

    browser_fetch's health/metrics tracking (merged into web-search-mcp from
    the retired standalone browser-mcp server) is a second, independent pair
    of module-level singletons (_browser_health/_browser_metrics) — reset
    those too for the same reason.
    """
    from mcp_servers.web_search import health, metrics

    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()
    yield
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()


@pytest.fixture(autouse=True)
def _forbid_production_paths(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None]:
    """Fail a test that opens a SQLite database or a FileHandler under /opt/llm.

    Tests that must use a real production path opt out with the marker
    ``production_paths_allowed``. Loggers created at import time are covered by the
    LLMAGENT_LOG_DIR redirect and the collection-time check above.
    """
    if request.node.get_closest_marker("production_paths_allowed") is not None:
        yield
        return
    real_connect = sqlite3.connect
    real_init = logging.FileHandler.__init__

    def guarded_connect(database: Any, *args: Any, **kwargs: Any) -> Any:
        if _is_production_path(database):
            raise AssertionError(
                f"{request.node.nodeid} opened production database {database!r}"
            )
        return real_connect(database, *args, **kwargs)

    def guarded_init(
        self: logging.FileHandler, filename: Any, *args: Any, **kwargs: Any
    ) -> None:
        if _is_production_path(filename):
            raise AssertionError(
                f"{request.node.nodeid} opened production log file {filename!r}"
            )
        real_init(self, filename, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", guarded_connect)
    monkeypatch.setattr(logging.FileHandler, "__init__", guarded_init)
    yield


@pytest.fixture(autouse=True)
def _reset_config_loader_state() -> Generator[None]:
    """Reset ConfigLoader's allowed-file state after every test.

    This is necessary because REQ-001 makes AgentContext.__init__ set
    ConfigLoader._allowed_files unconditionally for the remainder of any
    pytest process that constructs one. Without this fixture, cross-test
    ConfigLoader state leakage would occur.
    """
    from shared.config_loader import ConfigLoader

    ConfigLoader._reset_for_testing()
    yield
    try:
        ConfigLoader._reset_for_testing()
    except ImportError:
        pass
