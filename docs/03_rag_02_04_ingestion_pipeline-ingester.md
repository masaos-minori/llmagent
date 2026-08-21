---
title: "RagIngester Detail (Part 1)"
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
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_05_ingestion_pipeline-document-manager.md
  - 03_rag_02_06_ingestion_pipeline-supporting-components.md
  - 03_rag_05_1-configuration-reference.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
source:
  - 03_rag_02_04_ingestion_pipeline-ingester.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.1 Class Overview

`RagIngester` reads chunk files, generates embeddings via `embed-llm` (port 8081), and upserts them into SQLite (`documents` / `chunks` / `chunks_vec`). Processed chunks are moved to `rag-src/registered/`.

For a complete list of dataclasses and public methods, see `scripts/rag/ingestion/ingester.py`.

### 4.2 Detailed Behavior

- **E5 Prefix:** Prepends `passage: {text}` before embedding (uses `query: ` for queries).
- **Vector Encoding:** Uses `struct.pack(f"<{N}f", *values)` $\rightarrow$ Little-endian float32 BLOB.
- **Parallel Embedding:** Uses `ThreadPoolExecutor(embed_workers)` per URL group. Each thread uses an independent `SQLiteHelper().open()`.
- **WAL Mode:** Uses `PRAGMA journal_mode=WAL` for concurrent read/write safety.
- **Upsert (`--force`):** Deletes in order: `chunks_vec` $\rightarrow$ `chunks` $\rightarrow$ `documents`, then re-inserts. The original `chunking_strategy` value from the source file is preserved.

### 4.2.1 Immutable Deletion Order

The following deletion order is a design invariant and must be maintained in all code paths that delete document records.

``` text
chunks_vec (explicitly deleted) → documents (deleting documents triggers cascading deletion of chunks via ON DELETE CASCADE)
```

**Reason:** `chunks_vec` is a `sqlite-vec` virtual table and does not have a foreign key constraint pointing to `chunks`. Therefore, only `chunks_vec` requires explicit deletion; no explicit `DELETE` statement exists for `chunks` itself (it relies on the `CASCADE` from deleting `documents`).

1. Explicitly delete rows in `chunks_vec` corresponding to the document's `chunk_ids`.
2. Delete the row in `documents` (`ON DELETE CASCADE` cascades the deletion to `chunks`, which also triggers synchronization triggers for `chunks_fts`).

**Affected Code Paths:**
- `DocumentManager.delete_existing_document()` (`scripts/rag/ingestion/document_manager.py`) — ingestion pipeline path. Internally calls shared helper `delete_document_chain()`.
- `DocumentManager.delete_document(url)` (`scripts/mcp_servers/rag_pipeline/document_manager.py`) — MCP tool (`rag_delete_document`) path.
- Both paths follow the same order to prevent orphaned vector records (see [ADR-005](../adr/ADR-005-rag-source-derived-index-relationships.md) for details).
- **Idempotency:** If the URL already exists in `documents`, processing is skipped. However, due to the freshness guard described below, `etag`/`last_modified` may still be updated. When skipped, `chunking_strategy` is NOT updated.
- **Freshness Guard for Skip Path:** Compares the input `fetched_at` (from the chunk payload) with the stored `documents.fetched_at`. If the input is older, the update is skipped (ensures newer crawls take precedence over older ones overwriting metadata). If `fetched_at` is missing (old format without freshness info), semantic "embedding only" is used: `COALESCE(etag, ?)`. This sets the value only if currently NULL and never overwrites non-NULL values, preventing old chunk files from overwriting more recent data.
- **Embedding Failure Tracking:** Chunk and embedding results are returned as a tuple. `n_embed_failed` counts failures specific to embedding, separate from parsing/DB errors.
- **Local File Unchanged Detection:** Compares SHA-256 ETags for `file://` URLs.

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_05_ingestion_pipeline-document-manager.md`
- `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`

## Keywords

ingester
embedding
sqlite
rag

# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4a. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.1 Class Overview

`RagIngester` reads chunk files, generates embeddings via `embed-llm` (port 8081), and upserts them into SQLite (`documents` / `chunks` / `chunks_vec`). Processed chunks are moved to `rag-src/registered/`.

For a complete list of dataclasses and public methods, see `scripts/rag/ingestion/ingester.py`.

### 4.2 Detailed Behavior

- **E5 Prefix:** Prepends `passage: {text}` before embedding (uses `query: ` for queries).
- **Vector Encoding:** Uses `struct.pack(f"<{N}f", *values)` $\rightarrow$ Little-endian float32 BLOB.
- **Parallel Embedding:** Uses `ThreadPoolExecutor(embed_workers)` per URL group. Each thread uses an independent `SQLiteHelper().open()`.
- **WAL Mode:** Uses `PRAGMA journal_mode=WAL` for concurrent read/write safety.
- **Upsert (`--force`):** Deletes in order: `chunks_vec` $\rightarrow$ `chunks` $\rightarrow$ `documents`, then re-inserts. The original `chunking_strategy` value from the source file is preserved.

### 4.2.1 Immutable Deletion Order

The following deletion order is a design invariant and must be maintained in all code paths that delete document records.

``` text
chunks_vec (explicitly deleted) → documents (deleting documents triggers cascading deletion of chunks via ON DELETE CASCADE)
```

**Reason:** `chunks_vec` is a `sqlite-vec` virtual table and does not have a foreign key constraint pointing to `chunks`. Therefore, only `chunks_vec` requires explicit deletion; no explicit `DELETE` statement exists for `chunks` itself (it relies on the `CASCADE` from deleting `documents`).

1. Explicitly delete rows in `chunks_vec` corresponding to the document's `chunk_ids`.
2. Delete the row in `documents` (`ON DELETE CASCADE` cascades the deletion to `chunks`, which also triggers synchronization triggers for `chunks_fts`).

**Affected Code Paths:**
- `DocumentManager.delete_existing_document()` (`scripts/rag/ingestion/document_manager.py`) — ingestion pipeline path. Internally calls shared helper `delete_document_chain()`.
- `DocumentManager.delete_document(url)` (`scripts/mcp_servers/rag_pipeline/document_manager.py`) — MCP tool (`rag_delete_document`) path.
- Both paths follow the same order to prevent orphaned vector records (see [ADR-005](../adr/ADR-005-rag-source-derived-index-relationships.md) for details).
- **Idempotency:** If the URL already exists in `documents`, processing is skipped. However, due to the freshness guard described below, `etag`/`last_modified` may still be updated. When skipped, `chunking_strategy` is NOT updated.
- **Freshness Guard for Skip Path:** Compares the input `fetched_at` (from the chunk payload) with the stored `documents.fetched_at`. If the input is older, the update is skipped (ensures newer crawls take precedence over older ones overwriting metadata). If `fetched_at` is missing (old format without freshness info), semantic "embedding only" is used: `COALESCE(etag, ?)`. This sets the value only if currently NULL and never overwrites non-NULL values. This prevents old chunk files from overwriting more recent data.
- **Embedding Failure Tracking:** Chunk and embedding results are returned as a tuple. `n_embed_failed` counts failures specific to embedding, separate from parsing/DB errors.
- **Local File Unchanged Detection:** Compares SHA-256 ETags for `file://` URLs.

### 4.3 CLI Arguments

| Argument | Description | Default |
|---|---|---|
| `--force` | Deletes existing `document`/`chunks`/`chunks_vec` records and re-embeds. For `file://` URLs, it always re-ingests regardless of ETag. | false |

### 4.4 Embedding API

``` http
POST http://127.0.0.1:8081/embedding
Content-Type: application/json

{"content": "passage: {text}"}
```

Response: `{"embedding": [float, ...]}` — 384 dimensions (multilingual-E5-small)

- `embedding_dims`: Specified in `config/ingester.toml` (default 384).
- docstring reference to `common.toml::embedding_dims` is outdated (`common.toml` does not exist).

### 4.5 Database Updates

Current DB schema definition $\rightarrow$ [RAG schema reference document](03_rag_02_06_ingestion_pipeline-supporting-components.md)

### 4.6 Error Handling

| Case | Action |
|---|---|
| Embedding API failure | Retries with exponential backoff up to `embed_retry` times (max 10s) |
| Retry limit reached (single chunk) | Logs a `WARNING`; skips the chunk and continues |
| Invalid `lang` value | Raises `ValueError`; skips the URL group; logs an `ERROR` with traceback |
| Improper `chunks_vec` deletion order | Raises `ValueError`; skips the chunk; logs a `WARNING` |
| Embedding dimension mismatch | Raises `ValueError`; skips the chunk; logs a `WARNING` |
| Artifact validation failure | Logs a `WARNING`; skips the chunk as an embedding failure |
| File move failure | Logs an `ERROR` containing structured fields: `url`, `source_type`, and `stage_name` |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`
- Detailed log message formats $\rightarrow$ `scripts/rag/ingestion/ingester.py`

Detailed ETagManager info $\rightarrow$ [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.8](03_rag_02_06_ingestion_pipeline-supporting-components.md)
Configuration details $\rightarrow$ [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.9](03_rag_02_06_ingestion_pipeline-supporting-components.md)

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_05_ingestion_pipeline-document-manager.md`
- `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`

## Keywords

ingester
embedding
sqlite
rag

# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4c. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.3 CLI Arguments

| Argument | Description | Default |
|---|---|---|
| `--force` | Deletes existing `document`/`chunks`/`chunks_vec` records and re-embeds. For `file://` URLs, it always re-ingests regardless of ETag. | false |

### 4.4 Embedding API

``` http
POST http://127.0.0.1:8081/embedding
Content-Type: application/json

{"content": "passage: {text}"}
```

Response: `{"embedding": [float, ...]}` — 384 dimensions (multilingual-E5-small)

- `embedding_dims`: Specified in `config/ingester.toml` (default 384).
- docstring reference to `common.toml::embedding_dims` is outdated (`common.toml` does not exist).

### 4.5 Database Updates

Current DB schema definition $\rightarrow$ [RAG schema reference document](03_rag_02_06_ingestion_pipeline-supporting-components.md)

### 4.6 Error Handling

| Case | Action |
|---|---|
| Embedding API failure | Retries with exponential backoff up to `embed_retry` times (max 10s) |
| Retry limit reached (single chunk) | Logs a `WARNING`; skips the chunk and continues |
| Invalid `lang` value | Raises `ValueError`; skips the URL group; logs an `ERROR` with traceback |
| Improper `chunks_vec` deletion order | Raises `ValueError`; skips the chunk; logs a `WARNING` |
| Embedding dimension mismatch | Raises `ValueError`; skips the chunk; logs a `WARNING` |
| Artifact validation failure | Logs a `WARNING`; skips the chunk as an embedding failure |
| File move failure | Logs an `ERROR` containing structured fields: `url`, `source_type`, and `stage_name` |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`
- Detailed log message formats $\rightarrow$ `scripts/rag/ingestion/ingester.py`

ETagManager detailed info $\rightarrow$ [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.8](03_rag_02_06_ingestion_pipeline-supporting-components.md)
Configuration detailed info $\rightarrow$ [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.9](03_rag_02_06_ingestion_pipeline-supporting-components.md)

---
