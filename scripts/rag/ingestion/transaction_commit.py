#!/usr/bin/env python3
"""scripts/rag/ingestion/transaction_commit.py

Isolate atomic commit logic from ingester.py into TransactionManager class.

TransactionManager owns the BEGIN IMMEDIATE transaction boundary — it's the single
source of truth for commit integrity. File routing happens AFTER commit success,
outside the transaction boundary.
"""

from dataclasses import replace as dataclasses_replace
from pathlib import Path

from db.helper import SQLiteHelper
from rag.ingestion.document_manager import DocumentManager
from rag.ingestion.document_persistence import DocumentStore
from rag.models_data import PreparedChunk
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class TransactionManager:
    """Atomically commit all database changes for a URL inside BEGIN IMMEDIATE transaction."""

    def __init__(
        self,
        db: SQLiteHelper,
        doc_mgr: DocumentManager,
        doc_store: DocumentStore,
    ) -> None:
        """Initialize with SQLiteHelper, DocumentManager, and DocumentStore."""
        self._db = db
        self._doc_mgr = doc_mgr
        self._doc_store = doc_store

    def commit(
        self,
        url: str,
        doc_id: int | None,
        prepared_chunks: list[PreparedChunk],
        prepared_paths: list[Path],
        force: bool,
        replace: bool,
        title: str,
        lang: str,
        *,
        etag: str | None,
        last_modified: str | None,
        chunking_strategy: str,
        fetched_at: str,
    ) -> tuple[int | None, bool, bool]:
        """Atomically commit all database changes for a URL inside BEGIN IMMEDIATE transaction.

        Returns (doc_id, skip, replace) — same contract as DocumentStore.get_or_create().
        """
        with self._db.begin_immediate():
            new_doc_id: int | None = None
            if doc_id is None or replace:
                if replace and doc_id is not None:
                    self._doc_mgr.delete_existing_document(doc_id)
                cursor = self._doc_store.insert(
                    self._db,
                    url,
                    title,
                    lang,
                    etag,
                    last_modified,
                    chunking_strategy,
                    fetched_at,
                )
                if cursor.lastrowid is None:
                    raise RuntimeError("Failed to retrieve lastrowid after insertion")
                new_doc_id = cursor.lastrowid
                prepared_chunks = [
                    dataclasses_replace(pc, doc_id=new_doc_id) for pc in prepared_chunks
                ]
                doc_id = new_doc_id

            # Now insert the prepared chunks using the (possibly new/updated) doc_id
            self._insert_chunks_batch(self._db, prepared_chunks)

        # Commit succeeded — caller handles file routing via FileRouter
        return doc_id, False, False

    def _insert_chunks_batch(
        self,
        db: SQLiteHelper,
        prepared_chunks: list[PreparedChunk],
    ) -> int:
        """Insert multiple prepared chunks atomically within a single transaction. Returns the number of inserted chunks."""
        n = len(prepared_chunks)
        if n == 0:
            return 0
        inserted = 0
        for pc in prepared_chunks:
            cur = db.execute(
                "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content, chunk_type, source_file)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    pc.doc_id,
                    pc.chunk_index,
                    pc.content,
                    pc.normalized_content or None,
                    pc.chunk_type,
                    pc.source_file,
                ),
            )
            chunk_id = cur.lastrowid
            db.execute(
                "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, pc.embedding_blob),
            )
            inserted += 1
        return inserted
