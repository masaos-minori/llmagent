"""tests/deploy/test_init_db_eventbus_schema.py

Delegation contract tests for eventbus.sqlite (REQ-003 cutover). After the
cutover, init_db.sh validates only workflow/rag/session with the shared
fingerprint gate and no longer creates, resolves, or validates eventbus.sqlite:
eventbus.sqlite is owned by eventbus.db_tools, whose ensure/verify enforce the
canonical shape, and deploy.sh delegates to them. These tests pin both sides:
init_db.sh completes even when a malformed eventbus database sits in the sandbox,
and eventbus.db_tools verify accepts canonical / refuses malformed databases.

Sandboxing: init_db.sh honors DEPLOY_SCRIPTS/DEPLOY_DB environment overrides, and the
driver points LLMAGENT_CONFIG_DIR at a rewritten copy of config/ whose db paths target a
throwaway directory under tmp_path, so the whole run — including the uv-spawned
create_schema.py subprocess — reads and writes only the sandbox. The subprocess
environment comes from the shared isolated_subprocess_env fixture in tests/conftest.py,
so it also inherits the suite's isolation variables. Nothing under
/opt/llm/db is touched; only /opt/llm's uv project root and the read-only sqlite-vec
extension are used, which is why the module skips when /opt/llm has no pyproject.toml.
"""

import pathlib
import shutil
import sqlite3
import subprocess
from collections.abc import Callable

import pytest
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims
from eventbus import db_tools
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

# One extra column added to events on an otherwise canonical database: the deviation
# is one DDL re-apply cannot repair (CREATE ... IF NOT EXISTS re-creates missing
# objects but never removes or alters existing ones).
_MALFORMED_EXTRA = "ALTER TABLE events ADD COLUMN malformed_extra TEXT"
_BANNER = "=== init_db.sh: 完了 ==="


def _provision_databases(db_dir: pathlib.Path, *, malformed: bool) -> None:
    """Create canonical eventbus, workflow, rag, and session databases in the sandbox.

    The fingerprint gate checks every deployed domain init_db.sh owns, so the
    fixture provides rag/session/workflow as well; eventbus is provisioned too to
    prove the gate and the create_schema.py step ignore it entirely.
    rag/session are built from the canonical builders with the sqlite-vec extension
    loaded, exactly as production create_schema.py does. eventbus is built from the
    raw canonical DDL (no normalization) so the file matches the shared validator's
    expected fingerprint exactly.
    """
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_dir / "eventbus.sqlite")
    try:
        conn.executescript(eventbus_schema_sql())
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
    dims = get_embedding_dims()
    builders = {
        "rag": build_rag_schema_sql(dims),
        "session": build_session_schema_sql(dims),
    }
    for name, ddl in builders.items():
        conn = sqlite3.connect(db_dir / f"{name}.sqlite")
        try:
            conn.enable_load_extension(True)
            conn.load_extension(_VEC_SO)  # nosec B608 — fixed extension path
            conn.enable_load_extension(False)
            conn.executescript(ddl)
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
    # cannot fall back to /opt/llm/db. The key is PREPENDED: appending lands it
    # inside the trailing [tool_definitions.*] table section, where the top-level
    # lookup still falls back to the production path (toolexec001 row 06 exposed
    # this with the 1.2.0 version refusal).
    pinned = f'workflow_db_path = "{db_dir / "workflow.sqlite"}"\n'
    agent_toml.write_text(pinned + agent_toml.read_text(encoding="utf-8"))
    return cfg_dir


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
                f'export EVENTBUS_CONFIG_PATH="{cfg_dir / "eventbus.toml"}"',
                f'export LLMAGENT_LOG_DIR="{log_dir}"',
                f'bash "{_INIT_DB}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return driver_path


def _run(
    driver_path: pathlib.Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    # The real init_db.sh needs uv, sqlite3, and uv's HOME-cached environment on PATH;
    # the env comes from the isolated_subprocess_env fixture.
    return subprocess.run(
        ["bash", str(driver_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        check=False,
    )


def test_init_db_ignores_eventbus_database(
    tmp_path: pathlib.Path, isolated_subprocess_env: Callable[..., dict[str, str]]
) -> None:
    # Delegation contract (REQ-003 cutover): a structurally malformed eventbus
    # database does not involve init_db.sh — it validates only workflow/rag/session
    # and must complete without creating, validating, or touching eventbus.sqlite.
    db_dir = tmp_path / "db"
    _provision_databases(db_dir, malformed=True)
    result = _run(
        _write_init_db_driver(
            tmp_path, db_dir=db_dir, scripts_dir=_REPO_ROOT / "scripts"
        ),
        isolated_subprocess_env(),
    )
    assert result.returncode == 0
    assert _BANNER in result.stdout


def test_db_tools_verify_accepts_canonical(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    _provision_databases(tmp_path, malformed=False)
    result = db_tools.verify(tmp_path / "eventbus.sqlite")
    assert result == tmp_path / "eventbus.sqlite"
    assert path.is_file()


def test_db_tools_verify_refuses_malformed(tmp_path: pathlib.Path) -> None:
    _provision_databases(tmp_path, malformed=True)
    with pytest.raises(RuntimeError, match="columns differ"):
        db_tools.verify(tmp_path / "eventbus.sqlite")
