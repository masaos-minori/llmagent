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

**Module-level Constants**

| Constant | Value | Description |
|---|---|---|
| `_SUPPORTED_LANGS` | `frozenset({"en", "ja"})` | Supported language codes after resolution (output) |
| `_VALID_HINT_LANGS` | `frozenset({"en", "ja", "auto"})` | Valid hint language values for per-page CJK ratio detection, including `"auto"` |
| `_CJK_RATIO_THRESHOLD` | `0.1` | CJK character ratio threshold above which text is identified as Japanese |
| `_TARGET_URL_ENTRY_LENGTH` | `2` | Expected number of elements in a `target_urls` entry: `[url, lang]` |
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` (from `rag.utils`) | Minimum text length required for language detection |

**CJK Detection Unicode Code Point Ranges**

| Constant | Range | Description |
|---|---|---|
| Hiragana + Katakana | "぀"–"ヿ" | Unicode range for Hiragana and Katakana |
| CJK Unified Ideographs | "一"–"鿿" | Unicode range for CJK Unified Ideographs |
| CJK Extension A | "㐀"–"䶿" | Unicode range for CJK Extension A |

**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `url_to_slug` | `(url: str) -> str` | Converts a URL into an ASCII slug safe for the filesystem (max 80 chars); removes scheme and replaces non-alphanumeric characters with hyphens |
| `normalize_url` | `(url: str) -> str` | Removes fragments and trailing slashes |
| `same_origin` | `(url: str, base: str) $\rightarrow$ bool` | Returns `True` if schemes and hostnames match |
| `extract_text` | `(soup: BeautifulSoup) $\rightarrow$ str` | Removes noise tags (nav, footer, aside, script, style, noscript) from soup; uses Trafilatura to extract main body text with settings `include_comments=False`, `include_tables=True`, `no_fallback=False`, `target_language=None`; falls back to BS4's `get_text(separator="\n", strip=True)` |
| `detect_lang` | `(text: str) $\rightarrow$ str \| None` | CJK ratio detection; returns `'ja'` if ratio $\ge$ 0.1, otherwise `'en'`; returns `None` for text shorter than 100 characters |
| `parse_target_urls` | `(target_raw: list[list[str]]) $\rightarrow$ list[tuple[str,str]]` | Validates `target_urls` configuration and parses them into `(url, lang)` tuples; uses `rag.utils.validate_url` (HTTP/HTTPS only) for URL validation; raises `ValueError` for invalid entries |
| `parse_targets_file` | `(path: Path) $\rightarrow$ list[tuple[str,str]]` | Parses TOML files containing `target_urls = [[url, lang], ...]`; raises `FileNotFoundError` if the file is not found, or `ValueError` on parse errors |

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

**Public Functions**

| Function | Signature | Description |
|---|---|---|
| `start_next_buf` | `(prev: str, next_item: str, sep: str, chunk_overlap: int) $\rightarrow$ str` | Starts a new accumulation buffer while optionally handling trailing duplicates from `prev`. If `chunk_overlap=0`, returns `next_item` directly. Otherwise, prepends the last $N$ characters ($N$ = `chunk_overlap`) of `prev` to the start of `next_item`. |
| `merge_text_items` | `(items: list[str], sep: str, min_chunk: int, max_chunk: int, chunk_overlap: int) $\rightarrow$ list[str]` | Accumulates items into chunks such that `min_chunk` $\le$ len $\le$ `max_chunk`. Short trailing items are not discarded but joined to the final chunk. |

**Actual Usage (Code Verified):**

| Caller | Function Used | Purpose |
|---|---|---|
| `ChunkEnglishMixin` (`chunk_english.py`) | `start_next_buf` | Handling trailing duplicates during paragraph accumulation |
| `ChunkSplitter._chunk_code` (`chunk_splitter.py`) | `merge_text_items` | Accumulating code blocks (empty line splitting) |
| `ChunkJapaneseMixin` (`chunk_japanese.py`) | (Does NOT import this module) | Uses proprietary implementation for accumulating sentence pairs. Sharing with `chunk_utils.py` was a design intent but implementation is incomplete. |

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
