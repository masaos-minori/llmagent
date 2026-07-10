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
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-ingester.md
  - 03_rag_02_ingestion_pipeline-utils.md
  - 03_rag_02_ingestion_pipeline-document-manager.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_02_ingestion_pipeline.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

---

## 4.8 ETagManager (`scripts/rag/ingestion/etag_manager.py`)

`ETagManager` — Manages ETag/Last-Modified updates for existing documents. Provides stale guard: if new_fetched_at < stored fetched_at, the incoming data is older and the existing DB values are kept. Two update modes:
- Freshness mode: Overwrite ETag/Last-Modified when freshness is proven (uses COALESCE for fetched_at)
- Null-fill mode: Fill NULL only; never overwrite existing values (uses COALESCE for both etag and last_modified)

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str \| None = None)` | Refresh ETag/Last-Modified for an existing document; returns early if both etag and last_modified are None |

## 4.9 Configuration (`config/rag_pipeline.toml`)

| Parameter | Default | Description |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint URL |
| `embed_retry` | 3 | Retry limit for embedding API failures (exponential backoff) |
| `embed_workers` | 4 | Max concurrent embed threads via ThreadPoolExecutor |
| `embedding_dims` | 384 | Expected embedding vector dimension; validated against API response |
| `strict_artifact_validation` | False | Require `schema_version`, `artifact_type`, `created_by` in chunk JSON payloads |

See [03_rag_05_configuration_and_operations.md §1.2](03_rag_05_1-configuration-reference.md).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-ingester.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

etag-manager
ingestion-configuration
rag
