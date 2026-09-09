## Goal

Remove ASCII tree diagrams showing system architecture and literal port numbers from the RAG system overview, replacing them with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries.

## Scope

Modify `docs/03_rag_01_system_overview.md`: remove ASCII tree diagrams (lines 46-67, 68-84) and literal port numbers (lines 35, 62, 129, 141), replace with prose organized around the five retain categories defined in `skills/DESIGN.md` Docs content policy.

## Assumptions

- The ASCII tree diagrams (lines 46-67, 68-84) are genuine file-tree/architecture diagram content that violates the policy.
- The literal port numbers (lines 35, 62, 129, 141) duplicate configuration values and go stale when ports change.
- The surrounding prose sections (Purpose, Scope, Ingestion Pipeline description, Query Pipeline description, Constraints) are design-intent prose that should be preserved unchanged.

## Design decisions

- Replace ASCII tree diagrams with prose organized into the five retain categories: component responsibilities, owned state, allowed dependency direction, reason for process separation, and design boundaries requiring joint review.
- Replace literal port numbers with descriptions of what the setting controls rather than its current value.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain ASCII trees as visual aids: rejected because the policy explicitly targets ASCII tree-drawing characters in documentation.
- Rewrite trees as different visualization formats: rejected because the policy targets the pattern itself, not just ASCII drawing characters.
- Retain port numbers with notes that they are illustrative: rejected because the policy targets literal port numbers in prose regardless of intent.

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Read all flagged lines to classify each as genuine violation (remove) or false positive (keep).
2. Replace ASCII tree diagrams with design-intent prose organized around the five retain categories.
3. Replace literal port numbers with prose describing what the setting controls.
4. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
5. Run `uv run python tools/check_docs_consistency.py --domain rag`.

### Method

Read all 5 flagged lines individually. For each, determine whether it is part of an ASCII tree structure (contains `├`, `│`, `└` characters as directory/file connectors) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

For literal port numbers, identify which configuration surface provides the authoritative value and describe what the setting controls without referencing the concrete value.

### Details

The ASCII tree diagram at lines 46-67 shows the ingestion pipeline data flow:
```
[Admin / Operator] → crawler.py → chunk_splitter.py → ingester.py → rag-src/registered/
```

The ASCII tree diagram at lines 68-84 shows the query pipeline architecture:
```
[Agent turn] → MCP :8010 → RagPipeline → KNN + BM25 → SQLite (rag.db)
```

Both diagrams use ASCII tree-drawing characters (`├`, `│`, `└`) to indicate parent-child relationships between components. These are structural diagrams of system architecture, not file/directory listings, but they still contain the ASCII tree-drawing character pattern targeted by the policy.

Replace the first ASCII tree block (lines 46-67) with prose organized into:

- **Component Responsibilities**: Admin/Operator initiates crawling via `crawler.py`; `WebCrawler` performs BFS crawl of same-origin URLs producing `{yyyymmddhhmmss}-{slug}.json` artifacts; `ChunkSplitter` splits crawled content using language-aware strategies (JA: Sudachi / EN: sentence / code: blank-line); `RagIngester` generates embeddings via embed-llm and upserts into SQLite; processed chunks are moved to `rag-src/registered/`.
- **Owned State**: `crawler.py` owns crawled JSON artifacts; `chunk_splitter.py` owns chunked JSON artifacts; `rag-src/registered/` owns post-ingestion staging area (retention TBD).
- **Allowed Dependency Direction**: Admin → crawler.py → chunk_splitter.py → ingester.py → rag-src/registered/. No circular dependencies among pipeline stages.
- **Reason for Process Separation**: Each pipeline stage runs as a separate script because failure isolation prevents one stage's crash from affecting others; independent scaling allows write-heavy domains (file-write-mcp) to require different resource allocation than read-only domains (web-search-mcp); deployment independence allows individual scripts to be updated or restarted without affecting the entire system.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

Replace the second ASCII tree block (lines 68-84) with prose organized into:

- **Component Responsibilities**: Agent turn invokes `RagPipeline.augment(query)` via MCP HTTP (:8010); RagPipeline executes MQE → Search → RRF → Rerank → Augment stages; KNN + BM25 search operates over SQLite (rag.db).
- **Owned State**: RagPipeline owns the query execution lifecycle; SQLite (rag.db) owns the vector store layer.
- **Allowed Dependency Direction**: Agent → MCP :8010 → RagPipeline → KNN + BM25 → SQLite. No circular dependencies among pipeline stages.
- **Reason for Process Separation**: MCP server operates independently of the agent lifecycle; each stage can be updated or restarted without affecting the entire system.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

For literal port numbers:
- Line 35: "MCP Wrapper: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (port 8010)" — replace with prose describing the MCP wrapper's role without referencing the specific port.
- Line 62: "embed (port 8081)" — replace with prose describing the embedding API endpoint without referencing the specific port.
- Line 129: "Caller: `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (via MCP HTTP, port 8010)" — replace with prose describing the caller's role without referencing the specific port.
- Line 141: "Embedding server running on port 8081" — replace with prose describing the prerequisite without referencing the specific port.

## Compatibility considerations

- The replacement prose must maintain the same information coverage as the original ASCII trees. All components listed in the trees must appear in the prose.
- Cross-references to other documents (e.g., `[04_mcp_05 MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)`) must be preserved.
- The terminology note about "3 Scripts" and "4 Processing Phases" should be preserved as it describes architectural concepts, not implementation details.

## Security considerations

- None identified. This is a documentation-only change removing ASCII tree characters and literal port numbers.

## Rollback considerations

- If the prose replacement loses critical structural information, the ASCII trees can be restored temporarily while a better prose representation is drafted.
- The rollback path is straightforward: revert the edit and restore the original ASCII tree blocks.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_01_system_overview.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md` | Zero ASCII tree findings; zero literal-port-number findings; structure check passes |

## Completion criteria

- All flagged lines have been classified (removed as genuine violation or kept as false positive).
- Any content actually removed is replaced with retain-category design intent prose.
- `check_docs_content_policy.py` reports zero ASCII tree findings and zero literal-port-number findings for this file.
- `check_docs_consistency.py --domain rag` passes.

## Out of scope

- Modifying the Ingestion Data Flow section (lines 103-118) if it does not contain ASCII tree-drawing characters.
- Altering `03_rag_02_01_ingestion_pipeline-overview.md`, `-02_...-crawler.md`, `-03_...-chunksplitter.md`, or `-09_...-shared-utilities.md`.
- Any file outside the RAG domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all flagged lines and classify each as genuine violation or false positive | Pending | — | — | |
| 2 | Replace removed ASCII trees with design-intent prose | Pending | — | — | |
| 3 | Replace literal port numbers with prose describing what the setting controls | Pending | — | — | |
| 4 | Run validation checks | Pending | — | — | |

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
- **Requirement ID**: REQ-003: Read and resolve the remaining findings in other five files, applying the same remove/replace pattern for genuine index-table or file-tree/location-mapping content
- **Source issue**: issues/20260905-153715_dcp005_rag_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211729_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/03_rag_01_system_overview.md
