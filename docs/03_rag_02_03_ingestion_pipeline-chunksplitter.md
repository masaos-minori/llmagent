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

See `CrawlJsonPayload` and `ChunkJsonRaw` in `scripts/rag/ingestion/pipeline_utils.py`
for the exact TypedDict field sets used for crawl-stage and chunk-stage JSON payloads,
and `ChunkMetadata` in the same file for the optional metadata dictionary expanded with
`**` into the output payload. Note: `_build_chunk_payload()` in `chunk_splitter.py`
returns `dict[str, object]`, not `ChunkJsonRaw` directly, because its return value
combines `**metadata` unpacking with additional literal keys, which is incompatible
with a strict `TypedDict` return annotation under current type-checker support.

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

### 3.1.3 Markdown Source Detection Behavior

URLs ending in `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`. For other files, heuristic detection (two or more heading lines in content) is used only if `md_index_enable=true`.

Note: No historical rationale for this extension-based rule is recorded in code comments or commit history (earliest traced commits: `ee035ff5e`/`c0b578e82`, "feat: Markdown ingest standardization — production code changes", contain no explanation). Contrary to what a reader might assume from the documentation, `md_index_enable` does not provide any way to override this rule for `.md`/`.markdown`/`.mdx` sources — including local `file://` sources (where `str.endswith()` matches the extension regardless of the `file://` scheme prefix, confirmed by inspecting `WebCrawler.crawl_file()`'s URL construction, `crawl_persister.py:62`: `f"file://{path.resolve()}"`). A plausible technical rationale is determinism vs. content-based heuristics (an extension-based check requires no content inspection), but this is inferred from the code's structure, not documented anywhere.

### 3.1.4 Markdown Heading Chunking Behavior

Text is split by Markdown headings (# through ######). Sections exceeding `md_snippet_max_chars` characters are further split using sentence-based chunking.

**Fallback trigger condition:** When a heading-delimited section exceeds `md_snippet_max_chars` characters (default 600), the section is split using sentence-boundary splitting via `_chunk_english()`. The exact trigger is `len(section) > md_snippet_max_chars`.

**Sequential per-section combination model:** The two strategies combine sequentially, per-section: the text is first split into heading-delimited sections, then *each section independently* either passes through as one chunk or is further split by `_chunk_english()`. The two strategies are not applied in parallel or merged; each section takes exactly one path.

**Metadata during fallback:** No distinction is made between whole-section chunks and fallback-split chunks at the metadata level. The caller tags every chunk returned by `_chunk_markdown_by_heading()` with the literal `"text"` chunk-type marker, regardless of whether that specific chunk came from a whole heading section or from a `_chunk_english()`-split fragment of an oversized one. There is no metadata field distinguishing "heading chunk" from "fallback-split chunk."

**Undersized-section edge case:** A section that fits within `md_snippet_max_chars` but is smaller than `self._min_chunk` is silently dropped. The `append` only happens inside the inner check (`if len(section) >= self._min_chunk:`); a too-small section produces no chunk at all, not an error or warning.

> Evidence: Explicit in code — Markdown heading chunking falls back to English sentence boundary splitting for overflowing sections. Even if `lang` is `"ja"`, Japanese morphological analysis (Sudachi) is NOT applied, and `normalized_content` is NOT generated (the entire heading chunk's `normalized_content` is always treated as empty, as described below).

### 3.1.6 Markdown Heading Chunking Fallback Mechanism

#### Trigger condition

The fallback to sentence-based chunking triggers **per individual heading-delimited section**, not for the document as a whole. `_chunk_markdown_by_heading()` (lines 158-175 of `scripts/rag/ingestion/chunk_splitter.py`) splits the entire text at heading boundaries first (one pass), then for each resulting section checks `len(section) <= self._md_snippet_max_chars` individually (line 169). Only sections exceeding `md_snippet_max_chars` are re-split via `_chunk_english()` (line 174).

#### Sequential combination

The two strategies combine **sequentially**, not in parallel. Heading-boundary splitting always runs first across the entire text (line 161-163: `re.split(rf"(?={MARKDOWN_HEADING_RE} )", text.strip(), flags=re.MULTILINE)`). Sentence-based splitting (`_chunk_english()`) is a second pass applied only to whichever individual sections exceed the size limit (line 174: `chunks.extend(self._chunk_english(section))`). It is not a parallel or whole-alternative strategy.

#### Chunk metadata during fallback

- `chunking_strategy`: Remains `"heading"` for the overall Markdown source regardless of which sections fell back to sentence splitting (per the document's existing note at line 134: "Heading chunking (`chunking_strategy="heading"`)... regardless of `lang`").
- `normalized_content`: Stays `null` for both non-fallback sections (size-fitting path) and fallback sections (sentence-split path), consistent with the Evidence note above.
- Sections below `min_chunk` after either path are silently discarded as noise (per `chunk_splitter.py` line 168-169: `if len(section) >= self._min_chunk` guard).

#### Known edge case

Japanese content loses Sudachi normalization when routed through heading chunking, including its sentence-split fallback portion — explicitly stated in the Evidence note above. This is the only documented edge case for this behavior.

### 3.1.5 Override Behavior and Known Edge Cases

#### No override for `.md`/`.markdown`/`.mdx` sources

There is no configuration or per-source override for `.md`/`.markdown`/`.mdx` URLs'
unconditional heading chunking. `_is_markdown_source()` (lines 138-154 of
`scripts/rag/ingestion/chunk_splitter.py`) checks the URL extension first (line 146:
`if url.endswith((".md", ".markdown", ".mdx")):` returns `True` immediately), and only
reaches the `self._md_index_enable` check (line 148) for non-`.md`-extension URLs. This
means any source ending in `.md`, `.markdown`, or `.mdx` — whether a remote URL or a local
`file://` source — always uses heading chunking regardless of `md_index_enable`.

#### Known edge case: Japanese content skips Sudachi normalization

The existing note in section 3.1.4 (above) states that even when `lang` is `"ja"`, Japanese
morphological analysis (Sudachi) is NOT applied for Markdown heading chunking, and
`normalized_content` is NOT generated. This is the only known edge case where the Markdown
heading chunking behavior causes problems — Japanese text processing relies on Sudachi
normalization for accurate segmentation, but the heading chunking path bypasses it entirely.

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

Run `uv run python scripts/rag/ingestion/chunk_splitter.py --help` for the current
argument list.

### 3.4 Output JSON Format

See `ChunkJsonRaw` in `scripts/rag/ingestion/pipeline_utils.py` for the exact output
JSON shape.

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
- **Rationale**: Traced to `CrawlPersister.save()`'s `.py`-file handling (`crawl_persister.py:70,76-77`). When processing a `.py` file, the crawler stores the source code in `code_blocks=[content]` with `content=""`, allowing the code chunker to apply. The cross-field rule permits this legitimate empty-content case while rejecting a genuinely broken/incomplete crawl result (both fields empty).
- **Chunk artifacts**: No equivalent exception — `content` is required and must be non-empty for chunk artifacts.
- **Valid example** (`.py` file): `{"content": "", "code_blocks": ["def foo(): ..."]}`
- **Invalid example**: `{"content": "", "code_blocks": []}` → rejected with `ChunkFormatError("crawl: empty 'content' requires non-empty 'code_blocks'")`

### 3.5 Error Handling

For the file-level-failure and existing-chunks cases, see
[03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md)'s
"ChunkSplitter" section. For the Sudachi-tokenization-error case specifically, see
`scripts/rag/ingestion/chunk_japanese.py::_normalize_ja_sentence` and
`scripts/rag/ingestion/chunk_splitter.py::process_all` directly instead —
error-handling-reference.md's entry for this one case is stale (it describes a
per-chunk skip, but the current code has no try/except at the chunk level: a
`TokenizationError` propagates to `process_all()`'s per-file catch, aborting the
**entire file**, not one chunk).

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
