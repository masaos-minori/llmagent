# RAG Configuration and Operations

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Ingestion commands → [03_rag_02_ingestion_pipeline.md §1](03_rag_02_ingestion_pipeline.md)

---

## 1. Configuration Reference

### 1.1 `config/rag_pipeline.toml`

Used by: crawler.py, chunk_splitter.py, ingester.py

| Parameter | Default | Description |
|---|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | Base directory for all pipeline files. crawler output: `{rag_src_dir}/*.txt`; chunks: `{rag_src_dir}/chunk/`; registered: `{rag_src_dir}/registered/` |
| `crawl_delay` | `1.5` | Seconds to wait between crawl requests (minimum 1.0 recommended) |
| `max_depth` | `6` | BFS maximum hop depth from start URL |
| `fetch_retry` | `3` | HTTP request retry limit (exponential backoff: `min(2**i, 10)` sec) |
| `fetch_timeout` | `15` | HTTP request timeout per request (seconds) |
| `crawl_concurrency` | `3` | `asyncio.Semaphore` limit for parallel BFS requests |
| `max_pages` | `500` | Maximum pages per site (BFS stops when `visited` reaches this) |
| `skip_nofollow` | `false` | When true, skip `rel="nofollow"` links from BFS queue |
| `skip_external` | `true` | When true, skip cross-origin links from BFS queue |
| `target_urls` | — | List of `[[url, lang], ...]` pairs; used when `--url` is not specified |
| `min_chunk` | `40` | Minimum chunk size (chars); smaller chunks are discarded as noise |
| `max_chunk` | `500` | Maximum chunk size (chars) |
| `chunk_overlap` | `50` | Overlap chars prepended from previous chunk to next (0 = disabled) |
| `md_index_enable` | `false` | Enable Markdown heading-boundary splitting for non-`.md` content with ≥2 heading lines. `.md`/`.markdown`/`.mdx` URLs always use heading split regardless |
| `md_snippet_max_chars` | `600` | Max chars per Markdown heading section; fallback to text split if exceeded |
| `embed_retry` | `3` | Embed API retry limit (exponential backoff) |
| `embed_workers` | `4` | `ThreadPoolExecutor` thread count for parallel embedding |
| `en_stopwords` | (see config) | English stopwords excluded from FTS5 indexing and chunking (articles, prepositions, conjunctions, common verbs) |
| `ja_stop_pos` | `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]` | Sudachi POS categories treated as stop words in Japanese FTS5 indexing |

### 1.2 `config/common.toml`

| Parameter | Default | Description |
|---|---|---|---|
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint (llama.cpp legacy format) |
| `embedding_dims` | `384` | Dimensionality of float32 embedding vectors (must match model: all-MiniLM-L6-v2 = 384) |
| `rag_db_path` | `/opt/llm/db/rag.sqlite` | SQLite database path |
| `sqlite_vec_so` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec extension shared library path |

### 1.3 `config/agent.toml`

Used by RagPipeline (loaded via `_get_cfg()` on first access):

| Parameter | Default | Description |
|---|---|---|
| `llm_url` | `http://127.0.0.1:8002/v1/chat/completions` | LLM endpoint for MQE and rerank |
| `mqe_n_queries` | `3` | Number of query variants to generate in MQE |
| `rrf_k` | `60` | RRF smoothing constant (Σ 1/(rrf_k + rank)) |
| `mqe_prompt_template` | (built-in) | MQE prompt template; placeholders: `{n_queries}`, `{query}` |
| `rerank_prompt_template` | (built-in) | Cross-encoder prompt template; placeholders: `{query}`, `{items_text}` |

**RagConfig Protocol fields** (injected via `AgentConfig`):

| Field | Description |
|---|---|
| `use_search` | Global RAG on/off switch |
| `use_mqe` | Enable query expansion |
| `use_rrf` | Enable RRF merge (True) or simple dedup fallback (False) |
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

## 2. Execution Guide

### 2.1 Prerequisites

```bash
# Confirm embed-llm is running
curl -s http://127.0.0.1:8003/health

# Confirm config file is present (defines rag_src_dir, defaults to /opt/llm/rag-src)
ls -la config/rag_pipeline.toml
```

### 2.2 Step 1: Crawl

```bash
# All target_urls from config/rag_pipeline.toml
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# Single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# Multiple URLs (same --lang applied to all)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en
```

### 2.3 Step 2: Chunk split

```bash
# All unprocessed .txt files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file (use absolute path from config)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.txt

# Regenerate existing chunks (--force)
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### 2.4 Step 3: Embed and store

```bash
# Confirm embed-llm before running
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# Force re-register (delete and re-insert) existing URLs
uv run python scripts/rag/ingestion/ingester.py --force
```

### 2.5 `--force` behavior per script

| Script | `--force` effect |
|---|---|
| `crawler.py` | Not applicable (crawler always overwrites; idempotency via `visited` set per run) |
| `chunk_splitter.py` | Delete existing `{stem}-*.txt` chunks and regenerate |
| `ingester.py` | Delete `chunks_vec` → `chunks` → `documents` records for the URL, then re-insert |

### 2.6 RAG Consistency Checks (`db/maintenance.py`)

Use `check_rag_consistency(db)` to detect trigger-based sync failures and orphan records.
Run after large ingestion, after force-reinsertion, or during diagnostics.

```python
from db.maintenance import check_rag_consistency, is_consistent, summarize_issues
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

**`RagConsistencyReport` fields:**

| Field | Description |
|---|---|
| `chunks` | Row count in `chunks` table |
| `fts` | Indexed document count in `chunks_fts_docsize` shadow table |
| `vec` | Row count in `chunks_vec` table |
| `orphan_vec_count` | `chunks_vec` rows whose `chunk_id` has no matching row in `chunks` |
| `fts_gap` | `chunks - fts`; 0 = FTS index is in sync |

**CLI:** `/db consistency` runs the same check from the REPL and prints issues.

**Post-ingest warning:** `ingester.py` runs a non-blocking consistency check after each `ingest_all()` run; warnings are logged but ingestion does not abort.

**Notes:**
- `fts` is read from `chunks_fts_docsize` (FTS5 shadow table), not from `chunks_fts` directly.
  This gives the true FTS5 indexed document count, independent of the backing table join.
- `orphan_vec_count > 0` indicates a vec trigger failure; repair by re-running `ingester.py --force`
  for the affected URL.
- This function is read-only; it does not repair inconsistencies.
- Performance: the `NOT IN` subquery in orphan detection is O(vec × chunks). Run during
  maintenance windows on large datasets.

---

## 3. Logging

| Script | Log file | Log levels |
|---|---|---|
| `crawler.py` | `/opt/llm/logs/crawl.log` + stderr | INFO: start/save/skip; WARNING: HTTP error/retry |
| `chunk_splitter.py` | `/opt/llm/logs/chunk.log` + stderr | INFO: file/chunk counts; WARNING: Sudachi error; ERROR: file failure (traceback) |
| `ingester.py` | `/opt/llm/logs/ingest.log` + stderr | INFO: chunk/insert/move counts; WARNING: embed error/retry/skip; ERROR: read/move/group failure (traceback) |

**Common format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

---

## 4. Error Handling Reference

### Crawler

| Error | Action |
|---|---|
| HTTP failure | Retry up to `fetch_retry` with exponential backoff (`min(2**i, 10)` sec) |
| URL-level exception | `WARNING` + continue |
| Language not `ja`/`en` | Skip URL |

### ChunkSplitter

| Error | Action |
|---|---|
| Sudachi tokenize error | Return `""`; skip chunk; `WARNING` |
| File-level failure | `ERROR` (traceback); continue to next file |
| Existing chunks | Skip unless `--force` |

### RagIngester

| Error | Action |
|---|---|
| Embed API failure | Retry up to `embed_retry` with exponential backoff |
| Retry exhausted (single chunk) | `WARNING`; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` (traceback) |

### RagPipeline

| Error | Action |
|---|---|
| DB open error | Raise `RagPipelineError` (not return `""`) |
| `use_search=False` | Return `""` immediately |
| `rag_service_url` set + failure | Fall back to in-process pipeline |
| Cross-encoder failure | Fall back to RRF order |

---

## 5. Constraints Reference

| Constraint | Value |
|---|---|
| Language detection threshold | CJK ratio ≥ 0.10 → `ja`; pages < 100 chars → use hint language |
| Chunk size range | 40–500 chars (configurable) |
| Chunk overlap | 50 chars sliding window |
| Embedding dimension | 384 (production, `config/common.toml:43`); dataclass default 768. float32 little-endian BLOB |
| Crawl depth | max 6 hops |
| Crawl page limit | max 500 pages/site |
| Replica | Single-node SQLite only |
