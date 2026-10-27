---
title: "RAG System Overview"
area: rag
tags:
  - rag
  - system
  - overview
  - architecture
  - pipeline
related:
  - rag_00_document-guide.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
  - governance_03_issue-and-uncertainty-management.md
  - mcp_05_04_mdq-rag-boundary.md
  - adr_02_06_005_rag-source-derived-index-relationships.md
  - adr_02_01_002_platform-config-isolation.md
  - rag_03_02_query_pipeline-rag-pipeline-class.md
  - rag_03_05_query_pipeline-augment-stages.md
  - mcp_02_02_startup-modes-and-health.md
  - mcp_04_03_rag-pipeline-and-cicd.md
  - db_02_architecture_and_schema-schema-reference.md
---


# RAG System Overview

- Documentation Guide → [rag_00_document-guide.md](rag_00_document-guide.md)

## Purpose

Provides document retrieval augmentation for LLM agents by crawling web pages and local files, building an index in SQLite, and injecting relevant context blocks into each LLM turn.

---

## Scope

**Included:**
- Ingestion Pipeline: the crawler, chunk splitter, and ingester scripts under `scripts/rag/ingestion/`
- Query Pipeline: `scripts/rag/` (pipeline, repository, LLM client, stages)
- Utilities: `scripts/rag/utils.py`
- MCP Wrapper: `scripts/mcp_servers/rag_pipeline/`

**Not Included:**
- MDQ (Markdown Context Compression Engine) — A separate service. For boundary definitions, see [mcp_05 MDQ vs RAG Boundary](../22_mcp/mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)
- Agent REPL — Only calls the pipeline via MCP; does not contain RAG logic.
- LLM and Embedding Servers — External services providing inference and vector generation.

---

## System Architecture

- **Component Responsibilities**:
  - Ingestion: Admin/Operator initiates crawling via `crawler.py`; `WebCrawler` performs BFS crawl of same-origin URLs producing `{yyyymmddhhmmss}-{slug}.json` artifacts; `ChunkSplitter` splits crawled content using language-aware strategies (JA: Sudachi / EN: sentence / code: blank-line); `RagIngester` generates embeddings via embed-llm and upserts into SQLite; processed chunks are moved to `rag-src/registered/`.
  - Query: the Agent calls the `rag_run_pipeline` MCP tool; `RagPipelineMCPService` calls `RagPipeline.augment(query)`; RagPipeline executes the MQE → Search → Fusion → Rerank → Augment stages, followed by the optional Refiner; KNN + BM25 search operates over `rag.sqlite`.
- **Owned State**: `crawler.py` owns crawled JSON artifacts; `chunk_splitter.py` owns chunked JSON artifacts; `rag-src/registered/` owns the post-ingestion staging area (see Retention of `registered/` below). RagPipeline owns the query execution lifecycle; SQLite (`rag.sqlite`) owns the vector store layer.
- **Allowed Dependency Direction**: Ingestion: Admin → crawler.py → chunk_splitter.py → ingester.py → rag-src/registered/. Query: Agent → MCP → RagPipeline → KNN + BM25 → SQLite. No circular dependencies among pipeline stages.
- **Process Separation**: Each ingestion stage (`crawler.py`, `chunk_splitter.py`, `ingester.py`) is a separate script with its own `main()` entry point and its own configuration file, and the stages hand off work through files (crawled JSON, chunked JSON, `rag-src/registered/`) rather than in-process calls, so each stage can be run, re-run or restarted on its own. In the Query Pipeline, the MCP server operates independently of the agent lifecycle; each stage can be updated or restarted without affecting the entire system.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes. Modifications to one component's owned state must consider downstream impact on dependent components.

### Ownership Rationale

`rag` layer's authority over query execution derives from the repository's layered-architecture rule (`rules/env.md`).

#### Why SQLite (`rag.sqlite`) owns the vector store layer

Per ADR-005, SQLite's `documents`/`chunks` tables are the canonical data and `chunks_fts`/`chunks_vec` are derived indexes; the in-process fallback model is defined by ADR-010. ADR-005's Rationale rests on three points: (1) Data Integrity — separating canonical from derived data prevents canonical data from being updated through a derived index; (2) Operability — the deletion-order invariant (`chunks_vec` before `documents`) prevents orphan records, and unified consistency checks and repair procedures leave operators without ambiguity; (3) Portability — because the indexes can be rebuilt from `documents` and `chunks`, FTS5 or the vector engine can be replaced. See [ADR-005](../10_adr/adr_02_06_005_rag-source-derived-index-relationships.md).

#### Retention of `registered/`

Chunk files are moved to `rag-src/registered/` after ingestion. No automated retention or cleanup of `rag-src/registered/` exists; files accumulate until removed manually, and adding cleanup requires a separate design decision.

---

## Ingestion Pipeline

**Scripts and Processing Phases**

| Script | Phase | Input | Output |
|---|---|---|---|
| `crawler.py` | Crawling | URL or local path | `rag-src/yyyymmddhhmmss-{slug}.json` (JSON) |
| `chunk_splitter.py` | Chunking | `rag-src/*.json` | `rag-src/chunk/{stem}-{idx:04d}.json` (JSON) |
| `ingester.py` | Embedding | `rag-src/chunk/*.json` | Embedding API call |
| `ingester.py` | Storage | Embedding vector | SQLite table + `rag-src/registered/` |

> **Terminology Note:** "Scripts" refers to the executable files (`crawler.py`, `chunk_splitter.py`, `ingester.py`).
> "Processing Phases" refers to the logical steps (Crawling, Chunking, Embedding, Storage), two of which are executed internally within `ingester.py`.
> The term "Stage" is reserved for query pipeline stages (MQE, Search, Fusion, Rerank, Augment) and is not used for ingestion.

### Ingestion Data Flow (Overview)

``` text
config/crawler.toml [target_urls]
  → crawler.py: BFS crawl (same-origin) → rag-src/
  → chunk_splitter.py (config/chunk_splitter.toml): language-aware splitting
                       (JA: Sudachi / EN: sentence / code: blank-line)
                       → rag-src/chunk/
  → ingester.py (config/ingester.toml): embed chunk text (no prefix)
                → struct.pack float32 BLOB → SQLite INSERT
                → rag-src/registered/
```

> **Configuration isolation:** Each script has its own configuration file (`config/crawler.toml`, `config/chunk_splitter.toml`, `config/ingester.toml`), loads only that file, and is restricted from reading the others. Per [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md) Decision Details #3 to #5 and #9.

---

## Query Pipeline

**Logical stages executed per agent turn**

Stages: MQE → Search → Fusion → Rerank → Augment, followed by the optional Refiner. For details on each stage, see `docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md` through `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`.

- **MQE**: Query expansion via LLM — generates related queries to broaden retrieval scope.
- **Search**: Hybrid retrieval — combines vector similarity search with FTS5 full-text search.
- **Fusion**: Reciprocal Rank Fusion — merges results from multiple search backends into a single ranked list.
- **Rerank**: Cross-Encoder reranking — re-scores fused results using a Cross-Encoder model for higher precision.
- **Augment**: Context formatting — formats retrieved chunks into a prompt-ready block with URL/title metadata and sanitizes injection patterns.

**Entrypoint:** `RagPipeline.augment(query) -> str`
**Caller:** `RagPipelineMCPService.run_pipeline()` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`), reached by the Agent through the `rag_run_pipeline` MCP tool

### Semantic Cache

The RAG pipeline has no semantic cache; a configuration source that carries semantic-cache settings fails validation (Explicit in code — `scripts/shared/config_validator.py`).

---

## Prerequisites

| Requirement | Verification Command |
|---|---|
| Embedding server available | `curl -s http://127.0.0.1:<PORT>/health` |
| `sqlite-vec` extension loadable | the file at `sqlite_vec_so` (see `config/ingester.toml`) exists |
| Configuration files exist | `config/crawler.toml`, `config/chunk_splitter.toml`, `config/ingester.toml` |
| Target URLs or files specified | `--url` in CLI, or `target_urls` in config |

**Embedding server health check:** The embedding server (`embed-llm`) is a `llama-server` process external to this repository. The curl command above is the check used by `deploy/setup_services.sh`; the response body is defined by `llama-server`, not by repository code, so this document does not specify it.

**RAG pipeline MCP server health check:** The `rag-pipeline-mcp` server answers `/health` with the common MCP health response, in which `liveness` is a boolean, `ready` is true only when no dependency check fails, and HTTP 503 is returned when it is not ready (`dependencies.embed_url` is `"not configured"` when no embedding URL is configured, or `"unreachable"` when the embedding URL is configured but the reachability probe cannot confirm it). For the response format see [mcp_02_02 Startup Modes and Health](../22_mcp/mcp_02_02_startup-modes-and-health.md) and [mcp_04_03](../22_mcp/mcp_04_03_rag-pipeline-and-cicd.md).

Troubleshooting:
- If the embedding server request times out: verify the embedding server is running and accessible at the specified address
- If the `rag-pipeline-mcp` `/health` reports `status` `"degraded"` with `dependencies.embed_url` `"not configured"`: verify the embedding server URL is set in the configuration
- If the `rag-pipeline-mcp` `/health` reports `status` `"degraded"` with `dependencies.embed_url` `"unreachable"`: the embedding server URL is set but the server is not reachable (down, wrong port, or network-blocked); verify the embedding server is running and reachable at the configured address. The `/health` probe is bounded by a timeout, so a hung server still returns within that bound.
- If an HTTP 503 is returned by an MCP server: the service is running but has failed dependency checks; inspect the `dependencies` field

**sqlite-vec extension:** A missing file at `sqlite_vec_so` means the extension cannot be loaded.

**Configuration files:** Missing files produce "No such file or directory" errors (check with `ls -la config/crawler.toml config/chunk_splitter.toml config/ingester.toml`).

**Target URLs or files:** At least one target is required, either by `--url` on the command line or by `target_urls` in `config/crawler.toml`.

---

## Constraints

Chunk-size, chunk-overlap, crawl-depth, and max-pages bounds exist to keep chunks at a useful retrieval granularity and to bound crawl time, storage growth, and external-site load. Current operational values are owned by `config/chunk_splitter.toml` and `config/crawler.toml` (see [Configuration Reference](rag_05_01-configuration-reference.md)); each file's inline comment states the bounds are unvalidated heuristics, and no empirical basis or trade-off analysis is recorded in this repository. If these values are tuned, verify the change against actual retrieval quality and performance for the intended use case — this documentation set provides no quality-impact guidance for any of them.

| Constraint | Behavior when violated | Enforcement |
|---|---|---|
| Language Detection | CJK ratio at or above a threshold → `ja`, otherwise `en`; text shorter than the minimum detection length falls back to the language hint. No error is raised. | Programmatic (`detect_lang()`, `scripts/rag/ingestion/crawler_utils.py`) |
| Chunk Size | Sub-minimum chunks are discarded as noise; over-maximum sections are split further by sentence-level chunking (discard-on-noise policy: [Configuration Reference](rag_05_01-configuration-reference.md)). | Programmatic (`scripts/rag/ingestion/chunk_splitter.py`) |
| Chunk Overlap | Any configured value is accepted and applied by sliding window without validation; there is no "violation" concept. | Programmatic |
| Embedding Dimension | `TypeError` if the blob is not bytes, `ValueError` if its length does not match the expected dimensions. The dimension is a fixed code-level constant (float32 little-endian BLOB), not config-driven, so changing the embedding model requires a code change. | Strict, programmatic (`validate_embedding_blob()`, `scripts/db/store_protocols.py`) |
| Crawl Depth / Max Pages Per Site | Exceeding the limit ends BFS traversal for that site; not an error. | Operational limit (`scripts/rag/ingestion/crawler.py`) |
| Database | SQLite single node only. An architectural assumption per `ADR-008` (Assumptions: "Target environment: a single host, multiple processes"); not enforced per request. Reconsidering it requires the ADR's own "Reconsideration Conditions". | Architectural |

---

## MCP Server Responsibility Division

- **rag-pipeline MCP server (`rag_pipeline_server.py`)**: HTTP routing and request/response formatting; translates `RagPipelineServiceError` into error responses.
- **`RagPipelineMCPService` (`rag_pipeline_service.py`)**: pipeline orchestration, lifecycle (start/stop), result formatting for MCP tool responses, and the tool-name dispatch.
- **`RagPipeline` (`scripts/rag/pipeline.py`)**: core search logic and stage execution, the `augment()` fallback chain (HTTP → search → refiner → raw chunks), and diagnostics collection.

The interaction flow is: MCP client → HTTP routing → service orchestration → pipeline execution. For details see `docs/21_rag/rag_03_01_query_pipeline-overview.md`.

Note: The rag-pipeline MCP server reads the corpus database through `rag_db_path` in `config/rag_pipeline_mcp_server.toml`, and the Agent reaches the same database only for admin-only maintenance through `rag_db_path` in `config/agent.toml`. HTTP delegation (`rag_query_service_url`) is not used in production (ADR-010). Both files are configured with the same path by convention, not by an enforced invariant — a misconfigured `rag_pipeline_mcp_server.toml` pointing at a different `rag_db_path` would silently diverge, undetected by any current automated check.

## Chapter Map

See the reading order and routing table in [rag_00_document-guide.md](rag_00_document-guide.md). The DB schema is owned by [db_02_architecture_and_schema-schema-reference.md](../41_db/db_02_architecture_and_schema-schema-reference.md), and known bugs and inconsistencies by [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) (Part 1, Area: RAG).

## Keywords

- rag
- system
- overview
- architecture
- pipeline
