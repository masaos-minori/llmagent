# Goal

Replace `parse_target_urls(list[Any])` with typed `CrawlTarget` DTO input/output,
remove `str(entry[0])` unconditional conversions, and change `detect_lang() → str | None`
to `LanguageCode | None`.

# Scope

- `scripts/rag/ingestion/crawler_utils.py`

# Assumptions

1. `CrawlTarget`, `LanguageCode` from `rag.models` / `rag.enums` (Steps 2-3, 2-2 prerequisite).
2. `parse_target_urls(target_raw: list[Any])` currently returns `list[tuple[str, str]]`.
   After this change, it validates each entry and returns `list[CrawlTarget]`.
3. `str(entry[0]), str(entry[1])` — entry[0] must be str (url), entry[1] must be str
   (lang code). Replace with `isinstance` check + `ValueError` on mismatch.
4. `detect_lang()` currently returns `str | None`; change to `LanguageCode | None`.
   If the detected string is not a valid `LanguageCode`, return `None` (not raise).

# Implementation

## Target file

`scripts/rag/ingestion/crawler_utils.py`

## Procedure

1. Change `parse_target_urls(target_raw: list[Any]) -> list[tuple[str, str]]` →
   `parse_target_urls(target_raw: list[Any]) -> list[CrawlTarget]`:
   ```python
   def parse_target_urls(target_raw: list[Any]) -> list[CrawlTarget]:
       result: list[CrawlTarget] = []
       for entry in target_raw:
           if isinstance(entry, (list, tuple)) and len(entry) >= 2:
               url, lang_str = entry[0], entry[1]
               if not isinstance(url, str) or not isinstance(lang_str, str):
                   raise ValueError(f"Target entry must be [str, str], got {entry!r}")
               try:
                   lang = LanguageCode(lang_str)
               except ValueError:
                   raise ValueError(f"Unknown language code {lang_str!r}")
               result.append(CrawlTarget(url=url, lang=lang))
           elif isinstance(entry, str):
               result.append(CrawlTarget(url=entry, lang=LanguageCode.EN))
           else:
               raise ValueError(f"Cannot parse target entry: {entry!r}")
       return result
   ```
2. Change `detect_lang() → str | None` → `LanguageCode | None`.
3. Run ruff + mypy.

## Method

Input validation + typed return.

# Validation plan

- `grep -n "list\[Any\]\|str(entry" scripts/rag/ingestion/crawler_utils.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/crawler_utils.py`
- `uv run mypy scripts/rag/ingestion/crawler_utils.py`
