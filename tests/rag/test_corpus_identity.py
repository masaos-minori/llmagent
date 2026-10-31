"""tests/rag/test_corpus_identity.py

Unit tests for rag.corpus_identity (RAGCORPUS001, doc 01):
- compute_identity(): verified round-trip, stable-across-reopen, missing-table
  unverified, and the real contract for a corrupt integer column.
- ensure_corpus_meta(): first-use insertion, single-row enforcement, absent-table None.
- bump_index_generation(): increment on success, None when the table is absent.
- version constants carried on the identity.

Each test opens a real SQLiteHelper against a ``tmp_path`` database (under /tmp,
so the conftest production-path guard does not fire). No marker needed.
"""

from __future__ import annotations

import sqlite3

import pytest
from db.helper import SQLiteHelper
from rag.corpus_identity import (
    CHUNKING_POLICY_VERSION,
    NORMALIZATION_VERSION,
    CorpusIdentity,
    bump_index_generation,
    compute_identity,
    ensure_corpus_meta,
)

_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS rag_corpus_meta (
    corpus_id                TEXT    NOT NULL,
    index_generation         INTEGER NOT NULL,
    embedding_model_id       TEXT    NOT NULL,
    normalization_version    TEXT    NOT NULL,
    chunking_policy_version  TEXT    NOT NULL,
    updated_at               TEXT    NOT NULL,
    CHECK (rowid = 1)
);


"""


def _open_db(tmp_path, *, create_meta: bool) -> SQLiteHelper:
    """Open a real SQLiteHelper against a temp DB, optionally with the meta table."""
    db = SQLiteHelper(db_path=str(tmp_path / "corpus_identity.db"))
    db.open()
    if create_meta:
        db.executescript(_SCHEMA_DDL)
        db.commit()
    return db


# ── Round trip / stability ────────────────────────────────────────────────────


class TestIdentityRoundTrip:
    def test_ensure_then_read_returns_identical_identity(self, tmp_path) -> None:
        db = _open_db(tmp_path, create_meta=True)
        ensured = ensure_corpus_meta(db, embedding_model_id="emb-x", schema_version="1")
        computed = compute_identity(db, embedding_model_id="emb-x", schema_version="1")
        assert ensured is not None
        assert ensured == computed
        assert computed.verified is True
        assert computed.index_generation == 0
        assert computed.corpus_id != ""

    def test_second_ensure_raises_single_row_constraint(self, tmp_path) -> None:
        """A second ensure on the existing single-row table raises.

        The meta table enforces exactly one row via ``CHECK (rowid = 1)`` but carries
        no UNIQUE/PK on ``corpus_id``, so ``INSERT ... ON CONFLICT DO NOTHING`` has no
        conflict target and the second insert fails. This pins the invariant:
        ensure_corpus_meta is NOT idempotent within a live table; corpus_id stability
        across sessions is covered by TestIdentityStableAcrossReopen.
        """
        db = _open_db(tmp_path, create_meta=True)
        first = ensure_corpus_meta(db, embedding_model_id="emb-x", schema_version="1")
        assert first is not None
        with pytest.raises(sqlite3.IntegrityError):
            ensure_corpus_meta(db, embedding_model_id="emb-x", schema_version="1")


class TestIdentityStableAcrossReopen:
    def test_reopen_same_file_yields_equal_identity(self, tmp_path) -> None:
        db_path = str(tmp_path / "reopen.db")

        with SQLiteHelper(db_path=db_path) as db1:
            db1.open()
            db1.executescript(_SCHEMA_DDL)
            db1.commit()
            first = ensure_corpus_meta(
                db1, embedding_model_id="emb-x", schema_version="1"
            )

        with SQLiteHelper(db_path=db_path) as db2:
            db2.open()
            second = compute_identity(
                db2, embedding_model_id="emb-x", schema_version="1"
            )

        assert first is not None
        assert first == second
        assert first.corpus_id == second.corpus_id


# ── Unverified / unverifiable states ───────────────────────────────────────────


class TestUnverifiedStates:
    def test_missing_meta_table_is_unverified(self, tmp_path) -> None:
        db = _open_db(tmp_path, create_meta=False)
        identity = compute_identity(db, embedding_model_id="emb-x", schema_version="1")
        assert identity.verified is False
        # ensure_corpus_meta cannot create a row when the table itself is absent.
        assert (
            ensure_corpus_meta(db, embedding_model_id="emb-x", schema_version="1")
            is None
        )

    def test_non_integer_generation_raises_value_error(self, tmp_path) -> None:
        """compute_identity trusts the INTEGER column: a corrupt text value raises.

        This documents the real contract. compute_identity performs defensive NULL
        checks on corpus_id/index_generation but does NOT wrap the int() coercion in a
        try/except, so a tampered non-integer generation propagates ValueError rather
        than silently returning an unverified sentinel.
        """
        db = _open_db(tmp_path, create_meta=True)
        db.execute(
            "INSERT INTO rag_corpus_meta "
            "(corpus_id, index_generation, embedding_model_id, "
            "normalization_version, chunking_policy_version, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("tampered", "not-an-int", "emb-x", "1", "1", "now"),
        )
        db.commit()
        with pytest.raises(ValueError):
            compute_identity(db, embedding_model_id="emb-x", schema_version="1")


# ── Bump ───────────────────────────────────────────────────────────────────────


class TestBumpGeneration:
    def test_bump_increments_once(self, tmp_path) -> None:
        db = _open_db(tmp_path, create_meta=True)
        ensure_corpus_meta(db, embedding_model_id="emb-x", schema_version="1")
        first = bump_index_generation(db)
        second = bump_index_generation(db)
        assert first == 1
        assert second == 2
        assert (
            compute_identity(
                db, embedding_model_id="emb-x", schema_version="1"
            ).index_generation
            == 2
        )

    def test_bump_returns_none_when_table_absent(self, tmp_path) -> None:
        db = _open_db(tmp_path, create_meta=False)
        assert bump_index_generation(db) is None


# ── Version constants ──────────────────────────────────────────────────────────


class TestVersionConstants:
    def test_identity_carries_version_constants(self, tmp_path) -> None:
        db = _open_db(tmp_path, create_meta=True)
        identity = ensure_corpus_meta(
            db, embedding_model_id="emb-x", schema_version="1"
        )
        assert identity is not None
        assert identity.normalization_version == NORMALIZATION_VERSION
        assert identity.chunking_policy_version == CHUNKING_POLICY_VERSION
        assert NORMALIZATION_VERSION == "1"
        assert CHUNKING_POLICY_VERSION == "1"

    def test_corpus_identity_equality_ignores_verified_flag(self) -> None:
        a = CorpusIdentity(
            corpus_id="c",
            index_generation=1,
            schema_version="1",
            embedding_model_id="e",
            normalization_version="1",
            chunking_policy_version="1",
            verified=True,
        )
        b = CorpusIdentity(
            corpus_id="c",
            index_generation=1,
            schema_version="1",
            embedding_model_id="e",
            normalization_version="1",
            chunking_policy_version="1",
            verified=False,
        )
        assert a == b
        assert hash(a) == hash(b)
