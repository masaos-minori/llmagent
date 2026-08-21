---
title: "1. Configuration Reference"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 1. Configuration Reference

Crawler / chunk_splitter / ingester / rag-pipeline-mcp are each independent processes, reading only their respective configuration files. There are no shared configuration files. If multiple processes require the same DB path or external service URL, they must specify them individually in their respective configuration files.

→ For details on the Process Separation Policy: [ADR-002](adr/ADR-002-config-isolation.md) / [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

## 1.1 `config/crawler.toml`

Used by: `crawler.py` only

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Crawler output directory: `{rag_src_dir}/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path (for ETag/Last-Modified reference) |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `crawl_delay` | `1.5` | Delay between crawl requests (minimum 1.0 recommended) |
| `max_depth` | `3` | Maximum BFS hop depth from starting URL |
| `fetch_retry` | `3` | Max HTTP request retries (exponential backoff: `min(2**i, 10)` seconds) |
| `fetch_timeout` | `15` | HTTP timeout per request (seconds) |
| `crawl_concurrency` | `3` | Upper limit for `asyncio.Semaphore` for parallel BFS requests |
| `max_pages` | `200` | Maximum pages per site (`visited` reaches this value stops BFS) |
| `skip_nofollow` | `true` | If true, skips links with `rel="nofollow"` from BFS queue |
| `skip_external` | `true` | If true, skips cross-origin links from BFS queue |
| `target_urls` | — | List of pairs in `[[url, lang], ...]` format. Used when `--url` is not specified |
| `min_chunk` | `40` | Minimum chunk size (characters). Chunks smaller than this are discarded as noise |

## 1.2 `config/chunk_splitter.toml`

Used by: `chunk_splitter.py` only

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Base directory for chunk input/output |
| `min_chunk` | `40` | Minimum chunk size (characters). Chunks smaller than this are discarded as noise |
| `max_chunk` | `500` | Maximum chunk size (characters) |
| `chunk_overlap` | `50` | Number of overlapping characters added from the previous chunk to the start of the next (0=disabled) |
| `md_index_enable` | `false` | Enables splitting at Markdown header boundaries for non-`.md` content with headers spanning 2+ lines. `.md`/`.markdown`/`.mdx` URLs always use heading splits |
| `md_snippet_max_chars` | `600` | Maximum characters per Markdown heading section. Falls back to text splitting if exceeded |
| `en_stopwords` | (Refer to settings) | English stopwords to exclude from FTS5 indexing and chunking |
| `ja_stop_pos` | ["Particle", "Auxiliary Verb", "Punctuation", "Whitespace", "Interjection", "Conjunction"] | Sudachi POS categories treated as stopwords in Japanese FTS5 indexing |

## 1.3 `config/ingester.toml`

Used by: `ingester.py` only

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Chunk input directory: `{rag_src_dir}/chunk/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | Shared library path for `sqlite-vec` extension |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `embed_url` | `http://127.0.0.1:8081/embedding` | Embedding API endpoint |
| `embedding_dims` | `384` | float32 embedding vector dimensions (must match model; see [docs/02_deployment.md section 1.4](./02_deployment.md#14-llm--How to get models) for canonical model names) |
| `embed_retry` | `3` | Max embedding API retries (exponential backoff) |
| `embed_workers` | `4` | Number of threads in `ThreadPoolExecutor` for parallel embedding |

**Note (2026-07-13):** Confirmed that `strict_artifact_validation` is not used as a setting (`RagIngester.__init__` does not read it, and artifact validation function calls do not specify `strict`). Thus, it was removed from `config/ingester.toml`. In practice, rejection of chunks with missing required fields is always enabled via Python defaults in the artifact validation function.

## 1.4 `config/rag_pipeline_mcp_server.toml`

Used by: `rag-pipeline-mcp` only (the rag-pipeline MCP server process). Loaded via `RagPipelineConfig.from_dict()` in `mcp_servers/rag_pipeline/rag_pipeline_models.py`. Does NOT use `agent.toml` (as stated in the header comment).

**Note (2026-07-13):** `host`/`port` were removed from the config file because they were not loaded into `RagPipelineConfig` and were unused. Actual values are hardcoded: `http_host="127.0.0.1"` (in `MCPServer` base class), `http_port=8010` (in `rag_pipeline_server.py`). `http_timeout` is hardcoded as `120.0` in `rag_pipeline_service.py`; this is the HTTP client timeout for the MCP server itself, while a different timeout (10s) is used for fallback calls to external RAG services.

| Parameter | Default | Description |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | Shared library path for `sqlite-vec` extension |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `llm_url` | `http://127.0.0.1:8080/v1/chat/completions` | LLM endpoint for MQE and reranking |
| `embed_url` | `http://127.0.0.1:8081/embedding` | Embedding API endpoint |
| `use_mqe` | `true` | Enable query expansion |
| `use_rrf` | `true` | Enable RRF merging |
| `rrf_k` | `60` | RRF smoothing constant (recommended value 60) |
| `use_rerank` | `true` | Enable reranking via cross-encoder |
| `use_refiner` | `false` | Enable chunk compression via LLM |
| `top_k_search` | `5` (code default; operational config uses `20`) | KNN/FTS hits per query |
| `top_k_rerank` | `10` (code default; operational config uses `15`) | Cross-encoder candidates |
| `rag_top_k` | `5` | Final number of chunks returned to LLM |
| `rag_min_score` | `0.0` (code default; operational config uses `2.0`) | Score threshold for cross-encoder |
| `max_chunks_per_doc` | `3` | Max chunks per document |
| `use_semantic_cache` | `false` | Whether to use SemanticCache |
| `semantic_cache_max_size` | `128` (code default; operational config uses `100`) | SemanticCache capacity |
| `semantic_cache_threshold` | `0.92` | Cosine similarity threshold for cache hit detection |
| `refiner_max_tokens` | `512` | Max tokens for Refiner LLM |
| `refiner_max_chars_per_chunk` | `800`(code default; operational config uses `300`) | Max characters per chunk for Refiner |
| `refiner_timeout` | `30.0`(operational config value) | Refiner LLM timeout (seconds) |
| `mqe_n_queries` | `3` | Number of query variations generated by MQE |
| `mqe_prompt_template` | (built-in) | MQE prompt template. Placeholders: `{n_queries}`, `{query}` |
| `rerank_prompt_template` | (built-in) | Cross-encoder prompt template. Placeholders: `{query}`, `{items_text}` |

**Note (2026-07-13):** For fallback calls to external RAG services (`call_rag_service()`), a `timeout=10.0` is hardcoded for each attempt (`scripts/rag/pipeline_service.py`). This value is not loaded from configuration or `RagPipelineConfig`, so changing it requires source code modification.

## Implementation Supplements (Current behavior)

- The following parameters—`top_k_search`, `top_k_rerank`, `rag_min_score`, `semantic_cache_max_size`, and `refiner_max_chars_per_chunk`—have different default values in the `RagPipelineConfig` (`mcp_servers/rag_pipeline/rag_pipeline_models.py`) compared to what is written in the operational `config/rag_pipeline_mcp_server.toml`. As long as values exist in the `.toml` file, the code defaults are ignored, so there is no harm; however, be aware of this difference if deleting or simplifying the `.toml` file. (Explicit in code)
- `rag_pipeline_mcp_server.toml` is completely independent of `agent.toml`, and both files can have different values for same-named keys like `use_mqe`. The header comment explicitly states: "To override module-level caches for `agent_rag`, `rag_llm`, and `sqlite_helper`, and run the RAG pipeline independently from the main agent process." (Explicit in code)

## 1.5 `config/agent.toml`

Used by: Agent process only. Loaded via `ConfigLoader().load_all()` to build `AgentConfig`.

**RagConfig Protocol Fields** (injected via `AgentConfig`):

| Field | Description |
|---|---|
| `use_search` | Toggle RAG on/off |
| `use_mqe` | Enable query expansion |
| `use_rrf` | Enable RRF merging (`True`, default) to perform rank-weighted fusion, or just deduplication (`False`). **Quality Trade-off:** Setting `False` disables rank scoring, making all hits' `rrf_score` equal to `0.0`. You also lose additional ranking effects from MQE. Unless you want to minimize overhead, it is recommended to keep this `True`. If set to `False`, a warning `WARNING rag config warning: use_rrf=false degrades retrieval quality` will be output during pipeline startup. |
| `use_rerank` | Enable reranking via cross-encoder |
| `use_refiner` | Enable chunk compression via LLM |
| `top_k_search` | KNN/FTS hits per query |
| `top_k_rerank` | Cross-encoder candidates |
| `rag_top_k` | Final number of chunks returned to LLM |
| `rag_min_score` | Score threshold for cross-encoder |
| `max_chunks_per_doc` | Max chunks per document |
| `rag_service_url` | URL for external RAG service (empty = in-process) |
| `semantic_cache_max_size` | SemanticCache capacity (0 = immediate eviction/effectively disabled, negative = validation error) |
| `semantic_cache_threshold` | Cosine similarity threshold for cache hit detection |
| `refiner_max_tokens` | Max tokens for Refiner LLM |
| `refiner_max_chars_per_chunk` | Max characters per chunk for Refiner |
| `refiner_timeout` | Refiner LLM timeout (seconds) |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
