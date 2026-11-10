#!/usr/bin/env python3
"""scripts/rag/identity_gate.py — Local corpus identity reader (RAGCORPUS001).

Reads the local corpus identity from the open RAG database. The identity is surfaced
through ``RagPipeline.get_diagnostics()`` (corpus generation) and the rag-pipeline-mcp
identity view.

Public surface:
  compute_local_identity() : read local identity from the open RAG DB
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from rag.corpus_identity import CorpusIdentity, compute_identity

if TYPE_CHECKING:
    from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)

# The single-row corpus-identity table (DDL owned by scripts/db/schema_sql.py, doc 02).
# Read-only here; this module never emits the CREATE TABLE statement.
_META_TABLE = "rag_corpus_meta"


def compute_local_identity(db: SQLiteHelper, *, schema_version: str) -> CorpusIdentity:
    """Compute the local corpus identity from the open RAG database (RAGCORPUS001).

    Reads the stored embedding-model id from the meta row and combines it with the
    caller-supplied schema version; a missing/corrupt meta row yields an unverified
    identity (``verified=False``). Never raises — a read failure yields an unverified
    identity rather than breaking the caller.
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
