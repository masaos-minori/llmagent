---
title: "Agent Data Layer - Access Patterns"
area: agent
tags:
  - agent
  - data-layer
  - rag-mcp
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_09_02_data-layer-access-patterns.md
---

# Agent Data Layer

- State and Persistence → [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

## Purpose

Documents the responsibility boundaries with the RAG layer and document access patterns from the agent.

## Design Intent

### Responsibility Boundaries with the RAG Layer

The Agent layer does not own `rag.sqlite`. These tables are owned by the RAG layer.

- The agent accesses document-level data through `rag-pipeline-mcp`.
- For statistics, use `DbMaintenanceService.stats()` or `RagMaintenanceService.stats_rag()`.

**Design judgment:** `/db rag urls` and `/db rag clean` call `rag_list_documents` and `rag_delete_document` via `rag-pipeline-mcp`. `DbMaintenanceService` no longer owns RAG document access for listing or deletion.

### Internal RAG MCP Paths

`RagPipelineMCPService` delegates `list_documents()` and `delete_document()` to its internal `DocumentManager`. `DocumentManager` directly accesses `rag.sqlite` through `SQLiteHelper("rag")`.

**Allowed:** `RagPipelineMCPService` / `DocumentManager` — the RAG MCP service owns these operations as part of its responsibility boundary.

**Not Allowed:** Application code in the agent, other MCP services, or shared layer code accessing `rag.sqlite` directly. They must use MCP tool calls or approved maintenance services.

#### Deletion Order Safety

To prevent orphaned records, `delete_document()` enforces a strict deletion order:

1. First, delete rows in `chunks_vec` (embedding vectors).
2. Then, delete rows in `documents` (parent documents).

**Design judgment:** This order is necessary because `chunks_vec` does not have a foreign key constraint pointing to `documents`. Deleting the document first would leave the embedding vector rows orphaned.

### Document Access Patterns on the Agent Side

| Path | Mechanism | Use Case |
|---|---|---|
| MCP Tools (Primary) | `ToolRouteResolver` → MCP server (`rag-pipeline-mcp` or `mdq-mcp`) | Standard operation |
| `/db` Command (Admin) | `/db rag urls` + `/db rag clean` → `rag-pipeline-mcp`; `/db rag stats` + maintenance → `DbMaintenanceService`/`RagMaintenanceService` | Administrative tasks only |
| Direct DB Access | Not recommended | Do NOT use in application code |

**Design judgment:** MCP tools are the recommended and supported route. Direct imports of `sqlite3` for `rag.sqlite` or `mdq.sqlite` are prohibited in standard application code.

## Responsibility Boundary

- **Canonical Source**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_document_manager.py`
- **Schema**: `schema_sql.py` (authority)

## Key Constraints

- Application code in the agent, other MCP services, or shared layer code is prohibited from accessing `rag.sqlite` directly.
- Since `chunks_vec` does not have a foreign key constraint to `documents`, deletion order is critical.

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_09_01_data-layer-session-db.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

RAG MCP internal path
document access patterns
responsibility boundary
