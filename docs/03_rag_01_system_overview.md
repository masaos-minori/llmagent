# RAG System Overview

- Document guide → [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Purpose

Provide document retrieval augmentation for the LLM agent by crawling web pages and
local files, indexing them in SQLite, and injecting relevant context blocks into each
LLM turn.

---

## Scope

**In scope:**
- Ingestion pipeline: `scripts/rag/ingestion/crawler.py`, `chunk_splitter.py`, `ingester.py`
- Query pipeline: `rag/pipeline.py`, `rag/repository.py`, `rag/llm.py`, `rag/stages/`
- Utility: `rag/utils.py`
- MCP wrapper: `mcp/rag_pipeline/server.py` (port 8010)

**Out of scope:**
- MDQ (Markdown-dedicated index) — separate service; see [04_mcp_07_mdq_rag_boundary.md](04_mcp_07_mdq_rag_boundary.md) for boundary definition
- Agent REPL — calls the pipeline via MCP; does not own RAG logic
- LLM and embedding servers — external services at ports 8001 and 8003

---

## System Architecture

```
[Admin / Agent]
      |
      | /ingest <url>  OR  crawler.py CLI
      v
+------------------+     rag-src/*.txt      +-------------------+     rag-src/chunk/*.txt
|  crawler.py      | -------------------->  | chunk_splitter.py | -------------------->
|  (WebCrawler)    |                         | (ChunkSplitter)   |
+------------------+                         +-------------------+
                                                                        |
                                                                        v
                                                              +------------------+
                                                              |  ingester.py     |
                                                              |  (RagIngester)   |
                                                              +------------------+
                                                                        |
                                                                        | embed (port 8003)
                                                                        | INSERT SQLite
                                                                        v
                                                              rag-src/registered/

[Agent turn]
      |
      | augment(query)
      v
+----------------------+    MCP :8010    +-------------------+
| mcp/rag_pipeline/    | <-------------> | RagPipeline       |
| service.py           |                 | (6 logical stages)|
+----------------------+                 +-------------------+
                                                   |
                                          +--------+--------+
                                          | KNN + BM25      |
                                          | SQLite (rag.db) |
                                          +-----------------+
```

---

## Ingestion Pipeline

**3 scripts / 4 processing phases**

| Script | Phase | Input | Output |
|---|---|---|---|
| `crawler.py` | Crawl | URL or local path | `rag-src/yyyymmddhhmmss-{slug}.txt` (JSON) |
| `chunk_splitter.py` | Chunk | `rag-src/*.txt` | `rag-src/chunk/{stem}-{idx:04d}.txt` (JSON) |
| `ingester.py` | Embed | `rag-src/chunk/*.txt` | embed API call (port 8003) |
| `ingester.py` | Store | embed vectors | SQLite tables + `rag-src/registered/` |

> **Note:** Some older documents describe "3 stages" (3 scripts) and others describe
> "4 stages" (4 processing phases). Both are correct from different perspectives.
> See [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) for details.

### Ingestion data flow (summary)

```
config/rag_pipeline.toml [target_urls]
  → crawler.py: BFS crawl (same-origin) → rag-src/
  → chunk_splitter.py: language-aware splitting (JA: Sudachi / EN: sentence / code: blank-line)
                       → rag-src/chunk/
  → ingester.py: "passage: {text}" embed → struct.pack float32 BLOB → SQLite INSERT
                → rag-src/registered/
```

---

## Query Pipeline

**6 logical stages executed per agent turn** (5 fixed + PluginHooks optional)

| Stage | Class | Function |
|---|---|---|
| 1. MQE | `MqeStage` | Expand query into N variants for higher recall |
| 2. Search | `SearchStage` | KNN (sqlite-vec) + BM25 (FTS5) per query variant |
| 3. Fusion | `FusionStage` | Merge multi-query results using RRF (Σ 1/(rrf_k+rank)); `rrf_k` configurable via config (default: 60) |
| 4. Rerank | `RerankStage` | Cross-encoder LLM scoring; filter by `rag_min_score`; post-rerank dedup by URL |
| 5. PluginHooks | registered hooks | Post-rerank plugin stage; runs after RerankStage, before AugmentStage; error-isolated (failures logged, skipped); configurable via `hook_strict` in `run()` |
| 6. Augment | `AugmentStage` | Format chunks as `[RAG_CONTEXT_START]...[RAG_CONTEXT_END]` |

**Entry point:** `RagPipeline.augment(query) -> str`  
**Caller:** `mcp/rag_pipeline/service.py` via MCP HTTP (port 8010)

### Semantic cache

When `use_semantic_cache=True`, query embedding cosine similarity ≥ `semantic_cache_threshold`
(default 0.92) returns the cached context block, skipping the pipeline. Thread-safe via `threading.RLock`. FIFO cache (oldest-first eviction); max size = `semantic_cache_max_size` (default 100 entries).

---

## Prerequisites

| Requirement | Check command |
|---|---|
| Embedding server running on port 8003 | `curl -s http://127.0.0.1:8003/health` |
| `sqlite-vec` extension loadable | `/opt/llm/sqlite-vec/vec0.so` must exist |
| Config file present | `config/rag_pipeline.toml` |
| Ingest target URL or file specified | CLI `--url` or `target_urls` in config |

---

## Constraints

| Constraint | Value | Source |
|---|---|---|
| Language detection | CJK ratio ≥ 0.10 → `ja`; else `en`; < 100 chars → fallback to hint | `crawler.py` |
| Chunk size | min 40 chars, max 500 chars | `rag_pipeline.toml` |
| Chunk overlap | 50 chars sliding window | `rag_pipeline.toml` |
| Embedding dimension | 384 (production, `config/common.toml:43`); dataclass default 384 (`models_config.py:53`). float32 little-endian BLOB | `config/common.toml` — see `03_rag_90` DOC-03 |
| Crawl depth | max 6 hops from start URL | `rag_pipeline.toml` |
| Crawl page limit | max 500 pages per site | `rag_pipeline.toml` |
| DB | SQLite single-node only | architecture |

---

## Related Chapters

| Topic | File |
|---|---|
| Ingestion scripts (API, CLI, config) | [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) |
| Query pipeline (API, stage details) | [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) |
| DB schema, type definitions | [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) |
| Configuration, run commands, logs | [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) |
| Known bugs and inconsistencies | [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) |
