---
title: "RagIngester Detail"
category: rag
tags:
  - ingester
  - embedding
  - sqlite
  - etag-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-utils.md
  - 03_rag_02_ingestion_pipeline-document-manager.md
  - 03_rag_02_ingestion_pipeline-supporting-components.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_02_ingestion_pipeline.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.1 Class overview

`RagIngester` — reads chunk files, generates embeddings via `embed-llm` (port 8003),
and upserts to SQLite (`documents` / `chunks` / `chunks_vec`). Moves processed chunks to
`rag-src/registered/`.

**Dataclass**

| Class | Purpose |
|---|---|
| `IngestUrlResult` | Per-URL ingestion outcome returned by `ingest_url_group()`; fields: `url`, `n_success`, `n_failed`, `skipped`, `n_embed_failed` (default 0) |

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `ingester.toml`; init `httpx.Client` |
| `ingest_all` | `(force: bool = False, on_ingest_complete: Callable[[], None] \| None = None) -> RagConsistencyReport \| None` | Group chunk files by URL; process each group. Returns consistency report or None if the post-ingest consistency check failed (rare failure case when DB errors occur during the check); also returns None when no chunk files exist |
| `ingest_url_group` | `(doc_mgr: DocumentManager, db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> IngestUrlResult` | Process one URL group in ascending chunk_index order; moves files to registered/ after processing including on skip; returns `{n_success, n_failed, n_embed_failed, skipped}` |
| `close` | `() -> None` | Close the underlying `httpx.Client` |
| `__del__` | `() -> None` | Safety cleanup: close httpx.Client if not already closed (handles missing explicit close) |

### 4.2 Behavior details

- **E5 prefix:** prepend `passage: {text}` before embedding (vs `query: ` at query time)
- **Vector encoding:** `struct.pack(f"<{N}f", *values)` → little-endian float32 BLOB
- **Parallel embed:** `ThreadPoolExecutor(embed_workers)` per URL group;
  each thread uses an independent `SQLiteHelper().open()`
- **WAL mode:** `PRAGMA journal_mode=WAL` for concurrent read/write safety
- **Upsert (`--force`):** delete in order `chunks_vec` → `chunks` → `documents`, then re-INSERT; `chunking_strategy` is preserved from the source file

### 4.2.1 Deletion order invariant

The following deletion order is a design invariant — it must be maintained by all code paths that delete document records:

```
chunks_vec (first) → chunks → documents
```

**Reason:** `chunks_vec` is a sqlite-vec virtual table with no foreign key constraint pointing to `chunks`. Deleting `chunks` first would leave orphaned vector records. The order must be strictly enforced in every code path:

1. Delete `chunks_vec` rows for the document's chunk_ids
2. Delete `chunks` rows (triggers auto-sync `chunks_fts`)
3. Delete `documents` row

**Affected code paths:**
- `DocumentManager.delete_existing_document()` — deletes chunks_vec, chunks, documents rows
- `DocumentManager.delete_existing_document()` — MCP tool path
- Both must follow the same order to prevent orphaned vector records
- **Idempotency:** skip URL if already in `documents`; still UPDATE `etag`/`last_modified` via skip-path guard (see below); `chunking_strategy` is not updated during skip
- **Skip-path stale guard:** incoming `fetched_at` (chunk payload) is compared against stored `documents.fetched_at`; if incoming < stored the update is skipped (newer crawl wins — prevents stale chunk files from overwriting fresher metadata). Missing `fetched_at` (legacy chunks without a freshness signal) uses fill-only semantics: `COALESCE(etag, ?)` — only populates the stored field if currently NULL; never overwrites a non-NULL value. This prevents stale chunk-file metadata from replacing fresher values stored by a more recent crawl.
- **Embed failure tracking:** chunk and embedding results are returned as a tuple;
  `n_embed_failed` counts embedding-specific failures separately from parse/DB errors
- **Local file unchanged detection:** SHA-256 etags are compared for `file://` URLs

### 4.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--force` | Delete existing document/chunks/chunks_vec records and re-embed; always re-ingests regardless of etag (for `file://` URLs) | false |

### 4.4 Embedding API

```
POST http://127.0.0.1:8003/embedding
Request:  {"content": "passage: {text}"}
Response: {"embedding": [float, ...]}   # 384-dim (multilingual-E5-small; config/agent.toml::embedding_dims)
```

### 4.5 DB tables updated

| Table | Operation |
|---|---|
| `documents` | SELECT to check; DELETE+INSERT (`force=True`) or skip+UPDATE etag (`force=False`); stores `url`, `title`, `lang`, `etag`, `last_modified`, `chunking_strategy`, `fetched_at` |
| `chunks` | INSERT (FK → documents; ON DELETE CASCADE) |
| `chunks_vec` | INSERT BLOB vector |
| `chunks_fts` | Auto-synced by `chunks_ai` trigger (`COALESCE(normalized_content, content)`) |

### 4.6 Error handling

| Case | Action |
|---|---|
| Embed API failure | Exponential backoff retry up to `embed_retry` times (capped at 10 seconds) |
| Retry exhausted (single chunk) | `WARNING` log; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` log with traceback |
| `chunks_vec` delete order | Must delete `chunks_vec` first (no FK constraint on sqlite-vec virtual table) |
| Embedding dimension mismatch | `ValueError`; skip chunk; `WARNING` log |
| Artifact validation failure | `WARNING` log; skip chunk as embed failure |
| File move failure | `ERROR` log with url, source_type, stage_name structured fields |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing | Structured fields |
|---|---|---|
| `INFO` | Chunks processed, DB inserts, file moves, skipped URLs | `doc_id`, `source_type`, `stage_name` (on insert); `url` (on skip) |
| `WARNING` | Embed API error, retry, embed skip | `source_type`, `stage_name` |
| `ERROR` | Chunk file read error, file move error, URL group failure (with traceback) | — |

For ETagManager details → [03_rag_02_ingestion_pipeline-supporting-components.md §4.8](03_rag_02_ingestion_pipeline-supporting-components.md)
For Configuration details → [03_rag_02_ingestion_pipeline-supporting-components.md §4.9](03_rag_02_ingestion_pipeline-supporting-components.md)

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-utils.md`
- `03_rag_02_ingestion_pipeline-document-manager.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

ingester
embedding
sqlite
rag
