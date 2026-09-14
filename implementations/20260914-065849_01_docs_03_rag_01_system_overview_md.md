## Goal

Expand `docs/03_rag_01_system_overview.md`'s "Query Pipeline" section with a one-line-per-stage flow summary, replace its "Semantic Cache" section (which describes a feature removed from the codebase) with an accurate note that the feature was removed, and expand "MCP Server Responsibility Division" with a concrete summary instead of a bare cross-reference (REQ-001, REQ-002, REQ-003).

## Scope

- Add a one-line description per stage to the "Query Pipeline" section after line 98's stage-name list
- Replace the "Semantic Cache" section's content (lines 103-105) with a note stating the feature was removed (citing removal commits `282b08f38` and `09093016d`) and that the three configuration keys are now rejected by `RagConfigValidator`
- Add a 3-line responsibility summary to "MCP Server Responsibility Division" (after line 136's existing cross-reference)

## Assumptions

- No other documentation file describes semantic cache as an active feature in a way that would also need correction (this Plan's search was scoped to the Issue's cited file; a broader repository-wide semantic-cache-documentation sweep is not part of this Plan)
- The three MCP components' own module docstrings are the current, authoritative source for their responsibilities
- The Query Pipeline section already states the 5-stage flow (MQE → Search → Fusion → Rerank → Augmentation) with an entrypoint and caller — what is missing is a one-line description of *what each stage does*, not the flow itself

## Design decisions

1. Use a textual one-line-per-stage summary for Query Pipeline rather than a diagram — this document's existing style (tables, short prose) does not use diagrams elsewhere, and a diagram would be a larger, disproportionate addition for what the Issue's own evidence shows is a small gap (missing one-line descriptions, not a missing flow)
2. Replace, rather than delete, the Semantic Cache section — a reader who encounters `use_semantic_cache` in an old config or a stale reference elsewhere benefits from an explicit "this was removed" note with the removal commit cited, rather than the section disappearing silently
3. Add the MCP responsibility summary as a supplement to, not a replacement for, the existing cross-reference — `docs/03_rag_03_01_query_pipeline-overview.md` remains the authoritative detailed source; this overview should summarize, not duplicate, that document

## Alternatives considered

1. Adding a flow diagram for Query Pipeline — rejected because this document's existing style does not use diagrams elsewhere, and a diagram would be a larger, disproportionate addition for what the Issue's own evidence shows is a small gap (missing one-line descriptions, not a missing flow)
2. Deleting the Semantic Cache section entirely — rejected because a reader encountering `use_semantic_cache` in an old config benefits from an explicit "this was removed" note with the removal commit cited, rather than the section disappearing silently
3. Replacing the existing cross-reference in MCP Server Responsibility Division with the inline summary — rejected because `docs/03_rag_03_01_query_pipeline-overview.md` remains the authoritative detailed source; this overview should summarize, not duplicate, that document

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Confirm each stage's one-line responsibility and the MCP components' docstrings
2. Expand and correct the three sections

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-read `scripts/rag/stages/{mqe,search,fusion,rerank,augment}.py`'s module docstrings/class docstrings to confirm accurate one-line summaries (REQ-001; `docs/03_rag_01_system_overview.md`)
- Re-read `rag_pipeline_server.py`/`rag_pipeline_service.py`/`pipeline.py`'s module docstrings to confirm accurate responsibility summaries (REQ-003; `docs/03_rag_01_system_overview.md`)

Phase 2: Core Logic — expand and correct the three sections
- Add one-line-per-stage descriptions to "Query Pipeline" (REQ-001; `docs/03_rag_01_system_overview.md`)
- Replace "Semantic Cache"'s content with a removal note citing `282b08f38`/`09093016d` and `RagConfigValidator`'s rejection mechanism (REQ-002; `docs/03_rag_01_system_overview.md`)
- Add a 3-line responsibility summary to "MCP Server Responsibility Division", keeping the existing cross-reference (REQ-003; `docs/03_rag_01_system_overview.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Each stage's responsibility confirmed from module docstrings:
  - MQE (`scripts/rag/stages/mqe.py`): Query expansion via LLM
  - Search (`scripts/rag/stages/search.py`): Vector + FTS5 hybrid retrieval
  - Fusion (`scripts/rag/stages/fusion.py`): Reciprocal Rank Fusion merge
  - Rerank (`scripts/rag/stages/rerank.py`): Cross-Encoder reranking
  - Augmentation (`scripts/rag/stages/augment.py`): Context-block formatting + sanitization
- MCP component responsibilities confirmed from module docstrings:
  - `rag_pipeline_server.py`: HTTP/MCP protocol layer — endpoint routing, tool listing, health check, debug endpoint
  - `rag_pipeline_service.py`: Service layer wrapping `RagPipeline` for MCP use
  - `pipeline.py`: Core pipeline logic itself, MQE→Search→RRF→Rerank→Augment
- Semantic cache removal confirmed via `git log` (`282b08f38`, `09093016d`) and `RagConfigValidator._check_removed_semantic_cache_keys()` (`config_validator.py:55-73`)
- No active implementation of semantic cache exists anywhere in `scripts/rag/` or `scripts/mcp_servers/rag_pipeline/`

**Phase 2:** Make the following changes:

1. **After line 98**, add one-line-per-stage descriptions:
   ```markdown
   - **MQE**: Query expansion via LLM — generates related queries to broaden retrieval scope.
   - **Search**: Hybrid retrieval — combines vector similarity search with FTS5 full-text search.
   - **Fusion**: Reciprocal Rank Fusion — merges results from multiple search backends into a single ranked list.
   - **Rerank**: Cross-Encoder reranking — re-scores fused results using a Cross-Encoder model for higher precision.
   - **Augmentation**: Context formatting — formats retrieved chunks into a prompt-ready block with URL/title metadata and sanitizes injection patterns.
   ```

2. **Replace lines 103-105** ("Semantic Cache") with:
   ```markdown
   ### Semantic Cache

   **Removed.** The semantic cache feature was deliberately removed from the RAG pipeline. The configuration keys `use_semantic_cache`, `semantic_cache_threshold`, and `semantic_cache_max_size` are no longer supported and will cause a validation error when present in any configuration source (see `RagConfigValidator._check_removed_semantic_cache_keys()` at `scripts/shared/config_validator.py`). Removal commits: `282b08f38` (req-005: remove SemanticCache from RAG pipeline and MCP server), `09093016d` (remove semantic cache configuration fields and references).
   ```

3. **After line 136**, add a 3-line responsibility summary:
   ```markdown
   - `rag_pipeline_server.py`: HTTP/MCP protocol layer — endpoint routing, tool listing, health check, debug endpoint.
   - `rag_pipeline_service.py`: Service layer wrapping `RagPipeline` for MCP use.
   - `scripts/rag/pipeline.py`: Core pipeline logic — MQE → Search → RRF → Rerank → Augment orchestration.
   ```

## Compatibility considerations

This is a documentation-only expansion/correction. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction/expansion only. However, accurately documenting that a security-related feature (semantic cache) was removed is important for readers who may encounter stale configuration references.

## Rollback considerations

Simple revert: restore the original Semantic Cache section text and remove the added Query Pipeline stage descriptions and MCP responsibility summary. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Manual — cross-check each new/corrected claim against code and commit history | Manual inspection + `git log --oneline -S "SemanticCache"` | Every claim traceable to a specific source |

## Completion criteria

- [ ] "Query Pipeline" describes MQE, Search, Fusion, Rerank, and Augmentation each in one clause (REQ-001)
- [ ] "Semantic Cache" no longer describes `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size` as active configuration; it states the feature was removed and cites the removal commit(s) (REQ-002)
- [ ] "MCP Server Responsibility Division" includes a one-line summary for each of `rag_pipeline_server.py`, `rag_pipeline_service.py`, and `scripts/rag/pipeline.py`, in addition to its existing cross-reference (REQ-003)

## Out of scope

- Adding a flow diagram (the Issue's Recommended Action offers this as one option for the Query Pipeline section; this Plan uses a textual one-line-per-stage summary instead, consistent with this document's existing style)
- Restoring or re-designing semantic cache functionality (it was a deliberate, already-completed removal — `282b08f38`'s commit message: "req-005: remove SemanticCache from RAG pipeline and MCP server" — not a gap to fill)
- Rewriting `docs/03_rag_03_01_query_pipeline-overview.md` (the cross-reference target for MCP responsibilities, which remains the authoritative detailed source — this Plan only adds a summary to the overview document, it does not duplicate that document's full content)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm stage responsibilities and MCP docstrings | Pending | — | — | |
| 2 | Phase 2: Add Query Pipeline stage descriptions | Pending | — | — | |
| 3 | Phase 2: Replace Semantic Cache section | Pending | — | — | |
| 4 | Phase 2: Add MCP responsibility summary | Pending | — | — | |
| 5 | Verification: manual review | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260913-183011_missing_rag_system_overview_content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-205143_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-065849
- **Related target files**: docs/03_rag_01_system_overview.md
