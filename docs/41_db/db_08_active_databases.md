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
  - adr_02_05_008_db-sqlite-4db-separation.md
---

# Active Databases

Inventory of the SQLite databases in use, their configuration sources, schema authorities, and lifecycle. Default file locations are defined by the configuration keys listed below, not by this document.

Backup and recovery operations are described in [db_06](db_06_api_and_operations-maintenance-and-rotation.md) and [db_07](db_07_api_and_operations-recovery-and-reference.md). No backup schedule is defined by the code in this repository.

Each database is owned by a single component (see the **Owner** line of each section) and uses WAL journal mode.

## rag.sqlite

- **Owner**: the RAG layer (`scripts/rag/`, `scripts/mcp_servers/rag_pipeline/`); the agent accesses it only through `rag-pipeline-mcp` and the admin-only maintenance services
- **Config source**: `rag_db_path` (set in `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `config/ingester.toml`, and `config/crawler.toml`; the values must refer to the same database)
- **Schema authority**: `scripts/db/schema_sql.py` (`build_rag_schema_sql(dims)`)
- **Lifecycle**: Created on first RAG pipeline use; persists until deleted
- **Vector schema**: `chunks_vec` with an L2 distance metric; the embedding dimension is the code-level constant `QWEN3_EMBEDDING_DIMS`

## session.sqlite

- **Owner**: the Agent layer (`scripts/agent/`)
- **Config source**: `session_db_path` in `config/agent.toml`
- **Schema authority**: `scripts/db/schema_sql.py` (`build_session_schema_sql(dims)`)
- **Lifecycle**: Created on first agent use; persists until deleted
- **Vector schema**: `memories_vec` with an L2 distance metric; the embedding dimension is the code-level constant `QWEN3_EMBEDDING_DIMS`

## workflow.sqlite

- **Owner**: the workflow engine in the Agent layer (`scripts/agent/workflow/`)
- **Config source**: `workflow_db_path` (read by `scripts/db/config.py`; optional key of the `agent.toml` configuration, with a code-level default)
- **Schema authority**: `scripts/db/schema_sql.py` (`build_workflow_schema_sql()`)
- **Lifecycle**: Created on first workflow use; persists until deleted

## eventbus.sqlite

- **Owner**: the EventBus service (`scripts/eventbus/`)
- **Config source**: `db_path` in `config/eventbus.toml` only; `agent.toml` carries no eventbus path
- **Schema source**: `scripts/eventbus/schema.sql` is the only DDL definition; the EventBus service and its tool read it
- **Lifecycle**: Created on first event bus use; persists until deleted

## mdq.sqlite

- **Owner**: the `mdq-mcp` server (`scripts/mcp_servers/mdq/`)
- **Config source**: `db_path` in `config/mdq_mcp_server.toml`
- **Schema authority**: `scripts/mcp_servers/mdq/db_schema.py`
- **Busy timeout**: `sqlite_busy_timeout` in the MDQ server configuration
- **Lifecycle**: Created on first MDQ use; persists until deleted
- **Rebuild**: derived store, rebuildable from the Markdown sources; backup and rotation helpers do not cover it. To rebuild, stop the `mdq-mcp` server, delete the `db_path` file if a clean index is required, start the server (it recreates the file and tables), re-run `index_paths` over the `allowed_dirs` roots, then confirm with `stats`. See [MDQ tools](../22_mcp/mcp_04_04_mdq.md) and [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) (Derived Stores Outside the Four Domains)

## mcp_dedup.sqlite

- **Owner**: the shared MCP dispatcher (`scripts/mcp_servers/dispatch.py`)
- **Config source**: `db_path` in `config/mcp_dedup.toml` only; `agent.toml` carries no dedup path
- **Schema authority**: `scripts/shared/mcp_dedup_schema.py` (canonical DDL: `dedup_call_state`,
  `store_meta`, `call_attempt_history`); creation also stamps the store identity: a `store_meta`
  row (store uuid + generation), `PRAGMA user_version = 1`, and the external installation marker
  `.mcp_dedup_installed` next to the database file
- **Lifecycle**: Created by `deploy/init_db.sh` at deploy time (which verifies the identity stamp
  and aborts on a refused open); reopened by every dispatcher process via `open_dedup_store`;
  persists until archived by the operator
- **Row semantics**: `dedup_call_state` rows carry lease columns (`owner_id`,
  `lease_expires_epoch`, `attempt_number`); `pending` rows hold a lease, terminal rows
  (`completed`/`failed`/`interrupted`) are immutable. `call_attempt_history` records each
  attempt/finalization/reconciliation decision. See [db_03_07](db_03_07_mcp-dedup-and-execution-snapshot.md).
- **Rebuild**: disposable dedup-log cache; backup and rotation helpers do not cover it. Unlike
  derived stores such as mdq, its evidence is archive-only: it is never auto-rebuilt from any
  source. Recovery is the operator runbook below. See [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) (Derived Stores Outside the Four Domains)

### Operator resolution runbook (mcp_dedup)

A store open classifies the file before any write and refuses with a `DedupStoreError` state:
`lost` (a known generation's file is gone), `replaced` (the installation marker names a
different store), `legacy_or_unverified` (pre-change shape, missing identity row, or missing
marker), or `schema_mismatch` (canonical fingerprint or `PRAGMA user_version` drift). The
refusal log line and `init_db.sh`'s `[gate]` abort message name the state and the file path.

Resolution is `scripts/shared/mcp_dedup.py::resolve_store(db_path)`:

1. It refuses a healthy store (resolution is only for lost, replaced, legacy, or drifted stores).
2. It records the previous generation (identity row first, installation marker as fallback).
3. It archives the old file as `<path>.corrupt-<timestamp>` (wal/shm sidecars included) and
   removes the installation marker.
4. It creates a new store generation, stamps it with `previous generation + 1`, and logs the
   decision line (`archived=... previous_generation=... new_generation=...`).

An empty or missing file alone never resolves anything by itself: only this operation performs
the rollover, and services restart normally afterwards — a fresh empty store only means the
next call of each key runs for real.

## Related ADRs

- [ADR-008](../10_adr/adr_02_05_008_db-sqlite-4db-separation.md) — Separating SQLite into Six Databases

## Keywords

- active databases
- rag.sqlite
- session.sqlite
- workflow.sqlite
- eventbus.sqlite
- mdq.sqlite
- mcp_dedup.sqlite
- WAL
- schema authority
