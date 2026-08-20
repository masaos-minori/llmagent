---
title: "Shared Utilities Detail"
category: rag
tags:
  - shared-utilities
  - unicode-normalization
  - cosine-similarity
  - prompt-injection
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_08_ingestion_pipeline-shared.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

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

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

shared-utilities
unicode-normalization
cosine-similarity
prompt-injection
rag
