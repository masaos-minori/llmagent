#!/usr/bin/env python3
"""scripts/rag/corpus_identity.py — Corpus identity for the local RAG database.

The RAG corpus carries a verifiable identity: a stable ``corpus_id``, the current index
generation, the schema version, the embedding-model id, and the normalization and
chunking-policy versions. The identity is compared before a remote-to-local fallback
result is accepted (RAGCORPUS001, REQ-003); a mismatch rejects the fallback by default.

The identity is computed from the single-row ``rag_corpus_meta`` table plus the
caller-supplied ``schema_version`` and ``embedding_model_id``. The meta-table DDL is owned
by ``scripts/db/schema_sql.py`` (doc 02); this module only ensures a row in an already
created table and never emits the ``CREATE TABLE`` statement itself.

Functions:
  compute_identity(db, *, embedding_model_id, schema_version) -> CorpusIdentity
  parse_remote_identity(body) -> CorpusIdentity | None
  ensure_corpus_meta(db, *, embedding_model_id, schema_version) -> CorpusIdentity | None
  bump_index_generation(db) -> int | None

This module imports only ``SQLiteHelper`` from ``db`` (``rag -> db`` layer contract) and
stdlib. It is a leaf: other ``rag.*`` modules (e.g. ``pipeline_service``, ``http_augment``)
import ``parse_remote_identity`` from here to avoid a runtime import cycle.
"""

import datetime
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any

from db.helper import SQLiteHelper

# Normalization and chunking-policy versions are module-level constants. Bump when the
# corresponding behavior changes; ``ensure_corpus_meta`` stamps the current value into the
# meta row on first creation so the identity records the value the corpus was built with
# (RAGCORPUS001 Assumptions: these are live constants, not persisted columns).
NORMALIZATION_VERSION = "1"
CHUNKING_POLICY_VERSION = "1"

_META_TABLE = "rag_corpus_meta"


@dataclass(frozen=True)
class CorpusIdentity:
    """Immutable corpus identity.

    ``verified=False`` encodes the identity-unverified state (REQ-007): the meta row is
    missing or corrupt, so the identity cannot be trusted for a fallback gate. Equality
    compares only the six identity fields, so two identities with identical identity values
    compare equal regardless of ``verified``.
    """

    corpus_id: str
    index_generation: int
    schema_version: str
    embedding_model_id: str
    normalization_version: str
    chunking_policy_version: str
    verified: bool = False

    def __eq__(self, other: object) -> bool:
        """Compare only the six identity fields, ignoring ``verified``.

        A frozen dataclass otherwise compares every field, so two identities that
        share identity values but differ in verification status would compare unequal.
        The fallback gate (REQ-003) compares identity values, not verification state.
        """
        if not isinstance(other, CorpusIdentity):
            return NotImplemented
        return (
            self.corpus_id,
            self.index_generation,
            self.schema_version,
            self.embedding_model_id,
            self.normalization_version,
            self.chunking_policy_version,
        ) == (
            other.corpus_id,
            other.index_generation,
            other.schema_version,
            other.embedding_model_id,
            other.normalization_version,
            other.chunking_policy_version,
        )

    def __hash__(self) -> int:
        """Hash the same six identity fields as ``__eq__``."""
        return hash(
            (
                self.corpus_id,
                self.index_generation,
                self.schema_version,
                self.embedding_model_id,
                self.normalization_version,
                self.chunking_policy_version,
            )
        )


def _unverified() -> CorpusIdentity:
    """Return an identity-unverified sentinel (``verified=False``)."""
    return CorpusIdentity(
        corpus_id="",
        index_generation=0,
        schema_version="",
        embedding_model_id="",
        normalization_version="",
        chunking_policy_version="",
        verified=False,
    )


def _table_exists(db: SQLiteHelper) -> bool:
    """Return True if the meta table exists in this database."""
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_META_TABLE,),
    ).fetchone()
    return row is not None


def compute_identity(
    db: SQLiteHelper,
    *,
    embedding_model_id: str,
    schema_version: str,
) -> CorpusIdentity:
    """Return the local corpus identity.

    Reads the single meta row and combines it with the caller-supplied current
    ``schema_version`` and ``embedding_model_id``. A missing or corrupt meta row yields an
    identity-unverified result (``verified=False``); an absent table (pre-migration
    database) also yields ``verified=False``.
    """
    if not _table_exists(db):
        return _unverified()
    row = db.execute(
        f"SELECT corpus_id, index_generation, normalization_version, "
        f"chunking_policy_version FROM {_META_TABLE} LIMIT 1"  # nosec B608 — table name is a module-level constant
    ).fetchone()
    if row is None or row[0] is None or row[1] is None:
        return _unverified()
    corpus_id, index_generation, normalization_version, chunking_policy_version = row
    return CorpusIdentity(
        corpus_id=str(corpus_id),
        index_generation=int(index_generation),
        schema_version=schema_version,
        embedding_model_id=embedding_model_id,
        normalization_version=""
        if normalization_version is None
        else str(normalization_version),
        chunking_policy_version=""
        if chunking_policy_version is None
        else str(chunking_policy_version),
        verified=True,
    )


def parse_remote_identity(body: Any) -> CorpusIdentity | None:
    """Parse a remote corpus identity from an HTTP response body.

    Reads the nested ``corpus_identity`` object (snake_case wire fields) and returns a
    :class:`CorpusIdentity`. Returns ``None`` when the body does not carry a complete
    identity — missing ``corpus_identity`` key, a non-object value, or any missing
    identity field — so callers treat it as unverifiable rather than guessing (REQ-002,
    REQ-003). Type coercion is best-effort; a coercion failure also yields ``None``.
    """
    if not isinstance(body, dict):
        return None
    raw = body.get("corpus_identity")
    if not isinstance(raw, dict):
        return None
    corpus_id = raw.get("corpus_id")
    index_generation = raw.get("index_generation")
    schema_version = raw.get("schema_version")
    embedding_model_id = raw.get("embedding_model_id")
    normalization_version = raw.get("normalization_version")
    chunking_policy_version = raw.get("chunking_policy_version")
    if corpus_id is None or index_generation is None or schema_version is None:
        return None
    if embedding_model_id is None or normalization_version is None:
        return None
    if chunking_policy_version is None:
        return None
    try:
        return CorpusIdentity(
            corpus_id=str(corpus_id),
            index_generation=int(index_generation),
            schema_version=str(schema_version),
            embedding_model_id=str(embedding_model_id),
            normalization_version=str(normalization_version),
            chunking_policy_version=str(chunking_policy_version),
            verified=bool(raw.get("verified", False)),
        )
    except (TypeError, ValueError):
        return None


def ensure_corpus_meta(
    db: SQLiteHelper,
    *,
    embedding_model_id: str,
    schema_version: str,
) -> CorpusIdentity | None:
    """Ensure a meta row exists and return the resulting identity.

    On first use inserts a row with a fresh ``uuid4`` ``corpus_id`` and
    ``index_generation=0`` (generated once, never regenerated) and stamps the current
    ``normalization_version`` / ``chunking_policy_version`` constants. Returns the identity,
    or ``None`` when the table is absent (pre-migration database). The table itself is
    created by the doc 02 DDL, never inline here.
    """
    if not _table_exists(db):
        return None
    db.execute(
        f"INSERT INTO {_META_TABLE} "  # nosec B608 — table name is a module-level constant; values parameterized
        "(corpus_id, index_generation, embedding_model_id, "
        "normalization_version, chunking_policy_version, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
        (
            str(uuid.uuid4()),
            0,
            embedding_model_id,
            NORMALIZATION_VERSION,
            CHUNKING_POLICY_VERSION,
            _now_iso(),
        ),
    )
    db.commit()
    return compute_identity(
        db, embedding_model_id=embedding_model_id, schema_version=schema_version
    )


def bump_index_generation(db: SQLiteHelper) -> int | None:
    """Best-effort increment of ``index_generation`` after a completed ingestion.

    Returns the new generation, or ``None`` on failure (leaving the previous generation in
    force). Never raises: a failed bump must not break ingestion completion (REQ-007).
    """
    try:
        if not _table_exists(db):
            return None
        db.execute(
            f"UPDATE {_META_TABLE} SET index_generation = index_generation + 1"  # nosec B608 — table name is a module-level constant
        )
        db.commit()
        row = db.execute(
            f"SELECT index_generation FROM {_META_TABLE} LIMIT 1"  # nosec B608 — table name is a module-level constant
        ).fetchone()
        return int(row[0]) if row is not None else None
    except sqlite3.Error:
        return None


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 ``Z`` string."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
