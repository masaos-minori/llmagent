"""tests/rag/test_identity_gate.py

Direct unit tests for the local corpus identity reader
(scripts/rag/identity_gate.py::compute_local_identity).
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from rag.corpus_identity import CorpusIdentity
from rag.identity_gate import compute_local_identity


def _identity(
    *,
    corpus_id: str = "cid-1",
    index_generation: int = 3,
    schema_version: str = "1",
    embedding_model_id: str = "embed-a",
    normalization_version: str = "n1",
    chunking_policy_version: str = "c1",
    verified: bool = True,
) -> CorpusIdentity:
    """Return a CorpusIdentity with the given field overrides."""
    return CorpusIdentity(
        corpus_id=corpus_id,
        index_generation=index_generation,
        schema_version=schema_version,
        embedding_model_id=embedding_model_id,
        normalization_version=normalization_version,
        chunking_policy_version=chunking_policy_version,
        verified=verified,
    )


# ── compute_local_identity ─────────────────────────────────────────────────────


class _Cursor:
    """Minimal cursor stand-in exposing fetchone()."""

    def __init__(self, rows: list) -> None:
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


def _make_db(
    *,
    embedding_row: tuple | None = ("embed-model-1",),
    meta_row: list | None = ["cid-9", 7, "norm-1", "chunk-1"],
) -> MagicMock:
    """Return a mock db whose execute() dispatches by SQL content."""
    db = MagicMock()

    def _execute(sql: str, *_args) -> _Cursor:
        if "sqlite_master" in sql:
            return _Cursor([(1,)])
        if "embedding_model_id" in sql:
            return _Cursor([list(embedding_row)] if embedding_row else [])
        if "rag_corpus_meta" in sql:
            return _Cursor([meta_row] if meta_row else [])
        return _Cursor([])

    db.execute.side_effect = _execute
    return db


def test_compute_local_identity_reads_verified() -> None:
    """A readable meta row yields a verified identity with the caller schema version."""
    identity = compute_local_identity(_make_db(), schema_version="1")
    assert identity.verified is True
    assert identity.corpus_id == "cid-9"
    assert identity.index_generation == 7
    assert identity.embedding_model_id == "embed-model-1"
    assert identity.schema_version == "1"


def test_compute_local_identity_fails_closed_on_read_error() -> None:
    """A read failure returns an unverified identity rather than raising."""
    db = MagicMock()
    db.execute.side_effect = sqlite3.OperationalError("boom")
    identity = compute_local_identity(db, schema_version="1")
    assert identity.verified is False
    assert identity.corpus_id == ""
    assert identity.schema_version == "1"
