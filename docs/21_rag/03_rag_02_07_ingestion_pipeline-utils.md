---
title: "Ingestion Pipeline Utilities"
area: rag
tags:
  - crawler-utils
  - chunk-english-mixin
  - chunk-japanese-mixin
  - chunk-utils
  - pipeline-utils
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_08_ingestion_pipeline-shared.md
  - 03_rag_02_09_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 Module Overview

`crawler_utils.py` — A collection of pure function utilities for `WebCrawler`: URL helpers, content extraction, language detection, and parsing target URLs. Extracted to keep the `WebCrawler` class under 400 lines.

For exhaustive signature and constant detail, see `scripts/rag/ingestion/crawler_utils.py` (crawler utils), `scripts/rag/ingestion/chunk_english.py` (chunk English mixin), and `scripts/rag/ingestion/chunk_utils.py` (chunk utils).

**Implementation Notes:**
- `parse_targets_file` uses module functions for URL validation. Unlike `rag.utils.validate_url` (which is limited to http/https), it allows the `file://` scheme because it is used for the `--targets-file` crawl path (per `crawler_utils.py` docstring). Conversely, `parse_target_urls` (the one that parses `target_urls` within `ingester.toml`) uses `rag.utils.validate_url` and therefore does NOT accept `file://`. While both functions appear to perform the same role of parsing a list of `(url, lang)`, they differ in allowed URL schemes based on their intended input source (TOML `--targets-file` vs config list). (Explicit in code)

---

## 6. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 6.1 Module Overview

`chunk_english.py` — `ChunkEnglishMixin`: Paragraph/sentence-based chunking for English text involving stopword filtering and sentence boundary splitting. Mixed into `ChunkSplitter` via multiple inheritance.

---

## 7. Chunk Utils (`scripts/rag/ingestion/chunk_utils.py`)

### 7.1 Module Overview

`chunk_utils.py` — Buffer helpers imported individually by `ChunkEnglishMixin` and `ChunkSplitter`. Provides management of trailing duplicate buffers and accumulation of items subject to min/max chunk size constraints. **`ChunkJapaneseMixin` does NOT import this module and uses its own implementation instead** (designed as a shared helper but currently unshared — refactoring incomplete).

For exhaustive signature and constant detail, see `scripts/rag/ingestion/crawler_utils.py` (crawler utils), `scripts/rag/ingestion/chunk_english.py` (chunk English mixin), and `scripts/rag/ingestion/chunk_utils.py` (chunk utils).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_02_09_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

crawler-utils
chunk-english-mixin
chunk-japanese-mixin
chunk-utils
pipeline-utils
rag
