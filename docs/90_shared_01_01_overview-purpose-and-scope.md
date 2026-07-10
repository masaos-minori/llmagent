---
title: "Shared and DB Layer Overview - Purpose and Scope"
category: shared
tags:
  - shared
  - overview
  - purpose
  - scope
  - out-of-scope
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_02_overview-layer-responsibilities.md
  - 90_shared_01_03_overview-constraints-and-reference.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 1. Purpose

This document provides the high-level overview of the `shared/` and `db/` layers:
their purpose, scope, dependency relationships, import constraints, and the overall
picture of persistent data.

**Key points:**
- `shared/` provides cross-cutting infrastructure: config loading, logging, types, tool routing, plugins, OTel, and DTOs
- `db/` provides persistent storage: SQLite connection management, schema creation, store protocols, and maintenance
- Both are bottom-layer dependencies used by all other layers (`agent/`, `mcp/`, `rag/`)

---

## 2. Scope

**In scope:**
- All modules under `shared/`: `config_loader`, `config_errors`, `config_validator`, `logger`, `types`, `llm_types`, `transport_dto`, `action_result`, `events`, `protocols/shell`, `tool_constants`, `route_resolver`, `mcp_config`, `mcp_health`, `tool_executor`, `http_transport`, `plugin_registry`, `plugin_auto_discover`, `plugin_result`, `otel_tracer`, `otel_noop`, `token_counter`, `token_estimation`, `git_helper`, `formatters`, `json_utils`, `llm_exceptions`, `llm_transport_errors`, `llm_sse_stream`, `llm_sse_helpers`, `llm_reconnect`, `llm_retry`, `llm_payload`, `llm_hot_config`, `sse_parser`, `tool_registry`, `tool_routing_validation`, `tool_transport_invoker`, `tool_lifecycle`, `tool_executor_helpers`, `tool_spec`, `tool_cache`, `plugin_tool_invoker`
- All modules under `db/`: `config.py`, `helper.py`, `create_schema.py`, `models.py`, `schema_sql.py`, `store.py`, `store_impl.py`, `store_protocols.py`, `maintenance.py`, `rotation.py`, `recovery.py`, `rag_consistency.py`
- DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`

**Out of scope:**
- MCP server implementations (`mcp/`)
- RAG pipeline logic (`rag/`)
- Agent REPL (`agent/`)
- LLM and embedding servers (external processes)

---

## 3. Out of Scope

- Distributed or replicated SQLite configurations
- External vector databases (only in-process sqlite-vec)
- LLM communication protocol details (covered in `05_agent_05_llm-and-streaming.md`)

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_01_02_overview-layer-responsibilities.md`
- `90_shared_01_03_overview-constraints-and-reference.md`

## Keywords

shared
purpose
scope
out of scope
layer overview
