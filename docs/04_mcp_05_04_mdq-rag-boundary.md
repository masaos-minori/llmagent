---
title: "MCP Security and Safety Model: MDQ vs RAG Boundary"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - mdq
  - rag
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
---

# MCP Security and Safety Model: MDQ vs RAG Boundary

## MDQ vs RAG boundary

> **Source of Truth.** This section consolidates content previously located in `04_mcp_07_mdq_rag_boundary.md` (removed in commit f24efc1).

### Purpose

Clearly defines the ownership boundaries between MDQ (Markdown Context Compression Engine) and RAG (Retrieval Augmented Generation), enabling engineers to decide which system to use for a specific task.

---

### When to use MDQ

Use MDQ when:

- Content is **Markdown only** (`.md`, `.markdown` files).
- Queries are related to **structure-aware search**: outlines, headings, hierarchical context.
- **Markdown-specific parsing** is required (section extraction, heading-based chunk boundaries).
- Workload is **low to medium volume** (thousands to tens of thousands of documents).

MDQ is optimized for Markdown documents where structural understanding is more critical than semantic embedding quality.

**Tools:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
**Database:** `mdq.sqlite` (separate from `rag.sqlite`)
**Status:** Production ready

---

### When to use RAG

Use RAG when:

- Content is **multi-format**: PDF, HTML, text, code, Markdown, etc.
- **Semantic search** via embeddings (similarity-based search) is required.
- **Chunking strategies** beyond heading-based splitting are needed (recursive, token-based, etc.).
- Workloads are **large scale**, or require **refinement** (reranking, hybrid search with RRF).
- A **document ingestion pipeline** with metadata extraction and validation is required.

RAG is the primary document retrieval system for the agent layer. It supports generic search across all content types.

**Tools:** `rag_run_pipeline` (execute pipeline), `rag_debug_pipeline` (debug execution/intermediate output), `rag_list_documents` (list documents), `rag_delete_document` (delete document) (via `rag-pipeline-mcp`).
*Note: There is no standalone search-only tool. Search is an inseparable stage within `rag_run_pipeline` or `rag_debug_pipeline`.*
**Database:** `rag.sqlite`
**Status:** Production ready

---

### Data Ownership

| System | Database | Owner | Administrator |
|---|---|---|---|
| MDQ | `mdq.sqlite` | MCP Layer (`scripts/mcp_servers/mdq/`) | mdq-mcp server (port 8013) |
| RAG | `rag.sqlite` | MCP Layer (`scripts/mcp_servers/rag_pipeline/`) | rag-pipeline-mcp server |

Neither system has direct access to the other's database. Each maintains its own schema, indexes, and search logic.

---

### Agent Access Patterns

The agent layer accesses both systems exclusively through **MCP tool calls**.

1. **Primary Path (Recommended):** The agent calls tools via MCP routing (`ToolRouteResolver`). All tool calls pass through the MCP server abstraction layer.
2. **Admin Bypass:** The `/db` command in the Agent REPL allows direct access to `rag.sqlite` for maintenance tasks. This is for administrators only and is not part of normal operation.
3. **Direct DB Access (Not Recommended):** Application code must NOT directly import `sqlite3` for `mdq.sqlite` or `rag.sqlite`. Always use MCP tools.

### RAG and Agent Responsibility Boundary

`RagPipeline` (`scripts/rag/pipeline.py`) handles the core RAG logic.
`rag-pipeline-mcp` (`scripts/mcp_servers/rag_pipeline/`) provides the production boundary via `RagPipelineMCPService` / `RagPipelineMCPServer`.
Direct imports are for testing and development purposes only.
*Note: This is currently a convention rather than enforced by `.importlinter` (the `agent -> rag` direction is currently permitted).*

---

### Routing Policy

#### 1. Routing Heuristics (Classifier)

The agent uses a lightweight classifier (`agent/mdq_rag_classifier.py`) to guide whether to choose MDQ or RAG based on the user query.

Queries containing Markdown structural terms (e.g., "heading", "outline", "hierarchy", "section", ".md", "table of contents") are classified as MDQ; otherwise, they default to RAG.

The classifier injects a single-line system prompt hint (~20-40 tokens) before each LLM turn. Since LLMs may not always follow this, use override mode if deterministic routing is required.

#### 2. Availability Fallback

| Condition | Behavior |
|---|---|
| MDQ selected, but `mdq-mcp` unavailable | Log WARNING; fallback to RAG hint |
| RAG selected, but `rag-pipeline-mcp` unavailable | Return error; no fallback |
| Override mode (`config_mode` = `mdq` or `rag`) | System prompt routing hint (`mdq_rag_classifier.py::resolve_mode()`, `mode_classification.py::classify_and_inject_mode()`); tool call failure returns error via `tool_transport_invoker.py` |

RAG is always the preferred fallback in production environments.

---

### Migration Criteria: MDQ to RAG

Consider migrating from MDQ to RAG when:

- Content volume exceeds approximately 100,000 documents.
- Non-Markdown content types need to be ingested alongside Markdown.
- Semantic similarity search quality becomes a bottleneck.
- Document deduplication or deduplication-aware search is required.

There is no automatic migration path. Migration requires re-ingestion via the RAG pipeline.

---

### Current State

- **MDQ:** Production ready. FTS5 search and indexing implemented.
- **RAG:** Production ready. Full ingestion pipeline, embedding support, and hybrid search (RRF) available.

For production workloads requiring general document search, prioritize `rag-pipeline-mcp`.
Use `mdq-mcp` only for Markdown-specific structural queries where embedding quality is not critical.

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`
- `00_security_01_architecture-and-trust-boundaries.md` — システムセキュリティアーキテクチャ / 信頼境界 / 脅威モデル / 認証認可 / 監査 / ローカルvs本番 / Fail-open/Fail-closed / プロンプトインジェクション責任境界

## Keywords

mcp
security
safety-model
mdq
rag
mdq-rag-boundary
routing
classifier
data-ownership
migration-criteria
