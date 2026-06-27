# RAG Data Model and Interfaces

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Ingestion API → [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md)
- Query pipeline API → [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md)

---

## 1. File Format Specifications

### 1.1 Crawler output file (`rag-src/yyyymmddhhmmss-{slug}.json`)

Created by `WebCrawler`. JSON format.

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

### 1.2 Chunk file (`rag-src/chunk/{stem}-{idx:04d}.json`)

Created by `ChunkSplitter`. JSON format.

```json
{
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
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

### 2.0 テーブル一覧

| テーブル | 種別 | 主な列 | 用途 |
|---|---|---|---|
| `documents` | 通常 | `doc_id` PK, `url` UNIQUE, `lang` | URL 単位のドキュメント管理 |
| `chunks` | 通常 | `chunk_id` PK, `doc_id` FK, `content` | 分割チャンク本文 |
| `chunks_fts` | FTS5 仮想 | `content`, `content_rowid='chunk_id'` | BM25 全文検索 |
| `chunks_vec` | vec0 仮想 | `chunk_id` PK, `embedding float[384]` | KNN ベクトル検索 |

FTS5 は `chunks` テーブルの INSERT/UPDATE/DELETE に対してトリガーで自動同期 (`chunks_ai` / `chunks_au` / `chunks_ad`)。

> **Note:** `sessions` and `messages` tables are owned by the Agent REPL layer, not the RAG layer.
> They reside in the same SQLite file for operational convenience but are managed exclusively by `agent/session.py`.
> See `docs/05_agent_09_data-layer.md` for the Agent session schema.

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
| `chunk_type` | TEXT | | `"text"` or `"code"` (added via migration) |
| `source_file` | TEXT | | Filename of crawler output (added via migration) |

### 2.3 `chunks_fts` (FTS5 virtual table)

- Full-text search index over `COALESCE(normalized_content, content)`
- Tokenizer: `'unicode61'` (Unicode 6.1 normalization; Japanese queries use Sudachi POS-filtered tokens at query time)
- Automatically synchronized by triggers:
  - `chunks_ai` (after INSERT): `INSERT INTO chunks_fts`
  - `chunks_au` (after UPDATE): `DELETE + INSERT`
  - `chunks_ad` (after DELETE): `DELETE FROM chunks_fts`
- Japanese: indexed on `normalized_content` (Sudachi forms)
- English/code: `normalized_content` is NULL → FTS5 uses `content` directly. Validated by `tests/test_fts_fallback.py`.

### 2.4 `chunks_vec` (sqlite-vec virtual table)

- Stores embedding vectors as little-endian float32 BLOB
- `embedding` column: `float[DIMS]` (DIMS replaced at runtime via `_build_rag_schema_sql()`); `struct.pack("<{N}f", *values)` format
- Production value set via `config/common.toml::embedding_dims` (default 384 — **Confirmed** from `common.toml:43`); no dataclass default exists
- No foreign key constraint (sqlite-vec virtual table); `chunks_vec` must be deleted
  **before** `chunks` when force-reinserting to avoid orphaned records

---

## 3. Hit Type Hierarchy

Defined in `scripts/rag/types.py`. Each stage produces a progressively richer hit type. All three are `@dataclasses.dataclass` (not TypedDict).

```
RawHit      — after SearchStage
MergedHit   — after FusionStage  (extends RawHit + rrf_score)
RankedHit   — after RerankStage  (extends MergedHit + rerank_score)

RagHit = RawHit | MergedHit | RankedHit  (type union alias, not TypedDict)
```

| Field | Type | Available in |
|---|---|---|
| `chunk_id` | int | RawHit, MergedHit, RankedHit |
| `content` | str | RawHit, MergedHit, RankedHit |
| `url` | str | RawHit, MergedHit, RankedHit |
| `title` | str | RawHit, MergedHit, RankedHit |
| `distance` | float | RawHit (KNN only; default: 0.0) |
| `bm25_score` | float | RawHit (FTS only; default: 0.0) |
| `rrf_score` | float | MergedHit, RankedHit (default: 0.0) |
| `rerank_score` | float \| None | RankedHit (default: None) |

---

## 4. Public Interfaces (summary)

For full API signatures, see the linked chapters.

| Class | Module | Entry point | Details |
|---|---|---|---|
| `RagPipeline` | `scripts/rag/pipeline.py` | `augment(query) -> str` | [03_rag_03 §2](03_rag_03_query_pipeline.md) |
| `WebCrawler` | `scripts/rag/ingestion/crawler.py` | `crawl(targets)` | [03_rag_02 §2](03_rag_02_ingestion_pipeline.md) |
| `ChunkSplitter` | `scripts/rag/ingestion/chunk_splitter.py` | `process_all()` | [03_rag_02 §3](03_rag_02_ingestion_pipeline.md) |
| `RagIngester` | `scripts/rag/ingestion/ingester.py` | `ingest_all()` | [03_rag_02 §4](03_rag_02_ingestion_pipeline.md) |
| `PipelineStage` | `scripts/rag/stage.py` | Protocol | [03_rag_03 §3](03_rag_03_query_pipeline.md) |

---

## 5. Supporting Types

### 5.1 PipelineContext (`scripts/rag/stage.py`)

See [03_rag_03 §4](03_rag_03_query_pipeline.md) for field details (includes `search_diagnostics` field).

### 5.2 LLMMessage (`shared/types.py`, re-exported from `scripts/rag/types.py`)

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

### 5.3 StageResult (`scripts/rag/stage.py`)

Used by `RagPipeline.last_stage_results` and `PipelineContext.stage_results`.

| Field | Type | Description |
|---|---|---|
| `stage_name` | str | Class name of the stage |
| `status` | str | `"success"` / `"fallback"` / `"failure"` |
| `elapsed_seconds` | float | Wall-clock seconds for the stage |
| `fallback_reason` | str \| None | Reason when status is `"fallback"`; `None` on success |

### 5.4 RagConfig Protocol (`shared/types.py`)

Structural type that `AgentConfig` implements. Injected as `cfg` into `RagPipeline.__init__`.

| Field | Type | Description |
|---|---|---|
| `use_search` | bool | False → skip pipeline entirely |
| `use_mqe` | bool | False → skip query expansion |
| `use_rrf` | bool | Controls FusionStage: True → RRF merge; False → `_dedup_hits()` fallback |
| `use_rerank` | bool | False → skip cross-encoder |
| `use_refiner` | bool | True → compress chunks via LLM |
| `use_semantic_cache` | bool | True → enable semantic cache lookup/insert |
| `top_k_search` | int | KNN/FTS result count per query |
| `top_k_rerank` | int | Candidates passed to cross-encoder |
| `rag_top_k` | int | Final chunks returned to LLM |
| `rag_min_score` | float | Cross-encoder score threshold |
| `max_chunks_per_doc` | int | Per-document chunk cap |
| `rag_service_url` | str | External RAG service URL; empty = in-process only |
| `rag_auth_token` | str | Optional auth token for `X-RAG-Token` header; `""` = no auth (default) |
| `semantic_cache_max_size` | int | SemanticCache entry limit |
| `semantic_cache_threshold` | float | Cache hit cosine similarity threshold |
| `refiner_max_tokens` | int | Max tokens for refiner LLM call |
| `refiner_max_chars_per_chunk` | int | Max chars per chunk for refiner |
| `refiner_timeout` | float | Refiner LLM call timeout (seconds) |

### 5.5 RagQuery (`scripts/rag/types.py`)

```python
from rag.types import RagQuery

query = RagQuery(query="search term", context="optional context")
```

| Field | Type | Description |
|---|---|---|
| `query` | str | The query string (required) |
| `context` | str | Optional context for MQE expansion |

### 5.6 CacheService Protocol (`scripts/rag/cache.py`)

```python
from rag.cache import CacheService, SemanticCache
```

Protocol defining the interface for semantic cache implementations. `SemanticCache` is the concrete implementation.

| Method | Signature | Description |
|---|---|---|
| `lookup` | `(embedding: list[float], history_context: str = "") -> str \| None` | Return cached context if cosine similarity ≥ threshold among matching `history_context` entries; else `None` |
| `put` | `(embedding: list[float], history_context: str, context_str: str) -> None` | Store entry; prunes if over capacity |
| `invalidate` | `() -> None` | Bump generation counter and clear all cached entries atomically (used after ingestion to bust stale cache) |
| `generation` | `property -> int` | Current generation number; incremented by `invalidate()` |

#### CacheEntry dataclass

```python
from rag.models_data import CacheEntry
```

| Field | Type | Default | Description |
|---|---|---|---|
| `embedding` | `list[float]` | — | Embedding vector for cache lookup |
| `context_str` | `str` | — | Cached context string |
| `history_context` | `str` | `""` | History context for filtering cache hits |
| `generation` | `int` | `0` | Cache generation; bumped on invalidation to invalidate stale entries |

### 5.7 RAG Enums (`scripts/rag/enums.py`)

All defined as `StrEnum` subclasses.

#### LanguageCode

| Value | Description |
|---|---|
| `"en"` | English |
| `"ja"` | Japanese |

#### PipelineStageName

| Value | Description |
|---|---|
| `"mqe"` | Query expansion stage |
| `"search"` | Vector/FTS search stage |
| `"fusion"` | RRF merge stage |
| `"rerank"` | Cross-encoder rerank stage |
| `"augment"` | Context formatting stage |

#### HitKind

| Value | Description |
|---|---|
| `"vector"` | KNN result |
| `"fts"` | BM25 result |
| `"merged"` | RRF-merged result |
| `"ranked"` | Post-rerank result |

#### SearchBackend

| Value | Description |
|---|---|
| `"vector"` | sqlite-vec KNN |
| `"fts"` | FTS5 BM25 |
| `"hybrid"` | Combined vector + FTS |

#### MqeStatus

| Value | Description |
|---|---|
| `"expanded"` | Query was expanded |
| `"disabled"` | MQE disabled in config |
| `"failed"` | MQE LLM call failed |
