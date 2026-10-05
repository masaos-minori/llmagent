# RAG crawler: crawl_file does not resolve lang "auto" (always rejected)

## Priority
Medium

## Summary
`CrawlPersister.save()` (the implementation behind `WebCrawler.crawl_file()`) never resolves `lang="auto"`. The local-file path rejects it and writes nothing, although the documentation and the CLI help state that `auto` is resolved by CJK ratio.

## Background
- `scripts/rag/ingestion/crawl_persister.py`, `save()`, has a comment saying it resolves "auto" by CJK-ratio detection on the file content, but the assignment is `resolved_lang = lang if lang != "auto" else lang`, which is an identity expression. The next check accepts only `en` and `ja`; anything else logs a warning ("lang not supported, skipping local file") and returns 0.
- The CLI in `scripts/rag/ingestion/crawler.py` (`--lang`) accepts `en`, `ja`, `auto` (default `en`). Its help says `auto` detects per-page language by CJK ratio; its module docstring shows only `{en,ja}`.
- Targets-file / config entries are validated by `scripts/rag/ingestion/crawler_utils.py` against `{en, ja, auto}`, and `WebCrawler.crawl()` routes `file://` targets to `crawl_file(path, lang)` with the raw hint, so a `file://` target with `auto` reaches the broken path.
- The real resolution exists for web pages: `LanguageResolver.resolve_lang(text, hint_lang)` in `scripts/rag/ingestion/language_resolver.py` uses `crawler_utils.detect_lang()` (CJK ratio) with `en` fallback for short or inconclusive text, and returns `en` or `ja` for `auto`. It is not used by `CrawlPersister.save()`.
- `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` section on `crawl_file` states that `lang == "auto"` is resolved by CJK ratio of the file content.

## Problem
Evidence (confirmed by code reading):
- `crawl_file(path, "auto")`, and a `file://` target with `auto` in the targets file or config, is silently skipped (warning only, return 0, no JSON written).
- Only `--lang auto` combined with `--url` of http(s) pages gets auto-detection, because that goes through the orchestrator and `LanguageResolver`.
- The existing comment and the documentation describe behavior the code does not implement. Whether the CLI can pass `--lang auto` together with local-file targets through another path is unknown; the verified path is `crawl()` calling `crawl_file()` with the raw lang.

## Reason for Change
Documented and CLI-advertised behavior is not implemented for local files; ingestion of local files with `auto` silently produces nothing.

## Implementation Intent
Resolve `auto` in the local-file path with the existing language detection, reusing `detect_lang()` or `LanguageResolver.resolve_lang()` (same CJK threshold and `en` fallback as web pages) instead of duplicating logic. Options: (A) resolve inside `CrawlPersister.save()` before the supported-language check (recommended; fixes all callers); (B) resolve in `WebCrawler.crawl_file()` before delegating; (C) do not support `auto` for local files: reject `auto` earlier with an explicit error, remove the misleading comment, and correct the documentation and CLI help.

## Target Files or Areas
- scripts/rag/ingestion/crawl_persister.py
- scripts/rag/ingestion/crawler.py
- scripts/rag/ingestion/language_resolver.py
- scripts/rag/ingestion/crawler_utils.py
- tests/rag (crawler / persister tests; exact files unknown)
- docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md

## Required Changes
- Choose option A, B or C and implement it.
- Make the resolved language one of the supported values before it is written to the crawl JSON `lang` field.
- Remove or correct the misleading identity expression/comment.
- Add tests for the local-file path.

## Constraints
- Keep `en`/`ja` explicit hints behaving as today.
- Keep the supported output languages limited to `en` and `ja`.
- Do not change the web-page resolution path.

## Acceptance Criteria
- `crawl_file(path, "auto")` on a CJK-dominant file writes a JSON with `lang` equal to `ja`; on an English file writes `en`; short or inconclusive text falls back to `en` (if option A or B is chosen).
- Unsupported values other than `auto`, `en`, `ja` still return 0 with a warning.
- A `file://` target with `auto` in the targets file is ingested.
- Documentation and CLI help describe the final behavior; the pointer to this issue in the RAG crawler document is removed.

## Testing Expectations
- Unit tests for `CrawlPersister.save()` with `auto` on Japanese, English and short files, and with an unsupported value.
- Test that `WebCrawler.crawl()` with a `file://` target and `auto` produces a JSON file.
- Run `uv run pytest tests/rag`, ruff, mypy, and the RAG docs checkers.

## Documentation Impact
Yes. `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (`crawl_file` behavior) must state the final behavior; it currently states that `crawl_file` accepts only `en`/`ja` and points to this issue. The crawler module docstring/CLI help may need alignment.

## Out of Scope
- Changing the CJK threshold or the minimum text length.
- Adding languages beyond `en` and `ja`.
- Changes to HTTP crawling.

## Dependencies
N/A: none

## Unresolved Questions
- Is rejecting `auto` for local files (option C) an acceptable product decision? Unknown; recommended option is A.

## AI Implementation Instruction
Keep the change minimal and reuse existing language detection; do not duplicate the CJK logic. Do not alter web crawling. Report if the intended product behavior for `auto` on local files is unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261005-102245
- **Related target files**: scripts/rag/ingestion/crawl_persister.py, scripts/rag/ingestion/crawler.py, scripts/rag/ingestion/language_resolver.py, docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md
