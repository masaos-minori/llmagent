## Goal

Design optional embedding/hybrid search extension for MDQ while keeping FTS5-only as production baseline. Add use_embedding = false by default, define vector table only when embedding is enabled, use RRF or another explicit merge strategy if hybrid search is enabled, preserve RAG/MDQ responsibility boundary, and document when to use MDQ hybrid search versus RAG.

## Scope

**In-Scope**:
- Keep FTS5-only as production baseline
- Add use_embedding = false by default
- Define vector table only when embedding is enabled
- Use RRF or another explicit merge strategy if hybrid search is enabled
- Preserve RAG/MDQ responsibility boundary
- Document when to use MDQ hybrid search versus RAG

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' search behavior
- Embedding model selection (future work)

## Assumptions

1. use_embedding = false by default (FTS5-only remains production baseline)
2. Vector table created only when use_embedding = true
3. RRF (Reciprocal Rank Fusion) used for hybrid search merge strategy
4. MDQ hybrid search does not access rag.sqlite (preserves RAG/MDQ boundary)

## Implementation

### Target file: config/mdq_mcp_server.toml

**Procedure**: Add embedding configuration fields.

**Method**: Add new fields to existing config file.

**Details**:
1. Add `use_embedding = false` (disabled by default)
2. Add `vector_table = "chunks_vec"` (when enabled)
3. Add `embedding_model = "default"` (configurable)

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Add EmbeddingResult model.

**Method**: Add new TypedDict class definition in models.py.

**Details**:
1. `EmbeddingResult`: TypedDict with chunk_id, embedding_score, rank fields

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Add vector table creation, embedding logic.

**Method**: Modify service.py to add conditional vector table and embedding methods.

**Details**:
1. Create vector table conditionally in schema initialization:
   - When use_embedding = true, add CREATE TABLE chunks_vec with chunk_id, embedding (BLOB)
   - Add vector index for ANN search
2. Add embedding generation method during indexing:
   - Generate embeddings for chunks using LLM API
   - Store embeddings in chunks_vec table

### Target file: scripts/mcp/mdq/search.py

**Procedure**: Implement hybrid search with RRF merge.

**Method**: Modify search.py to add hybrid search mode when use_embedding = true.

**Details**:
1. When mode=hybrid and use_embedding=true, run both FTS5 and vector search
2. Merge results using RRF (Reciprocal Rank Fusion):
   - Calculate rank score for each result from both sources
   - Combine scores using RRF formula: 1/(rank + k) where k is a constant
   - Sort merged results by combined score
3. Return merged ranking with source attribution

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Update tools.py schema to document hybrid mode availability.

**Method**: Modify tool definition in tools.py.

**Details**:
1. Document that hybrid mode is available only when use_embedding = true
2. Update mode enum description to indicate hybrid optionality

### Target file: docs/04_mcp_05_security_and_safety_model.md

**Procedure**: Add MDQ hybrid search vs RAG documentation.

**Method**: Add new section to existing documentation.

**Details**:
1. Document when to use MDQ hybrid search (Markdown-only semantic retrieval)
2. Document when to use RAG (general-purpose semantic retrieval)
3. Clarify that MDQ hybrid search does not access rag.sqlite

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| service.py | Verify vector table created only when use_embedding=true | Check DB schema after startup | chunks_vec exists only when enabled |
| search.py | Verify hybrid search merges FTS5 + vector results | Call search_docs with mode=hybrid | Results merged using RRF |
| docs | Verify MDQ vs RAG documentation exists | Check documentation | Clear guidance on when to use each |

## Risks

- **Risk**: Embedding adds latency and complexity to indexing | **Likelihood**: Medium | **Mitigation**: Keep embedding optional; document performance implications | False
- **Risk**: RRF merge strategy may not be optimal for all use cases | **Likelihood**: Low | **Mitigation**: Document RRF limitations; allow alternative merge strategies in future | False
