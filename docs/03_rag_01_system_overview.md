---
title: "RAG System Overview (Part 1)"
area: rag
tags:
  - rag
  - system
  - overview
  - architecture
  - pipeline
related:
  - 03_rag_00_document-guide.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_03_01_query_pipeline-overview.md
source:
  - 03_rag_01_system_overview.md
---


# RAG System Overview

- Documentation Guide → [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Purpose

Provides document retrieval augmentation for LLM agents by crawling web pages and local files, building an index in SQLite, and injecting relevant context blocks into each LLM turn.

---

## Scope

**Included:**
- Ingestion Pipeline: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`
- Query Pipeline: `scripts/rag/pipeline.py`, `scripts/rag/repository.py`, `scripts/rag/llm_client.py`, `scripts/rag/stages/`
- Utilities: `scripts/rag/utils.py`
- MCP Wrapper: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

**Not Included:**
- MDQ (Markdown Only Query) — A separate service. For boundary definitions, see [04_mcp_05 MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)
- Agent REPL — Only calls the pipeline via MCP; does not contain RAG logic.
- LLM and Embedding Servers — External services providing inference and vector generation.

---

## System Architecture

- **Component Responsibilities**: Admin/Operator initiates crawling via `crawler.py`; `WebCrawler` performs BFS crawl of same-origin URLs producing `{yyyymmddhhmmss}-{slug}.json` artifacts; `ChunkSplitter` splits crawled content using language-aware strategies (JA: Sudachi / EN: sentence / code: blank-line); `RagIngester` generates embeddings via embed-llm and upserts into SQLite; processed chunks are moved to `rag-src/registered/`.
- **Owned State**: `crawler.py` owns crawled JSON artifacts; `chunk_splitter.py` owns chunked JSON artifacts; `rag-src/registered/` owns post-ingestion staging area (retention TBD).
- **Allowed Dependency Direction**: Admin → crawler.py → chunk_splitter.py → ingester.py → rag-src/registered/. No circular dependencies among pipeline stages.
- **Reason for Process Separation**: Each pipeline stage runs as a separate script because failure isolation prevents one stage's crash from affecting others; independent scaling allows write-heavy domains (file-write-mcp) to require different resource allocation than read-only domains (web-search-mcp); deployment independence allows individual scripts to be updated or restarted without affecting the entire system.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

- **Component Responsibilities**: Agent turn invokes `RagPipeline.augment(query)` via MCP HTTP; RagPipeline executes MQE → Search → RRF → Rerank → Augment stages; KNN + BM25 search operates over SQLite (rag.db).
- **Owned State**: RagPipeline owns the query execution lifecycle; SQLite (rag.db) owns the vector store layer.
- **Allowed Dependency Direction**: Agent → MCP → RagPipeline → KNN + BM25 → SQLite. No circular dependencies among pipeline stages.
- **Reason for Process Separation**: MCP server operates independently of the agent lifecycle; each stage can be updated or restarted without affecting the entire system.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

---

## Ingestion Pipeline

**3 Scripts / 4 Processing Phases**

| Script | Phase | Input | Output |
|---|---|---|---|
| `crawler.py` | Crawling | URL or local path | `rag-src/yyyymmddhhmmss-{slug}.json` (JSON) |
| `chunk_splitter.py` | Chunking | `rag-src/*.json` | `rag-src/chunk/{stem}-{idx:04d}.json` (JSON) |
| `ingester.py` | Embedding | `rag-src/chunk/*.json` | Embedding API call |
| `ingester.py` | Storage | Embedding vector | SQLite table + `rag-src/registered/` |

> **Terminology Note:** "3 Scripts" refers to the three executable files (`crawler.py`, `chunk_splitter.py`, `ingester.py`).
> "4 Processing Phases" refers to the four logical steps (Crawling, Chunking, Embedding, Storage), two of which are executed internally within `ingester.py`.
> The term "Stage" is reserved for query pipeline stages (MQE, Search, Fusion, Rerank, Augment) and is not used for ingestion.

### Ingestion Data Flow (Overview)

``` text
config/crawler.toml [target_urls]
  → crawler.py: BFS crawl (same-origin) → rag-src/
  → chunk_splitter.py (config/chunk_splitter.toml): language-aware splitting
                       (JA: Sudachi / EN: sentence / code: blank-line)
                       → rag-src/chunk/
  → ingester.py (config/ingester.toml): "passage: {text}" embed
                → struct.pack float32 BLOB → SQLite INSERT
                → rag-src/registered/
```

> **Implementation Note:** Configuration consists of three separate files per script rather than a single `config/rag_pipeline.toml`:
> (`config/crawler.toml`, `config/chunk_splitter.toml`, `config/ingester.toml`). Each script loads only its own configuration using `ConfigLoader().load("<script>.toml")` and restricts access to other files using `ConfigLoader.restrict_to("<script>.toml")` (verified in `scripts/rag/ingestion/crawler.py` and `ingester.py`).
> Basis: [ADR-002](adr/ADR-002-config-isolation.md) §Decision #9, #13. Explicit in code.

---

## Query Pipeline

**5 Logical Stages executed per agent turn**

Stages: MQE → Search → Fusion → Rerank → Augmentation. For details on each stage, see `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` through `docs/03_rag_03_05_query_pipeline-augment-stages.md`.

**Entrypoint:** `RagPipeline.augment(query) -> str`
**Caller:** `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (via MCP HTTP)

### Semantic Cache

When `use_semantic_cache=True`, if the cosine similarity of the query embedding is above `semantic_cache_threshold` (default 0.92), the pipeline skips processing and returns the cached context block. It uses `threading.RLock` for thread safety. It is a FIFO cache (oldest entries deleted first) with a maximum size defined by `semantic_cache_max_size` (code default 128, operational setting 100).

---

## Prerequisites

| Requirement | Verification Command |
|---|---|
| Embedding server available | `curl -s http://127.0.0.1:<PORT>/health` |
| `sqlite-vec` extension loadable | `/opt/llm/sqlite-vec/vec0.so` exists |
| Configuration files exist | `config/crawler.toml`, `config/chunk_splitter.toml`, `config/ingester.toml` |
| Target URLs or files specified | `--url` in CLI, or `target_urls` in config |

---

## Constraints

| Constraint | Value | Source |
|---|---|---|
| Language Detection | CJK ratio ≥ 0.10 → `ja`; otherwise `en`; fallback to hint if < 100 chars | `crawler.py` |
| Chunk Size | Min 40 chars, Max 500 chars | `config/chunk_splitter.toml` |
| Chunk Overlap | 50 character sliding window | `config/chunk_splitter.toml` |
| Embedding Dimension | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB | `scripts/db/store_protocols.py` |
| Crawl Depth | Operational value is 3 (max 3 hops from start URL, `config/crawler.toml`'s `max_depth`). Differs from code fallback; use operational config | `config/crawler.toml` |
| Max Pages Per Site | Operational value is 200 (max 200 pages per site, `config/crawler.toml`'s `max_pages`). Code fallback is 500; use operational config | `config/crawler.toml` |
| Database | SQLite single node only | Architecture |

---

## MCP Server Responsibility Division

For details on responsibilities of `rag_pipeline_server.py`, `rag_pipeline_service.py`, and `scripts/rag/pipeline.py`, please refer to `docs/03_rag_03_01_query_pipeline-overview.md`.

## Related Chapters

| Topic | File |
|---|---|
| Ingestion Scripts (API, CLI, Config) | [03_rag_02_01_ingestion_pipeline-overview.md](03_rag_02_01_ingestion_pipeline-overview.md) |
| Query Pipeline (API, Stage Details) | [03_rag_03_01_query_pipeline-overview.md](03_rag_03_01_query_pipeline-overview.md) |
| DB Schema, Type Definitions | [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md) |
| Config, Execution Commands, Logs | [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) |
| Known Bugs and Inconsistencies | [00_governance_03_issue-and-uncertainty-management.md](00_governance_03_issue-and-uncertainty-management.md) (Part 1, Area: RAG) |

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_01_system_overview.md`

## Keywords

rag
system
overview
architecture
pipeline
