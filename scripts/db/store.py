#!/usr/bin/env python3
"""db/store.py — Re-export stub for backward compatibility.

Protocols and embedding helpers are in db/store_protocols.py.
SQLite implementations are in db/store_impl.py.

All existing imports through this module continue to work:
    from db.store import VectorStore, SQLiteVectorStore, get_embedding_dims
    from db.store import DocumentStore, SQLiteDocumentStore
    from db.store import SessionStore, SQLiteSessionStore
    from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore
"""

from db.store_impl import (
    SQLiteDocumentStore,
    SQLiteMemoryDeleteStore,
    SQLiteSessionStore,
    SQLiteVectorStore,
)
from db.store_protocols import (
    DocumentStore,
    MemoryDeleteResult,
    MemoryDeleteStore,
    SessionStore,
    VectorStore,
    get_embedding_bytes,
    get_embedding_dims,
    validate_embedding_blob,
)

__all__ = [
    "DocumentStore",
    "MemoryDeleteResult",
    "MemoryDeleteStore",
    "SessionStore",
    "VectorStore",
    "SQLiteDocumentStore",
    "SQLiteMemoryDeleteStore",
    "SQLiteSessionStore",
    "SQLiteVectorStore",
    "get_embedding_bytes",
    "get_embedding_dims",
    "validate_embedding_blob",
]
