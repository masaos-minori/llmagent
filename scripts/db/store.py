#!/usr/bin/env python3
"""db/store.py
Stable public import surface for the DB store layer.

ALWAYS import from this module — do NOT import from store_protocols.py or
store_impl.py directly.  Importing from sub-modules directly breaks the
abstraction boundary and makes future refactoring harder.

Module responsibilities:
  store.py           — THIS FILE: re-exports everything; the public API surface.
  store_protocols.py — Abstract Protocol contracts. Extend here when adding
                        a new storage operation or changing an existing signature.
  store_impl.py      — SQLite implementations. Extend here when adding or
                        modifying the concrete SQLite behavior.

How to extend the DB store:
  1. Add the new method to the Protocol in store_protocols.py.
  2. Implement it in the corresponding SQLite class in store_impl.py.
  3. Export the new symbol from store.py (__all__ and the import line).

Import examples:
    from db.store import VectorStore, SQLiteVectorStore
    from db.store import DocumentStore, SQLiteDocumentStore
    from db.store import SessionStore, SQLiteSessionStore
    from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore
    from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob
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
