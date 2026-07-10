---
title: "DocumentManager Detail"
category: rag
tags:
  - document-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-ingester.md
  - 03_rag_02_ingestion_pipeline-utils.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_02_ingestion_pipeline.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

---

## 4.10 DocumentManager (`scripts/rag/ingestion/document_manager.py`)

`DocumentManager` — Manages document lifecycle for RagIngester. Handles existing document detection, ETag updates, and post-ingestion consistency reports. Extracted from `RagIngester` to reduce class size and separate concerns.

**Module-level function**

| Function | Signature | Description |
|---|---|---|
| `delete_document_chain` | `(db: SQLiteHelper, doc_id: int) -> None` | Delete `chunks_vec` → `chunks` → `documents` in order; chunks_vec must be deleted first because it has no FK constraint to chunks |

**Class: `DocumentManager`**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(db: SQLiteHelper) -> None` | Store DB connection reference |
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at\|None, is_file_url: Callable[[str], bool]) -> bool` | Handle an existing document; return True when the caller should skip insertion. force=False → update etag via ETagManager; file:// URLs with unchanged SHA-256 → skip; force=True → delete document chain and return False to allow re-insertion |
| `delete_existing_document` | `(doc_id: int) -> None` | Delete a document and its chunks; chunks_vec removed first because it has no FK constraint to chunks |
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]\|None = None) -> RagConsistencyReport \| None` | Run post-ingestion consistency check and callback; returns report or None if the check failed (DB errors during the check) |

**Intent inferred from code:**
- `handle_existing_document` receives `is_file_url` as a callable instead of checking `url.startswith("file://")` directly, allowing testability with mock implementations

**CLI entry point:**

```bash
uv run python scripts/rag/ingestion/ingester.py --force
```

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

document-manager
rag
