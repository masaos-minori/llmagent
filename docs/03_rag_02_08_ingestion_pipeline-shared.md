---
title: "Chunk Japanese Mixin, Pipeline Utils, and FTS5 Notes"
area: rag
tags:
  - chunk-japanese
  - pipeline-utils
  - fts5
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_09_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 8. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 8.1 Module Overview

`chunk_japanese.py` — `ChunkJapaneseMixin`: Morphological analysis-based chunking for Japanese text using Sudachi SplitMode.C. Includes NFKC normalization, sentence boundary splitting, and buffer-based accumulation with overlap. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkJapaneseMixin`**

---

## 9. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 9.1 Module Overview

`pipeline_utils.py` — Shared I/O utilities for the RAG ingestion pipeline: reading chunk JSONs with validation, collecting source files, and checking processed sentinels. Provides the `ChunkJsonRaw` dataclass for raw chunk/crawl JSON payload fields.

**Module-level Constants**

| Constant | Value | Description |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | Pipeline logging instance |

**TypedDict**

| TypedDict | Purpose |
|---|---|
| `ChunkJsonRaw` | Raw chunk JSON payload fields; Required: `url`, `content`, `fetched_at`; Optional: `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `chunking_strategy`, `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `artifact_type`, `schema_version`, `created_by` |

**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `read_json_file` | `(path: Path) -> ChunkDocument` | **Legacy fallback reader, not called by any current pipeline path** (confirmed via repository-wide search) — see "Historical: `read_json_file()` Legacy Fallback Reader" below. Current production readers are `read_crawl_json()` / `read_chunk_json()`, documented canonically in [03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md). |
| `collect_source_files` | `(rag_src_dir: Path, target: Path \| None = None) $\rightarrow$ tuple[list[Path], list[SkipInfo]]` | Returns (target files, skip information); if `target` is specified and exists, returns `[target]`; if `target` does not exist, returns an empty list with `SkipInfo`; otherwise, globs `*.json` from `rag_src_dir` |
| `is_already_processed` | `(sentinel_path: Path, force: bool) $\rightarrow$ bool` | Returns `True` if the sentinel file exists and `force=False` (skip signal for `chunk_splitter`) |

**Historical: `read_json_file()` Legacy Fallback Reader (superseded)**

The following field-mapping table describes `read_json_file()`'s lenient fallback
behavior, retained for historical reference only. This function is **not** used by any
current pipeline code path (verified: no caller exists outside its own definition in
`pipeline_utils.py`) — it predates the strict-reader migration
(`read_crawl_json()`/`read_chunk_json()`, both raising `ChunkFormatError` on
missing/invalid fields instead of silently substituting a default). It remains in
source only because removing it is out of scope for the strict-reader documentation
alignment (see this document's `Source plan`). Do not rely on this fallback behavior
for any new artifact producer — use the canonical readers documented in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md)
instead.

| JSON Field | ChunkDocument Field | Fallback |
|---|---|---|
| `url` | `url` | (Required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (Required, no fallback) |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |

---

## 10. Shared Utilities (`scripts/rag/utils.py`)

Details $\rightarrow$ [03_rag_02_09_ingestion_pipeline-shared-utilities.md](03_rag_02_09_ingestion_pipeline-shared-utilities.md)

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

**Used by:**

| Script | Functions Used |
|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/stages/augment.py` | `sanitize_document` |
| `scripts/rag/repository.py` | `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## 11. Note on FTS5 Implementation

### FTS5 / LLM Content Separation

See [ADR-009](adr/ADR-009-rag-ft5-text-separation.md) for rationale, alternatives, tradeoffs, and invariants.

Japanese chunks store two versions:
- `chunks.content` — Original text (passed as context to the LLM)
- `chunks.normalized_content` — Space-joined result of Sudachi's `normalized_form()` (for FTS5 indexing)

`chunks_ai` / `chunks_au` / `chunks_ad` triggers write `COALESCE(normalized_content, content)` to `chunks_fts`. Since English and code chunks have `normalized_content = NULL`, FTS5 uses `content` directly.

### Tokenization of FTS5 Queries

Japanese queries use the Sudachi tokenizer to extract only nouns, verbs, and adjectives (excluding particles and auxiliary verbs) using `normalized_form()`.
English queries use regex tokenization `[a-zA-Z0-9]+`. The Sudachi tokenizer is lazily initialized and has no side effects at import time.

### FTS5 Query Token Limit

Token limit for FTS5 queries: 20 (defined by `_MAX_FTS_TOKENS` in `repository.py`).
Tokens exceeding this limit are silently truncated to prevent query explosion. Double quotes (FTS5 metacharacters) and whitespace are removed from each token, and empty tokens are discarded. If no valid tokens remain, `'""'` (an empty FTS5 query) is returned.

**[Needs Confirmation]:** There is currently no documented rationale within the project for this specific value (20) based on measurement or load testing. As it appears to be a heuristic setting, it should be re-validated during performance tuning.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_09_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

chunk-japanese
pipeline-utils
fts5
rag
