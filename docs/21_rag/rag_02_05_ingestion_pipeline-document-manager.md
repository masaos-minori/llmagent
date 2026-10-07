---
title: "DocumentManager Detail"
area: rag
tags:
  - document-manager
  - rag
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_05_01-configuration-reference.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)

---

## 4.10 DocumentManager (`scripts/rag/ingestion/document_manager.py`)

`DocumentManager` manages the lifecycle of documents for `RagIngester`: detection of existing documents, ETag refresh, document deletion, and post-ingestion consistency reporting. (Explicit in code — `scripts/rag/ingestion/document_manager.py`)

**Existing-document handling (`handle_existing_document()`):** returns the document id together with a skip flag and a replace-chunks flag.

- With `--force`, the document is never skipped and its chunks are replaced.
- For `file://` sources, the stored and new content hashes (kept in the `etag` column) are compared: a match skips the document, a mismatch triggers automatic re-ingestion, and a missing hash on either side counts as changed.
- For other sources, a skip happens only when both the stored ETag and Last-Modified equal the new values; otherwise the ETag fields are refreshed and the chunks are replaced.
- When no stored row is found, the document is neither skipped nor replaced.

**Deletion:** `delete_existing_document()` and the module-level `delete_document_chain()` delete the `chunks_vec` rows of the document first and then the `documents` row; the cascade removes `chunks`. This order is the invariant defined by [ADR-005](../10_adr/ADR-005-rag-source-derived-index-relationships.md).

**Post-ingestion consistency check (`check_consistency()`):** runs the RAG consistency check and logs each issue as a warning without failing the ingestion run. If the check itself raises a database or value error, the failure is logged and `None` is returned. The optional completion callback is invoked afterwards; an exception raised by the callback is logged and not re-raised. See [rag_05_07](rag_05_07-rag-index-consistency-checks.md).

**CLI Entrypoint:**

```bash
uv run python scripts/rag/ingestion/ingester.py --force
```

---

## Keywords

document-manager
etag-manager
doc_id
rag
