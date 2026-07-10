---
title: "Ingestion Pipeline Utilities"
category: rag
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
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_02_ingestion_pipeline-crawler.md
  - 03_rag_02_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_ingestion_pipeline-ingester.md
  - 03_rag_02_ingestion_pipeline-shared.md
  - 03_rag_02_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_ingestion_pipeline-overview.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 Module overview

`crawler_utils.py` — Pure-function utilities for WebCrawler: URL helpers, content extraction, language detection, and target URL parsing. Extracted from `WebCrawler` class to keep it under 400 lines.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `_SUPPORTED_LANGS` | `frozenset({"en", "ja"})` | Supported language codes for resolved (output) lang values |
| `_VALID_HINT_LANGS` | `frozenset({"en", "ja", "auto"})` | Valid hint lang values including "auto" for per-page CJK-ratio detection |
| `_CJK_RATIO_THRESHOLD` | `0.1` | CJK character ratio threshold above which text is classified as Japanese |
| `_TARGET_URL_ENTRY_LENGTH` | `2` | Expected element count for target_urls entries: [url, lang] |
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` (from `rag.utils`) | Minimum text length for language detection |

**Unicode code point ranges for CJK detection**

| Constant | Range | Description |
|---|---|---|
| Hiragana + Katakana | "぀"–"ヿ" | |
| CJK Unified Ideographs | "一"–"鿿" | |
| CJK Extension A | "㐀"–"䶿" | |

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `url_to_slug` | `(url: str) -> str` | Convert URL to filesystem-safe ASCII slug (max 80 chars); strips scheme, replaces non-alphanumeric with hyphens |
| `normalize_url` | `(url: str) -> str` | Strip fragment and trailing slash |
| `same_origin` | `(url: str, base: str) -> bool` | True if scheme + hostname match |
| `extract_text` | `(soup: BeautifulSoup) -> str` | Remove noise tags (nav, footer, aside, script, style, noscript) from soup; extract body text via Trafilatura with `include_comments=False`, `include_tables=True`, `no_fallback=False`, `target_language=None`; fall back to BS4 `get_text(separator="\n", strip=True)` |
| `detect_lang` | `(text: str) -> str \| None` | CJK ratio detection; returns 'ja' if ratio ≥ 0.1, 'en' otherwise; None for texts < 100 chars |
| `parse_target_urls` | `(target_raw: list[Any]) -> list[tuple[str,str]]` | Validate and parse target_urls config into (url, lang) tuples; raises ValueError on invalid entries |
| `parse_targets_file` | `(path: Path) -> list[tuple[str,str]]` | Parse a TOML file containing target_urls = [[url, lang], ...] pairs; raises FileNotFoundError if file not found, ValueError on parse error |

---

## 6. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 6.1 Module overview

`chunk_english.py` — `ChunkEnglishMixin`: paragraph/sentence-level chunking for English text with stopword filtering and sentence boundary splitting. Mixed into `ChunkSplitter` via multiple inheritance.

---

## 7. Chunk Utils (`scripts/rag/ingestion/chunk_utils.py`)

### 7.1 Module overview

`chunk_utils.py` — Shared buffer helpers for `ChunkEnglishMixin` and `ChunkJapaneseMixin`. Provides tail-overlap buffer management and item accumulation with min/max chunk size constraints. Imported by both mixin classes and `chunk_splitter.py`.

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `start_next_buf` | `(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str` | Start a new accumulation buffer with optional tail-overlap from prev. When `chunk_overlap=0`, returns next_item directly. Otherwise prepends the last N characters of prev (where N = chunk_overlap) to next_item |
| `merge_text_items` | `(items: list[str], sep: str, min_chunk: int, max_chunk: int, chunk_overlap: int) -> list[str]` | Accumulate items into chunks satisfying min_chunk ≤ len ≤ max_chunk. A short tail item is merged into the last chunk instead of discarded |

**Usage in mixins:**

| Mixin | Function used | Purpose |
|---|---|---|
| `ChunkEnglishMixin` | `merge_text_items` | Paragraph/sentence accumulation with overlap |
| `ChunkJapaneseMixin` | `start_next_buf`, `merge_text_items` | Sentence pair accumulation with overlap |
| `ChunkSplitter` | `merge_text_items` | Code block accumulation (blank-line split) |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-ingester.md`
- `03_rag_02_ingestion_pipeline-shared.md`
- `03_rag_02_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

crawler-utils
chunk-english-mixin
chunk-japanese-mixin
chunk-utils
pipeline-utils
rag
