"""tests/db/test_schema_validation_per_database.py

Per-database drift matrix (adrrev005 REQ-003/REQ-005, row 20).

For each of rag, session, workflow, eventbus, mcp_dedup, mdq: four drift cases
(missing CHECK, extra legacy table, extra column, missing index) make the
domain's real open/startup entry refuse the database with the explicit
archive-and-recreate error, leaving the file unchanged. A clean baseline
built from the same canonical DDL passes the same entry.

Domains whose canonical schema declares no table CHECK or no CREATE INDEX
(mdq, rag) carry the closest structural substitute, documented per entry:
mdq uses its FOREIGN KEY and its PRIMARY KEY autoindex; rag uses the table-level
UNIQUE that backs its only index. A mutation that changes nothing is caught by
the baseline-vs-mutant fingerprint guard, so a substitute can never silently
degrade into a no-op.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.services.workflow_schema import check_workflow_schema
from db.config import DbConfig
from db.create_schema import create_rag_schema, create_session_schema
from db.helper import SQLiteHelper
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from eventbus.db_tools import ensure as eventbus_ensure
from eventbus.db_tools import schema_sql as eventbus_schema_sql
from mcp_servers.mdq.db_schema import _CREATE_STATEMENTS, create_production_tables
from shared.mcp_dedup import _CANONICAL_DDL as dedup_canonical_ddl
from shared.mcp_dedup import DedupStore
from shared.schema_fingerprint import REFUSAL_MESSAGE, build_fingerprint

_VEC0_STATEMENT_RE = re.compile(
    r"CREATE VIRTUAL TABLE IF NOT EXISTS \w+ USING vec0\(.*?\);",
    re.DOTALL,
)


def _without_vec0(sql: str) -> str:
    """Return canonical DDL with vec0 statements removed.

    Mirrors tests/db/test_create_schema.py: the fingerprint gate is exercised
    without loading sqlite-vec. fts5 statements stay; fts5 ships with SQLite.
    """
    return _VEC0_STATEMENT_RE.sub("", sql)


def _executescript(path: Path, sql: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _fingerprint(path: Path) -> tuple:
    conn = sqlite3.connect(path)
    try:
        return build_fingerprint(conn)
    finally:
        conn.close()


def _append_mutated(canonical: str, extra_sql: str) -> str:
    """Canonical DDL plus a trailing mutation statement."""
    return f"{canonical.rstrip()}\n{extra_sql}"


@dataclass(frozen=True)
class _Domain:
    """One row of the per-database matrix: entry, canonical DDL, drift knobs."""

    name: str
    entry: Callable[[Path], str | None]
    canonical: Callable[[], str]
    primary_table: str
    # Substring removed from the canonical text to produce the "missing CHECK"
    # mutant. mdq declares no CHECK: its FOREIGN KEY is the substitute.
    check_snippet: str
    # For drop_index_by_name domains: the index name whose CREATE is followed
    # by a DROP. Otherwise the substring removed to produce the "missing index"
    # mutant, replaced by index_replacement. Domains without a CREATE INDEX
    # (rag, mdq) remove the constraint that backs their only index.
    index_snippet: str
    index_replacement: str = ""
    drop_index_by_name: bool = True


def _refusal(entry: Callable[[], object]) -> str | None:
    """Run an open/startup entry; return its refusal text, or None when accepted."""
    try:
        result = entry()
    except RuntimeError as exc:
        return str(exc)
    if isinstance(result, tuple) and hasattr(result, "valid"):
        # SchemaCheckResult: preflight entries report refusals, not raises.
        return None if result.valid else result.error
    return None


@contextmanager
def _rag_entry_patches(db_file: Path, canonical: str):
    cfg = DbConfig(rag_db_path=str(db_file), session_db_path=str(db_file.parent / "s"))
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.create_schema.build_rag_schema_sql", return_value=canonical),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
    ):
        yield


@contextmanager
def _session_entry_patches(db_file: Path, canonical: str):
    cfg = DbConfig(rag_db_path=str(db_file.parent / "r"), session_db_path=str(db_file))
    with (
        patch("db.helper.build_db_config", return_value=cfg),
        patch("db.create_schema.build_session_schema_sql", return_value=canonical),
        patch.object(SQLiteHelper, "_load_vec_extension", return_value=None),
    ):
        yield


_RAG_CANONICAL = _without_vec0(build_rag_schema_sql(8))
_SESSION_CANONICAL = _without_vec0(build_session_schema_sql(8))
_MDQ_CANONICAL = ";\n".join(_CREATE_STATEMENTS) + ";"


def _entry_rag(path: Path) -> str | None:
    with _rag_entry_patches(path, _RAG_CANONICAL):
        return _refusal(create_rag_schema)


def _entry_session(path: Path) -> str | None:
    with _session_entry_patches(path, _SESSION_CANONICAL):
        return _refusal(create_session_schema)


def _entry_workflow(path: Path) -> str | None:
    result = check_workflow_schema(str(path))
    return None if result.valid else result.error


def _entry_eventbus(path: Path) -> str | None:
    return _refusal(lambda: eventbus_ensure(path))


def _entry_dedup(path: Path) -> str | None:
    def _open() -> None:
        store = DedupStore(str(path))
        store.close()

    return _refusal(_open)


def _entry_mdq(path: Path) -> str | None:
    def _open() -> None:
        conn = sqlite3.connect(path)
        try:
            create_production_tables(conn, str(path), 5000)
        finally:
            conn.close()

    return _refusal(_open)


_DOMAINS: tuple[_Domain, ...] = (
    _Domain(
        name="rag",
        entry=_entry_rag,
        canonical=lambda: _RAG_CANONICAL,
        primary_table="chunks",
        check_snippet="CHECK (chunk_index >= 0),",
        # rag declares no CREATE INDEX; the table-level UNIQUE is its only
        # index (sqlite_autoindex_chunks_1).
        index_snippet="UNIQUE (doc_id, chunk_index),",
        drop_index_by_name=False,
    ),
    _Domain(
        name="session",
        entry=_entry_session,
        canonical=lambda: _SESSION_CANONICAL,
        primary_table="messages",
        check_snippet="CHECK(memory_type IN ('semantic','episodic'))",
        index_snippet="idx_session_diagnostics_session",
    ),
    _Domain(
        name="workflow",
        entry=_entry_workflow,
        canonical=build_workflow_schema_sql,
        primary_table="tasks",
        check_snippet="CHECK (status IN ('pending', 'running', 'completed', 'failed', 'halted'))",
        index_snippet="idx_tool_call_state_task_state",
    ),
    _Domain(
        name="eventbus",
        entry=_entry_eventbus,
        canonical=eventbus_schema_sql,
        primary_table="events",
        check_snippet="CHECK (status IN ('pending', 'done', 'failed'))",
        index_snippet="idx_events_topic",
    ),
    _Domain(
        name="mcp_dedup",
        entry=_entry_dedup,
        canonical=lambda: dedup_canonical_ddl,
        primary_table="tool_call_state",
        check_snippet="CHECK (status IN ('pending', 'completed', 'failed', 'interrupted'))",
        index_snippet="idx_tcs_updated",
    ),
    _Domain(
        name="mdq",
        entry=_entry_mdq,
        canonical=lambda: _MDQ_CANONICAL,
        primary_table="chunks",
        # mdq declares no CHECK: removing the chunks FK is the constraint case.
        check_snippet=" REFERENCES documents(doc_id) ON DELETE CASCADE",
        # mdq declares no CREATE INDEX: dropping the documents PRIMARY KEY
        # removes its only index (sqlite_autoindex_documents_1).
        index_snippet="doc_id TEXT PRIMARY KEY",
        index_replacement="doc_id TEXT NOT NULL",
        drop_index_by_name=False,
    ),
)

_DOMAIN_IDS = [d.name for d in _DOMAINS]


def _mutate_missing_check(domain: _Domain, canonical: str) -> str:
    assert domain.check_snippet in canonical, (
        f"{domain.name}: CHECK substitute no longer in the canonical DDL"
    )
    return canonical.replace(domain.check_snippet, "", 1)


def _mutate_missing_index(domain: _Domain, canonical: str) -> str:
    assert domain.index_snippet in canonical, (
        f"{domain.name}: index (or index-backing constraint) no longer in the "
        "canonical DDL"
    )
    if domain.drop_index_by_name:
        return _append_mutated(canonical, f"DROP INDEX {domain.index_snippet};")
    return canonical.replace(domain.index_snippet, domain.index_replacement, 1)


def _mutate_extra_table(canonical: str) -> str:
    return _append_mutated(
        canonical, "CREATE TABLE drift_legacy (id INTEGER PRIMARY KEY);"
    )


def _mutate_extra_column(domain: _Domain, canonical: str) -> str:
    return _append_mutated(
        canonical, f"ALTER TABLE {domain.primary_table} ADD COLUMN drift_column TEXT;"
    )


def _build(tmp_path: Path, domain: _Domain, ddl: str, label: str) -> Path:
    path = tmp_path / f"{domain.name}-{label}.sqlite"
    _executescript(path, ddl)
    return path


def _assert_refused(tmp_path: Path, domain: _Domain, mutated_ddl: str) -> None:
    canonical = domain.canonical()
    baseline = _build(tmp_path, domain, canonical, "baseline")
    mutant = _build(tmp_path, domain, mutated_ddl, "mutant")
    # A mutation that does not actually change the shape cannot pass the gate;
    # guard against a silently degraded mutation before blaming the gate.
    assert _fingerprint(mutant) != _fingerprint(baseline), (
        f"{domain.name}: mutation produced no schema change"
    )

    before = _fingerprint(mutant)
    error = domain.entry(mutant)
    assert error is not None, f"{domain.name}: drifted database was accepted"
    assert REFUSAL_MESSAGE in error
    assert _fingerprint(mutant) == before, f"{domain.name}: entry modified the file"


class TestCleanBaseline:
    """The gate accepts what the same canonical DDL built."""

    @pytest.mark.parametrize("domain", _DOMAINS, ids=_DOMAIN_IDS)
    def test_baseline_passes(self, tmp_path: Path, domain: _Domain) -> None:
        baseline = _build(tmp_path, domain, domain.canonical(), "clean")
        assert domain.entry(baseline) is None


class TestFourDrifts:
    """Each drift case refuses the domain's real open/startup entry."""

    @pytest.mark.parametrize("domain", _DOMAINS, ids=_DOMAIN_IDS)
    def test_missing_check(self, tmp_path: Path, domain: _Domain) -> None:
        _assert_refused(
            tmp_path, domain, _mutate_missing_check(domain, domain.canonical())
        )

    @pytest.mark.parametrize("domain", _DOMAINS, ids=_DOMAIN_IDS)
    def test_extra_legacy_table(self, tmp_path: Path, domain: _Domain) -> None:
        _assert_refused(tmp_path, domain, _mutate_extra_table(domain.canonical()))

    @pytest.mark.parametrize("domain", _DOMAINS, ids=_DOMAIN_IDS)
    def test_extra_column(self, tmp_path: Path, domain: _Domain) -> None:
        _assert_refused(
            tmp_path, domain, _mutate_extra_column(domain, domain.canonical())
        )

    @pytest.mark.parametrize("domain", _DOMAINS, ids=_DOMAIN_IDS)
    def test_missing_index(self, tmp_path: Path, domain: _Domain) -> None:
        _assert_refused(
            tmp_path, domain, _mutate_missing_index(domain, domain.canonical())
        )
