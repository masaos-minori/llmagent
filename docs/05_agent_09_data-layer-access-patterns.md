---
title: "Agent Data Layer"
category: agent
tags:
  - agent
  - agent
  - data-layer
  - database
  - sqlite
related:
  - 05_agent_00_document-guide.md
---

# Agent Data Layer

s (Agent-facing)

The agent layer does NOT own rag.sqlite. These tables are owned by the RAG layer.
The agent accesses document-level data through `rag-pipeline-mcp` (for `/db rag urls` and `/db rag clean`),
and counts through `DbMaintenanceService.stats()` or `RagMaintenanceService.stats_rag()` (for `/db rag stats`).

| Table | Used by agent for |
|---|---|
| `documents` | `/db rag urls` (via `rag_list_documents` MCP), `/db rag clean` (via `rag_delete_document` MCP) |
| `chunks` | `/db rag stats`, `/db rag rebuild-fts` |
| `chunks_fts` | `/db rag rebuild-fts` (FTS5 virtual table) |
| `chunks_vec` | `/db rag stats` |

**Responsibility boundary:** `/db rag urls` and `/db rag clean` call `rag_list_documents` and
`rag_delete_document` via rag-pipeline-mcp. `DbMaintenanceService` no longer owns RAG
document access for listing or deletion.

---

## RAG MCP Internal

 Path

`RagPipelineMCPService` directly accesses `rag.sqlite` through `SQLiteHelper("rag")` for
`list_documents()` and `delete_document()`. This is an internal operation of the RAG MCP
service owner, not Agent-layer direct DB access.

**Allowed:** `RagPipelineMCPService` (scripts/mcp/rag_pipeline/service.py) — RAG MCP service owns
these operations as part of its responsibility boundary.

**Not allowed:** Agent application code, other MCP services, or shared-layer code accessing
`rag.sqlite` directly. These must use MCP tool calls or approved maintenance services.

### Deletion order safety

`delete_document()` enforces a strict deletion order to prevent orphan records:

1. Delete `chunks_vec` rows first (embedding vectors)
2. Delete `documents` row (parent document)

This order is necessary because `chunks_vec` has no foreign key constraint pointing to
`documents`. Deleting the document first would leave orphaned embedding vector rows.

```python
# delete_document() — order matters
db.execute(
    "DELETE FROM chunks_vec"
    " WHERE chunk_id IN"
    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
    (doc_id,),
)
db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
```

Other derived records (e.g., `chunks` table rows) rely on cascade deletes or triggers
where applicable.

---

## Agent-Side Docum

ent Access Patterns

The agent accesses document data through three paths:

| Path | Mechanism | When to use |
|---|---|---|
| MCP tools (primary) | `ToolRouteResolver` → MCP server (rag-pipeline-mcp or mdq-mcp) | Normal operation; all agent turns |
| `/db` commands (admin) | `/db rag urls`+`/db rag clean` → rag-pipeline-mcp; `/db rag stats`+maintenance → `DbMaintenanceService`/`RagMaintenanceService` | Admin tasks only |
| Direct DB access | Not recommended | Never in application code |

MCP tools are the preferred and supported path. Direct `sqlite3` imports against `rag.sqlite` or `mdq.sqlite` are not allowed in normal application code. The `/db` admin commands use `RagMaintenanceService` as an explicit maintenance exception (see [04_mcp_05 §Agent Access Patterns](04_mcp_05_security_and_safety_model.md#agent-access-patterns)). See [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary) for the boundary between RAG and MDQ systems.

- **MDQ**: Markdown query server. Access via `mdq-mcp` tools only. FTS5 search and indexing implemented. See [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary) for the RAG/MDQ boundary.

## Memory Tables (o

ptional)

When `use_memory_layer=True`, the memory subsystem uses both JSONL and SQLite:

| Storage | Path | Contents |
|---|---|---|
| JSONL | `{memory_jsonl_dir}/memories.jsonl` | Append-only archive for import/export and disaster recovery |
| SQLite: `memories` | `session.sqlite` (same DB as sessions/messages) | Authoritative current memory state |
| SQLite: `memories_fts` | same DB | FTS5 index over memory content |
| SQLite: `memory_links` | same DB | Many-to-many links between memories |
| SQLite: `memories_vec` | same DB | Optional KNN embeddings |

Data ownership: memory layer owns these tables. Agent accesses via `ctx.services.memory`.

**Current behavior:** SQLite memory tables are authoritative for current memory state. JSONL is retained as an append-only archive for import/export and disaster recovery. Deletes and pin/unpin state changes are not replayed from JSONL.

All memory SQLite tables (`memories`, `memories_fts`, `memory_links`, `memories_vec`) live in `session.sqlite`. No separate memory SQLite database is used.

---

## Context Manager 

## Related Documents

- `agent`
- `data-layer`
- `database`

## Keywords

agent
data-layer
database
sqlite
