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
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_08_ingestion_pipeline-shared.md
  - rag_02_09_ingestion_pipeline-shared-utilities.md
  - rag_05_01-configuration-reference.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)

---

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 Module Overview

`crawler_utils.py` — A collection of pure function utilities for `WebCrawler`: URL helpers, content extraction, language detection, and parsing target URLs.

For exhaustive signature and constant detail, see `crawler_utils.py`, `chunk_english.py`, and `chunk_utils.py` under `scripts/rag/ingestion/`.

**Implementation Notes:**
- `parse_targets_file` uses module functions for URL validation. Unlike `rag.utils.validate_url` (which is limited to http/https), it allows the `file://` scheme because it is used for the `--targets-file` crawl path (per `crawler_utils.py` docstring). Conversely, `parse_target_urls` (the one that parses `target_urls` within `ingester.toml`) uses `rag.utils.validate_url` and therefore does NOT accept `file://`. While both functions appear to perform the same role of parsing a list of `(url, lang)`, they differ in allowed URL schemes based on their intended input source (TOML `--targets-file` vs config list).

---

## 6. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 6.1 Module Overview

`chunk_english.py` — `ChunkEnglishMixin`: Paragraph/sentence-based chunking for English text involving stopword filtering and sentence boundary splitting. Mixed into `ChunkSplitter` via multiple inheritance.

---

## 7. Chunk Utils (`scripts/rag/ingestion/chunk_utils.py`)

### 7.1 Module Overview

`chunk_utils.py` — Shared buffer helpers imported individually by `ChunkEnglishMixin`, `ChunkJapaneseMixin`, and `ChunkSplitter`. Its two responsibilities are trailing duplicate-buffer management (`start_next_buf`) and the min/max/overlap accumulation loop (`accumulate_items`).

`accumulate_items` owns the single greedy-accumulation loop for one chunking path. The three chunkers previously encoded the same min/max/overlap intent with divergent oversized-item, short-tail, and end-of-stream rules; the collaborator keeps one loop and takes each path's divergent decisions as explicit strategy callbacks (fits test, oversized-item segmentation and placement, emit threshold, overlap, short-tail handling, end-of-stream finalize), so no path re-implements the loop. `T` is the element type for the path — a plain `str` (code/English) or an `(original, normalized)` pair (Japanese), where an empty normalized value is preserved and surfaced so downstream `COALESCE` falls back to the original text.

The three chunking paths route through it while keeping their language-specific splitting: `merge_text_items` (code), `_merge_paragraphs_en` (English), and `_merge_ja_sentence_pairs` (Japanese). Each path supplies its own oversized-item, short-tail, separator, and end-of-stream rules as strategy callbacks; oversized items are segmented by the path's own splitter — character-level `_split_overlong` for the code and Japanese paths, sentence-level `_split_sentences_en` for English — so the shared loop never re-implements either the splitting or the accumulation.

---

## Keywords

- crawler-utils
- chunk-english-mixin
- chunk-japanese-mixin
- chunk-utils
- pipeline-utils
- rag
