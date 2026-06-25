# docs/04_mcp_05_security_and_safety_model.md — restore MDQ vs RAG boundary content

**Plan:** `plans/20260625-094555_plan.md` (req #66)
**Target:** `docs/04_mcp_05_security_and_safety_model.md`

## What to change

### 1. Fix broken link at line 296

**Before:**
```markdown
6. **mdq-mcp is experimental.** FTS5 indexing and search are functionally implemented but not production-validated. Use `rag-pipeline-mcp` for production workloads. See [MDQ vs RAG boundary](04_mcp_07_mdq_rag_boundary.md) for guidance.
```

**After:**
```markdown
6. **mdq-mcp is experimental.** FTS5 indexing and search are functionally implemented but not production-validated. Use `rag-pipeline-mcp` for production workloads. See [§MDQ vs RAG Boundary](#mdq-vs-rag-boundary) below for guidance.
```

### 2. Replace stub section at lines 303-305 with full content

**Before (lines 303-305):**
```markdown
## MDQ vs RAG Boundary

詳細は「[MDQ vs RAG 境界定義](04_mcp_07_mdq_rag_boundary.md)」を参照。
```

**After** — replace with the full recovered content from `git show f24efc1~1:docs/04_mcp_07_mdq_rag_boundary.md`:

```markdown
## MDQ vs RAG Boundary

> **Canonical location.** This section consolidates content previously in `04_mcp_07_mdq_rag_boundary.md` (deleted in commit f24efc1).

### Purpose

Define clear ownership boundaries between MDQ (Markdown Context Compression Engine) and RAG (Retrieval Augmented Generation) so engineers can decide which system to use for a given task.

---

### When to Use MDQ

Use MDQ when:

- The content is **Markdown-only** (`.md`, `.markdown` files).
- The query is about **structure-aware retrieval**: outlines, headings, hierarchical context.
- You need **Markdown-specific parsing** (section extraction, chunk boundaries aligned with headings).
- The workload is **low-to-moderate volume** (thousands to tens of thousands of documents).

MDQ is optimized for Markdown documents where structural understanding matters more than semantic embedding quality.

**Tools:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
**Database:** `mdq.sqlite` (separate from `rag.sqlite`)
**Status:** Experimental — FTS5 search is functional but not production-validated.

---

### When to Use RAG

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

### Data Ownership

| System | Database | Owned by | Managed by |
|---|---|---|---|
| MDQ | `mdq.sqlite` | MCP layer (`mcp/mdq/`) | mdq-mcp server (port 8013) |
| RAG | `rag.sqlite` | MCP layer (`scripts/mcp/rag_pipeline/`) | rag-pipeline-mcp server |

Neither system accesses the other's database directly. Each maintains its own schema, indexing, and search logic.

---

### Agent Access Patterns

The agent layer accesses both systems through **MCP tool calls** only:

1. **Primary path (preferred):** Agent calls tools via MCP routing (`ToolRouteResolver`). All tool calls go through the MCP server abstraction.
2. **Admin bypass:** `/db` command in the agent REPL can access `rag.sqlite` directly for maintenance tasks. This is admin-only and not part of normal operation.
3. **Direct DB access (not recommended):** Application code should never import `sqlite3` against `mdq.sqlite` or `rag.sqlite`. Always use MCP tools.

---

### Routing Policy

#### 1. Routing Heuristic (Classifier)

The agent uses a lightweight classifier (`agent/mdq_rag_classifier.py`) to guide
tool selection between MDQ and RAG based on the user's query.

Queries containing Markdown-structural terms (e.g., "heading", "outline", "hierarchy",
"section", ".md", "table of contents") are classified as MDQ; all others default to RAG.

The classifier injects a one-line system prompt hint (~20-40 tokens) before each
LLM turn. The LLM may still deviate; use override mode for deterministic routing.

#### 2. Availability Fallback

| Condition | Behavior |
|---|---|
| MDQ selected, mdq-mcp unavailable | Log WARNING; fall back to RAG hint |
| RAG selected, rag-pipeline-mcp unavailable | Return error; no fallback |
| Override mode, forced server unavailable | Return error |

RAG is always the production-preferred fallback.

---

### Migration Criteria: MDQ to RAG

Consider migrating from MDQ to RAG when:

- Content volume exceeds ~100K documents.
- Non-Markdown content types need to be ingested alongside Markdown.
- Semantic similarity search quality becomes a bottleneck.
- Cross-document deduplication or dedup-aware retrieval is needed.

No automatic migration path exists. Migration requires re-ingesting through the RAG pipeline.

---

### Current Status

- **MDQ:** Experimental. FTS5 search is functional but not production-validated.
- **RAG:** Production-ready. Full ingestion pipeline, embedding support, and hybrid search (RRF) available.

For production workloads involving general-purpose document retrieval, prefer `rag-pipeline-mcp`.
Use `mdq-mcp` only for Markdown-specific structural queries where embedding quality is not critical.

---

### Boundary Enforcement

An automated pytest check (`tests/test_mdq_rag_boundary.py`) verifies the MDQ/RAG
boundary on every CI run. It scans source files for forbidden cross-DB references
and disallowed direct SQLite access in the agent layer.

#### Allowed access paths

| Layer | DB | Mechanism | Context |
|---|---|---|---|
| `mcp/mdq/` | `mdq.sqlite` | Own service | Normal operation |
| `scripts/mcp/rag_pipeline/` | `rag.sqlite` | Own service | Normal operation |
| Agent layer | `session.sqlite` | `SQLiteHelper("session")` | Normal operation |
| Agent layer | `workflow.sqlite` | `SQLiteHelper("workflow")` | Normal operation |
| Agent layer | `rag.sqlite` | `SQLiteHelper("rag")` via `RagMaintenanceService` | Admin-only `/db` commands |

#### Forbidden access paths

| Layer | DB | Reason |
|---|---|---|
| `mcp/mdq/` | `rag.sqlite` | Cross-DB dependency |
| `scripts/mcp/rag_pipeline/` | `mdq.sqlite` | Cross-DB dependency |
| Agent layer (normal) | `mdq.sqlite` or `rag.sqlite` | Use MCP tools, not direct DB access |

#### Handling false positives

If a new admin maintenance file requires direct `rag.sqlite` access, add its filename
to the `ALLOWED` set in `tests/test_mdq_rag_boundary.py` and document the exception
in the allowed-paths table above. Changes to `ALLOWED` require a design review comment in the PR.

---

### Known Issues

- FTS5 search is functional but not production-validated. The `/health` endpoint and tool metadata include `"stub": true` as an experimental status marker; this does not indicate non-functional behavior.
- **DB path alignment (resolved):** All config files now use `mdq.sqlite`. If an existing deployment has a `mdq.db` file on disk, rename it to `mdq.sqlite` before restarting the service.
```

## Validation

```
grep "04_mcp_07" docs/04_mcp_05_security_and_safety_model.md
# → 0 results
grep "MDQ vs RAG Boundary" docs/04_mcp_05_security_and_safety_model.md
# → section heading present
```
