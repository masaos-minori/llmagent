## 1. Goal
- Document MDQ hybrid search (Phase 2) design and clarify the MDQ FTS5 vs RAG semantic search responsibility boundary in `docs/04_mcp_04_server_catalog.md`.

## 2. Scope
- **In-Scope**:
  - Add to MDQ section in `docs/04_mcp_04_server_catalog.md`:
    - Distinction between FTS5-only (Phase 1) and hybrid search (Phase 2)
    - `use_embedding = false` is the default
    - Decision criteria for MDQ hybrid search vs RAG usage
    - Overview of RRF (Reciprocal Rank Fusion) merge strategy
- **Out-of-Scope**:
  - `_search_vector` implementation (stub remains, Phase 2 out of scope)
  - Production use of `use_embedding = true`
  - RAG pipeline code changes

## 3. Requirements
### Functional
- MDQ section in server catalog documents both search modes clearly
- Decision criteria for when to use MDQ hybrid vs RAG semantic search
- RRF merge strategy overview documented

### Non-functional
- No content duplication with existing `docs/04_mcp_07_mdq_rag_boundary.md` — reference link only, not duplicate content

## 4. Architecture
### Component Boundaries
```
docs/04_mcp_04_server_catalog.md (mdq-mcp section)
  ├── FTS5-only (Phase 1) — production baseline, use_embedding = false
  ├── Hybrid Search (Phase 2) — use_embedding = true, RRF merge
  │     └── _search_vector stub in search.py (empty list return)
  ├── MDQ hybrid vs RAG decision criteria
  └── Link to docs/04_mcp_07_mdq_rag_boundary.md for detailed boundary
```

## 5. Module Design
No code changes. Documentation-only update to `docs/04_mcp_04_server_catalog.md`.

## 6. Interface Design
### New MDQ Section Content

```markdown
## mdq-mcp (port 8013)

**Purpose:** Markdown document indexing and context compression

**Search modes:**

| Mode | Description | Config |
|---|---|---|
| FTS5-only (Phase 1) | Full-text search via FTS5; production baseline | `use_embedding = false` (default) |
| Hybrid (Phase 2) | FTS5 + semantic vector search merged via RRF | `use_embedding = true` |

**Hybrid Search (Phase 2):**

When `use_embedding = true`, MDQ performs hybrid search:
1. FTS5 keyword search on `chunks_fts`
2. Semantic vector search via `_search_vector()` (stub — returns empty list in Phase 1)
3. Results merged via Reciprocal Rank Fusion (RRF)

**MDQ Hybrid vs RAG Decision Criteria:**

| Use Case | Recommended | Rationale |
|---|---|---|
| Markdown structural queries (headings, sections, outlines) | MDQ hybrid | MDQ understands Markdown document structure; FTS5 is precise for keyword matching within documents |
| General semantic search across all indexed content | RAG pipeline | RAG has broader corpus coverage and mature embedding model integration |
| Cross-document structural comparison | MDQ hybrid | MDQ chunk_id includes heading hierarchy (level, parent_path, ordinal) |

**DB path:** `/opt/llm/db/mdq.sqlite` (`config/mdq_mcp_server.toml`: `db_path`)

> **Note:** For detailed MDQ vs RAG boundary definition, see [04_mcp_07_mdq_rag_boundary.md](04_mcp_07_mdq_rag_boundary.md).

**Log:** `/opt/llm/logs/mdq-mcp.log`
```

## 7. Data Model & Serialization
No changes to data models. Documentation update only.

## 8. Error Handling & Resource Lifecycle
No changes to error handling or resource lifecycle. Documentation update only.

## 9. Configuration
- `use_embedding = false` is already set in `config/mdq_mcp_server.toml` (assumption from plan)
- No config file changes needed for documentation update

## 10. Test Strategy
### Verification
- Run `pre-commit run --all-files` to confirm docs check passes
- Manual verification: `grep -n "hybrid\|embedding" docs/04_mcp_04_server_catalog.md` — confirm new sections exist

## 11. Implementation Plan
### Phase 1: Existing Document Review
- Read `docs/04_mcp_07_mdq_rag_boundary.md` to check for hybrid search references
- Avoid content duplication — reference link only, not duplicate content

### Phase 2: Docs Update
- Add hybrid search design explanation to mdq-mcp section in `docs/04_mcp_04_server_catalog.md`:
  - Hybrid Search (Phase 2): `use_embedding = true` enables it
  - FTS5-only is production baseline (`use_embedding = false`)
  - RRF merge strategy overview
  - MDQ hybrid vs RAG selection criteria

### Phase 3: Verification
- Run `pre-commit run --all-files` to confirm docs check passes

## 12. Risks / Open Questions
- **UNK-01**: Whether `docs/04_mcp_07_mdq_rag_boundary.md` contains hybrid search references → **Resolution**: Read the file before implementing; avoid duplication, reference link only.
- **Risk**: Content duplication between server catalog and boundary docs → **Mitigation**: Server catalog documents "what" (search modes, decision criteria); boundary doc documents "how" (detailed architecture). Reference link in server catalog, not duplicate content.
