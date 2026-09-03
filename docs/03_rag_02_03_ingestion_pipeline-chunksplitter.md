---
title: "ChunkSplitter Detail (Part 1)"
area: rag
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
| `ChunkMetadata` | Optional metadata dictionary to be expanded with ** in the output payload (total=False). Fields: url, title, lang, fetched_at (str, mandatory), etag, last_modified, source_file, chunking_strategy. |

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
| `ChunkMetadata` | Optional metadata dictionary to be expanded with ** in the output payload (total=False). Fields: url, title, lang, fetched_at (str, mandatory), etag, last_modified, source_file, chunking_strategy. |

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

### 3.4a Canonical Artifact-Field Contract

This is the canonical field-contract table for both artifact types in the RAG
ingestion pipeline — other `docs/03_rag_*.md` documents link here instead of
duplicating this table. Classification is derived directly from the validator each
field is checked against in `scripts/rag/ingestion/pipeline_utils.py`
(`read_crawl_json()` / `read_chunk_json()`); both raise `ChunkFormatError` (see
[03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md))
on a missing required key or an invalid field type.

**Missing key vs. `null` vs. empty string**: a key absent from the JSON payload is
always rejected by an exact-key-set check, regardless of classification below —
`null`/empty-string tolerance applies only once the key is present. `null` is accepted
only for `Nullable` fields; empty string is accepted only for `Conditional` fields;
`Required` fields accept neither.

#### Crawl artifacts (8 required keys) — reader: `read_crawl_json()`

| Field | Classification | Validator | Notes |
|---|---|---|---|
| `url` | Required | `_validate_str` | non-empty string |
| `content` | Conditional | `_validate_str_or_empty` | empty string allowed only when `code_blocks` is non-empty (cross-field rule) |
| `title` | Nullable | `_validate_nullable_str` | defaults to `""` when `null` |
| `lang` | Required | `_validate_str` | any non-empty string accepted; the `en`/`ja` value set (`LanguageCode`) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended) |
| `code_blocks` | Required | `_validate_list_of_str` | list of `str`; may be an empty list |
| `etag` | Nullable | `_validate_nullable_str` | optional upstream metadata, not always available at crawl time |
| `last_modified` | Nullable | `_validate_nullable_str` | optional upstream metadata, not always available at crawl time |
| `fetched_at` | Required | `_validate_str` | non-empty string |

Crawl artifacts do not carry `normalized_content` / `chunk_index` / `source_file` /
`chunk_type` / `chunking_strategy` as input keys — `read_crawl_json()` sets these
internally rather than reading them: `chunking_strategy="text"`,
`normalized_content=None`, `chunk_index=0`, `source_file=""`, `chunk_type=""` (these
crawl-stage values do not exist yet).

#### Chunk artifacts (13 required keys) — reader: `read_chunk_json()`

| Field | Classification | Validator | Notes |
|---|---|---|---|
| `url` | Required | `_validate_str` | non-empty string |
| `content` | Required | `_validate_str` | non-empty string — no cross-field exception here, unlike crawl artifacts |
| `title` | Nullable | `_validate_nullable_str` | defaults to `""` when `null` |
| `lang` | Required | `_validate_str` | same non-enforcement note as crawl artifacts |
| `code_blocks` | Required | `_validate_list_of_str` | list of `str`; may be an empty list |
| `etag` | Nullable | `_validate_nullable_str` | optional upstream metadata |
| `last_modified` | Nullable | `_validate_nullable_str` | optional upstream metadata |
| `normalized_content` | Nullable | `_validate_nullable_str` | Japanese-only Sudachi normalization; `null` for English/code chunks |
| `chunk_index` | Required | `_validate_int_non_negative` | non-negative int; `bool` is explicitly rejected before the `int` check |
| `source_file` | Conditional | `_validate_str_or_empty` | empty string allowed unconditionally; otherwise the crawler output filename stem without `.json` |
| `chunk_type` | Conditional | `_validate_str_or_empty` | `"text"` or `"code"` by convention; empty string allowed unconditionally; no enum enforced in code |
| `chunking_strategy` | Required | `_validate_str` | `"text"` or `"heading"` by convention; no enum enforced in code (Needs confirmation: whether a closed value set is intended) |
| `fetched_at` | Required | `_validate_str` | non-empty string |

`read_chunk_json()` additionally rejects any key beyond these 13, except
`schema_version`, `artifact_type`, and `created_by`, which are accepted but not
validated or mapped onto `ChunkDocument`'s own fields.

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

See [03_rag_05_1-configuration-reference.md section 1.1](03_rag_05_1-configuration-reference.md).

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
