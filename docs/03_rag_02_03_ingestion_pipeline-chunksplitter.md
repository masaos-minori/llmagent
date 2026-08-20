---
title: "ChunkSplitter Detail (Part 1)"
category: rag
tags:
  - chunk-splitter
  - chunking-strategies
  - sudachi
  - markdown-heading
  - crawler
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
source:
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class Overview

`ChunkSplitter` splits `rag-src/*.json` files into chunks based on language and content type, saving them to `rag-src/chunk/`. It is idempotent: if a `{stem}-0000.json` sentinel exists, processing is skipped (can be overwritten with `--force`).

**Module-level Constants**

This module defines the following constants. See source code for details. Note that the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` is unconfirmed (Needs Confirmation).

**Typed dict**

| TypedDict | Purpose |
|---|---|
| `CrawlFilePayload` | Typed dictionary for crawl output JSON files (url, title, lang, content, code_blocks are required; etag, last_modified are optional via NotRequired) |
| `ChunkOutputPayload` | Typed dictionary for chunk output JSON files (schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, content are required; normalized_content is optional via NotRequired) |
| `ChunkMetadata` | Optional metadata dictionary to be expanded with ** in the output payload (total=False). All fields including url, title, lang, etag, last_modified, source_file, and chunking_strategy are optional. |

> Evidence: Explicit in code — `CrawlFilePayload` and `ChunkOutputPayload` are declared as types in `chunk_splitter.py`, but they are not used as type annotations in the actual implementation within the same file (actual input/output is handled via `ChunkJsonRaw` (`pipeline_utils.py`) or `dict[str, object]`).

**Inheritance**

`ChunkSplitter` uses multiple inheritance from both `ChunkEnglishMixin` and `ChunkJapaneseMixin`.
Method Resolution Order (MRO): `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`.

**Public Methods**

This module provides the following public methods. See source code for details.

### 3.1.1 Markdown Heading Chunking Configuration

| Parameter | Default | Description |
|---|---|---|
| `md_index_enable` | False | Enables heuristic Markdown detection for non-.md files |
| `md_snippet_max_chars` | 600 | Maximum characters per single Markdown heading section before falling back to sentence-based chunking |

### 3.1.2 Chunking Parameters (Shared with crawler)

| Parameter | Default | Description |
|---|---|---|
| `min_chunk` | 40 | Minimum number of characters per chunk. Chunks smaller than this are discarded as noise. |
| `max_chunk` | 500 | Maximum number of characters per chunk. Text exceeding this limit will be split. |
| `chunk_overlap` | 50 | Sliding window chunk overlap (in characters). Adds this many characters from the end of the previous chunk to the beginning of the next; 0 disables it. |
| `en_stopwords` | — | English stopwords to exclude from chunking (defined in `config/chunk_splitter.toml`. Corrected from old docs mentioning `rag_pipeline.toml` which does not exist). |
| `ja_stop_pos` | — | Sudachi part-of-speech categories treated as stopwords in Japanese. Default value: `["Particle", "Auxiliary", "Symbol", "Whitespace", "Interjection", "Conjunction"]` (defined in `config/chunk_splitter.toml`). |

> Evidence: Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::__init__` uses `ConfigLoader().load("chunk_splitter.toml")`, and `en_stopwords`/`ja_stop_pos` are defined in `config/chunk_splitter.toml`. The file `config/rag_pipeline.toml` does not exist in this repository.

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag

# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3a. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class Overview

`ChunkSplitter` splits `rag-src/*.json` files into chunks based on language and content type, saving them to `rag-src/chunk/`. It is idempotent: if a `{stem}-0000.json` sentinel exists, processing is skipped (can be overwritten with `--force`).

**Module-level Constants**

This module defines the following constants. See source code for details. Note that the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` is unconfirmed (Needs Confirmation).

**Typed dict**

| TypedDict | Purpose |
|---|---|
| `CrawlFilePayload` | Typed dictionary for crawl output JSON files (url, title, lang, content, code_blocks are required; etag, last_modified are optional via NotRequired) |
| `ChunkOutputPayload` | Typed dictionary for chunk output JSON files (schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, content are required; normalized_content is optional via NotRequired) |
| `ChunkMetadata` | Optional metadata dictionary to be expanded with ** in the output payload (total=False). All fields including url, title, lang, etag, last_modified, source_file, and chunking_strategy are optional. |

> Evidence: Explicit in code — `CrawlFilePayload` and `ChunkOutputPayload` are declared as types in `chunk_splitter.py`, but they are not used as type annotations in the actual implementation within the same file (actual input/output is handled via `ChunkJsonRaw` (`pipeline_utils.py`) or `dict[str, object]`).

**Inheritance**

`ChunkSplitter` uses multiple inheritance from both `ChunkEnglishMixin` and `ChunkJapaneseMixin`.
Method Resolution Order (MRO): `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`.

**Public Methods**

This module provides the following public methods. See source code for details.

### 3.1.1 Markdown Heading Chunking Configuration

| Parameter | Default | Description |
|---|---|---|
| `md_index_enable` | False | Enables heuristic Markdown detection for non-.md files |
| `md_snippet_max_chars` | 600 | Maximum characters per single Markdown heading section before falling back to sentence-based chunking |

### 3.1.2 Chunking Parameters (Shared with crawler)

| Parameter | Default | Description |
|---|---|---|
| `min_chunk` | 40 | Minimum number of characters per chunk. Chunks smaller than this are discarded as noise. |
| `max_chunk` | 500 | Maximum number of characters per chunk. Text exceeding this limit will be split. |
| `chunk_overlap` | 50 | Sliding window chunk overlap (in characters). Adds this many characters from the end of the previous chunk to the beginning of the next; 0 disables it. |
| `en_stopwords` | — | English stopwords to exclude from chunking (defined in `config/chunk_splitter.toml`. Corrected from old docs mentioning `rag_pipeline.toml` which does not exist). |
| `ja_stop_pos` | — | Sudachi part-of-speech categories treated as stopwords in Japanese. Default value: `["Particle", "Auxiliary", "Symbol", "Whitespace", "Interjection", "Conjunction"]` (defined in `config/chunk_splitter.toml`). |

> Evidence: Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::__init__` uses `ConfigLoader().load("chunk_splitter.toml")`, and `en_stopwords`/`ja_stop_pos` are defined in `config/chunk_splitter.toml`. The file `config/rag_pipeline.toml` does not exist in this repository.

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag

# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3b. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1.3 Markdown Source Detection Behavior

URLs ending in `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`. For other files, heuristic detection (two or more heading lines in content) is used only if `md_index_enable=true`.

### 3.1.4 Markdown Heading Chunking Behavior

Text is split by Markdown headings (# through ######). Sections exceeding `md_snippet_max_chars` characters are further split using sentence-based chunking.

> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.2 Splitting Strategies

| Content Type | Strategy |
|---|---|
| Japanese text | Morphological analysis via Sudachi SplitMode.C; pair of `(original sentence, space-joined normalized form)` |
| English text | Sentence boundary splitting via regex (`(?<=[.!?])\s+`); short paragraphs are joined, and chunks smaller than `min_chunk` after stopword removal are discarded |
| `.md`/`.markdown`/`.mdx` URLs | Heading boundary splitting (`#`/`##`/`###`); always applied regardless of `md_index_enable` |
| Non-.md content with ≥2 heading lines | Heading boundary splitting; applied only if `md_index_enable=true` |
| Code blocks | Empty line splitting (language independent); excluded from stopword removal or morphological analysis |

- Japanese chunks: `content` = original text, `normalized_content` = normalized form via Sudachi
- English/Code chunks: `normalized_content = null`
- `chunk_type`: `"text"` or `"code"`
- `chunking_strategy`: `"text"` or `"heading"`

> Evidence: Explicit in code — Heading chunking (`chunking_strategy="heading"`) always sets `normalized_content` to `null` regardless of `lang`. This means Markdown sources in Japanese prioritize heading chunking, skipping Sudachi normalization. FTS5 uses `COALESCE(normalized_content, content)` to index the original text (`content`) directly.

### 3.3 CLI Arguments

| Argument | Description | Default |
|---|---|---|
| `--file PATH` | Processes only a single file (path is relative to `rag_src_dir`) | All unprocessed `.json` in `rag-src/` |
| `--force` | Regenerates chunks ignoring the sentinel check | false |

### 3.4 Output JSON Format

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag",
  "last_modified": "optional-http-date"
}
```

- `chunk_type`: `text` / `code`
- `chunking_strategy`: `text` / `heading`
- `normalized_content`: Japanese only (Sudachi normalization), null for English/code
- `source_file`: Filename of the crawler output without the `.json` extension

### 3.5 Error Handling

| Case | Action |
|---|---|
| Sudachi tokenization error | `_normalize_ja_sentence()` raises a `TokenizationError` (subclass of `RagLayerError`/`RuntimeError`). There is no try/except at the individual chunk level; instead, errors propagate to the `except (OSError, RuntimeError, ValueError)` block in the file-level loop of `process_all()`. As a result, processing fails for the **entire file**, not just the individual chunk. |
| File-level failure | Logs an `ERROR` (with traceback, via `logger.exception`); continues to the next file |
| Existing chunks (`{stem}-0000.json`) | Skipped unless `--force` is used |

### 3.6 Logging

- **File:** `/opt/llm/logs/chunk.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing |
|---|---|
| `INFO` | Processed files, generated chunks, skipped files (with URL) |
| `WARNING` | Sudachi errors |
| `ERROR` | File read errors, file-level failures (with traceback) |

### 3.7 Configuration

See [03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag
