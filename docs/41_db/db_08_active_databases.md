---
title: "Active Databases"
area: shared
tags:
  - shared
  - db
  - sqlite
  - active-databases
related:
  - shared_00_document-guide.md
  - db_01_architecture_and_schema-overview-and-config.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_06_api_and_operations-maintenance-and-rotation.md
  - db_07_api_and_operations-recovery-and-reference.md
---

# Active Databases

Inventory of the SQLite databases in use, their configuration sources, schema authorities, and lifecycle. Default file locations are defined by the configuration keys listed below, not by this document.

Backup and recovery operations are described in [db_06](db_06_api_and_operations-maintenance-and-rotation.md) and [db_07](db_07_api_and_operations-recovery-and-reference.md). No backup schedule is defined by the code in this repository.

All databases are owned by the Agent team and use WAL journal mode, except as noted below.

## rag.sqlite

- **Config source**: `rag_db_path` (set in `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `config/ingester.toml`, and `config/crawler.toml`; the values must refer to the same database)
- **Schema authority**: `scripts/db/schema_sql.py` (`build_rag_schema_sql(dims)`)
- **Lifecycle**: Created on first RAG pipeline use; persists until deleted
- **Vector schema**: `chunks_vec` with an L2 distance metric; the embedding dimension is the code-level constant `QWEN3_EMBEDDING_DIMS`

## session.sqlite

- **Config source**: `session_db_path` in `config/agent.toml`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_session_schema_sql(dims)`)
- **Lifecycle**: Created on first agent use; persists until deleted
- **Vector schema**: `memories_vec` with an L2 distance metric; the embedding dimension is the code-level constant `QWEN3_EMBEDDING_DIMS`

## workflow.sqlite

- **Config source**: `workflow_db_path` (read by `scripts/db/config.py`; optional key of the `agent.toml` configuration, with a code-level default)
- **Schema authority**: `scripts/db/schema_sql.py` (`build_workflow_schema_sql()`)
- **Lifecycle**: Created on first workflow use; persists until deleted
- **Tables**: tasks, attempts, processed_events, artifacts, approvals, workflow_schema_version

## eventbus.sqlite

- **Config source**: `eventbus_db_path` in `config/agent.toml` and `db_path` in `config/eventbus.toml` (the values must refer to the same database)
- **Schema authority**: `scripts/db/schema_sql.py` (`build_eventbus_schema_sql()`)
- **Lifecycle**: Created on first event bus use; persists until deleted
- **Tables**: events, consumer_delivery, consumer_offsets

## mdq.sqlite

- **Config source**: `db_path` in `config/mdq_mcp_server.toml`
- **Schema authority**: `scripts/mcp_servers/mdq/db_schema.py`
- **Busy timeout**: `sqlite_busy_timeout` in the MDQ server configuration
- **Lifecycle**: Created on first MDQ use; persists until deleted

## Related ADRs

- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — Separating SQLite into Four Databases

## Keywords

- active databases
- rag.sqlite
- session.sqlite
- workflow.sqlite
- eventbus.sqlite
- mdq.sqlite
- WAL
- schema authority
