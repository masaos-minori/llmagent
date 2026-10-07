---
title: "1. Configuration Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
---

# 9. Configuration Reference

Crawler / chunk_splitter / ingester / rag-pipeline-mcp are each independent processes, reading only their respective configuration files. There are no shared configuration files. If multiple processes require the same DB path or external service URL, they must specify them individually in their respective configuration files.

→ For details on the Process Separation Policy: [ADR-002](../10_adr/ADR-002-config-isolation.md) / [Process Separation Policy](../40_shared/shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

## 9.1 `config/crawler.toml`

Used by: `crawler.py` only

This file is the owner of the current operational values; the code defaults are defined in the corresponding config dataclass. Concrete values are intentionally not listed here.

| Parameter | Description |
|---|---|
| `rag_src_dir` | Crawler output directory: `{rag_src_dir}/*.json` |
| `rag_db_path` | SQLite database path (for ETag/Last-Modified reference) |
| `sqlite_timeout` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | SQLite busy timeout (milliseconds) |
| `crawl_delay` | Delay between crawl requests |
| `max_depth` | Maximum BFS hop depth from starting URL |
| `fetch_retry` | Max HTTP request retries (exponential backoff with a capped delay) |
| `fetch_timeout` | HTTP timeout per request (seconds) |
| `crawl_concurrency` | Upper limit for `asyncio.Semaphore` for parallel BFS requests |
| `max_pages` | Maximum pages per site (`visited` reaches this value stops BFS) |
| `skip_nofollow` | If true, skips links with `rel="nofollow"` from BFS queue |
| `skip_external` | If true, skips cross-origin links from BFS queue |
| `target_urls` | List of pairs in `[[url, lang], ...]` format. Used when `--url` is not specified |
| `min_chunk` | Minimum chunk size (characters). Chunks smaller than this are discarded as noise |

## 9.2 `config/chunk_splitter.toml`

Used by: `chunk_splitter.py` only

| Parameter | Description |
|---|---|
| `rag_src_dir` | Base directory for chunk input/output |
| `min_chunk` | Minimum chunk size (characters). Chunks smaller than this are discarded as noise |
| `max_chunk` | Maximum chunk size (characters) |
| `chunk_overlap` | Number of overlapping characters added from the previous chunk to the start of the next (zero disables overlap) |
| `md_index_enable` | Enables splitting at Markdown header boundaries for non-`.md` content with headers spanning 2+ lines. `.md`/`.markdown`/`.mdx` URLs always use heading splits |
| `md_snippet_max_chars` | Maximum characters per Markdown heading section. Falls back to text splitting if exceeded |
| `en_stopwords` | English stopwords to exclude from FTS5 indexing and chunking |
| `ja_stop_pos` | Sudachi POS categories treated as stopwords in Japanese FTS5 indexing |

## 9.3 `config/ingester.toml`

Used by: `ingester.py` only

| Parameter | Description |
|---|---|
| `rag_src_dir` | Chunk input directory: `{rag_src_dir}/chunk/*.json` |
| `rag_db_path` | SQLite database path |
| `sqlite_vec_so` | Shared library path for `sqlite-vec` extension |
| `sqlite_timeout` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | SQLite busy timeout (milliseconds) |
| `embed_url` | Embedding API endpoint |
| Embedding dimension | `scripts/db/store_protocols.py::get_embedding_dims()` — must match the actual deployed embedding model; see [deployment_01_deployment.md section 1.4](../90_deployment/deployment_01_deployment.md#14-obtaining-llm-models) for canonical model names |
| `embed_retry` | Max embedding API retries (exponential backoff) |
| `embed_workers` | Number of threads in `ThreadPoolExecutor` for parallel embedding |

**Note:** `strict_artifact_validation` is not a setting (`RagIngester.__init__` does not read it, and artifact validation function calls do not specify `strict`). Rejection of chunks with missing required fields is always enabled via Python defaults in the artifact validation function.

## 9.4 `config/rag_pipeline_mcp_server.toml`

Used by: `rag-pipeline-mcp` only (the rag-pipeline MCP server process). Loaded via `RagPipelineConfig.from_dict()` in `mcp_servers/rag_pipeline/rag_pipeline_models.py`. Does NOT use `agent.toml` (as stated in the header comment).

**Note:** `host`/`port` are not configuration keys because `RagPipelineConfig` does not load them. The bind host (in the `MCPServer` base class) and port (in `rag_pipeline_server.py`) are hardcoded. `http_timeout` is hardcoded in `rag_pipeline_service.py`; this is the HTTP client timeout for the MCP server itself, while a separate, shorter timeout is used for fallback calls to external RAG services.

| Parameter | Description |
|---|---|
| `rag_db_path` | SQLite database path |
| `sqlite_vec_so` | Shared library path for `sqlite-vec` extension |
| `sqlite_timeout` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | SQLite busy timeout (milliseconds) |
| `llm_url` | LLM endpoint for MQE and reranking |
| `embed_url` | Embedding API endpoint |
| `use_mqe` | Enable query expansion |
| `use_rrf` | Enable RRF merging |
| `rrf_k` | RRF smoothing constant |
| `use_rerank` | Enable reranking via cross-encoder |
| `use_refiner` | Enable chunk compression via LLM |
| `top_k_search` | KNN/FTS hits per query |
| `top_k_rerank` | Cross-encoder candidates |
| `rag_top_k` | Final number of chunks returned to LLM |
| `rag_min_score` | Score threshold for cross-encoder |
| `max_chunks_per_doc` | Max chunks per document |
| `refiner_max_tokens` | Max tokens for Refiner LLM |
| `refiner_max_chars_per_chunk` | Max characters per chunk for Refiner |
| `refiner_timeout` | Refiner LLM timeout (seconds) |
| `rag_auth_token` | Token sent as `X-RAG-Token` to a remote RAG service; empty means no header |
| `mqe_n_queries` | Number of query variations generated by MQE |
| `mqe_prompt_template` | MQE prompt template. Placeholders: `{n_queries}`, `{query}` |
| `rerank_prompt_template` | Cross-encoder prompt template. Placeholders: `{query}`, `{items_text}` |

**Note:** For fallback calls to external RAG services (`call_rag_service()`), a fixed per-attempt timeout is hardcoded (`scripts/rag/pipeline_service.py`). This value is not loaded from configuration or `RagPipelineConfig`, so changing it requires source code modification.

## Implementation Supplements (Current behavior)

- `rag_pipeline_mcp_server.toml` is completely independent of `agent.toml`, and both files can have different values for same-named keys like `use_mqe`. The header comment explicitly states: "To override module-level caches for `agent_rag`, `rag_llm`, and `sqlite_helper`, and run the RAG pipeline independently from the main agent process." (Explicit in code)

## Hardcoded Values

The following values are **hardcoded** and cannot be changed via
`config/rag_pipeline_mcp_server.toml`; modifying them requires a source code change:

| Value | Source File |
|---|---|
| `http_host` | `MCPServer` base class (`server.py`) |
| `http_port` | `rag_pipeline_server.py` |
| `http_timeout` | `rag_pipeline_service.py` |
| Fallback `timeout` | `scripts/rag/pipeline_service.py::call_rag_service()` |

**Precedence rule:** When a key exists in `config/rag_pipeline_mcp_server.toml`, its
value overrides the corresponding code default in `RagPipelineConfig`; code defaults apply
only when a key is absent from the `.toml` file.

> **Warning:** Hardcoded values listed above cannot be changed by editing
> `config/rag_pipeline_mcp_server.toml`. Any modification must be made in the
> corresponding source file.

## 9.5 `config/agent.toml`

Used by: Agent process only. Loaded via `ConfigLoader().load_all()` to build `AgentConfig`.

**RagConfig Protocol Fields** (injected via `AgentConfig`):

| Field | Description |
|---|---|
| `use_search` | Toggle RAG on/off |
| `use_mqe` | Enable query expansion |
| `use_rrf` | Enable RRF merging (`True`) to perform rank-weighted fusion, or just deduplication (`False`). **Quality Trade-off:** Setting `False` disables rank scoring, making all hits' `rrf_score` equal to `0.0`. You also lose additional ranking effects from MQE. Unless you want to minimize overhead, it is recommended to keep this `True`. If set to `False`, a warning `WARNING rag config warning: use_rrf=false degrades retrieval quality` will be output during pipeline startup. |
| `use_rerank` | Enable reranking via cross-encoder |
| `use_refiner` | Enable chunk compression via LLM |
| `top_k_search` | KNN/FTS hits per query |
| `top_k_rerank` | Cross-encoder candidates |
| `rag_top_k` | Final number of chunks returned to LLM |
| `rag_min_score` | Score threshold for cross-encoder |
| `max_chunks_per_doc` | Max chunks per document |
| `rag_service_url` | URL for external RAG service (empty = in-process) |
| `refiner_max_tokens` | Max tokens for Refiner LLM |
| `refiner_max_chars_per_chunk` | Max characters per chunk for Refiner |
| `refiner_timeout` | Refiner LLM timeout (seconds) |

---


## Keywords

- configuration
