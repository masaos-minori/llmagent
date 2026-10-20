---
title: "ChunkSplitter Detail"
area: rag
tags:
  - chunk-splitter
  - chunking-strategies
  - sudachi
  - markdown-heading
  - crawler
  - rag
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_05_01-configuration-reference.md
  - rag_05_04-error-handling-reference.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)


## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class Overview

`ChunkSplitter` splits `rag-src/*.json` files into chunks based on language and content type, saving them to `rag-src/chunk/`. It is idempotent: if a `{stem}-0000.json` sentinel exists, processing is skipped (can be overwritten with `--force`). Language-specific splitting is composed from `ChunkEnglishMixin` and `ChunkJapaneseMixin`. The JSON payload shapes are defined by `CrawlJsonPayload`, `ChunkJsonRaw`, and `ChunkMetadata` in `scripts/rag/ingestion/pipeline_utils.py`.

### 3.1.1 Markdown Heading Chunking Configuration

Current values are owned by `config/chunk_splitter.toml`. `md_index_enable` enables heuristic Markdown detection for non-`.md` sources, and `md_snippet_max_chars` bounds one heading section before it falls back to sentence-based chunking.

### 3.1.2 Chunking Parameters (Shared with crawler)

`min_chunk` and `max_chunk` bound chunk size in characters: chunks smaller than `min_chunk` are discarded as noise, and text exceeding `max_chunk` is split. `chunk_overlap` prepends that many trailing characters of the previous chunk to the next (zero disables it). `en_stopwords` and `ja_stop_pos` (Sudachi part-of-speech categories) define the stopwords excluded from chunking; see [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md).

### 3.1.3 Markdown Source Detection Behavior

URLs ending in `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`, and there is no configuration or per-source override for this. This applies to remote URLs and to local `file://` sources alike (the suffix check ignores the scheme prefix). For other files, heuristic detection (a minimum number of heading lines in the content) is used only if `md_index_enable=true`. (Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::_is_markdown_source`)

### 3.1.4 Markdown Heading Chunking Behavior

Text is split by Markdown headings (# through ######) in one pass over the whole text. Each heading-delimited section then takes exactly one of three paths:

- **Fits** (`len(section) <= md_snippet_max_chars` and at least `min_chunk` characters): the section becomes one chunk.
- **Oversized** (`len(section) > md_snippet_max_chars`): the section alone is split by sentence boundaries. The fallback is decided per section, not for the document as a whole, and runs after heading splitting; the two strategies are never applied in parallel.
- **Undersized** (fits but is smaller than `min_chunk`): the section is silently dropped, with no error or warning.

**Metadata:** Every chunk returned by this path is tagged with the `"text"` chunk-type marker, so no metadata field distinguishes a whole-section chunk from a fallback-split fragment. `chunking_strategy` is `"heading"` for the whole source regardless of which sections fell back.

**Japanese content:** Even when `lang` is `"ja"`, Sudachi morphological analysis is not applied on this path, including the sentence-split fallback portion, and `normalized_content` is not generated (it is stored as null). Japanese text routed through heading chunking therefore bypasses Sudachi normalization. FTS5 indexes `COALESCE(normalized_content, content)`, so the original `content` is indexed directly.

### 3.2 Splitting Strategies

| Content Type | Strategy |
|---|---|
| Japanese text | Morphological analysis via Sudachi SplitMode.C; pair of `(original sentence, space-joined normalized form)` |
| English text | Sentence boundary splitting via regex (`(?<=[.!?])\s+`); short paragraphs are joined, and chunks smaller than `min_chunk` after stopword removal are discarded |
| `.md`/`.markdown`/`.mdx` URLs | Heading boundary splitting (`#` through `######`); always applied regardless of `md_index_enable` |
| Non-.md content with ≥2 heading lines | Heading boundary splitting; applied only if `md_index_enable=true` |
| Code blocks | Empty line splitting (language independent); excluded from stopword removal or morphological analysis |

- Japanese chunks: `content` = original text, `normalized_content` = normalized form via Sudachi
- English/Code chunks: `normalized_content = null`
- `chunk_type`: `"text"` or `"code"`
- `chunking_strategy`: `"text"` or `"heading"`

### 3.3 CLI Arguments

Run `uv run python scripts/rag/ingestion/chunk_splitter.py --help` for the current
argument list.

### 3.4 Output JSON Format

The exact output JSON shape is `ChunkJsonRaw` in `scripts/rag/ingestion/pipeline_utils.py`; the field contract is in 3.4a. `source_file` holds the filename of the crawler output, including the `.json` extension.

### 3.4a Canonical Artifact-Field Contract

This is the canonical field-contract table for both artifact types in the RAG
ingestion pipeline — other `docs/rag_*.md` documents link here instead of
duplicating this table. Classification is derived directly from the validator each
field is checked against in `scripts/rag/ingestion/pipeline_utils.py`
(`read_crawl_json()` / `read_chunk_json()`); both raise `ChunkFormatError` (see
[rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md))
on a missing required key or an invalid field type.

**Missing key vs. `null` vs. empty string**: a key absent from the JSON payload is
always rejected by an exact-key-set check, regardless of classification below —
`null`/empty-string tolerance applies only once the key is present. `null` is accepted
only for `Nullable` fields; empty string is accepted only for `Conditional` fields;
`Required` fields accept neither.

#### Crawl artifacts (8 required keys) — reader: `read_crawl_json()`

See `read_crawl_json()` and its `_validate_*` helper functions in
`scripts/rag/ingestion/pipeline_utils.py` for the exact per-field
classification/validator mapping.

Crawl artifacts do not carry `normalized_content` / `chunk_index` / `source_file` /
`chunk_type` / `chunking_strategy` as input keys — `read_crawl_json()` sets these
internally rather than reading them: `chunking_strategy="text"`,
`normalized_content=None`, `chunk_index=0`, `source_file=""`, `chunk_type=""` (these
crawl-stage values do not exist yet).

#### Chunk artifacts (13 required keys) — reader: `read_chunk_json()`

See `read_chunk_json()` and its `_validate_*` helper functions in
`scripts/rag/ingestion/pipeline_utils.py` for the exact per-field
classification/validator mapping.

`read_chunk_json()` additionally rejects any key beyond these 13, except
`schema_version`, `artifact_type`, and `created_by`, which are accepted but not
validated or mapped onto `ChunkDocument`'s own fields.

#### Cross-Field Validation Rules

There is exactly one cross-field validation rule among the crawl/chunk artifact fields documented above. It applies only to crawl artifacts:

- **Rule**: For crawl artifacts, `content` may be an empty string only when `code_blocks` is non-empty. If both are empty, the payload is rejected with `ChunkFormatError`.
- **Rationale**: Traced to `CrawlPersister.save()`'s `.py`-file handling (`crawl_persister.py`). When processing a `.py` file, the crawler stores the source code in `code_blocks=[content]` with `content=""`, allowing the code chunker to apply. The cross-field rule permits this legitimate empty-content case while rejecting a genuinely broken/incomplete crawl result (both fields empty).
- **Chunk artifacts**: No equivalent exception — `content` is required and must be non-empty for chunk artifacts.
- **Valid example** (`.py` file): `{"content": "", "code_blocks": ["def foo(): ..."]}`
- **Invalid example**: `{"content": "", "code_blocks": []}` → rejected with `ChunkFormatError("crawl: empty 'content' requires non-empty 'code_blocks'")`

### 3.5 Error Handling

For the file-level-failure, existing-chunks and Sudachi-tokenization-error cases, see
[rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md)'s
"ChunkSplitter" section. There is no try/except at the chunk level: a
`TokenizationError` propagates to the per-file catch in `process_all`
(`scripts/rag/ingestion/chunk_splitter.py`), aborting the **entire file**, not one chunk.

### 3.6 Logging

See [rag_05_03-logging.md](rag_05_03-logging.md) for the chunk splitter log destination, format, and levels.

### 3.7 Configuration

See [rag_05_01-configuration-reference.md, `config/chunk_splitter.toml`](rag_05_01-configuration-reference.md).

## Keywords

- chunk-splitter
- chunking-strategies
- sudachi
- markdown-heading
- crawler
- rag
