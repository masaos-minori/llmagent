---
title: "DocumentManager Detail"
category: rag
tags:
  - document-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4.10 DocumentManager (`scripts/rag/ingestion/document_manager.py`)

`DocumentManager` manages the lifecycle of documents for `RagIngester`. It handles detection of existing documents, updating ETags, and post-ingestion consistency reporting. It was extracted from `RagIngester` to reduce class size and separate concerns.

**Module-level Functions**

| Function | Signature | Description |
|---|---|---|
| `delete_document_chain` | `(db: SQLiteHelper, doc_id: int) -> None` | Deletes in order: `chunks_vec` $\rightarrow$ `chunks` $\rightarrow$ `documents`. `chunks_vec` must be deleted first as it lacks an FK constraint to `chunks`. |

**Class: `DocumentManager`**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(db: SQLiteHelper) -> None` | Holds a reference to the DB connection |
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at\|None, is_file_url: Callable[[str], bool]) -> bool` | Processes an existing document; returns `True` if the caller should skip insertion. If `force=False` $\rightarrow$ updates ETag via ETagManager; if `file://` URL and SHA-256 hasn't changed $\rightarrow$ skips; if `force=True` $\rightarrow$ deletes the document chain and returns `False` to allow re-insertion. |
| `delete_existing_document` | `(doc_id: int) -> None` | Deletes the document and its chunks; `chunks_vec` is deleted first because it lacks an FK constraint to `chunks`. |
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]\|None = None) -> RagConsistencyReport \| None` | Executes post-ingestion consistency checks and callbacks; returns a report or `None` if the check fails (e.g., DB error during checking). If the consistency check completes successfully (even if the report contains issues), the `on_ingest_complete` callback is called. If the consistency check itself raises an exception, the callback is not called. |



**CLI Entrypoint:**

```bash
uv run python scripts/rag/ingestion/ingester.py --force
```

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

document-manager
etag-manager
doc_id
rag
