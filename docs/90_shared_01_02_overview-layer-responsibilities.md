---
title: "Shared and DB Layer Overview - Layer Responsibilities"
category: shared
tags:
  - shared
  - db
  - layer-structure
  - responsibilities
  - architecture
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_01_overview-purpose-and-scope.md
  - 90_shared_01_03_overview-constraints-and-reference.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 4. Overall Layer Structure

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

## 5. Responsibilities of `shared/`

Bottom layer. All other layers depend on it.

**Ownership:** `shared` owns configuration types, DTOs, logging infrastructure, caching, client abstractions (LLM/MCP), token measurement, format utilities, OTel tracing, constants, streaming protocol.

**NOT in `shared/`:**
- Schema definitions, query execution, DB connection management → `db/`
- Business logic for tool calls → `agent/`
- RAG pipeline control → `rag/`

---

## 6. Responsibilities of `db/`

`db/` depends only on `shared/`.

**Ownership:** `db` owns schema management, migration, store protocols, backend implementations, recovery.

**NOT in `db/`:**
- Common type definitions → `shared/`
- Tool execution logic → `shared/tool_executor.py`
- LLM communication → `shared/llm_client.py`

---
