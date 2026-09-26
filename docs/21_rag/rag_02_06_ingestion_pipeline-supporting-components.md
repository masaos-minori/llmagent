---
title: "RAG Ingestion Pipeline - Supporting Components"
area: rag
tags:
  - etag-manager
  - ingestion-configuration
  - rag
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_02_05_ingestion_pipeline-document-manager.md
  - rag_05_1-configuration-reference.md
source:
  - rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)

---

## 4.8 ETagManager (`scripts/rag/ingestion/etag_manager.py`)

`ETagManager` manages updates for existing document ETags and Last-Modified timestamps. It provides freshness guards: if `new_fetched_at` is older than the stored `fetched_at`, the input data is considered stale and the existing DB values are preserved. There is one update mode:
- **Freshness Mode:** Overwrites ETag/Last-Modified when freshness is confirmed.

For exhaustive detail, see `scripts/rag/ingestion/etag_manager.py` (ETagManager public methods) and `config/ingester.toml` (configuration parameters).

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

See [rag_02_04_ingestion_pipeline-ingester.md](rag_02_04_ingestion_pipeline-ingester.md)
and [rag_02_05_ingestion_pipeline-document-manager.md](rag_02_05_ingestion_pipeline-document-manager.md)
for how callers rely on this contract, and
[rag_05_4-error-handling-reference.md](rag_05_4-error-handling-reference.md) for
the `ValueError` conditions in the shared error-handling reference table.

## 4.9 Configuration (`config/ingester.toml`)

See [rag_05_1-configuration-reference.md section 1.2](rag_05_1-configuration-reference.md).

---

## Related Documents

- `rag_00_document-guide.md`
- `rag_01_system_overview.md`
- `rag_02_01_ingestion_pipeline-overview.md`
- `rag_02_02_ingestion_pipeline-crawler.md`
- `rag_02_03_ingestion_pipeline-chunksplitter.md`
- `rag_02_04_ingestion_pipeline-ingester.md`
- `rag_05_1-configuration-reference.md`

## Keywords

etag-manager
ingestion-configuration
rag
