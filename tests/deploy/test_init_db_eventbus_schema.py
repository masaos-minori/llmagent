"""tests/deploy/test_init_db_eventbus_schema.py

Integration tests for the deploy/init_db.sh EventBus shape gate (REQ-003): the real
script aborts when the EventBus database is stamped with the current version but
structurally malformed, and passes when it is canonical.

Sandboxing: init_db.sh honors DEPLOY_SCRIPTS/DEPLOY_DB environment overrides, and the
driver points LLMAGENT_CONFIG_DIR at a rewritten copy of config/ whose db paths target a
throwaway directory under tmp_path, so the whole run — including the uv-spawned
create_schema.py subprocess — reads and writes only the sandbox. Nothing under
/opt/llm/db is touched; only /opt/llm's uv project root and the read-only sqlite-vec
extension are used, which is why the module skips when /opt/llm has no pyproject.toml.
"""

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

# One extra column added to events on an otherwise canonical stamped database: the
# deviation is one DDL re-apply cannot repair (CREATE ... IF NOT EXISTS re-creates
# missing objects but never removes or alters existing ones) and the version stamp
# stays intact.
_MALFORMED_EXTRA = "ALTER TABLE events ADD COLUMN malformed_extra TEXT"
_GATE_FATAL = "[FATAL] EventBus database schema is missing or malformed"
_BANNER = "=== init_db.sh: 完了 ==="


def _provision_databases(db_dir: pathlib.Path, *, malformed: bool) -> None:
    """Create stamped canonical eventbus + workflow databases in the sandbox.

    rag.sqlite and session.sqlite are left to the init_db.sh create_schema.py step; the
    script's own checks for them are passive .tables prints. The eventbus databases are
    built from the raw canonical DDL (no normalization) so the stamped file matches the
    shared validator's expected fingerprint exactly.
    """
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_dir / "eventbus.sqlite")
    try:
        conn.executescript(build_eventbus_schema_sql())
        conn.execute(f"PRAGMA user_version = {eventbus_schema_version()}")
        if malformed:
            conn.execute(_MALFORMED_EXTRA)
        conn.commit()
    finally:
        conn.close()
    conn = sqlite3.connect(db_dir / "workflow.sqlite")
    try:
        conn.executescript(build_workflow_schema_sql())
        conn.commit()
    finally:
        conn.close()


def _write_config(tmp_path: pathlib.Path, db_dir: pathlib.Path) -> pathlib.Path:
    """Copy config/ into the sandbox with every /opt/llm/db path rewritten to db_dir."""
    cfg_dir = tmp_path / "config"
    shutil.copytree(_REPO_ROOT / "config", cfg_dir)
    for toml_file in cfg_dir.rglob("*.toml"):
        text = toml_file.read_text(encoding="utf-8").replace(
            "/opt/llm/db/", f"{db_dir}/"
        )
        toml_file.write_text(text, encoding="utf-8")
    agent_toml = cfg_dir / "agent.toml"
    # agent.toml has no workflow_db_path key (production code defaults it to the
    # production path); the sandbox must pin it so the create_schema.py subprocess
    # cannot fall back to /opt/llm/db.
    with agent_toml.open("a", encoding="utf-8") as handle:
        handle.write(f'\nworkflow_db_path = "{db_dir / "workflow.sqlite"}"\n')
    return cfg_dir


def _write_stub_scripts(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a DEPLOY_SCRIPTS stand-in whose create_schema.py is a no-op.

    The shared validator package is copied unchanged so the init_db.sh gate itself
    resolves exactly as in production; the stub isolates the gate from the
    create_schema.py shape gate.
    """
    stub = tmp_path / "scripts"
    (stub / "db").mkdir(parents=True)
    (stub / "db" / "create_schema.py").write_text(
        '"""No-op stub isolating the init_db.sh EventBus shape gate."""\n',
        encoding="utf-8",
    )
    shutil.copytree(_REPO_ROOT / "scripts" / "shared", stub / "shared")
    return stub


def _write_init_db_driver(
    tmp_path: pathlib.Path, *, db_dir: pathlib.Path, scripts_dir: pathlib.Path
) -> pathlib.Path:
    """Driver script that exports the sandbox overrides and runs the real init_db.sh."""
    cfg_dir = _write_config(tmp_path, db_dir)
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    driver_path = tmp_path / "driver.sh"
    driver_path.write_text(
        "\n".join(
            [
                "set -euo pipefail",
                f'export DEPLOY_SCRIPTS="{scripts_dir}"',
                f'export DEPLOY_DB="{db_dir}"',
                f'export LLMAGENT_CONFIG_DIR="{cfg_dir}"',
                f'export LLMAGENT_LOG_DIR="{log_dir}"',
                f'bash "{_INIT_DB}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
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
        timeout=180,
        check=False,
    )


def test_init_db_malformed_stamped_aborts(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    _provision_databases(db_dir, malformed=True)
    result = _run(
        _write_init_db_driver(
            tmp_path, db_dir=db_dir, scripts_dir=_REPO_ROOT / "scripts"
        )
    )
    assert result.returncode != 0
    assert _BANNER not in result.stdout


def test_init_db_canonical_passes(tmp_path: pathlib.Path) -> None:
    db_dir = tmp_path / "db"
    _provision_databases(db_dir, malformed=False)
    result = _run(
        _write_init_db_driver(
            tmp_path, db_dir=db_dir, scripts_dir=_REPO_ROOT / "scripts"
        )
    )
    assert result.returncode == 0
    assert _BANNER in result.stdout
    assert "matches the canonical EventBus schema" in result.stdout


def test_shape_gate_rejects_malformed_isolated_from_create_schema_gate(
    tmp_path: pathlib.Path,
) -> None:
    # The stub scripts make the create_schema.py step a no-op, so the abort can only
    # come from the init_db.sh EventBus shape gate itself.
    db_dir = tmp_path / "db"
    _provision_databases(db_dir, malformed=True)
    scripts_dir = _write_stub_scripts(tmp_path)
    result = _run(
        _write_init_db_driver(tmp_path, db_dir=db_dir, scripts_dir=scripts_dir)
    )
    assert result.returncode != 0
    assert _GATE_FATAL in result.stderr
    assert _BANNER not in result.stdout
