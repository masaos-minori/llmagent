"""tests/db/test_recovery_drill.py — Recovery drill harness tests (all four domains).

Exercises scripts/db/recovery_drill.py against sandboxed file-based fixtures for
rag, session, workflow, and eventbus (row 11 drill tooling, REQ-007): artifact
emission, measurement fields, per-domain verification, live-database immutability,
the all-four sweep, and the audited-failure path. No production DB or archive
paths are opened; every fixture lives under tmp_path.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from db.config import DbConfig
from db.recovery_drill import DOMAINS, MIGRATE_POLICY_DOMAINS, run_drill

_EVENTBUS_SCHEMA = (
    Path(__file__).resolve().parents[2] / "scripts" / "eventbus" / "schema.sql"
)

# Minimal core-table DDL per domain. rag/session/workflow ship vec0/fts5 virtual
# tables that require the external sqlite-vec extension; the drill only verifies
# integrity + the required table, so the fixtures carry the core tables that the
# verification actually checks (no external-extension dependency).
_RAG_DDL = """CREATE TABLE documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    lang TEXT NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at TEXT NOT NULL
)"""

_SESSION_DDL = """CREATE TABLE sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
)"""

_WORKFLOW_TABLES_DDL = """CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    workflow_id TEXT,
    workflow_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE workflow_schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL
)"""

_LEDGER_DDL = """CREATE TABLE schema_migrations (
    id TEXT PRIMARY KEY,
    applied_at TEXT,
    from_version INTEGER,
    to_version INTEGER
)"""

_COMMON_ARTIFACT_KEYS = {
    "domain",
    "archive_path",
    "archive_ts",
    "drill_ts",
    "rto_seconds",
    "rpo_window_seconds",
    "integrity",
    "verification",
    "policy",
    "error",
}

_LEDGER_KEYS = {"current_version", "baseline_row", "ledger_present"}


# ── Fixtures ────────────────────────────────────────────────────────────────


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path))


def _build_rag(path: Path) -> None:
    conn = _connect(path)
    try:
        conn.executescript(_RAG_DDL)
        conn.commit()
    finally:
        conn.close()


def _build_session(path: Path) -> None:
    conn = _connect(path)
    try:
        conn.executescript(_SESSION_DDL)
        conn.commit()
    finally:
        conn.close()


def _build_workflow(path: Path, *, with_ledger: bool = True) -> None:
    conn = _connect(path)
    try:
        conn.executescript(_WORKFLOW_TABLES_DDL)
        if with_ledger:
            conn.executescript(_LEDGER_DDL)
        conn.commit()
    finally:
        conn.close()


def _build_eventbus(path: Path) -> None:
    conn = _connect(path)
    try:
        conn.executescript(_EVENTBUS_SCHEMA.read_text())
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def _domain_dbs(tmp_path: Path) -> dict[str, Path]:
    """Build all four healthy domain DBs under tmp_path; return {domain: path}."""
    paths = {domain: tmp_path / f"{domain}.sqlite" for domain in DOMAINS}
    _build_rag(paths["rag"])
    _build_session(paths["session"])
    _build_workflow(paths["workflow"], with_ledger=True)
    _build_eventbus(paths["eventbus"])
    return paths


def _config(paths: dict[str, Path]) -> DbConfig:
    return DbConfig(
        rag_db_path=str(paths["rag"]),
        session_db_path=str(paths["session"]),
        workflow_db_path=str(paths["workflow"]),
        eventbus_db_path=str(paths["eventbus"]),
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_artifacts(drill_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(drill_dir.glob("*.json"))]


def _write_cli_config(config_dir: Path, paths: dict[str, Path]) -> None:
    """Write a sandboxed agent.toml pointing every DB path inside *config_dir*."""
    (config_dir / "agent.toml").write_text(
        f'rag_db_path = "{config_dir / "rag.sqlite"}"\n'
        f'session_db_path = "{config_dir / "session.sqlite"}"\n'
        f'workflow_db_path = "{paths["workflow"]}"\n'
        f'eventbus_db_path = "{config_dir / "eventbus.sqlite"}"\n'
        "sqlite_timeout = 30\n"
        "sqlite_busy_timeout_ms = 30000\n",
        encoding="utf-8",
    )


def _run_cli(config_dir: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the recovery drill CLI as a subprocess with a sandboxed env."""
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    env = {
        **os.environ,
        "PYTHONPATH": str(scripts),
        "LLMAGENT_CONFIG_DIR": str(config_dir),
    }
    return subprocess.run(  # nosec B603 — fixed argv list, no shell
        [sys.executable, "-m", "db.recovery_drill", *args],
        cwd=str(scripts),
        env=env,
        capture_output=True,
        text=True,
    )


# ── Healthy sweep ────────────────────────────────────────────────────────────


def test_all_four_domains_drill_passes_and_live_dbs_untouched(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    paths = _domain_dbs
    before = {domain: _sha256(path) for domain, path in paths.items()}
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        ok = run_drill("all", str(archive), str(drill))
    assert ok is True
    after = {domain: _sha256(path) for domain, path in paths.items()}
    assert before == after  # the harness never rewrites a live database


def test_each_domain_artifact_carries_schema_fields(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    paths = _domain_dbs
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        run_drill("all", str(archive), str(drill))

    artifacts = {art["domain"]: art for art in _load_artifacts(drill)}
    assert [art["domain"] for art in _load_artifacts(drill)] == sorted(DOMAINS)
    assert set(artifacts) == set(DOMAINS)
    for domain, art in artifacts.items():
        assert _COMMON_ARTIFACT_KEYS <= set(art)
        assert art["domain"] == domain
        assert art["policy"] == (
            "migrate" if domain in MIGRATE_POLICY_DOMAINS else "recreate"
        )
        assert art["integrity"] is True
        assert art["rto_seconds"] > 0  # monotonic clock measured a restore
        assert art["rpo_window_seconds"] >= 0
        assert art["archive_path"] is not None
        assert art["archive_ts"] is not None
        assert art["drill_ts"] is not None
        if domain in MIGRATE_POLICY_DOMAINS:
            assert "ledger" in art
            assert _LEDGER_KEYS <= set(art["ledger"])
        else:
            assert "ledger" not in art  # recreate domains record no ledger


def test_verify_per_domain_reports_expected_verdicts(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    paths = _domain_dbs
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        run_drill("all", str(archive), str(drill))
    artifacts = {art["domain"]: art for art in _load_artifacts(drill)}
    assert artifacts["rag"]["verification"] == {
        "integrity": True,
        "required_table_rag": True,
    }
    assert artifacts["session"]["verification"] == {
        "integrity": True,
        "required_table_session": True,
    }
    assert artifacts["workflow"]["verification"] == {
        "integrity": True,
        "tasks_table": True,
    }
    assert artifacts["eventbus"]["verification"] == {
        "integrity": True,
        "fingerprint": True,
    }


# ── Audited failure ──────────────────────────────────────────────────────────


def test_missing_ledger_is_an_audited_finding(tmp_path: Path) -> None:
    # A migrate-policy domain whose create path should have stamped a ledger but
    # did not is itself a drill finding (row 11): the drill fails, yet still
    # writes an artifact for every domain and leaves the live DB untouched.
    paths = {domain: tmp_path / f"{domain}.sqlite" for domain in DOMAINS}
    _build_rag(paths["rag"])
    _build_session(paths["session"])
    _build_workflow(paths["workflow"], with_ledger=False)
    _build_eventbus(paths["eventbus"])
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    before_wf = _sha256(paths["workflow"])
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        ok = run_drill("all", str(archive), str(drill))
    assert ok is False
    artifacts = {art["domain"]: art for art in _load_artifacts(drill)}
    assert set(artifacts) == set(DOMAINS)  # every artifact still written
    assert artifacts["workflow"]["verification"].get("ledger_present") is False
    assert archive.exists()  # used the drill archive dir, not /opt/llm
    assert _sha256(paths["workflow"]) == before_wf  # live DB untouched


# ── CLI (subprocess) ─────────────────────────────────────────────────────────


def test_cli_exits_zero_on_success(
    _domain_dbs: dict[str, Path], tmp_path: Path
) -> None:
    paths = _domain_dbs
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _write_cli_config(config_dir, paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    result = _run_cli(
        config_dir,
        "--domain",
        "workflow",
        "--archive-dir",
        str(archive),
        "--drill-dir",
        str(drill),
    )
    assert result.returncode == 0, result.stderr
    assert _load_artifacts(drill)  # the CLI process wrote its own artifact


def test_cli_exits_nonzero_on_failure(tmp_path: Path) -> None:
    paths = {domain: tmp_path / f"{domain}.sqlite" for domain in DOMAINS}
    _build_rag(paths["rag"])
    _build_session(paths["session"])
    _build_workflow(paths["workflow"], with_ledger=False)
    _build_eventbus(paths["eventbus"])
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _write_cli_config(config_dir, paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    result = _run_cli(
        config_dir,
        "--domain",
        "workflow",
        "--archive-dir",
        str(archive),
        "--drill-dir",
        str(drill),
    )
    assert result.returncode == 1, result.stderr
    artifacts = _load_artifacts(drill)
    assert artifacts and artifacts[0]["verification"].get("ledger_present") is False
