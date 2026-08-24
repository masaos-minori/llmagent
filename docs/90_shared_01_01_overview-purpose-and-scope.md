---
title: "Shared and DB Layer Overview - Purpose and Scope"
area: shared
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

---

## 3. Out of Scope

- Distributed or replicated SQLite configurations
- External vector databases (only in-process `sqlite-vec` is supported)
- Detailed LLM communication protocols (handled in [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md))

---
