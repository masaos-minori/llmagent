"""tests/rag/test_identity_gate.py

Direct unit tests for the extracted RAG fallback identity gate
(scripts/rag/identity_gate.py). These lock in the pure decision logic at its new
layer boundary; pipeline-level behavior is covered separately by tests/rag/*.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from rag.corpus_identity import CorpusIdentity
from rag.identity_gate import (
    GateDecision,
    _identity_gate,
    _safe_corpus_id,
    compute_local_identity,
)


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


# ── GateDecision properties ────────────────────────────────────────────────────


def test_gate_decision_properties_default_proceed() -> None:
    """Default GateDecision proceeds and is neither reject nor degraded."""
    decision = GateDecision(proceed=True)
    assert decision.proceed is True
    assert decision.reject is False
    assert decision.degraded is False


def test_gate_decision_properties_reject() -> None:
    """A non-proceeding decision with a mismatch reason rejects, not degrades."""
    decision = GateDecision(proceed=False, reason="identity_mismatch")
    assert decision.proceed is False
    assert decision.reject is True
    assert decision.degraded is False


def test_gate_decision_properties_degraded() -> None:
    """A non-proceeding decision with the degraded reason degrades, not rejects."""
    decision = GateDecision(proceed=False, reason="identity_degraded")
    assert decision.proceed is False
    assert decision.reject is False
    assert decision.degraded is True


# ── _identity_gate ─────────────────────────────────────────────────────────────


def test_gate_rejects_when_both_present_and_unequal() -> None:
    """Both identities present and unequal -> reject under the default policy."""
    remote = _identity(corpus_id="cid-1")
    local = _identity(corpus_id="cid-2")
    decision = _identity_gate(remote, local, policy="reject")
    assert decision.reject is True
    assert decision.reason == "identity_mismatch"


def test_gate_degrades_when_policy_degraded() -> None:
    """Both present and unequal under 'degraded' policy -> degrade (not reject)."""
    remote = _identity(corpus_id="cid-1")
    local = _identity(corpus_id="cid-2")
    decision = _identity_gate(remote, local, policy="degraded")
    assert decision.degraded is True
    assert decision.reason == "identity_degraded"


def test_gate_proceeds_when_remote_missing() -> None:
    """Remote identity missing -> proceed (unverifiable); never rejects."""
    local = _identity(corpus_id="cid-1")
    decision = _identity_gate(None, local, policy="reject")
    assert decision.proceed is True
    assert decision.reject is False


def test_gate_proceeds_when_local_missing() -> None:
    """Local identity missing -> proceed (unverifiable); never rejects."""
    remote = _identity(corpus_id="cid-1")
    decision = _identity_gate(remote, None, policy="reject")
    assert decision.proceed is True
    assert decision.reject is False


def test_gate_proceeds_when_equal() -> None:
    """Both present and equal -> proceed regardless of policy."""
    remote = _identity(corpus_id="cid-1")
    local = _identity(corpus_id="cid-1")
    decision = _identity_gate(remote, local, policy="reject")
    assert decision.proceed is True


def test_gate_fails_closed_on_unknown_policy() -> None:
    """Any policy other than 'degraded' fails closed (reject)."""
    remote = _identity(corpus_id="cid-1")
    local = _identity(corpus_id="cid-2")
    decision = _identity_gate(remote, local, policy="bogus")
    assert decision.reject is True
    assert decision.reason == "identity_mismatch"


# ── _safe_corpus_id ────────────────────────────────────────────────────────────


def test_safe_corpus_id_returns_public_id() -> None:
    """Emits only the public corpus id, never a secret."""
    assert _safe_corpus_id(_identity(corpus_id="uuid-42")) == "uuid-42"


def test_safe_corpus_id_unverified_when_absent() -> None:
    """Returns 'unverified' when no identity is present."""
    assert _safe_corpus_id(None) == "unverified"


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
