---
title: "Shared and DB Layer Overview"
area: shared
tags:
  - shared
  - db
  - overview
  - purpose
  - scope
  - out-of-scope
  - layer-structure
  - responsibilities
  - architecture
  - import-direction
  - constraints
  - executive-summary
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 00_governance_03_issue-and-uncertainty-management.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 1. Purpose

This document provides an overview of the `shared/` and `db/` layers. It covers purpose, scope, dependencies, import constraints, and the overall architecture of persistent data.

**Key Points:**
- `shared/` provides cross-cutting infrastructure: configuration loading, logging, types, tool routing, OTel, and DTOs.
- `db/` provides persistent storage: SQLite connection management, schema creation, store protocols, and maintenance.
- Both are low-level dependencies used by all other layers (`agent/`, `mcp_servers/`, `rag/`).

---

## 2. Scope

**In Scope:**
- `shared` provides configuration types, DTOs, logging infrastructure, caching, and client abstractions.
- `db` provides schema management, migration, store protocols, backend implementations, and recovery.
- DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`

**Out of Scope:**
- MCP server implementations (`mcp_servers/`)
- RAG pipeline logic (`rag/`)
- Agent REPL (`agent/`)
- LLM and embedding servers (external processes)
- Distributed or replicated SQLite configurations
- External vector databases (only in-process `sqlite-vec` is supported)
- Detailed LLM communication protocols (handled in [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md))

---

## 3. Overall Layer Structure

``` text
External Libraries
        ↑
   shared/          ← Bottom layer. All other layers depend on this.
        ↑
       db/           ← Depends only on shared/
        ↑
  rag/ | mcp_servers/   ← Depend on db/ and shared/
        ↑
      agent/           ← Depends on all layers
```

Import direction is enforced by `.importlinter`. Violations cause `lint-imports` to fail.

---

## 4. Responsibilities of `shared/`

Bottom layer. All other layers depend on it.

**Ownership:** `shared` owns configuration types, DTOs, logging infrastructure, caching, client abstractions (LLM/MCP), token measurement, format utilities, OTel tracing, constants, streaming protocol.

**NOT in `shared/`:**
- Schema definitions, query execution, DB connection management → `db/`
- Business logic for tool calls → `agent/`
- RAG pipeline control → `rag/`

---

## 5. Responsibilities of `db/`

`db/` depends only on `shared/`.

**Ownership:** `db` owns schema management, migration, store protocols, backend implementations, recovery.

**NOT in `db/`:**
- Common type definitions → `shared/`
- Tool execution logic → `shared/tool_executor.py`
- LLM communication → `shared/llm_client.py`

---

## 6. Import Direction Constraints

**Rule:** `shared/` → external libraries only. Imports from `agent/`, `mcp_servers/`, `rag/`, or `db/` are **prohibited**.

**Rule:** `db/` → `shared/` only. Imports from `agent/`, `mcp_servers/`, or `rag/` are **prohibited**.

Enforced by `.importlinter` (violations cause `PYTHONPATH=scripts uv run lint-imports` to fail).

Critical constraint: `orjson.dumps()` returns `bytes` (`not str`). If a `str` is required, you must call `.decode()`. For asynchronous HTTP, use `httpx.AsyncClient` instead of `requests`.

---

## 7. Persistent Data Overview

| DB File | Purpose |
|---|---|
| `rag.sqlite` | RAG document index + vector + FTS search |
| `session.sqlite` | Agent conversation state + memory layer |
| `workflow.sqlite` | Workflow engine task tracking |

All three databases use WAL mode and `busy_timeout`. `sqlite-vec` is loaded only for `rag.sqlite` (target=`"rag"`).

---

## 8. Other Key Constraints

Constraints not already covered above (import direction, JSON library, HTTP client — see section 6):

- **Configuration Format:** TOML / JSON under `/opt/llm/config/` — see [section 2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-config-ownership) for ownership table
- **Log Messages:** English only (do not use Japanese in code comments or logs)
- **SQLite WAL:** Use `PRAGMA journal_mode=WAL` for all connections
- **Security Profile:** `SecurityProfile` enum in `mcp_config.py` (`local`/`production`). `ProductionConfigValidator` in `production_config_validator.py` validates strict keys, `tool_safety_tiers`, and `allowed_tools` when in production mode

---

## 9. Summary

`shared/` is the lowest dependency layer, providing configuration, logging, types, routing, plugin support, and DTOs. Code within `shared/` must not import higher-level layers.

`db/` provides typed, WAL-enabled SQLite access with FTS5 and sqlite-vec integration. It is the canonical source for schema definitions. `db/` depends only on `shared/`.

All persistent data resides in three SQLite files: `rag.sqlite` (RAG index), `session.sqlite` (conversation + memory), and `workflow.sqlite` (task tracking).

---

## 10. AI Reference Guide

You can identify corresponding documents from the section titles: Types/DTOs → [section 2](90_shared_02_01_types_and_protocols-core-types.md), ConfigLoader → [section 3](90_shared_03_01_runtime_and_execution-config-and-logging.md), SQLite Schema → [section 4](90_shared_04_01_db_architecture_and_schema-overview-and-config.md), SQLiteHelper API → [section 5](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md), Inconsistencies → [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md) (Part 1, Area: Shared/DB).
