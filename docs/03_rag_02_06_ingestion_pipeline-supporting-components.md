---
title: "RAG Ingestion Pipeline - Supporting Components"
category: rag
tags:
  - etag-manager
  - ingestion-configuration
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_05_ingestion_pipeline-document-manager.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4.8 ETagManager (`scripts/rag/ingestion/etag_manager.py`)

`ETagManager` manages updates for existing document ETags and Last-Modified timestamps. It provides freshness guards: if `new_fetched_at` is older than the stored `fetched_at`, the input data is considered stale and the existing DB values are preserved. There are two update modes:
- **Freshness Mode:** Overwrites ETag/Last-Modified when freshness is confirmed (uses `COALESCE` for `fetched_at`).
- **Null Fill Mode:** Fills only `NULL` values; does not overwrite existing values (uses `COALESCE` for both `etag` and `last_modified`).

**Public Methods**

| Method | Signature | Description |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str \| None = None)` | Updates the ETag/Last-Modified of an existing document; returns early if both `etag` and `last_modified` are `None`. |

**Boundary Conditions:**
- `ETagManager` itself issues SQL only for the `doc_id` received in its `__init__`. The caller is responsible for passing the correct `doc_id`. **Resolved (NC-003)**: `document_manager.py`'s `_update_etag()` has been fixed to accept a `doc_id: int` argument and pass it to `ETagManager(self._db, doc_id)`, and since `handle_existing_document()` passes `existing_doc_id` through the entire path, ETag updates during existing document re-fetching function as intended.

## 4.9 Configuration (`config/ingester.toml`)

| Parameter | Default | Description |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8081/embedding` | Endpoint URL for the embedding API |
| `embed_retry` | 3 | Maximum retries on embedding API failure (exponential backoff) |
| `embed_workers` | 4 | Maximum number of concurrent embedding threads via `ThreadPoolExecutor` |
| `embedding_dims` | 384 | Expected dimensions of the embedding vector; verified against API response |

See [03_rag_05_1-configuration-reference.md section 1.2](03_rag_05_1-configuration-reference.md).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

etag-manager
ingestion-configuration
rag
