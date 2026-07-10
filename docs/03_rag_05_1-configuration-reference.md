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

## 1. Configuration Reference

crawler / chunk_splitter / ingester / rag-pipeline-mcp are each independent processes that read only their own config file. There is no shared config file. If DB path or external service URL is needed across multiple processes, each config file must specify it individually.

→ Process separation policy details: [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

### 1.1 `config/crawler.toml`

Used by: `crawler.py` のみ

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Crawler output directory: `{rag_src_dir}/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path (ETag/Last-Modified lookups) |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `crawl_delay` | `1.5` | Seconds to wait between crawl requests (minimum 1.0 recommended) |
| `max_depth` | `3` | BFS maximum hop depth from start URL |
| `fetch_retry` | `3` | HTTP request retry limit (exponential backoff: `min(2**i, 10)` sec) |
| `fetch_timeout` | `15` | HTTP request timeout per request (seconds) |
| `crawl_concurrency` | `3` | `asyncio.Semaphore` limit for parallel BFS requests |
| `max_pages` | `200` | Maximum pages per site (BFS stops when `visited` reaches this) |
| `skip_nofollow` | `true` | When true, skip `rel="nofollow"` links from BFS queue |
| `skip_external` | `true` | When true, skip cross-origin links from BFS queue |
| `target_urls` | — | List of `[[url, lang], ...]` pairs; used when `--url` is not specified |
| `min_chunk` | `40` | Minimum chunk size (chars); smaller chunks are discarded as noise |

### 1.2 `config/chunk_splitter.toml`

Used by: `chunk_splitter.py` only

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Base directory for chunk input/output |
| `min_chunk` | `40` | Minimum chunk size (chars); smaller chunks are discarded as noise |
| `max_chunk` | `500` | Maximum chunk size (chars) |
| `chunk_overlap` | `50` | Overlap chars prepended from previous chunk to next (0 = disabled) |
| `md_index_enable` | `false` | Enable Markdown heading-boundary splitting for non-`.md` content with ≥2 heading lines. `.md`/`.markdown`/`.mdx` URLs always use heading split regardless |
| `md_snippet_max_chars` | `600` | Max chars per Markdown heading section; fallback to text split if exceeded |
| `en_stopwords` | (see config) | English stopwords excluded from FTS5 indexing and chunking |
| `ja_stop_pos` | `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]` (particle, auxiliary verb, supplementary symbol, blank, interjection, conjunction) | Sudachi POS categories treated as stop words in Japanese FTS5 indexing |

### 1.3 `config/ingester.toml`

Used by: `ingester.py` only

| Parameter | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Chunk input directory: `{rag_src_dir}/chunk/*.json` |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec extension shared library path |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint |
| `embedding_dims` | `384` | Dimensionality of float32 embedding vectors (must match model: all-MiniLM-L6-v2 = 384) |
| `embed_retry` | `3` | Embed API retry limit (exponential backoff) |
| `embed_workers` | `4` | `ThreadPoolExecutor` thread count for parallel embedding |
| `strict_artifact_validation` | `true` | Reject chunks with missing required fields |

### 1.4 `config/rag_pipeline_mcp_server.toml`

Used by: `rag-pipeline-mcp` only (rag-pipeline MCP server process)

| Parameter | Default | Description |
|---|---|---|
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec extension shared library path |
| `sqlite_timeout` | `30` | SQLite connection timeout (seconds) |
| `sqlite_busy_timeout_ms` | `30000` | SQLite busy timeout (milliseconds) |
| `llm_url` | `http://127.0.0.1:8001/v1/chat/completions` | LLM endpoint for MQE and rerank |
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint |
| `mqe_n_queries` | `3` | Number of query variants to generate in MQE |
| `mqe_prompt_template` | (built-in) | MQE prompt template; placeholders: `{n_queries}`, `{query}` |
| `rerank_prompt_template` | (built-in) | Cross-encoder prompt template; placeholders: `{query}`, `{items_text}` |

### 1.5 `config/agent.toml`

Used by: Agent process only. Loaded from `ConfigLoader().load_all()` to build `AgentConfig`.

**RagConfig Protocol fields** (injected via `AgentConfig`):

| Field | Description |
|---|---|
| `use_search` | Global RAG on/off switch |
| `use_mqe` | Enable query expansion |
| `use_rrf` | Enable RRF merge (`True`, default) for rank-weighted fusion, or dedup-only (`False`). **Quality tradeoff:** `False` disables rank scoring — all hits get `rrf_score=0.0`; MQE provides no additional ranking benefit. Recommended: keep `True` unless minimizing overhead. Setting `False` emits `WARNING rag config warning: use_rrf=false degrades retrieval quality` at pipeline startup. |
| `use_rerank` | Enable cross-encoder reranking |
| `use_refiner` | Enable chunk compression via LLM |
| `top_k_search` | KNN/FTS hit count per query |
| `top_k_rerank` | Cross-encoder candidate count |
| `rag_top_k` | Final chunk count returned to LLM |
| `rag_min_score` | Cross-encoder score floor |
| `max_chunks_per_doc` | Per-document chunk cap |
| `rag_service_url` | External RAG service URL (empty = in-process) |
| `semantic_cache_max_size` | SemanticCache capacity |
| `semantic_cache_threshold` | Cache hit cosine similarity threshold |
| `refiner_max_tokens` | Max tokens for refiner LLM |
| `refiner_max_chars_per_chunk` | Max chars per chunk for refiner |
| `refiner_timeout` | Refiner LLM timeout (seconds) |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
