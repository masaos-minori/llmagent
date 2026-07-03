#!/usr/bin/env python3
"""db — SQLite database layer for RAG and session management.

Public API (import from db.* submodules directly for clarity):
  - db.config:     DbConfig, build_db_config
  - db.helper:     SQLiteHelper
  - db.models:     DTO dataclasses
  - db.store:      Protocols + SQLite impls (protocol re-exports)
  - db.store_protocols: Protocol definitions + embedding helpers
  - db.store_impl:  SQLite-backed implementations
  - db.tool_results: ToolResultStore
  - db.maintenance: WAL checkpoint, vacuum, purge, rotation, recovery
  - db.schema_sql:  DDL templates for schema creation
"""

from db.config import DbConfig, build_db_config
from db.helper import SQLiteHelper
from db.maintenance import (
    RetentionConfig,
    checkpoint_wal,
    prune_old_memories,
    purge_old_sessions,
    vacuum_db,
)
from db.models import (
    DbHealthMetrics,
    DocumentRow,
    MessageRow,
    PurgeCounts,
    RagConsistencyReport,
    RecoveryResult,
    SessionRow,
    ToolResultRow,
    WalCheckpointCounts,
)
from db.rag_consistency import (
    check_rag_consistency,
    is_consistent,
    summarize_issues,
)
from db.recovery import recover_corruption
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
from db.tool_results import ToolResultStore

__all__ = [
    "DbConfig",
    "DbHealthMetrics",
    "DocumentRow",
    "DocumentStore",
    "MessageRow",
    "MemoryDeleteResult",
    "MemoryDeleteStore",
    "PurgeCounts",
    "RagConsistencyReport",
    "RecoveryResult",
    "RetentionConfig",
    "SessionRow",
    "SQLiteDocumentStore",
    "SQLiteHelper",
    "SQLiteMemoryDeleteStore",
    "SQLiteSessionStore",
    "SQLiteVectorStore",
    "SessionStore",
    "ToolResultRow",
    "ToolResultStore",
    "VectorStore",
    "WalCheckpointCounts",
    "build_db_config",
    "check_rag_consistency",
    "checkpoint_wal",
    "get_embedding_bytes",
    "get_embedding_dims",
    "is_consistent",
    "prune_old_memories",
    "purge_old_sessions",
    "recover_corruption",
    "rotate_all_dbs",
    "rotate_db",
    "rotate_session_db",
    "rotate_workflow_db",
    "summarize_issues",
    "validate_embedding_blob",
    "vacuum_db",
]
