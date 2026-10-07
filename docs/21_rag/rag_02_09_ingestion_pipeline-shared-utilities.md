---
title: "Shared Utilities Detail"
area: rag
tags:
  - shared-utilities
  - unicode-normalization
  - cosine-similarity
  - prompt-injection
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_02_08_ingestion_pipeline-shared.md
  - rag_05_01-configuration-reference.md
---

# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)

---

## 10. Shared Utilities (`scripts/rag/utils.py`)

```python
from rag.utils import (
    cosine_sim,
    floats_to_blob,
    normalize_unicode,
    sanitize_document,
    sanitize_document_full,
    validate_url,
)
```

This module provides stateless helpers shared by ingestion and query code. (Explicit in code — `scripts/rag/utils.py`)

**Vectors**

- `cosine_sim()` returns cosine similarity and returns `0.0` when either vector has zero magnitude.
- `floats_to_blob()` packs a float list into a little-endian float32 BLOB for sqlite-vec. It raises `TypeError` for a non-list and `ValueError` for an empty list or non-numeric or non-finite elements; a packing failure is logged and the `struct.error` is re-raised.

**Text normalization**

- `normalize_unicode()` applies NFKC normalization so that full-width and compatibility characters index consistently. It raises `TypeError` for a non-str input.

**Prompt injection sanitization**

- `sanitize_document()` replaces text matching the known injection patterns (for example "ignore instructions", "system:", "new instructions:") with a `[REMOVED]` marker and leaves clean text unchanged.
- `sanitize_document_full()` does the same and also returns a `SanitizeResult` recording whether sanitization happened and which patterns matched.

**URL validation**

- `validate_url()` returns true only for an http or https URL with a non-empty host.

**Language detection and logging keys**

- A module constant defines the minimum text length for language detection; shorter text is not classified and falls back to the language hint (Explicit in code — `scripts/rag/ingestion/crawler_utils.py`).
- Module constants define the structured log keys (url, doc_id, chunk_id, source_type, stage_name) used to trace the RAG lifecycle.

The module is a library module: it attaches no log handler, and the caller controls log routing.

---

## Keywords

shared-utilities
unicode-normalization
cosine-similarity
prompt-injection
rag
