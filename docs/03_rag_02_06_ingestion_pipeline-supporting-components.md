---
title: "RAG Ingestion Pipeline - Supporting Components"
area: rag
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

`ETagManager` manages updates for existing document ETags and Last-Modified timestamps. It provides freshness guards: if `new_fetched_at` is older than the stored `fetched_at`, the input data is considered stale and the existing DB values are preserved. There is one update mode:
- **Freshness Mode:** Overwrites ETag/Last-Modified when freshness is confirmed.

**Public Methods**

| Method | Signature | Description |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str)` | Updates the ETag/Last-Modified of an existing document; returns early if both `etag` and `last_modified` are `None`. |

**Boundary Conditions:**
- `ETagManager` itself issues SQL only for the `doc_id` received in its `__init__`. The caller is responsible for passing the correct `doc_id`. `document_manager.py`'s `_update_etag()` accepts a `doc_id: int` argument and passes it to `ETagManager(self._db, doc_id)`, and since `handle_existing_document()` passes `existing_doc_id` through the entire path, ETag updates during existing document re-fetching function as intended.

### 4.8.1 Freshness Comparison: Edge Cases and Error Handling

- **Only current update mode:** Freshness Mode (above) is `ETagManager`'s only update
  mode — Null Fill Mode / `COALESCE`-based missing-`fetched_at` handling has been
  fully removed; no `_update_null_fill`, `null_fill`, or `COALESCE` reference remains
  anywhere under `scripts/rag/ingestion/`.
- **Timestamp format:** both the incoming and stored `fetched_at` are parsed via
  `datetime.fromisoformat()` after replacing a trailing `Z` with `+00:00`; a
  timezone-naive value is accepted and normalized to UTC (`replace(tzinfo=UTC)`).
- **Invalid incoming timestamp:** if the incoming `fetched_at` fails to parse,
  `_is_stale_update()` raises `ValueError(f"Invalid incoming timestamp: {value}")`.
- **Invalid stored timestamp:** if the stored `fetched_at` fails to parse,
  `_is_stale_update()` raises `ValueError(f"Invalid stored timestamp: {value}")`. Both
  cases raise the same `ValueError` type — the message text is the only current
  distinguishing mechanism; no separate exception classes exist for the two cases
  (Needs confirmation: whether distinct exception types are intended in the future).
- **Equal timestamps:** the staleness check is a strict `new_dt < stored_dt` — an
  incoming `fetched_at` equal to the stored value is **not** treated as stale, so the
  update proceeds.
- **Missing/empty stored `fetched_at`:** if no `documents` row exists for the
  `doc_id`, or its stored `fetched_at` is empty/absent (e.g. a pre-migration row),
  `_is_stale_update()` returns `False` (not stale) without attempting to parse it —
  the incoming value always wins in this case.
- **Both `etag` and `last_modified` absent:** as already documented above, `update()`
  returns early without any database write in this case — no staleness check occurs.

See [03_rag_02_04_ingestion_pipeline-ingester.md](03_rag_02_04_ingestion_pipeline-ingester.md)
and [03_rag_02_05_ingestion_pipeline-document-manager.md](03_rag_02_05_ingestion_pipeline-document-manager.md)
for how callers rely on this contract, and
[03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md) for
the `ValueError` conditions in the shared error-handling reference table.

## 4.9 Configuration (`config/ingester.toml`)

| Parameter | Default | Description |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8081/embedding` | Endpoint URL for the embedding API |
| `embed_retry` | 3 | Maximum retries on embedding API failure (exponential backoff) |
| `embed_workers` | 4 | Maximum number of concurrent embedding threads via `ThreadPoolExecutor` |
| Embedding dimension | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`) | Expected dimensions of the embedding vector |

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
