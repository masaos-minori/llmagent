"""tests/deploy/test_init_db_ledger_gate.py

Integration tests for the deploy/init_db.sh ledger baseline gate (REQ-006) and the
opt-in recovery-drill hook (REQ-007). The real script aborts (fail-closed) when
workflow.sqlite or eventbus.sqlite lacks the schema_migrations ledger, and runs the
read-only drill only under RUN_RECOVERY_DRILL=1.

Sandboxes: init_db.sh honors DEPLOY_SCRIPTS/DEPLOY_DB/LLMAGENT_CONFIG_DIR overrides,
and the driver points LLMAGENT_CONFIG_DIR at a rewritten copy of config/ whose db
paths target a throwaway directory under tmp_path, so the whole run -- including the
uv-spawned create_schema.py subprocess, the archive-dir resolution, and the drill --
reads and writes only the sandbox. Nothing under /opt/llm/db is touched; only /opt/llm's
uv project root and the read-only sqlite-vec extension are used, which is why the module
skips when /opt/llm has no pyproject.toml.
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

_LEDGER_FATAL = "is missing the schema_migrations ledger table"
_LEDGER_OK = "schema_migrations ledger present"
_BANNER = "=== init_db.sh: 完了 ==="

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


def _provision_workflow(path: pathlib.Path, *, with_ledger: bool) -> None:
    """Create workflow.sqlite with the required tables, optionally without the ledger.

    Dropping schema_migrations simulates a pre-baseline database: the workflow table
    gate still sees tasks/attempts/processed_events/artifacts, so only the ledger gate
    catches it (the eventbus shape gate would catch a dropped eventbus ledger first).
    """
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(build_workflow_schema_sql())
        if not with_ledger:
            conn.execute("DROP TABLE schema_migrations")
        conn.commit()
    finally:
        conn.close()


def _provision_minimal_rag(path: pathlib.Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()


def _provision_minimal_session(path: pathlib.Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE sessions (id INTEGER PRIMARY KEY)")
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
    create_schema.py is replaced. This isolates the ledger gate from create_schema.py
    (which would otherwise re-add the ledger via IF NOT EXISTS DDL) while leaving the
    eventbus shape gate and the drill/archive-dir resolution fully functional.
    """
    stub = tmp_path / "scripts"
    shutil.copytree(_REPO_ROOT / "scripts", stub)
    (stub / "db" / "create_schema.py").write_text(
        '"""No-op stub isolating the init_db.sh ledger gate from create_schema.py."""\n',
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


def test_ledger_gate_passes_on_canonical_databases(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite", with_ledger=True)
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode == 0, result.stderr
    assert _BANNER in result.stdout
    assert _LEDGER_OK in result.stdout


def test_ledger_gate_aborts_when_workflow_ledger_missing(
    tmp_path: pathlib.Path,
) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_canonical_eventbus(db_dir / "eventbus.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite", with_ledger=False)
    result = _run(_write_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir))
    assert result.returncode != 0
    assert _LEDGER_FATAL in result.stderr
    assert "migrate_db.py --apply" in result.stderr
    assert _BANNER not in result.stdout


def test_recovery_drill_runs_under_flag_and_leaves_fixtures_untouched(
    tmp_path: pathlib.Path,
) -> None:
    db_dir = tmp_path / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    _provision_minimal_rag(db_dir / "rag.sqlite")
    _provision_minimal_session(db_dir / "session.sqlite")
    _provision_workflow(db_dir / "workflow.sqlite", with_ledger=True)
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
