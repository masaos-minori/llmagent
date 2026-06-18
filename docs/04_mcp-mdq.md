# MCP: MDQ vs RAG — Boundary Definition

## Purpose

Define clear ownership boundaries between MDQ (Markdown Context Compression Engine) and RAG (Retrieval Augmented Generation) so engineers can decide which system to use for a given task.

---

## When to Use MDQ

Use MDQ when:

- The content is **Markdown-only** (`.md`, `.markdown` files).
- The query is about **structure-aware retrieval**: outlines, headings, hierarchical context.
- You need **Markdown-specific parsing** (section extraction, chunk boundaries aligned with headings).
- The workload is **low-to-moderate volume** (thousands to tens of thousands of documents).

MDQ is optimized for Markdown documents where structural understanding matters more than semantic embedding quality.

**Tools:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
**Database:** `mdq.sqlite` (separate from `rag.sqlite`)
**Status:** Experimental (`stub: true` in server catalog)

---

## When to Use RAG

Use RAG when:

- The content is **multi-format**: PDF, HTML, text, code, Markdown, etc.
- **Semantic search** via embeddings is needed (similarity-based retrieval).
- You need **chunking strategies** beyond heading-aligned splits (recursive, token-based, etc.).
- The workload involves **high volume** or requires **refinement** (re-ranking, hybrid search with RRF).
- You need **document ingestion pipelines** with metadata extraction and validation.

RAG is the primary document retrieval system for the agent layer. It supports general-purpose retrieval across all content types.

**Tools:** `ingest`, `search`, `get_document`, `delete_document`, `list_documents` (via rag-pipeline-mcp)
**Database:** `rag.sqlite`
**Status:** Production-ready

---

## Data Ownership

| System | Database | Owned by | Managed by |
|---|---|---|---|
| MDQ | `mdq.sqlite` | MCP layer (`mcp/mdq/`) | mdq-mcp server (port 8013) |
| RAG | `rag.sqlite` | MCP layer (`mcp/rag_pipeline/`) | rag-pipeline-mcp server |

Neither system accesses the other's database directly. Each maintains its own schema, indexing, and search logic.

---

## Agent Access Patterns

The agent layer accesses both systems through **MCP tool calls** only:

1. **Primary path (preferred):** Agent calls tools via MCP routing (`ToolRouteResolver`). All tool calls go through the MCP server abstraction.
2. **Admin bypass:** `/db` command in the agent REPL can access `rag.sqlite` directly for maintenance tasks. This is admin-only and not part of normal operation.
3. **Direct DB access (not recommended):** Application code should never import `sqlite3` against `mdq.sqlite` or `rag.sqlite`. Always use MCP tools.

---

## Migration Criteria: MDQ to RAG

Consider migrating from MDQ to RAG when:

- Content volume exceeds ~100K documents.
- Non-Markdown content types need to be ingested alongside Markdown.
- Semantic similarity search quality becomes a bottleneck.
- Cross-document deduplication or dedup-aware retrieval is needed.
- Multi-modal content (images, code blocks with syntax awareness) requires specialized chunking.

No automatic migration path exists. Migration would require:
1. Exporting MDQ documents (index_paths → file list).
2. Re-ingesting through the RAG pipeline with appropriate chunking strategy.
3. Updating tool routing to point to rag-pipeline-mcp instead of mdq-mcp.

---

## Current Status

- **MDQ:** Experimental. FTS5 search is functional but not production-validated. Tool responses may be stub data in some configurations.
- **RAG:** Production-ready. Full ingestion pipeline, embedding support, and hybrid search (RRF) available.

For production workloads involving general-purpose document retrieval, prefer `rag-pipeline-mcp`. Use `mdq-mcp` only for Markdown-specific structural queries where embedding quality is not critical.
