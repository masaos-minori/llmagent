"""tests/deploy/test_init_db_schema_gate.py

Integration tests for the deploy/init_db.sh legacy-marker gate (REQ-005,
compatrm001) and the opt-in recovery-drill hook (REQ-007). The real script
aborts (fail-closed) when workflow.sqlite or eventbus.sqlite carries a legacy
migration marker table (schema_migrations / workflow_schema_version) and runs
the read-only drill only under RUN_RECOVERY_DRILL=1.

Sandboxes: init_db.sh honors DEPLOY_SCRIPTS/DEPLOY_DB/LLMAGENT_CONFIG_DIR
overrides (driver pattern ported from the deleted test_init_db_ledger_gate.py),
and the driver points LLMAGENT_CONFIG_DIR at a rewritten copy of config/ whose
db paths target a throwaway directory under tmp_path, so the whole run reads and
writes only the sandbox. Nothing under /opt/llm/db is touched; only /opt/llm's
uv project root and the read-only sqlite-vec extension are used, which is why
the module skips when /opt/llm has no pyproject.toml.
"""

import hashlib
import os
import pathlib
import shutil
import sqlite3
import subprocess

import pytest
from db.schema_sql import (
    build_eventbus_schema_sql,
    build_workflow_schema_sql,
    eventbus_schema_version,
)

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_INIT_DB = _REPO_ROOT / "deploy" / "init_db.sh"
_UV_PROJECT = pathlib.Path("/opt/llm/pyproject.toml")

pytestmark = pytest.mark.skipif(
    not _UV_PROJECT.is_file(),
    reason="init_db.sh runs create_schema.py through uv from /opt/llm; hosts "
    "without a deployed uv project cannot run the script",
)

_MARKER_FATAL = "carries legacy migration marker table(s) and does not match the current schema"
_MARKER_OK = "no legacy migration marker tables"
_BANNER = "=== init_db.sh: 完了 ==="

# Legacy marker DDL (pre-cutover shapes; any presence must be refused).
_SCHEMA_MIGRATIONS_DDL = """CREATE TABLE schema_migrations (
    id TEXT PRIMARY KEY,
    applied_at TEXT,
    from_version INTEGER,
    to_version INTEGER
)"""
_WORKFLOW_VERSION_DDL = """CREATE TABLE workflow_schema_version (
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL
)"""

# Live databases the drill must leave byte-identical (row 07: read-only).
_LIVE_FILES = (
    "rag.sqlite",
    "session.sqlite",
    "workflow.sqlite",
    "eventbus.sqlite",
)


def _provision_canonical_eventbus(path: pathlib.Path) -> None:
    """Create a canonical, stamped eventbus.sqlite (matches the shape gate fingerprint)."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(build_eventbus_schema_sql())
        conn.execute(f"PRAGMA user_version = {eventbus_schema_version()}")
        conn.commit()
    finally:
        conn.close()


def _provision_workflow(path: pathlib.Path, *, marker: str | None = None) -> None:
    """Create marker-free workflow.sqlite from the current DDL; optionally seed a marker."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(build_workflow_schema_sql())
        if marker == "schema_migrations":
            conn.executescript(_SCHEMA_MIGRATIONS_DDL)
        elif marker == "workflow_schema_version":
            conn.executescript(_WORKFLOW_VERSION_DDL)
        conn.commit()
    finally:
        conn.close()


def _seed_eventbus_marker(path: pathlib.Path) -> None:
    """Add a legacy schema_migrations table to an otherwise canonical eventbus.sqlite."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_SCHEMA_MIGRATIONS_DDL)
        conn.commit()
    finally:
        conn.close()


def _provision_rag_core(path: pathlib.Path) -> None:
    """Create the plain RAG core schema (no vec0/fts5-extension dependency).

    The drill's rag domain runs the fail-closed logical layer (check_rag_consistency),
    so the fixture mirrors the plain schema used by tests/db/test_recovery_drill.py:
    a documents-only table would mark every probe dimension unverified and fail the drill.
    """
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """CREATE TABLE documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    lang TEXT,
    fetched_at TEXT
);
CREATE TABLE chunks (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    normalized_content TEXT,
    chunk_index INTEGER,
    chunk_type TEXT
);
CREATE TABLE chunks_vec (
    chunk_id INTEGER PRIMARY KEY,
    embedding BLOB
);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
)"""
        )
        conn.commit()
    finally:
        conn.close()


def _provision_session(path: pathlib.Path) -> None:
    """Create a complete session fixture (all seven logical-check tables).

    The drill's session domain runs the fail-closed logical layer
    (check_session_consistency), whose read-smoke-test requires all seven tables; a
    single-table fixture would report session_consistent False and fail the drill.
    `memories_vec` is a regular table here (a vec0 virtual table needs the external
    sqlite-vec extension, which this env lacks); the check reads it like any table.
    """
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """CREATE TABLE sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE memories (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
    source_type TEXT NOT NULL DEFAULT 'conversation',
    session_id INTEGER,
    turn_id TEXT,
    project TEXT NOT NULL DEFAULT '',
    repo TEXT NOT NULL DEFAULT '',
    branch TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    importance REAL NOT NULL DEFAULT 0.5,
    pinned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE VIRTUAL TABLE memories_fts USING fts5(
    memory_id UNINDEXED,
    content,
    summary,
    tags
);
CREATE TABLE memory_links (
    src_id TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    dst_id TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    PRIMARY KEY (src_id, dst_id)
);
CREATE TABLE session_diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    workflow_id TEXT,
    task_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX idx_session_diagnostics_session ON session_diagnostics(session_id);
CREATE TABLE memories_vec (
    memory_id TEXT PRIMARY KEY,
    embedding BLOB
)"""
        )
        conn.commit()
    finally:
        conn.close()


def _write_config(tmp_path: pathlib.Path, db_dir: pathlib.Path) -> pathlib.Path:
    """Copy config/ into the sandbox with every /opt/llm/db path rewritten to db_dir.

    workflow_db_path is absent from agent.toml (build_db_config() defaults it to the
    production path), so it is inserted as a top-level key before the first table
    header. Appending it at EOF would land inside a [tool_definitions...] table and be
    ignored by the flat loader, silently falling back to /opt/llm/db.
    """
    cfg_dir = tmp_path / "config"
    shutil.copytree(_REPO_ROOT / "config", cfg_dir)
    agent = cfg_dir / "agent.toml"
    text = agent.read_text(encoding="utf-8").replace("/opt/llm/db/", f"{db_dir}/")
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("["):
            lines.insert(index, f'workflow_db_path = "{db_dir / "workflow.sqlite"}"')
            break
    else:
        lines.insert(0, f'workflow_db_path = "{db_dir / "workflow.sqlite"}"')
    agent.write_text("\n".join(lines), encoding="utf-8")
    return cfg_dir


def _write_stub_scripts(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a DEPLOY_SCRIPTS stand-in whose create_schema.py is a no-op.

    The whole scripts/ tree is copied so the shared validator package, the eventbus
    schema.sql, and the full db package resolve exactly as in production; only
    create_schema.py is replaced. This isolates the marker gate from create_schema.py
    (which would otherwise refuse the seeded legacy databases with its own message)
    while leaving the eventbus shape gate and the drill/archive-dir resolution fully
    functional.
    """
    stub = tmp_path / "scripts"
    shutil.copytree(_REPO_ROOT / "scripts", stub)
    (stub / "db" / "create_schema.py").write_text(
        '"""No-op stub isolating the init_db.sh marker gate from create_schema.py."""\n',
        encoding="utf-8",
    )
    return stub


def _write_driver(
    tmp_path: pathlib.Path,
    *,
    db_dir: pathlib.Path,
    scripts_dir: pathlib.Path,
    extra_env: dict[str, str] | None = None,
) -> pathlib.Path:
    """Driver script that exports the sandbox overrides and runs the real init_db.sh."""
    cfg_dir = _write_config(tmp_path, db_dir)
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    lines = [
        "set -euo pipefail",
        f'export DEPLOY_SCRIPTS="{scripts_dir}"',
        f'export DEPLOY_DB="{db_dir}"',
        f'export LLMAGENT_CONFIG_DIR="{cfg_dir}"',
        f'export LLMAGENT_LOG_DIR="{log_dir}"',
    ]
    for key, value in (extra_env or {}).items():
        lines.append(f'export {key}="{value}"')
    lines.append(f'bash "{_INIT_DB}"')
    lines.append("")
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text("\n".join(lines), encoding="utf-8")
    return driver_path


def _run(driver_path: pathlib.Path) -> subprocess.CompletedProcess[str]:
    # The real init_db.sh needs uv, sqlite3, and uv's HOME-cached environment on PATH.
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(pathlib.Path.home())),
    }
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=240,
        check=False,
    )


def _hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_marker_gate_passes_on_marker_free_databases(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite")
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode == 0, result.stderr
    assert _BANNER in result.stdout
    assert _MARKER_OK in result.stdout


@pytest.mark.parametrize("marker", ["schema_migrations", "workflow_schema_version"])
def test_marker_gate_aborts_when_workflow_carries_marker(
    tmp_path: pathlib.Path, marker: str
) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite", marker=marker)
    before = _hash(db_dir / "workflow.sqlite")
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert _MARKER_FATAL in result.stderr
    assert "archive the existing database" in result.stderr
    assert "create a new database using the current schema" in result.stderr
    assert "migrate_db.py" not in result.stderr  # deleted CLI must not be named
    assert _BANNER not in result.stdout
    assert _hash(db_dir / "workflow.sqlite") == before  # refusal performs no write


def test_marker_gate_aborts_when_eventbus_carries_marker(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _seed_eventbus_marker(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite")
    before = _hash(db_dir / "eventbus.sqlite")
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert _MARKER_FATAL in result.stderr
    assert "migrate.py" not in result.stderr  # deleted CLI must not be named
    assert _BANNER not in result.stdout
    assert _hash(db_dir / "eventbus.sqlite") == before  # refusal performs no write


def test_recovery_drill_runs_under_flag_and_leaves_fixtures_untouched(
    tmp_path: pathlib.Path,
) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_rag_core(db_dir / "rag.sqlite")
    _provision_session(db_dir / "session.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite")
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    before = {name: _hash(db_dir / name) for name in _LIVE_FILES}

    result = _run(
        _write_driver(
            tmp_path,
            db_dir=db_dir,
            scripts_dir=scripts_dir,
            extra_env={"RUN_RECOVERY_DRILL": "1"},
        )
    )

    assert result.returncode == 0, result.stderr
    assert "recovery drill passed for all domains" in result.stdout
    artifacts = list((db_dir / "archive" / "drills").glob("*.json"))
    assert len(artifacts) == 4, [p.name for p in artifacts]
    after = {name: _hash(db_dir / name) for name in _LIVE_FILES}
    assert before == after, "the read-only drill must not mutate live databases"
