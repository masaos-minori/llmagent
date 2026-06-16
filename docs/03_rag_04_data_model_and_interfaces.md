# RAG Data Model and Interfaces

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Ingestion API → [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md)
- Query pipeline API → [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md)

---

## 1. File Format Specifications

### 1.1 Crawler output file (`rag-src/yyyymmddhhmmss-{slug}.txt`)

Created by `WebCrawler`. Extension is `.txt`; content is JSON.

```json
{
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "body text",
  "code_blocks": ["code block 1", "code block 2"]
}
```

| Field | Type | Description |
|---|---|---|
| `url` | string | Normalized URL (fragment removed) |
| `title` | string | Page `<title>` tag content |
| `lang` | string | `"ja"` or `"en"` |
| `fetched_at` | string | ISO-8601 timestamp |
| `content` | string | Main body text (trafilatura extraction) |
| `code_blocks` | list[string] | `<pre>` block contents |

### 1.2 Chunk file (`rag-src/chunk/{stem}-{idx:04d}.txt`)

Created by `ChunkSplitter`. Same `.txt` extension; content is JSON.

```json
{
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.txt",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag-string",
  "last_modified": "optional-http-date"
}
```

| Field | Type | Description |
|---|---|---|
| `url` | string | Source document URL |
| `title` | string | Source document title |
| `lang` | string | `"ja"` or `"en"` |
| `source_file` | string | Filename of crawler output (`rag-src/{filename}`) |
| `chunk_index` | integer | Position within document (0-based) |
| `chunk_type` | string | `"text"` or `"code"` |
| `chunking_strategy` | string | `"text"` (sentence/paragraph split) or `"heading"` (Markdown heading boundary split) |
| `content` | string | Original chunk text; passed to LLM |
| `normalized_content` | string \| null | Sudachi normalized forms (JA only); used for FTS5 |
| `etag` | string \| null | HTTP ETag from original crawl |
| `last_modified` | string \| null | HTTP Last-Modified from original crawl |

---

## 2. SQLite Schema (`rag.sqlite`)

### 2.1 `documents` table

| Column | Type | Constraints | Description |
|---|---|---|---|
| `doc_id` | INTEGER | PRIMARY KEY | Auto-increment |
| `url` | TEXT | UNIQUE NOT NULL | Document URL |
| `title` | TEXT | | Page title |
| `lang` | TEXT | | Language code (`"ja"` / `"en"`) |
| `fetched_at` | TEXT | | Fetch timestamp (ISO-8601) |
| `etag` | TEXT | | HTTP ETag |
| `last_modified` | TEXT | | HTTP Last-Modified |
| `chunking_strategy` | TEXT | DEFAULT `'text'` | Chunk split strategy (`"text"` / `"heading"`). Added to existing DBs via `migrate_schema()`. |

> **Note:** `chunking_strategy` column was added to existing databases via `migrate_schema()`.
> Pre-migration rows will have `'text'` as the default.

### 2.2 `chunks` table

| Column | Type | Constraints | Description |
|---|---|---|---|
| `chunk_id` | INTEGER | PRIMARY KEY | Auto-increment |
| `doc_id` | INTEGER | FK → documents (ON DELETE CASCADE) | Parent document |
| `chunk_index` | INTEGER | | Position in document (0-based) |
| `content` | TEXT | | Original chunk text (for LLM) |
| `normalized_content` | TEXT | | Sudachi normalized text (JA FTS) |

### 2.3 `chunks_fts` (FTS5 virtual table)

- Full-text search index over `COALESCE(normalized_content, content)`
- Automatically synchronized by triggers:
  - `chunks_ai` (after INSERT): `INSERT INTO chunks_fts`
  - `chunks_au` (after UPDATE): `DELETE + INSERT`
  - `chunks_ad` (after DELETE): `DELETE FROM chunks_fts`
- Japanese: indexed on `normalized_content` (Sudachi forms)
- English/code: `normalized_content` is NULL → FTS5 uses `content` directly

### 2.4 `chunks_vec` (sqlite-vec virtual table)

- Stores embedding vectors as little-endian float32 BLOB
- `embedding` column: `struct.pack("<{N}f", *values)` format
- Dataclass default: 768 (`models_config.py:53` `IngesterConfig.embed_dimension`); production value set via `config/common.toml::embedding_dims` (default 384 — **Confirmed** from `common.toml:43`)
- No foreign key constraint (sqlite-vec virtual table); `chunks_vec` must be deleted
  **before** `chunks` when force-reinserting to avoid orphaned records

---

## 3. Hit Type Hierarchy

Defined in `rag/types.py`. Each stage produces a progressively richer hit type.

```
RawHit      — after SearchStage
MergedHit   — after FusionStage  (extends RawHit + rrf_score)
RankedHit   — after RerankStage  (extends MergedHit + rerank_score)

RagHit = RawHit | MergedHit | RankedHit  (backward-compat union alias)
```

| Field | Type | Available in |
|---|---|---|
| `chunk_id` | int | RawHit, MergedHit, RankedHit |
| `content` | str | RawHit, MergedHit, RankedHit |
| `url` | str | RawHit, MergedHit, RankedHit |
| `title` | str | RawHit, MergedHit, RankedHit |
| `distance` | float | RawHit (KNN only) |
| `bm25_score` | float | RawHit (FTS only) |
| `rrf_score` | float | MergedHit, RankedHit |
| `rerank_score` | float | RankedHit |

---

## 4. Public Interfaces (summary)

For full API signatures, see the linked chapters.

| Class | Module | Entry point | Details |
|---|---|---|---|
| `RagPipeline` | `rag/pipeline.py` | `augment(query) -> str` | [03_rag_03 §2](03_rag_03_query_pipeline.md) |
| `WebCrawler` | `rag/ingestion/crawler.py` | `crawl(targets)` | [03_rag_02 §2](03_rag_02_ingestion_pipeline.md) |
| `ChunkSplitter` | `rag/ingestion/chunk_splitter.py` | `process_all()` | [03_rag_02 §3](03_rag_02_ingestion_pipeline.md) |
| `RagIngester` | `rag/ingestion/ingester.py` | `ingest_all()` | [03_rag_02 §4](03_rag_02_ingestion_pipeline.md) |
| `PipelineStage` | `rag/stage.py` | Protocol | [03_rag_03 §3](03_rag_03_query_pipeline.md) |

---

## 5. Supporting Types

### 5.1 PipelineContext (`rag/stage.py`)

See [03_rag_03 §4](03_rag_03_query_pipeline.md) for field details.

### 5.2 LLMMessage (`shared/types.py`, re-exported from `rag/types.py`)

```python
from rag.types import LLMMessage
```

TypedDict with `total=False` (all keys optional per role).

| Key | Type | Role that uses it |
|---|---|---|
| `role` | str | All (`"user"` / `"assistant"` / `"tool"` / `"system"`) |
| `content` | str \| None | All (None when message contains only `tool_calls`) |
| `tool_calls` | list[dict] | `"assistant"` only |
| `tool_call_id` | str | `"tool"` only |
| `name` | str | `"tool"` only |

### 5.3 PipelineStageResult (`rag/types.py`)

| Field | Type | Description |
|---|---|---|
| `stage` | str | Stage name |
| `success` | bool | Execution success |
| `failure_reason` | str \| None | Reason on failure; None on success |
| `elapsed_s` | float | Elapsed seconds |

### 5.4 RagConfig Protocol (`shared/types.py`)

Structural type that `AgentConfig` implements. Injected as `cfg` into `RagPipeline.__init__`.

| Field | Type | Description |
|---|---|---|
| `use_search` | bool | False → skip pipeline entirely |
| `use_mqe` | bool | False → skip query expansion |
| `use_rrf` | bool | Currently unused (FusionStage always runs RRF) |
| `use_rerank` | bool | False → skip cross-encoder |
| `use_refiner` | bool | True → compress chunks via LLM |
| `top_k_search` | int | KNN/FTS result count per query |
| `top_k_rerank` | int | Candidates passed to cross-encoder |
| `rag_top_k` | int | Final chunks returned to LLM |
| `rag_min_score` | float | Cross-encoder score threshold |
| `max_chunks_per_doc` | int | Per-document chunk cap |
| `rag_service_url` | str | External RAG service URL; empty = in-process only |
| `semantic_cache_max_size` | int | SemanticCache entry limit |
| `semantic_cache_threshold` | float | Cache hit cosine similarity threshold |
| `refiner_max_tokens` | int | Max tokens for refiner LLM call |
| `refiner_max_chars_per_chunk` | int | Max chars per chunk for refiner |
| `refiner_timeout` | float | Refiner LLM call timeout (seconds) |
