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
  - rag_05_1-configuration-reference.md
source:
  - rag_02_01_ingestion_pipeline-overview.md
---

# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)

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

This module exposes the following functions. Please refer to the source code for details.

**Constants:**

This module defines the following constants. Please refer to the source code for details. Specifically, the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` is unconfirmed (Needs Confirmation).

**Prompt Injection Patterns:**

Please refer to the source code for details.

**Structured Log Keys (Tracing the RAG Lifecycle):**

Please refer to the source code for details.

**Usage:**

Please refer to the source code for details.

---

## Related Documents

- `rag_00_document-guide.md`
- `rag_01_system_overview.md`
- `rag_02_01_ingestion_pipeline-overview.md`
- `rag_02_02_ingestion_pipeline-crawler.md`
- `rag_02_03_ingestion_pipeline-chunksplitter.md`
- `rag_02_04_ingestion_pipeline-ingester.md`
- `rag_02_07_ingestion_pipeline-utils.md`
- `rag_02_08_ingestion_pipeline-shared.md`
- `rag_05_1-configuration-reference.md`

## Keywords

shared-utilities
unicode-normalization
cosine-similarity
prompt-injection
rag
