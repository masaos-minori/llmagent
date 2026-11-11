"""Tests for scripts/shared/schema_fingerprint.py: the shared schema fingerprint
utility (Plan 20261110-095137 rows 01 and 19, REQ-002/REQ-005).

Drift cases use a small canonical DDL fixture and derive variants by string
edits, so each fixture drift is a schema difference and not a mutation that
could trip the comparison for the wrong reason. The canonical builds cover the
real DDL of all four domains (rag, session, workflow, eventbus) from the
existing builders.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest
from eventbus.db_tools import schema_sql as eventbus_schema_sql

from scripts.db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from scripts.shared import schema_fingerprint

VEC_EXTENSION = "/opt/llm/sqlite-vec/vec0"
DIMS = 1024

REFUSAL_PHRASE = "The database does not match the current schema."

SMALL_CANONICAL = """
CREATE TABLE IF NOT EXISTS widgets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(name) <= 32),
    qty INTEGER NOT NULL DEFAULT 0,
    UNIQUE (name)
);
CREATE INDEX IF NOT EXISTS idx_widgets_qty ON widgets(qty);
CREATE TABLE IF NOT EXISTS widget_audit (
    id INTEGER PRIMARY KEY,
    widget_id INTEGER NOT NULL REFERENCES widgets(id)
);
CREATE TRIGGER IF NOT EXISTS trg_widgets_audit
AFTER INSERT ON widgets
BEGIN
    INSERT INTO widget_audit (widget_id) VALUES (NEW.id);
END;
"""


def _canonical_ddls() -> dict[str, str]:
    return {
        "rag": build_rag_schema_sql(DIMS),
        "session": build_session_schema_sql(DIMS),
        "workflow": build_workflow_schema_sql(),
        "eventbus": eventbus_schema_sql(),
    }


def _extension_available() -> bool:
    try:
        conn = sqlite3.connect(":memory:")
        conn.enable_load_extension(True)
        conn.load_extension(VEC_EXTENSION)
        conn.close()
        return True
    except (AttributeError, sqlite3.Error):
        return False


requires_vec_extension = pytest.mark.skipif(
    not _extension_available(), reason="sqlite-vec extension unavailable"
)


def _apply_full_ddl(ddl: str, *, load_vec_extension: bool) -> sqlite3.Connection:
    """Apply DDL verbatim (virtual tables included), mirroring production bootstrap."""
    conn = sqlite3.connect(":memory:")
    if load_vec_extension:
        conn.enable_load_extension(True)
        conn.load_extension(VEC_EXTENSION)
    conn.executescript(ddl)
    return conn


def _virtual_base_names(ddl: str) -> set[str]:
    return set(schema_fingerprint._strip_virtual_statements(ddl)[1])


class TestCanonicalBuildsPass:
    @pytest.mark.parametrize("domain", ["rag", "session", "workflow", "eventbus"])
    def test_matching_build_passes_assertion(self, domain: str) -> None:
        ddl = _canonical_ddls()[domain]
        conn = _apply_full_ddl(ddl, load_vec_extension="vec0" in ddl)
        try:
            schema_fingerprint.assert_matches(conn, ddl, label=domain)
        finally:
            conn.close()

    @pytest.mark.parametrize("domain", ["rag", "session"])
    def test_virtual_tables_satisfied_by_name_without_extension(
        self, domain: str
    ) -> None:
        """Plain stand-in tables with the virtual names satisfy the name-only
        requirement — the stdlib-only fallback provisioning shape."""
        ddl = _canonical_ddls()[domain]
        conn = schema_fingerprint.apply_ddl_in_memory(ddl)
        try:
            for name in _virtual_base_names(ddl):
                conn.execute(f"CREATE TABLE {name} (id INTEGER PRIMARY KEY)")  # nosec B608 — names from the canonical DDL
            schema_fingerprint.assert_matches(conn, ddl, label=domain)
        finally:
            conn.close()

    def test_in_memory_apply_honours_an_explicit_pragma_stamp(self) -> None:
        conn = schema_fingerprint.apply_ddl_in_memory(
            "PRAGMA user_version = 6;\nCREATE TABLE t (id INTEGER);"
        )
        try:
            assert conn.execute("PRAGMA user_version").fetchone() == (6,)
        finally:
            conn.close()

    def test_canonical_eventbus_ddl_leaves_the_database_unstamped(self) -> None:
        # REQ-004: the canonical eventbus DDL no longer stamps a version; a fresh
        # apply leaves user_version 0 and the fingerprint gate ignores the value.
        conn = schema_fingerprint.apply_ddl_in_memory(eventbus_schema_sql())
        try:
            assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        finally:
            conn.close()


class TestDomainShape:
    @requires_vec_extension
    def test_assert_matches_works_on_a_file_db_with_real_virtual_tables_without_reloading_extension(
        self, tmp_path: Path
    ) -> None:
        """A database built with real vec0/fts5 tables asserts cleanly when the
        checking connection has no extension loaded: the live virtual tables are
        recorded by name only, so their module is never needed."""
        ddl = build_rag_schema_sql(DIMS)
        db_path = tmp_path / "rag-fixture.sqlite"
        build = sqlite3.connect(db_path)
        build.enable_load_extension(True)
        build.load_extension(VEC_EXTENSION)
        build.executescript(ddl)
        build.close()
        conn = sqlite3.connect(db_path)
        try:
            schema_fingerprint.assert_matches(conn, ddl, label="rag-file")
        finally:
            conn.close()

    def test_eventbus_expected_equals_build(self) -> None:
        """Without virtual tables, expected_fingerprint(ddl) equals
        build_fingerprint(conn) for a database built from the same DDL."""
        ddl = eventbus_schema_sql()
        conn = _apply_full_ddl(ddl, load_vec_extension=False)
        try:
            assert schema_fingerprint.expected_fingerprint(
                ddl
            ) == schema_fingerprint.build_fingerprint(conn)
        finally:
            conn.close()

    def test_rag_virtual_bases_are_name_only(self) -> None:
        expected = schema_fingerprint.expected_fingerprint(build_rag_schema_sql(DIMS))
        names = {str(entry[0]): entry for entry in expected}
        for base in ("chunks_vec", "chunks_fts"):
            assert names[base] == (base, (), (), (), (), ())

    @requires_vec_extension
    def test_rag_real_virtual_tables_compare_by_name_and_shadows_are_omitted(
        self,
    ) -> None:
        ddl = build_rag_schema_sql(DIMS)
        conn = _apply_full_ddl(ddl, load_vec_extension=True)
        try:
            live = schema_fingerprint.build_fingerprint(conn)
            live_names = {str(entry[0]) for entry in live}
            assert "chunks_vec" in live_names and "chunks_fts" in live_names
            shadows = {
                n for n in live_names if n.startswith(("chunks_vec_", "chunks_fts_"))
            }
            assert shadows, "the virtual modules create shadow tables"
            schema_fingerprint.assert_matches(
                conn, ddl, label="rag"
            )  # shadows do not refuse
        finally:
            conn.close()

    def test_expected_names_are_tables_plus_virtual_bases_for_every_domain(
        self,
    ) -> None:
        table_re = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+)", re.IGNORECASE)
        for domain, ddl in _canonical_ddls().items():
            declared = set(table_re.findall(ddl)) | _virtual_base_names(ddl)
            expected = {
                str(entry[0]) for entry in schema_fingerprint.expected_fingerprint(ddl)
            }
            assert expected == declared, domain


class TestSmallFixtureDriftRefusals:
    """Each case applies a drifted DDL and asserts refusal against the canonical one."""

    def _refuses(self, drifted_ddl: str, *, label: str = "fixture") -> str:
        conn = _apply_full_ddl(drifted_ddl, load_vec_extension=False)
        try:
            with pytest.raises(RuntimeError) as excinfo:
                schema_fingerprint.assert_matches(conn, SMALL_CANONICAL, label=label)
        finally:
            conn.close()
        message = str(excinfo.value)
        assert label in message
        assert REFUSAL_PHRASE in message
        assert schema_fingerprint.REFUSAL_MESSAGE in message
        return message

    def test_matching_fixture_passes(self) -> None:
        conn = _apply_full_ddl(SMALL_CANONICAL, load_vec_extension=False)
        try:
            schema_fingerprint.assert_matches(conn, SMALL_CANONICAL, label="fixture")
        finally:
            conn.close()

    def test_missing_check_constraint_refuses(self) -> None:
        drifted = SMALL_CANONICAL.replace(
            "CHECK (length(name) <= 32)", "CHECK (length(name) <= 64)"
        )
        assert drifted != SMALL_CANONICAL
        message = self._refuses(drifted)
        assert "constraints differ" in message

    def test_extra_legacy_table_refuses(self) -> None:
        drifted = (
            SMALL_CANONICAL
            + "\nCREATE TABLE IF NOT EXISTS legacy_leftover (id INTEGER PRIMARY KEY);\n"
        )
        message = self._refuses(drifted)
        assert "unexpected table 'legacy_leftover'" in message

    def test_extra_column_refuses(self) -> None:
        drifted = SMALL_CANONICAL.replace(
            "qty INTEGER NOT NULL DEFAULT 0,",
            "qty INTEGER NOT NULL DEFAULT 0,\n    surprise TEXT,",
        )
        assert drifted != SMALL_CANONICAL
        message = self._refuses(drifted)
        assert "columns differ" in message

    def test_missing_index_refuses(self) -> None:
        drifted = SMALL_CANONICAL.replace(
            "CREATE INDEX IF NOT EXISTS idx_widgets_qty ON widgets(qty);", ""
        )
        assert drifted != SMALL_CANONICAL
        message = self._refuses(drifted)
        assert "indexes differ" in message

    def test_trigger_drift_refuses(self) -> None:
        drifted = SMALL_CANONICAL.replace(
            "AFTER INSERT ON widgets", "AFTER UPDATE ON widgets"
        )
        assert drifted != SMALL_CANONICAL
        message = self._refuses(drifted)
        assert "triggers differ" in message

    def test_missing_table_refuses(self) -> None:
        drifted = SMALL_CANONICAL.replace("widget_audit", "widget_auditz")
        assert drifted != SMALL_CANONICAL
        message = self._refuses(drifted)
        assert "missing table 'widget_audit'" in message


class TestDomainDriftRefusals:
    """One drift case per real domain DDL, asserted against the canonical build."""

    def _refuses(self, canonical_ddl: str, drifted_ddl: str, label: str) -> str:
        assert drifted_ddl != canonical_ddl
        conn = _apply_full_ddl(drifted_ddl, load_vec_extension="vec0" in drifted_ddl)
        try:
            with pytest.raises(RuntimeError) as excinfo:
                schema_fingerprint.assert_matches(conn, canonical_ddl, label=label)
        finally:
            conn.close()
        message = str(excinfo.value)
        assert REFUSAL_PHRASE in message
        return message

    def test_eventbus_check_drift_refuses(self) -> None:
        canonical = eventbus_schema_sql()
        drifted = canonical.replace(
            "CHECK (status IN ('pending', 'done', 'failed'))",
            "CHECK (status IN ('pending', 'done'))",
        )
        message = self._refuses(canonical, drifted, "eventbus")
        assert "dlq_outbox" in message

    def test_rag_trigger_drift_refuses(self) -> None:
        canonical = build_rag_schema_sql(DIMS)
        drifted = canonical.replace(
            "COALESCE(new.normalized_content, new.content)", "new.content"
        )
        message = self._refuses(canonical, drifted, "rag")
        assert "triggers differ" in message

    def test_session_index_drift_refuses(self) -> None:
        canonical = build_session_schema_sql(DIMS)
        drifted = canonical.replace(
            "CREATE INDEX IF NOT EXISTS idx_session_diagnostics_session",
            "CREATE INDEX IF NOT EXISTS idx_session_diagnostics_sessionz",
        )
        message = self._refuses(canonical, drifted, "session")
        assert "indexes differ" in message

    def test_workflow_extra_table_refuses(self) -> None:
        canonical = build_workflow_schema_sql()
        drifted = (
            canonical + "\nCREATE TABLE workflow_extra (id INTEGER PRIMARY KEY);\n"
        )
        message = self._refuses(canonical, drifted, "workflow")
        assert "unexpected table 'workflow_extra'" in message


class TestStatementSplitting:
    def test_trigger_bodies_survive_splitting(self) -> None:
        fragments = schema_fingerprint._split_statements(SMALL_CANONICAL)
        trigger_fragments = [f for f in fragments if "CREATE TRIGGER" in f]
        assert len(trigger_fragments) == 1
        fragment = trigger_fragments[0]
        assert fragment.count("BEGIN") == 1 and fragment.count("END") == 1
        assert "VALUES (NEW.id);" in fragment

    def test_small_fixture_trigger_fires_after_in_memory_apply(self) -> None:
        conn = schema_fingerprint.apply_ddl_in_memory(SMALL_CANONICAL)
        try:
            conn.execute("INSERT INTO widgets (name) VALUES ('a')")
            rows = conn.execute("SELECT widget_id FROM widget_audit").fetchall()
            assert rows == [(1,)]
        finally:
            conn.close()

    def test_rag_triggers_created_by_virtual_stripped_apply(self) -> None:
        conn = schema_fingerprint.apply_ddl_in_memory(build_rag_schema_sql(DIMS))
        try:
            names = {
                str(row[0])
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                )
            }
            assert {"chunks_ai", "chunks_ad", "chunks_au", "chunks_vec_ad"} <= names
        finally:
            conn.close()
