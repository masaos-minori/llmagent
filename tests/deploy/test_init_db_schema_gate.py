"""tests/deploy/test_init_db_schema_gate.py

Integration tests for the deploy/init_db.sh schema fingerprint gate (REQ-005,
adrrev005). The real script refuses workflow/rag/session databases that deviate
from the canonical DDL shape (shared.schema_fingerprint) — including databases
carrying the legacy migration marker tables schema_migrations /
workflow_schema_version, which the exact-match comparison now subsumes as
unexpected tables — and exits 0 only when every deployed database matches.
eventbus.sqlite is outside init_db.sh's scope (delegated to eventbus.db_tools,
tested in test_init_db_eventbus_schema.py), so a marker-carrying eventbus
database must not affect the run. The opt-in recovery-drill hook (REQ-007) runs
only under RUN_RECOVERY_DRILL=1 and stays read-only.

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
from db.helper import SQLiteHelper
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims
from eventbus.db_tools import schema_sql as eventbus_schema_sql

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_INIT_DB = _REPO_ROOT / "deploy" / "init_db.sh"
_UV_PROJECT = pathlib.Path("/opt/llm/pyproject.toml")
_VEC_SO = "/opt/llm/sqlite-vec/vec0"

pytestmark = pytest.mark.skipif(
    not _UV_PROJECT.is_file(),
    reason="init_db.sh runs create_schema.py through uv from /opt/llm; hosts "
    "without a deployed uv project cannot run the script",
)

_FINGERPRINT_OK = "match the canonical schema fingerprint"
_FINGERPRINT_FATAL = "[FATAL] Database schema does not match the current schema"
_BANNER = "=== init_db.sh: 完了 ==="

# Legacy marker DDL (pre-cutover shapes; the fingerprint gate reports them as
# unexpected tables, which this suite pins as regression coverage).
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

# Live databases the whole run must leave byte-identical (refusals and the
# drill are read-only). eventbus.sqlite proves the delegation: init_db.sh
# neither touches nor validates it.
_LIVE_FILES = (
    "rag.sqlite",
    "session.sqlite",
    "workflow.sqlite",
    "eventbus.sqlite",
)


def _provision_canonical_eventbus(path: pathlib.Path) -> None:
    """Create a canonical, marker-free eventbus.sqlite from the raw canonical DDL."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(eventbus_schema_sql())
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


def _provision_canonical_vec_db(name: str, path: pathlib.Path) -> None:
    """Create rag/session from the canonical builders with sqlite-vec loaded.

    The fingerprint gate compares rag/session against build_*_schema_sql(dims),
    and the recovery drill's fail-closed logical layer (check_rag_consistency /
    check_session_consistency) must pass on the fixtures, so the databases are
    built exactly as production create_schema.py builds them and seeded with one
    healthy row set per domain.
    """
    dims = get_embedding_dims()
    builders = {
        "rag": build_rag_schema_sql(dims),
        "session": build_session_schema_sql(dims),
    }
    conn = sqlite3.connect(str(path))
    try:
        conn.enable_load_extension(True)
        conn.load_extension(_VEC_SO)  # nosec B404 — fixed read-only extension path
        conn.enable_load_extension(False)
        conn.executescript(builders[name])
        conn.commit()
    finally:
        conn.close()
    helper = SQLiteHelper(name, db_path=str(path), sqlite_vec_so=_VEC_SO)
    helper.open()
    try:
        if name == "rag":
            helper.execute(
                "INSERT INTO documents (url, lang, fetched_at) "
                "VALUES ('https://example.com/a', 'ja', '2026-01-01T00:00:00Z')"
            )
            helper.execute(
                "INSERT INTO chunks (doc_id, content, normalized_content, chunk_index, chunk_type) "
                "VALUES (1, 'sample rag content', 'sample rag content', 0, 'text')"
            )
            helper.execute(
                "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (1, ?)",
                (bytes(1024 * 4),),
            )
        else:
            helper.execute(
                "INSERT INTO sessions (created_at) VALUES ('2026-01-01T00:00:00Z')"
            )
            helper.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (1, 'user', 'hi', '2026-01-01T00:00:00Z')"
            )
            helper.execute(
                "INSERT INTO memories (memory_id, memory_type, content) "
                "VALUES ('m1', 'semantic', 'mem content')"
            )
            helper.execute(
                "INSERT INTO memory_links (src_id, dst_id) VALUES ('m1', 'm1')"
            )
        helper.commit()
    finally:
        helper.close()


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
    # The EventBus tool resolves its database from eventbus.toml, so the sandbox copy
    # must point db_path into db_dir (otherwise it would address /opt/llm/db).
    eventbus_toml = cfg_dir / "eventbus.toml"
    eventbus_toml.write_text(
        eventbus_toml.read_text(encoding="utf-8").replace("/opt/llm/db/", f"{db_dir}/"),
        encoding="utf-8",
    )
    return cfg_dir


def _write_stub_scripts(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a DEPLOY_SCRIPTS stand-in whose create_schema.py is a no-op.

    The whole scripts/ tree is copied (pycache aside) so the fingerprint gate's
    imports (db.schema_sql, db.store_protocols, shared.schema_fingerprint) and the
    recovery drill resolve exactly as in production; only create_schema.py is
    replaced, isolating the gate from the create/verify step it would otherwise run
    first.
    """
    stub = tmp_path / "scripts"
    shutil.copytree(
        _REPO_ROOT / "scripts",
        stub,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (stub / "db" / "create_schema.py").write_text(
        '"""No-op stub isolating the init_db.sh fingerprint gate from create_schema.py."""\n',
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
        f'export EVENTBUS_CONFIG_PATH="{cfg_dir / "eventbus.toml"}"',
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


def _provision_all_canonical(db_dir: pathlib.Path) -> None:
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite")
    _provision_canonical_vec_db("rag", db_dir / "rag.sqlite")
    _provision_canonical_vec_db("session", db_dir / "session.sqlite")


def test_fingerprint_gate_passes_on_canonical_databases(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_all_canonical(db_dir)
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode == 0, result.stderr
    assert _BANNER in result.stdout
    assert _FINGERPRINT_OK in result.stdout


@pytest.mark.parametrize("marker", ["schema_migrations", "workflow_schema_version"])
def test_fingerprint_gate_aborts_when_workflow_carries_marker(
    tmp_path: pathlib.Path, marker: str
) -> None:
    # The legacy marker tables are no longer queried directly: the exact-match
    # fingerprint refuses them as unexpected tables, with the same archive-and-
    # recreate guidance and no automatic migration.
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_all_canonical(db_dir)
    _provision_workflow(db_dir / "workflow.sqlite", marker=marker)
    before = _hash(db_dir / "workflow.sqlite")
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert _FINGERPRINT_FATAL in result.stderr
    assert f"unexpected table '{marker}'" in result.stderr
    assert "archive the existing database" in result.stderr
    assert "create a new database using the current schema" in result.stderr
    assert "migrate_db.py" not in result.stderr  # deleted CLI must not be named
    assert _BANNER not in result.stdout
    assert _hash(db_dir / "workflow.sqlite") == before  # refusal performs no write


def test_fingerprint_gate_aborts_on_column_drift(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_all_canonical(db_dir)
    conn = sqlite3.connect(db_dir / "workflow.sqlite")
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN drifted_extra TEXT")
        conn.commit()
    finally:
        conn.close()
    before = {name: _hash(db_dir / name) for name in _LIVE_FILES}
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert _FINGERPRINT_FATAL in result.stderr
    assert "columns differ" in result.stderr
    assert _BANNER not in result.stdout
    assert {name: _hash(db_dir / name) for name in _LIVE_FILES} == before


def test_fingerprint_gate_aborts_when_database_is_missing_or_empty(
    tmp_path: pathlib.Path,
) -> None:
    # A missing database is refused fail-closed. In the normal flow the earlier
    # table-echo step creates an empty file first, and the fingerprint gate then
    # reports it as missing the canonical tables — either way the run aborts.
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite")
    _provision_canonical_vec_db("rag", db_dir / "rag.sqlite")
    # session.sqlite deliberately absent.
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert (
        "[gate] missing database" in result.stderr or "missing table" in result.stderr
    )
    assert _FINGERPRINT_FATAL in result.stderr
    assert _BANNER not in result.stdout


def test_eventbus_marker_does_not_affect_init_db(tmp_path: pathlib.Path) -> None:
    # Delegation contract: eventbus.sqlite is validated by eventbus.db_tools,
    # not init_db.sh. A marker-carrying eventbus database must not abort the run,
    # and init_db.sh must leave the file untouched.
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_all_canonical(db_dir)
    _seed_eventbus_marker(db_dir / "eventbus.sqlite")
    before = _hash(db_dir / "eventbus.sqlite")
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode == 0, result.stderr
    assert _BANNER in result.stdout
    assert _FINGERPRINT_OK in result.stdout
    assert _hash(db_dir / "eventbus.sqlite") == before


def test_recovery_drill_runs_under_flag_and_leaves_fixtures_untouched(
    tmp_path: pathlib.Path,
) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_all_canonical(db_dir)
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
    # recovery_drill.py drills the three Agent-side domains only; eventbus.sqlite
    # is no longer verified by init_db.sh at all (delegation contract).
    artifacts = list((db_dir / "archive" / "drills").glob("*.json"))
    assert len(artifacts) == 3, [p.name for p in artifacts]
    after = {name: _hash(db_dir / name) for name in _LIVE_FILES}
    assert before == after, "the read-only drill must not mutate live databases"
