# Remove dead crawl code paths from the ingestion crawler

## Priority
Low

## Summary
Several crawler functions and constants are unreachable or unused in the current pipeline
but still ship in `scripts/rag/ingestion`: `WebCrawler._process_url`, `WebCrawler._crawl`,
`crawler_utils.parse_targets_args`, and `http_fetcher.DEFAULT_RAG_DB_PATH`. Remove them to
prevent maintenance of code that nothing exercises.

## Problem
- `WebCrawler._process_url` is the old synchronous per-URL handler (fetch → validate →
  extract → detect_lang → save); the active path is the BFS loop
  (`WebCrawler.crawl` → `CrawlOrchestrator.crawl`). Nothing calls `_process_url`.
- `WebCrawler._crawl` exists only as a wrapper calling `self.orchestrator.crawl(self)`; no
  caller references it (the entry point calls `crawl` directly).
- `crawler_utils.parse_targets_args` is exported but no module or test imports it; CLI
  target parsing goes through `parse_target_urls` / `parse_targets_file`.
- `http_fetcher.DEFAULT_RAG_DB_PATH` duplicates the value resolved by
  `shared.runtime_paths.resolve_rag_db_path()`; only the module itself references the
  constant.
Dead code in this subsystem duplicates the active component chain (HttpFetcher,
ContentExtractor, LanguageResolver, CrawlPersister) and can be mistaken for a supported
second entry path.

## Background
Leftovers from the WebCrawler decomposition refactor that split the monolith into
concern components; the old facade methods and helper were left behind.

## Reason for Change
Reduce confusion about which crawl path is canonical, and remove an unused DB-path
constant that could drift from `runtime_paths` resolution.

## Implementation Intent
Delete the four dead symbols after confirming no references remain (source, tests,
deploy scripts).

## Target Files or Areas
- `scripts/rag/ingestion/crawler.py`
- `scripts/rag/ingestion/crawler_utils.py`
- `scripts/rag/ingestion/http_fetcher.py`

## Required Changes
- Remove `WebCrawler._process_url` and `WebCrawler._crawl`.
- Remove `parse_targets_args` from `crawler_utils.py` (keep `parse_target_urls` and
  `parse_targets_file`).
- Remove `DEFAULT_RAG_DB_PATH` from `http_fetcher.py` if truly unreferenced.
- Prune imports that become unused.

## Constraints
- Confirm zero references with a repository-wide search before each deletion.
- Do not change the active BFS path or component contracts.

## Acceptance Criteria
- `uv run ruff check scripts/rag/ingestion` and the type gates pass with no unused-symbol
  findings in the touched files.
- `uv run pytest tests/rag/ingestion` passes.

## Testing Expectations
- No new tests required; existing crawler tests must keep passing.

## Documentation Impact
Check docs that enumerate crawler helpers; remove mentions of the deleted functions if
present.

## Out of Scope
- Any redesign of the crawl entry API.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Deletion-only change; verify references first, delete, then run the standard gates.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/http_fetcher.py`
