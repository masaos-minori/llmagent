# RAG crawler: crawl_file does not resolve lang "auto" (always rejected)

## Priority
Medium

## Summary
`CrawlPersister.save()` (the implementation behind `WebCrawler.crawl_file()`) never resolves `lang="auto"`. The local-file path rejects it and writes nothing, although the CLI help states that `auto` is resolved by CJK ratio. The documentation correctly describes the current rejection behavior, creating a contradiction between CLI help and docs.

## Background
- `scripts/rag/ingestion/crawl_persister.py`, `save()`, has a comment saying it resolves "auto" by CJK-ratio detection on the file content, but the assignment is `resolved_lang = lang if lang != "auto" else lang`, which is an identity expression. The next check accepts only `en` and `ja`; anything else logs a warning ("lang not supported, skipping local file") and returns 0.
- The CLI in `scripts/rag/ingestion/crawler.py` (`--lang`) accepts `en`, `ja`, `auto` (default `en`). Its help says `auto` detects per-page language by CJK character ratio; its module docstring shows only `{en,ja}` (also incorrect).
- Targets-file / config entries are validated by `scripts/rag/ingestion/crawler_utils.py` against `{en, ja, auto}`, and `WebCrawler.crawl()` routes `file://` targets to `crawl_file(path, lang)` with the raw hint, so a `file://` target with `auto` reaches the broken path.
- The real resolution exists for web pages: `LanguageResolver.resolve_lang(text, hint_lang)` in `scripts/rag/ingestion/language_resolver.py` uses `crawler_utils.detect_lang()` (CJK ratio) with `en` fallback for short or inconclusive text, and returns `en` or `ja` for `auto`. It is not used by `CrawlPersister.save()`.
- `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` section on `crawl_file` correctly states that `lang == "auto"` is rejected (not resolved), contradicting the CLI help.
- `CrawlPersister.save_http()` also rejects `auto` (line 108: `if lang not in frozenset({"en", "ja"})`), but this is less impactful because HTTP crawling always goes through `LanguageResolver` before calling `save_http()`.

## Problem
Evidence (confirmed by code reading):
- `crawl_file(path, "auto")`, and a `file://` target with `auto` in the targets file or config, is silently skipped (warning only, return 0, no JSON written).
- Only `--lang auto` combined with `--url` of http(s) pages gets auto-detection, because that goes through the orchestrator and `LanguageResolver`.
- The CLI help claims `auto` works for local files, but the code rejects it. The documentation correctly describes the rejection, but this contradicts the CLI help.
- The existing comment in `save()` describes behavior the code does not implement. Whether the CLI can pass `--lang auto` together with local-file targets through another path is unknown; the verified path is `crawl()` calling `crawl_file()` with the raw lang.

## Reason for Change
Documented and CLI-advertised behavior is not implemented for local files; ingestion of local files with `auto` silently produces nothing. Additionally, the CLI help and documentation contradict each other on whether `auto` is accepted for local files.

## Implementation Intent
Resolve `auto` in the local-file path with the existing language detection, reusing `detect_lang()` or `LanguageResolver.resolve_lang()` (same CJK threshold and `en` fallback as web pages) instead of duplicating logic. Options: (A) resolve inside `CrawlPersister.save()` before the supported-language check (recommended; fixes all callers); (B) resolve in `WebCrawler.crawl_file()` before delegating; (C) do not support `auto` for local files: reject `auto` earlier with an explicit error, remove the misleading comment, correct the documentation, and update the CLI help to clarify that `auto` applies only to HTTP URLs.

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
- Align CLI help and documentation on the final behavior for `auto`.

## Constraints
- Keep `en`/`ja` explicit hints behaving as today.
- Keep the supported output languages limited to `en` and `ja`.
- Do not change the web-page resolution path.

## Acceptance Criteria
- If option A or B is chosen:
  - `crawl_file(path, "auto")` on a CJK-dominant file writes a JSON with `lang` equal to `ja`; on an English file writes `en`; short or inconclusive text falls back to `en`.
- If option C is chosen:
  - `crawl_file(path, "auto")` returns 0 with an explicit error message (not just a warning).
  - CLI help and documentation clearly state that `auto` applies only to HTTP URLs, not local files.
- Unsupported values other than `auto`, `en`, `ja` still return 0 with a warning.
- A `file://` target with `auto` in the targets file is ingested (if option A or B is chosen).
- Documentation and CLI help describe the final behavior; the pointer to this issue in the RAG crawler document is removed.

## Testing Expectations
- Unit tests for `CrawlPersister.save()` with `auto` on Japanese, English and short files, and with an unsupported value.
- Test that `WebCrawler.crawl()` with a `file://` target and `auto` produces a JSON file (if option A or B is chosen).
- Run `uv run pytest tests/rag`, ruff, mypy, and the RAG docs checkers.

## Documentation Impact
Yes. `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (`crawl_file` behavior) must state the final behavior; it currently correctly describes the rejection but contradicts the CLI help. The crawler module docstring/CLI help may need alignment depending on the chosen option.

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
