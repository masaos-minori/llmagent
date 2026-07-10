---
title: "Chunk Japanese Mixin, Pipeline Utils, and FTS5 Notes"
category: rag
tags:
  - chunk-japanese
  - pipeline-utils
  - fts5
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-ingester.md
  - 03_rag_02_ingestion_pipeline-utils.md
  - 03_rag_02_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_ingestion_pipeline-overview.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 8. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 8.1 Module overview

`chunk_japanese.py` — `ChunkJapaneseMixin`: morphological-analysis-based chunking for Japanese text using Sudachi SplitMode.C. Includes NFKC normalization, clause boundary splitting, and buffer-based accumulation with overlap. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkJapaneseMixin`**

---

## 9. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 9.1 Module overview

`pipeline_utils.py` — Shared I/O utilities for the RAG ingestion pipeline: chunk JSON reading with validation, source file collection, and processing sentinel checks. Provides `ChunkJsonRaw` dataclass for raw chunk/crawl JSON payload fields.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | Pipeline logging instance |

**TypedDict**

| TypedDict | Purpose |
|---|---|
| `ChunkJsonRaw` | Raw chunk JSON payload fields; required: `url`, `content`; optional: `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`, `chunking_strategy`, `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `artifact_type`, `schema_version`, `created_by` |

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `read_json_file` | `(path: Path) -> ChunkDocument` | Read and parse JSON file into ChunkDocument; raises ChunkFormatError on failure |
| `collect_source_files` | `(rag_src_dir: Path, target: Path \| None = None) -> tuple[list[Path], list[SkipInfo]]` | Return (files_to_process, skipped); if target is given and exists, returns [target]; if target doesn't exist returns empty list with SkipInfo; otherwise glob *.json from rag_src_dir |
| `is_already_processed` | `(sentinel_path: Path, force: bool) -> bool` | True when sentinel file exists and force=False (skip signal for chunk_splitter) |

**read_json_file field mapping**

| JSON field | ChunkDocument field | Fallback |
|---|---|---|
| `url` | `url` | (required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (required, no fallback) |
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

For full details → [03_rag_02_ingestion_pipeline-shared-utilities.md](03_rag_02_ingestion_pipeline-shared-utilities.md)

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

| Script | Functions used |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/pipeline.py` | `sanitize_document`, `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## 11. FTS5 Implementation Notes

### FTS5 / LLM content separation

Japanese chunks store two versions:
- `chunks.content` — original text (passed to LLM as context)
- `chunks.normalized_content` — Sudachi `normalized_form()` space-joined (used for FTS5 indexing)

The `chunks_ai` / `chunks_au` / `chunks_ad` triggers write `COALESCE(normalized_content, content)`
to `chunks_fts`. English and code chunks have `normalized_content = NULL`, so FTS5 uses `content` directly.

### FTS5 query tokenization

Japanese queries use Sudachi tokenizer to extract `normalized_form()` for nouns, verbs, and adjectives only (excludes particles, auxiliaries).
English queries use regex `[a-zA-Z0-9]+` tokenization. Sudachi tokenizer is lazily initialized with zero import-time side effects.

### FTS5 query token limit

Maximum tokens in an FTS5 query: 20 (`repository.py:29`).
Excess tokens are silently truncated to prevent query explosion. Double-quotes (FTS5 metachar)
and whitespace are stripped from each token; empty tokens are dropped. If no valid tokens remain,
returns `'""'` (empty FTS5 query).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-ingester.md`
- `03_rag_02_ingestion_pipeline-utils.md`
- `03_rag_02_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

chunk-japanese
pipeline-utils
fts5
rag
