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
  - 90_shared_01_01_overview-purpose-and-scope.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 7. Import Direction Constraints

**Rule:** `shared/` → external libraries only. Imports from `agent/`, `mcp_servers/`, `rag/`, or `db/` are **prohibited**.

**Rule:** `db/` → `shared/` only. Imports from `agent/`, `mcp_servers/`, or `rag/` are **prohibited**.

Enforced by `.importlinter` (violations cause `PYTHONPATH=scripts uv run lint-imports` to fail).

Critical constraint: `orjson.dumps()` returns `bytes` (`not str`). If a `str` is required, you must call `.decode()`. For asynchronous HTTP, use `httpx.AsyncClient` instead of `requests`.

---

## 8. Persistent Data Overview

| DB File | Purpose |
|---|---|
| `rag.sqlite` | RAG document index + vector + FTS search |
| `session.sqlite` | Agent conversation state + memory layer |
| `workflow.sqlite` | Workflow engine task tracking |

All three databases use WAL mode and `busy_timeout`. `sqlite-vec` is loaded only for `rag.sqlite` (target=`"rag"`).

---

## 9. Key Constraints

- **Import Direction:** `shared/` → external only, `db/` → `shared/` only
- **JSON Library:** `orjson` (not the standard `json`); `orjson.dumps()` returns `bytes`
- **HTTP Client:** `httpx` (not `requests`); use `httpx.AsyncClient` for async
- **Configuration Format:** TOML / JSON under `/opt/llm/config/` — see [§2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-config-ownership) for ownership table
- **Log Messages:** English only (do not use Japanese in code comments or logs)
- **SQLite WAL:** Use `PRAGMA journal_mode=WAL` for all connections
- **Security Profile:** `SecurityProfile` enum in `mcp_config.py` (`local`/`production`). `ProductionConfigValidator` in `production_config_validator.py` validates strict keys, `tool_safety_tiers`, and `allowed_tools` when in production mode

---

## 10. Summary

`shared/` is the lowest dependency layer, providing configuration, logging, types, routing, plugin support, and DTOs. Code within `shared/` must not import higher-level layers.

`db/` provides typed, WAL-enabled SQLite access with FTS5 and sqlite-vec integration. It is the canonical source for schema definitions. `db/` depends only on `shared/`.

All persistent data resides in three SQLite files: `rag.sqlite` (RAG index), `session.sqlite` (conversation + memory), and `workflow.sqlite` (task tracking).

---

## 11. AI Reference Guide

You can identify corresponding documents from the section titles: Types/DTOs → [§2](90_shared_02_01_types_and_protocols-core-types.md), ConfigLoader → [§3](90_shared_03_01_runtime_and_execution-config-and-logging.md), SQLite Schema → [§4](90_shared_04_01_db_architecture_and_schema-overview-and-config.md), SQLiteHelper API → [§5](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md), Inconsistencies → [§90](90_shared_90_inconsistencies_and_known_issues.md).
