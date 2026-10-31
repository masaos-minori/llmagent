#!/usr/bin/env python3
"""scripts/rag/identity_gate.py — RAG fallback identity gate (RAGCORPUS001, REQ-003).

Pure decision logic for comparing a remote corpus identity against the local one
before accepting a remote-to-local fallback result, plus a helper that reads the
local identity from the open RAG database.

Extracted from ``scripts/rag/pipeline.py`` so the pipeline core stays under the
module-size gate while the identity-gate concern remains cohesive.

Public surface:
  GateDecision             : reject/degraded/proceed outcome
  _identity_gate(...)      : pure gate decision
  _safe_corpus_id(...)     : secret-free corpus id for logging
  compute_local_identity() : read local identity from the open RAG DB
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rag.corpus_identity import CorpusIdentity, compute_identity

if TYPE_CHECKING:
    from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)

# The single-row corpus-identity table (DDL owned by scripts/db/schema_sql.py, doc 02).
# Read-only here; this module never emits the CREATE TABLE statement.
_META_TABLE = "rag_corpus_meta"


@dataclass(frozen=True)
class GateDecision:
    """Outcome of the fallback identity gate (RAGCORPUS001, REQ-003).

    ``reject`` / ``degraded`` fire only when both identities are present and unequal;
    otherwise the gate proceeds and records the unverifiable state (user-approved
    2026-10-31 semantics: the fallback path carries ``remote_identity=None`` always,
    so a literal "missing on either side = reject" would reject every fallback and
    make the gate non-functional).
    """

    proceed: bool
    reason: str | None = None

    @property
    def reject(self) -> bool:
        """True when the fallback must be hard-rejected (reason recorded in diagnostics).

        Distinct from ``degraded``: a ``degraded`` mismatch does not reject — the
        caller proceeds to local re-execution and marks the result degraded. This
        keeps the ``degraded`` policy reachable rather than shadowed by the
        ``if gate.reject: return ""`` check in the pipeline.
        """
        return not self.proceed and self.reason != "identity_degraded"

    @property
    def degraded(self) -> bool:
        """True when the mismatch is tolerated under the ``degraded`` policy."""
        return not self.proceed and self.reason == "identity_degraded"


def _identity_gate(
    remote_identity: CorpusIdentity | None,
    local_identity: CorpusIdentity | None,
    *,
    policy: str,
) -> GateDecision:
    """Decide whether to accept a remote-to-local fallback (pure helper).

    Both sides present and unequal -> ``reject`` (default) or ``degraded`` (policy).
    Either side missing or identities equal -> proceed; the unverifiable state is left
    for the caller to record in diagnostics. ``policy`` is a plain string (``"reject\"``
    / ``"degraded\"``); any other value fails closed (reject).
    """
    if remote_identity is None or local_identity is None:
        return GateDecision(proceed=True)
    if remote_identity == local_identity:
        return GateDecision(proceed=True)
    if policy != "degraded":
        return GateDecision(proceed=False, reason="identity_mismatch")
    return GateDecision(proceed=False, reason="identity_degraded")


def _safe_corpus_id(identity: CorpusIdentity | None) -> str:
    """Return the corpus id for logging, or ``"unverified"`` when absent.

    Never logs a secret: only the public ``corpus_id`` (a UUID) is emitted.
    """
    return identity.corpus_id if identity is not None else "unverified"


def compute_local_identity(db: SQLiteHelper, *, schema_version: str) -> CorpusIdentity:
    """Compute the local corpus identity from the open RAG database (RAGCORPUS001).

    Reads the stored embedding-model id from the meta row and combines it with the
    caller-supplied schema version; a missing/corrupt meta row yields an unverified
    identity (``verified=False``). Never raises — a read failure fails closed at the
    gate (unverified local side) rather than breaking the fallback.
    """
    try:
        row = db.execute(
            f"SELECT embedding_model_id FROM {_META_TABLE} LIMIT 1"  # nosec B608 — table name is a module-level constant
        ).fetchone()
        embedding_model_id = row[0] if row is not None and row[0] is not None else ""
        return compute_identity(
            db,
            embedding_model_id=embedding_model_id,
            schema_version=schema_version,
        )
    except (sqlite3.Error, ValueError, TypeError):
        logger.warning(
            "RAG identity: local identity read failed; treating as unverified"
        )
        return CorpusIdentity(
            corpus_id="",
            index_generation=0,
            schema_version=schema_version,
            embedding_model_id="",
            normalization_version="",
            chunking_policy_version="",
            verified=False,
        )
