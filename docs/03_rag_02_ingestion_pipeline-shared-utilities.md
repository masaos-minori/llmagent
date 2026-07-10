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
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-ingester.md
  - 03_rag_02_ingestion_pipeline-utils.md
  - 03_rag_02_ingestion_pipeline-shared.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_02_ingestion_pipeline.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

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

| Function / Constant | Signature | Returns | Description |
|---|---|---|---|
| `normalize_unicode` | `(text: str) -> str` | `str` | NFKC normalization; converts full-width alphanumerics and variant chars |
| `floats_to_blob` | `(values: list[float]) -> bytes` | `bytes` | Little-endian float32 BLOB; sqlite-vec `MATCH` operator format. Raises TypeError/ValueError on invalid input |
| `validate_url` | `(url: str) -> bool` | `bool` | `True` if `http`/`https` scheme with non-empty netloc |
| `cosine_sim` | `(a: list[float], b: list[float]) -> float` | `float` | Cosine similarity; returns 0.0 when either vector has zero magnitude. Used by SemanticCache |
| `sanitize_document` | `(text: str) -> str` | `str` | Remove prompt injection patterns (e.g., "ignore instructions", "[SYSTEM OVERRIDE]"); replaces matches with `[REMOVED]` |
| `sanitize_document_full` | `(text: str) -> SanitizeResult` | `SanitizeResult` | Same as sanitize_document but returns audit trail (detected patterns, was_sanitized flag); returns SanitizeResult dataclass with `was_sanitized: bool`, `patterns: list[str]`, `sanitized_text: str` |

**Constants:**

| Constant | Value | Description |
|---|---|---|
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` | Minimum text length for language detection; pages shorter than this use hint language; also used by `detect_lang()` in crawler_utils |
| `LOG_KEY_URL` | `"url"` | Structured log field key for URL |
| `LOG_KEY_DOC_ID` | `"doc_id"` | Structured log field key for document ID |
| `LOG_KEY_CHUNK_ID` | `"chunk_id"` | Structured log field key for chunk ID |
| `LOG_KEY_SOURCE_TYPE` | `"source_type"` | Structured log field key for source type (http/file) |
| `LOG_KEY_STAGE_NAME` | `"stage_name"` | Structured log field key for stage name |

**Prompt injection patterns:**

| Pattern | Regex | Description |
|---|---|---|
| Ignore instructions | `(?i)(ignore\s+(?:(?:all\|previous)\s+)*instructions?)` | Catch "ignore all instructions", "ignore previous instructions" etc. |
| System prefix | `(?i)(system\s*:\s*)` | Catch "system:" prefix |
| SYSTEM OVERRIDE | `(?i)\[SYSTEM\s*OVERRIDE\]` | Catch "[SYSTEM OVERRIDE]" |
| Disregard instructions | `(?i)(disregard\s+(?:(?:all\|prior\|previous)\s+)*instructions?)` | Catch "disregard all instructions" etc. |
| New instructions | `(?i)(new\s+instructions?:)` | Catch "new instructions:" etc. |

**Structured log keys (RAG lifecycle tracing):**

| Key | Value | Used by |
|---|---|---|
| `url` | URL string | crawler, ingester |
| `doc_id` | INTEGER document ID | ingester |
| `chunk_id` | INTEGER chunk ID | ingester (via chunks_vec insert) |
| `source_type` | `"http"` / `"file"` | crawler, ingester |
| `stage_name` | Script name ("ingester") | ingester |

**Used by:**

| Script | Functions used |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/pipeline.py` | `sanitize_document`, `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-ingester.md`
- `03_rag_02_ingestion_pipeline-utils.md`
- `03_rag_02_ingestion_pipeline-shared.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

shared-utilities
unicode-normalization
cosine-similarity
prompt-injection
rag
