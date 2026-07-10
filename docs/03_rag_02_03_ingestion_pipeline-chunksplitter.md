---
title: "ChunkSplitter Detail"
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
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class overview

`ChunkSplitter` — splits `rag-src/*.json` files into chunks by language and content type;
saves to `rag-src/chunk/`. Idempotent: skips if `{stem}-0000.json` sentinel exists (`--force` overrides).

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `MIN_HEADING_LINES_FOR_MARKDOWN` | 2 | Minimum heading lines to trigger heuristic Markdown detection for non-.md files |
| `MARKDOWN_HEADING_RE` | `r"^#{1,6}"` | Regex pattern for matching Markdown headings (1-6 levels) |

**Typed dicts**

| TypedDict | Purpose |
|---|---|
| `CrawlFilePayload` | Typed dict for crawl output JSON files (url, title, lang, content, code_blocks required; etag, last_modified optional via NotRequired) |
| `ChunkOutputPayload` | Typed dict for chunk output JSON files (schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, content required; normalized_content optional via NotRequired) |
| `ChunkMetadata` | Optional metadata dict for ** spreading into output payload (total=False); all fields optional including url, title, lang, etag, last_modified, source_file, chunking_strategy |

**Inheritance**

`ChunkSplitter` inherits from both `ChunkEnglishMixin` and `ChunkJapaneseMixin` via multiple inheritance.
Method resolution order: `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`.

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None) -> None` | Load `chunk_splitter.toml`; init Sudachi tokenizer (SplitMode.C, `core` dict) |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | Process all *.json files in rag-src/ (or a single target); returns total chunks written |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | Read a crawler JSON file, split into chunks, and write to chunk_dir; returns chunk count; skips already-chunked files when force=False |

### 3.1.1 Markdown heading chunking configuration

| Parameter | Default | Description |
|---|---|---|
| `md_index_enable` | False | Enable heuristic Markdown detection for non-.md files |
| `md_snippet_max_chars` | 600 | Max characters per markdown heading section before falling back to sentence-level chunking |

### 3.1.2 Chunking parameters (shared with crawler)

| Parameter | Default | Description |
|---|---|---|
| `min_chunk` | 40 | Minimum chunk character count; chunks below this are discarded as noise |
| `max_chunk` | 500 | Maximum chunk character count; longer text is split |
| `chunk_overlap` | 50 | Sliding window chunk overlap (chars); prepends this many chars from previous chunk tail; 0 = disabled |
| `en_stopwords` | — | English stop words excluded from chunking (see config/rag_pipeline.toml) |
| `ja_stop_pos` | — | Sudachi part-of-speech categories treated as stop words in Japanese (see config/rag_pipeline.toml) |

### 3.1.3 Markdown source detection behavior

URLs ending with `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`.
Non-`.md` files use heuristic detection (≥2 heading lines in content) only when `md_index_enable=true`.

### 3.1.4 Markdown heading chunking behavior

Split text at Markdown headings (# through ######); sections exceeding `md_snippet_max_chars` characters are further split via sentence-level chunking.

### 3.2 Splitting strategies

| Content type | Strategy |
|---|---|
| Japanese text | Sudachi SplitMode.C morphological analysis; `(original_sentence, normalized_form_space_joined)` pairs |
| English text | Regex sentence boundary split (`(?<=[.!?])\s+`); merges short paragraphs, discards chunks below min_chunk after stopword removal |
| `.md`/`.markdown`/`.mdx` URL | Heading boundary split (`#`/`##`/`###`); always applied regardless of `md_index_enable` |
| Non-`.md` content with ≥2 heading lines | Heading boundary split; applied only when `md_index_enable=true` |
| Code blocks | Blank-line split (language-agnostic); not subject to stopword removal or morphological analysis |

- Japanese chunks: `content` = original text, `normalized_content` = Sudachi normalized forms
- English/code chunks: `normalized_content = null`
- `chunk_type`: `"text"` or `"code"`
- `chunking_strategy`: `"text"` or `"heading"`

### 3.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--file PATH` | Process single file only (path relative to rag_src_dir) | all unprocessed `.json` in rag-src/ |
| `--force` | Regenerate existing chunks (overrides sentinel check) | false |

### 3.4 Output JSON format (`rag-src/chunk/{stem}-{idx:04d}.json`)

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

The `source_file` field retains the original `.json` extension from the crawler output filename.
All fields from `ChunkMetadata` TypedDict (total=False) are included via `**metadata` spread.

### 3.5 Error handling

| Case | Action |
|---|---|
| Sudachi tokenize error | Catch; return `""`; skip that chunk |
| File-level failure | `ERROR` log (with traceback); continue to next file |
| Existing chunk (`{stem}-0000.json`) | Skip unless `--force` |

### 3.6 Logging

- **File:** `/opt/llm/logs/chunk.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing |
|---|---|
| `INFO` | Files processed, chunks generated, skipped files (with URL) |
| `WARNING` | Sudachi error |
| `ERROR` | File read error, file-level failure (with traceback) |

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

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag
