---
title: "Shared and DB Layer Overview - Constraints and Reference"
category: shared
tags:
  - shared
  - db
  - import-direction
  - constraints
  - executive-summary
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_01_overview-purpose-and-scope.md
  - 90_shared_01_02_overview-layer-responsibilities.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 7. Import Direction Constraints

**Rule:** `shared/` → external libraries only. Import from `agent/`, `mcp/`, `rag/`, `db/` is **prohibited**.

**Rule:** `db/` → `shared/` only. Import from `agent/`, `mcp/`, `rag/` is **prohibited**.

Enforced by `.importlinter` (fails `PYTHONPATH=scripts uv run lint-imports`).

Key constraint: `orjson.dumps()` returns `bytes`, not `str`. Always call `.decode()` when a `str` is required. Use `httpx.AsyncClient` (not `requests`) for async HTTP.

---

## 8. Overall Picture of Persistent Data

| DB File | Tables | Purpose |
|---|---|---|
| `rag.sqlite` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` | RAG document index + vector + FTS search |
| `session.sqlite` | `sessions`, `messages`, `memories`, `memories_fts`, `memories_vec`, `memory_links` | Agent conversation state + memory layer |
| `workflow.sqlite` | `tasks`, `attempts`, `processed_events`, `approvals`, `artifacts` | Workflow engine task tracking |

All three DBs use WAL mode and `busy_timeout`. sqlite-vec is loaded only for `rag.sqlite` (target=`"rag"`).

---

## 9. Major Constraints

| Constraint | Value |
|---|---|
| Import direction | `shared/` → external only; `db/` → `shared/` only |
| JSON library | `orjson` (not stdlib `json`); `orjson.dumps()` returns `bytes` |
| HTTP client | `httpx` (not `requests`); `httpx.AsyncClient` for async |
| Config format | TOML / JSON in `/opt/llm/config/`; `_`-prefixed keys are excluded |
| Log messages | English only (no Japanese in code comments or logs) |
| SQLite WAL | All connections use `PRAGMA journal_mode=WAL` |
| `agent.toml` | See [90_shared_03](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2a Config Ownership for full ownership table |
| Embedding dimension | `embedding_dims` in `agent.toml` (default 384) |

---

## 10. Executive Summary

`shared/` is the lowest dependency layer. It provides config, logging, types, routing,
plugin support, and DTOs. No code in `shared/` may import from upper layers.

`db/` provides typed, WAL-enabled SQLite access with FTS5 and sqlite-vec integration.
It is the canonical source for schema definitions. `db/` depends on `shared/` only.

All persistent data lives in three SQLite files: `rag.sqlite` (RAG index), `session.sqlite`
(conversation + memory), and `workflow.sqlite` (task tracking).

---

## 11. AI Reference Guide

| Question | Look in |
|---|---|
| What types/DTOs are defined in shared/? | [90_shared_02_01_types_and_protocols-core-types.md](90_shared_02_01_types_and_protocols-core-types.md) |
| How does ConfigLoader work? | [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md) |
| What SQLite schemas exist? | [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md) |
| What is the SQLiteHelper API? | [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md) |
| What bugs or inconsistencies exist? | [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_01_01_overview-purpose-and-scope.md`
- `90_shared_01_02_overview-layer-responsibilities.md`

## Keywords

import direction
constraints
persistent data
executive summary
ai reference guide
