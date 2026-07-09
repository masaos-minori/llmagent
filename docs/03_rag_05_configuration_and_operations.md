# RAG Configuration and Operations

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Ingestion commands → [03_rag_02_ingestion_pipeline.md §1](03_rag_02_ingestion_pipeline.md)

---

## 1. Configuration Reference

crawler / chunk_splitter / ingester / rag-pipeline-mcp are each independent processes that read only their own config file. There is no shared config file. If DB path or external service URL is needed across multiple processes, each config file must specify it individually.

→ Process separation policy details: [90_shared_03 §2a](90_shared_03_runtime_and_execution.md#2a-process-separation-policy-config-isolation-policy)

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
| `ja_stop_pos` | `["particle", "auxiliary verb", "supplementary symbol", "blank", "interjection", "conjunction"]` | Sudachi POS categories treated as stop words in Japanese FTS5 indexing |

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
# All unprocessed .json files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file (use absolute path from config)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

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
| `chunk_splitter.py` | Delete existing `{stem}-*.json` chunks and regenerate |
| `ingester.py` | Delete `chunks_vec` → `chunks` → `documents` records for the URL, then re-insert |

### 2.6 RAG Consistency Checks (`db/maintenance.py`)

Use `check_rag_consistency(db)` to detect trigger-based sync failures and orphan records.
Run after large ingestion, after force-reinsertion, or during diagnostics.

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
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
| `fts_orphan_count` | `fts - chunks`; positive = extra FTS entries (data loss risk) |
| `affected_chunk_ids` | chunk_ids missing from FTS (up to 10) |
| `affected_doc_ids` | doc_ids for chunks missing from FTS (up to 10) |
| `affected_orphan_chunk_ids` | chunk_ids in `chunks_vec` with no matching `chunks` row (up to 10) |
| `affected_orphan_urls` | URLs of documents with orphan vec rows (up to 10; `None` when no parent document can be resolved) |

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
| Cross-encoder failure | `RagRerankError` is caught as `RuntimeError`, records `StageResult.status="failure"`, and logs a warning. The pipeline continues with `ctx.reranked=[]` (no RRF fallback). `use_rerank=False` uses RRF order + dedup instead. |

---

## 5. Constraints Reference

| Constraint | Value |
|---|---|
| Language detection threshold | CJK ratio ≥ 0.10 → `ja`; pages < 100 chars → use hint language |
| Chunk size range | 40–500 chars (configurable) |
| Chunk overlap | 50 chars sliding window |
| Embedding dimension | 384 (production, `config/agent.toml:43`). float32 little-endian BLOB |
| Crawl depth | max 6 hops |
| Crawl page limit | max 500 pages/site |
| Replica | Single-node SQLite only |

---

## 6. Local file re-ingestion

### First-time ingestion

Add the file path to `target_urls` in `config/rag_pipeline.toml` with scheme `file://`:

```toml
[[target_urls]]
url = "file:///path/to/file.py"
lang = "en"
```

Then run:

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

The crawler calls `crawl_file()`, writes a JSON to `rag-src/`, chunks it,
and embeds it into the SQLite vector store.

### Re-ingesting after file changes

The ingester compares the SHA-256 hash of the current file content against the
stored `etag` in `documents`:

- **Unchanged** (hash match): skipped automatically, no re-ingestion.
- **Changed** (hash differs): automatically re-ingested — delete old doc + chunks, re-chunk, re-embed.
- **`--force`**: delete and re-ingest regardless of hash.

Log messages during ingestion:

- `"file:// unchanged (sha256 match): file:///path/to/file"` — skipped
- `"file:// changed — auto re-ingesting: file:///path/to/file"` — re-ingested

### Batch re-ingestion of many local files

When multiple files change, run the crawler with `--targets-file` to re-crawl all listed `file://` URLs.
The crawler does not support `--force`; unchanged files are skipped automatically via SHA-256 hash comparison.
To force re-embedding of already-ingested URLs, run `ingester.py --force` after crawling:

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
uv run python scripts/rag/ingestion/ingester.py --force
```

### Comparison: local files vs. web URLs

| Aspect | Web URL | Local file (file://) |
|---|---|---|
| Skip unchanged | Yes (ETag/304) | Yes (SHA-256 hash) |
| Force re-index | `--force` | `--force` |

---

## RAG index consistency checks

The RAG index requires three tables to remain synchronized:
- `chunks` — canonical chunk records
- `chunks_fts` — FTS5 full-text index (populated by SQLite triggers)
- `chunks_vec` — vector embedding index

### Startup warning

On every agent startup, the RAG consistency check runs `check_rag_consistency()` (3 COUNT queries,
read-only, fast). If any inconsistency is detected, a warning is emitted to the console:

```
[RAG] Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

No warning is shown on a healthy index (only `logger.info("RAG consistency: OK")` is written).

### `/db rag rebuild-fts` command

The `/db rag rebuild-fts` command rebuilds `chunks_fts` from the canonical `chunks` table.

**Rebuild rule:** The rebuild indexes `COALESCE(normalized_content, content)`, identical to the FTS5 trigger (`chunks_ai`).

- Japanese chunks: when `normalized_content` is present (Sudachi-normalized), it is indexed
- English/code chunks: `normalized_content` is NULL → FTS5 falls back to `content` directly
- `chunks_fts` must not be manually edited — it is a derived index maintained by triggers or rebuild operations

**When to use:**
- `fts_gap > 0` (missing FTS entries) detected by `/db consistency`
- `fts_orphan_count > 0` (extra FTS entries, data loss risk)
- After large-scale ingestion to verify FTS index integrity

**Repair decision tree:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | Run `/db rag rebuild-fts` — FTS entries are missing; rebuild from `chunks` |
| `fts_orphan_count > 0` | Run `/db rag rebuild-fts` — FTS has extra entries (data loss risk; urgent) |

### `/db consistency` command

The `/db consistency` command shows numeric counts followed by an OK or error summary:

```
  chunks: 1042  fts: 1042  vec: 1042  fts_gap: 0  orphan_vec: 0  fts_orphan: 0
RAG consistency: OK (chunks/FTS/vec in sync)
```

On inconsistency:

```
  chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
RAG consistency: FAIL
Consistency issue: [WARNING] FTS gap detected (chunks=1042, fts=1039, gap=3). Affected doc_ids: [1, 2, 3]. Run '/db rag rebuild-fts' to repair.
```

### Threshold policy

The check uses a **strict-zero** threshold: any non-zero `fts_gap`, `fts_orphan_count`,
or `orphan_vec_count` is reported as inconsistent. Configurable thresholds (e.g. allowing
`fts_gap <= 5`) are not implemented. **Needs confirmation** if partial-OK policy is required.

### Fixing inconsistencies

Use `/db consistency` to detect issues. The report includes affected `chunk_id`/URL
identifiers (up to 10 each) so operators can act without manual DB investigation.

**Repair decision tree:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | Run `/db rag rebuild-fts` — FTS entries are missing; rebuild from `chunks` |
| `fts_orphan_count > 0` | Run `/db rag rebuild-fts` — FTS has extra entries (data loss risk; urgent) |
| `orphan_vec_count > 0` | Run `ingester.py --force` for affected URLs — `chunks_vec` rows without `chunks` counterparts |
| `vec != chunks` | Run `ingester.py --force` for the affected URL — embedding step likely failed |

Run `/db rag rebuild-fts` to resynchronize `chunks_fts` from the `chunks` table.


<!-- AUTO-GENERATED: gen_rag_reference.py config -->
| Key | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | — |
| `crawl_delay` | `1.5` | — |
| `max_depth` | `6` | — |
| `min_chunk` | `40` | — |
| `max_chunk` | `500` | — |
| `embed_retry` | `3` | — |
| `embed_workers` | `4` | — |
| `fetch_retry` | `3` | — |
| `fetch_timeout` | `15` | — |
| `crawl_concurrency` | `3` | — |
| `max_pages` | `500` | — |
| `chunk_overlap` | `50` | — |
| `md_index_enable` | `False` | — |
| `md_snippet_max_chars` | `600` | — |
| `skip_nofollow` | `False` | — |
| `skip_external` | `True` | — |
| `target_urls` | `[['https://ziglang.org/documentation/master/', 'en'], ['https://zig.guide/', 'en'], ['https://www.ruby-lang.org/en/documentation/quickstart/', 'en'], ['https://www.ruby-lang.org/ja/documentation/quickstart/', 'ja'], ['https://docs.ruby-lang.org/en/3.4/doc/', 'en'], ['https://docs.ruby-lang.org/ja/3.4/doc/', 'ja'], ['https://www.gnu.org/software/emacs/manual/html_node/elisp/', 'en']]` | — |
| `en_stopwords` | `['a', 'an', 'the', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'i', 'you', 'he', 'she', 'we', 'they', 'them', 'their', 'our', 'your', 'my', 'his', 'her', 'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'each', 'other', 'such', 'into', 'through', 'about', 'than', 'then', 'when', 'where', 'who', 'which', 'what', 'how', 'all', 'any', 'more', 'most', 'also', 'up', 'out', 'as', 'just', 'over', 'after', 'before', 'while', 'since', 'because', 'although', 'however', 'therefore', 'thus', 'hence', 'whether', 'once', 'only', 'even', 'still', 'now', 'here', 'there', 'very', 'too', 'much', 'many', 'some', 'few', 'must', 'let', 'get', 'got', 'make', 'made', 'use', 'used', 'using', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'new', 'old', 'first', 'last', 'long', 'great', 'little', 'own', 'right', 'big', 'high', 'small', 'large', 'next', 'early', 'young', 'important', 'public', 'private', 'real', 'best', 'free', 'same', 'different']` | — |
| `ja_stop_pos` | `['particle', 'auxiliary verb', 'supplementary symbol', 'blank', 'interjection', 'conjunction']` | — |

---

## RAG MCP Internal Operations (Direct DB Access)

The following operations are internal to the RAG MCP service and directly access `rag.sqlite`
through `SQLiteHelper("rag")`. These are **not** Agent-layer direct DB access — they are
part of the RAG MCP service's responsibility boundary.

### `list_documents()`

Returns a list of documents with chunk counts, used by `/db rag urls` (via `rag_list_documents`
MCP tool).

```python
def list_documents(lang: str | None = None, limit: int = 20) -> list[DocumentItem]
```

**Access pattern:** Read-only query against `documents` and `chunks` tables.

### `delete_document()`

Deletes a document and its associated chunks/embeddings, used by `/db rag clean` (via
`rag_delete_document` MCP tool).

```python
def delete_document(url: str) -> bool
```

**Deletion order (critical):** The method enforces a strict deletion order to prevent orphan
records:

1. Delete `chunks_vec` rows first (embedding vectors for this document's chunks)
2. Delete `chunks` rows (triggers auto-sync `chunks_fts`)
3. Delete `documents` row (parent document)

This order is necessary because `chunks_vec` has no foreign key constraint pointing to
`chunks`. Deleting `chunks` first would leave orphaned vector records.

```python
# Order matters — chunks_vec before chunks before documents
db.execute(
    "DELETE FROM chunks_vec"
    " WHERE chunk_id IN"
    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
    (doc_id,),
)
db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
```

Other derived records (e.g., `chunks` table rows) rely on cascade deletes or triggers
where applicable.

---

### crawler

```
usage: crawler.py [-h] [--url URL [URL ...]] [--lang {en,ja,auto}]

BFS crawler: saves documents to rag-src/yyyymmddhhmmss-{slug}.json

options:
  -h, --help           show this help message and exit
  --url URL [URL ...]  URLs to crawl (multiple allowed; defaults to all
                       target_urls from config)
  --lang {en,ja,auto}  Hint language when --url is given (default: en). 'auto'
                       detects per-page language by CJK character ratio.
```

### chunk_splitter

```
usage: chunk_splitter.py [-h] [--file FILE] [--force]

Chunking: rag-src/*.json → rag-src/chunk/{stem}-{idx:04d}.json

options:
  -h, --help   show this help message and exit
  --file FILE  Process a single file (default: process all files in rag-
               src/*.json)
  --force      Re-process even if output chunks already exist
```

### ingester

```
usage: ingester.py [-h] [--force]

Embedding generation and DB ingestion: rag-src/chunk/*.json → SQLite → rag-
src/registered/

options:
  -h, --help  show this help message and exit
  --force     Force delete and re-ingest already registered URLs
```

<!-- END AUTO-GENERATED -->