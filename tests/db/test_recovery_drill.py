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
from db.models import RagConsistencyReport
from db.recovery_drill import DOMAINS, MIGRATE_POLICY_DOMAINS, run_drill
from db.schema_sql import build_rag_schema_sql, build_session_schema_sql

_EVENTBUS_SCHEMA = (
    Path(__file__).resolve().parents[2] / "scripts" / "eventbus" / "schema.sql"
)

# Per-domain fixtures. session/workflow ship vec0/fts5 virtual tables that require
# the external sqlite-vec extension; the drill's identity+integrity checks for them
# cover only the core tables, but rag/session additionally run the fail-closed
# logical layer (`check_rag_consistency` / `check_session_consistency`), whose
# read-smoke-test requires the full table set. When the sqlite-vec extension loads,
# the production DDL SSOT (`build_rag_schema_sql` / `build_session_schema_sql`) is
# used verbatim so the fixture is structurally identical to production. When it does
# not load (this CI env), the rag fixture falls back to the plain RAG core schema
# (chunks, a plain `chunks_vec` carrying a valid 1024-dim embedding BLOB, fts5 +
# triggers, matching tests/db/test_rag_consistency.py) and the session fixture falls
# back to a plain 7-table copy of the session schema with `memories_vec` as a regular
# table instead of a vec0 virtual table. Both fallbacks still satisfy the logical
# checks, so the healthy sweep stays green without the extension.
_RAG_DDL = """CREATE TABLE documents (
    doc_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT NOT NULL UNIQUE,
    title     TEXT,
    lang      TEXT,
    fetched_at TEXT,
    etag      TEXT,
    last_modified TEXT,
    chunking_strategy TEXT
);
CREATE TABLE chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    content            TEXT NOT NULL,
    normalized_content TEXT,
    chunk_index        INTEGER,
    chunk_type         TEXT
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
);
CREATE TRIGGER chunks_ai
AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER chunks_ad
AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
END;
CREATE TRIGGER chunks_au
AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END"""

# Plain-table fallback for session when vec0 is unavailable. Mirrors
# build_session_schema_sql() exactly, except `memories_vec` is a regular table
# (a vec0 virtual table cannot be created without the extension). The logical
# check reads all seven tables, so this keeps the read-smoke-test green.
_SESSION_FALLBACK_DDL = """CREATE TABLE sessions (
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

#: Concrete embedding dimension for fixtures. Must match get_embedding_dims()
#: (Qwen3, 1024) so the rag dimension probe passes on a populated fixture.
EMBED_DIMS = 1024


def _has_vec_extension() -> bool:
    """True when the sqlite-vec extension loads in this environment."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE t USING vec0(a INTEGER)")
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


#: Whether this environment can create vec0 virtual tables. Drives whether the
#: rag/session fixtures use the production DDL SSOT or the plain-table fallback.
_VEC_AVAILABLE = _has_vec_extension()


def _build_rag(path: Path, *, prod: bool = False) -> None:
    conn = _connect(path)
    try:
        if prod:
            conn.executescript(build_rag_schema_sql(EMBED_DIMS))
        else:
            conn.executescript(_RAG_DDL)
        conn.commit()
    finally:
        conn.close()


def _build_session(path: Path, *, prod: bool = False) -> None:
    conn = _connect(path)
    try:
        if prod:
            conn.executescript(build_session_schema_sql(EMBED_DIMS))
        else:
            conn.executescript(_SESSION_FALLBACK_DDL)
        conn.commit()
    finally:
        conn.close()


_WORKFLOW_TABLES_DDL = """CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    workflow_id TEXT,
    workflow_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    task_nonce TEXT UNIQUE NOT NULL,
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
    "drill_start_ts",
    "archive_ts_epoch",
    "restore_start_ts",
    "restore_end_ts",
    "rto_seconds",
    "backup_duration_seconds",
    "rpo_seconds",
    "integrity",
    "verification",
    "policy",
    "error",
}

_LEDGER_KEYS = {"current_version", "baseline_row", "ledger_present"}


# ── Fixtures ────────────────────────────────────────────────────────────────


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path))


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
    _build_rag(paths["rag"], prod=_VEC_AVAILABLE)
    _build_session(paths["session"], prod=_VEC_AVAILABLE)
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
        assert art["backup_duration_seconds"] >= 0
        assert art["rto_seconds"] > 0  # monotonic clock measured a restore
        assert (
            art["rpo_seconds"] >= 0
        )  # recovery-point age, non-negative by construction
        # Epoch anchors are monotonic: drill start -> archive -> restore start.
        assert art["restore_start_ts"] >= art["archive_ts_epoch"]
        assert art["archive_ts_epoch"] >= art["drill_start_ts"]
        # rto_seconds is the rounded restore span; the raw span matches within rounding.
        assert (
            abs(art["rto_seconds"] - (art["restore_end_ts"] - art["restore_start_ts"]))
            <= 1e-3
        )
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
        "rag_consistency": True,
    }
    assert artifacts["session"]["verification"] == {
        "integrity": True,
        "required_table_session": True,
        "session_consistent": True,
    }
    assert artifacts["workflow"]["verification"] == {
        "integrity": True,
        "tasks_table": True,
    }
    assert artifacts["eventbus"]["verification"] == {
        "integrity": True,
        "fingerprint": True,
    }


# ── Rag fail-closed logical layer (ragverify001 AC-004/AC-005) ──────────────


def test_rag_verified_fixture_passes_drill(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    """A fully verified rag database drills with rag_consistency True (healthy path)."""
    paths = _domain_dbs
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        assert run_drill("rag", str(archive), str(drill)) is True
    (art,) = _load_artifacts(drill)
    assert art["verification"]["rag_consistency"] is True


def test_rag_unverified_dimension_fails_drill(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    """An unverified dimension records rag_consistency False and fails the domain.

    Report injection (not fixture breakage): the drill must fail on the report
    contract alone, mirroring a probe error or unavailable sqlite-vec.
    """
    paths = _domain_dbs
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    unverified = RagConsistencyReport(
        chunks=1,
        fts=1,
        vec=1,
        orphan_vec_count=0,
        fts_gap=0,
        fts_orphan_count=0,
        read_smoke_test_ok=True,
        corpus_meta_verified=True,
        fk_unverified=True,
    )
    with (
        patch("db.recovery_drill.build_db_config", return_value=cfg),
        patch("db.recovery_drill.check_rag_consistency", return_value=unverified),
    ):
        assert run_drill("rag", str(archive), str(drill)) is False
    (art,) = _load_artifacts(drill)
    assert art["verification"]["rag_consistency"] is False


def test_rag_broken_fts_fixture_fails_drill(
    _domain_dbs: dict[str, Path],
    tmp_path: Path,
) -> None:
    """A real rag fixture with core tables present but a broken FTS relationship
    must surface as rag_consistency False: the drill does not report a clean pass
    for an unusable restored copy."""
    paths = _domain_dbs
    conn = _connect(paths["rag"])
    try:
        conn.execute("INSERT INTO documents (url) VALUES ('https://example.com/1')")
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, content) VALUES (1, 'broken fts row')"
        )
        chunk_id = cur.lastrowid
        conn.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, bytes(1024 * 4)),
        )
        # Simulate a broken trigger: remove the FTS entry without touching chunks.
        conn.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "broken fts row"),
        )
        conn.commit()
    finally:
        conn.close()

    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        assert run_drill("rag", str(archive), str(drill)) is False
    (art,) = _load_artifacts(drill)
    assert art["verification"]["rag_consistency"] is False
    # The core table is present: the failure is the consistency layer, not identity.
    assert art["verification"]["required_table_rag"] is True


# ── Negative fixtures: one per damage class (AC-002) ─────────────────────────
# Each starts from a healthy, seeded fixture and deletes exactly one element, so a
# failing drill is provably caused by the damage and not the fixture. The damage is
# detectable through row-count / referential mismatches, which hold whether or not
# the sqlite-vec extension is present (the vec tables are exercised via their row
# counts here); a loadable copy is what gates these tests.
_EMBED_1024 = bytes(1024 * 4)  # float32 embedding, matches get_embedding_dims()


def _seed_healthy_rag(path: Path) -> int:
    """Insert one document/chunk/vector into an already-built rag fixture.

    Returns the new chunk_id. The fts5 trigger populates chunks_fts, so the seeded
    copy is consistent (chunks == vec == fts == 1).
    """
    conn = _connect(path)
    try:
        doc = conn.execute(
            "INSERT INTO documents (url, fetched_at) "
            "VALUES ('https://example.com/a', '2026-01-01T00:00:00Z')"
        ).lastrowid
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, content, normalized_content) VALUES (?, ?, ?)",
            (doc, "sample rag content", "sample rag content"),
        )
        chunk_id = cur.lastrowid
        assert chunk_id is not None
        conn.execute(
            "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, _EMBED_1024),
        )
        conn.commit()
    finally:
        conn.close()
    return chunk_id


def _seed_healthy_session(path: Path) -> None:
    """Insert one session/message and one memory/link into an already-built session fixture."""
    conn = _connect(path)
    try:
        sid = conn.execute(
            "INSERT INTO sessions (created_at) VALUES ('2026-01-01T00:00:00Z')"
        ).lastrowid
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) "
            "VALUES (?, 'user', 'hi', '2026-01-01T00:00:00Z')",
            (sid,),
        )
        conn.execute(
            "INSERT INTO memories (memory_id, memory_type, content) "
            "VALUES ('m1', 'semantic', 'mem content')"
        )
        conn.execute("INSERT INTO memory_links (src_id, dst_id) VALUES ('m1', 'm1')")
        conn.commit()
    finally:
        conn.close()


def _drill_one(
    domain: str, paths: dict[str, Path], tmp_path: Path
) -> tuple[bool, dict]:
    """Drill a single domain and return (passed, artifact)."""
    cfg = _config(paths)
    archive = tmp_path / "archive"
    drill = tmp_path / "drills"
    with patch("db.recovery_drill.build_db_config", return_value=cfg):
        ok = run_drill(domain, str(archive), str(drill))
    (art,) = _load_artifacts(drill)
    return ok, art


def test_rag_fts_gap_fails_drill_with_integrity_ok(_domain_dbs, tmp_path):
    """A chunk with no FTS entry (fts_gap) fails the rag drill while integrity holds."""
    chunk_id = _seed_healthy_rag(_domain_dbs["rag"])
    conn = _connect(_domain_dbs["rag"])
    try:
        # Remove the FTS entry for the chunk without touching the chunk row.
        conn.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) "
            "VALUES ('delete', ?, ?)",
            (chunk_id, "sample rag content"),
        )
        conn.commit()
    finally:
        conn.close()
    ok, art = _drill_one("rag", _domain_dbs, tmp_path)
    assert ok is False
    assert art["integrity"] is True
    assert art["verification"]["rag_consistency"] is False
    assert art["verification"]["required_table_rag"] is True


def test_rag_missing_vec_fails_drill_with_integrity_ok(_domain_dbs, tmp_path):
    """A chunk with no vector row (vec < chunks) fails the rag drill; integrity holds."""
    _seed_healthy_rag(_domain_dbs["rag"])
    conn = _connect(_domain_dbs["rag"])
    try:
        conn.execute("DELETE FROM chunks_vec WHERE chunk_id = 1")
        conn.commit()
    finally:
        conn.close()
    ok, art = _drill_one("rag", _domain_dbs, tmp_path)
    assert ok is False
    assert art["integrity"] is True
    assert art["verification"]["rag_consistency"] is False


def test_session_orphaned_message_fails_drill_with_integrity_ok(_domain_dbs, tmp_path):
    """A message referencing a deleted session fails the session drill; integrity holds."""
    _seed_healthy_session(_domain_dbs["session"])
    conn = _connect(_domain_dbs["session"])
    try:
        conn.execute("DELETE FROM sessions")
        conn.commit()
    finally:
        conn.close()
    ok, art = _drill_one("session", _domain_dbs, tmp_path)
    assert ok is False
    assert art["integrity"] is True
    assert art["verification"]["session_consistent"] is False


def test_session_orphaned_memory_link_fails_drill_with_integrity_ok(
    _domain_dbs, tmp_path
):
    """A memory link referencing a deleted memory fails the session drill; integrity holds."""
    _seed_healthy_session(_domain_dbs["session"])
    conn = _connect(_domain_dbs["session"])
    try:
        conn.execute("DELETE FROM memories WHERE memory_id = 'm1'")
        conn.commit()
    finally:
        conn.close()
    ok, art = _drill_one("session", _domain_dbs, tmp_path)
    assert ok is False
    assert art["integrity"] is True
    assert art["verification"]["session_consistent"] is False


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
