# Fail fast on unset rag_db_path instead of per-URL ValueError

## Priority
Medium

## Summary
Surface a missing or empty `rag_db_path` at crawler startup as a clear fail-fast error, instead of raising an uncaught `ValueError` per crawled URL that silently fails the whole site crawl.

## Background
`HttpFetcher.get_conditional_headers` looks up cached `etag`/`last_modified` before each fetch. It opens a connection via `SQLiteHelper(db_path=self._rag_db_path, ...)` inside `except (sqlite3.OperationalError, sqlite3.DatabaseError)`. `SQLiteHelper._connect` raises `ValueError` when `not self._db_path`.

## Problem
`ValueError` is not in the caught tuple, so an empty/misconfigured `rag_db_path` propagates out of `get_conditional_headers`. In `_process_crawl_url_async` this fails the individual URL task and is only logged as "Crawl task error" by the orchestrator's `asyncio.wait` exception handler. Net effect: when `rag_db_path` is unset, every HTTP URL is dropped and the site crawl produces no documents, with no startup signal that the DB is misconfigured. Test configs use `""` or `":memory:"`, so the gap is not exercised.

## Reason for Change
A misconfigured DB path should be a loud, single startup failure, not hundreds of per-URL failures that look like ordinary crawl errors. Operators cannot distinguish "DB not configured" from "pages had no content."

## Implementation Intent
Validate `rag_db_path` (and the SQLite settings) at `WebCrawler.__init__` and raise a clear error before any network I/O when it is empty. Alternatively narrow the catch in `get_conditional_headers` to log a warning and return `{}` so a missing cache simply means unconditional fetches. Prefer fail-fast at init, since conditional headers are a cache optimization and a missing DB is a configuration error, not a per-page condition.

## Target Files or Areas
`scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/http_fetcher.py`

## Required Changes
- Reject an empty `rag_db_path` at `WebCrawler.__init__` with an explicit error, or make `get_conditional_headers` degrade safely (log + return `{}`) on configuration errors.
- Document the chosen behavior in the raised message or log.

## Constraints
- Do not change the successful conditional-header path or its caching semantics.
- Preserve backward compatibility for a validly configured `rag_db_path`.
- Keep the change within crawler initialization; do not touch the ingester DB config.

## Acceptance Criteria
- An empty `rag_db_path` fails at construction with a clear message (fail-fast), OR conditional-header lookup degrades to unconditional fetch with a logged warning.
- A valid `rag_db_path` crawls unchanged.
- The behavior is covered by a test.

## Testing Expectations
- Test that constructing a crawler with an empty `rag_db_path` raises (or logs a warning and proceeds) as implemented.
- Test that a valid path still performs conditional-header lookups.
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
Document the fail-fast vs. degrade choice in the crawler config notes if such notes exist.

## Out of Scope
- Changing the DB schema or the `documents` table.
- Altering ingester DB configuration handling.

## Dependencies
N/A: none

## Unresolved Questions
- Fail-fast at init versus safe degradation (log + return `{}`). Fail-fast is recommended because an unset DB path is a configuration error; confirm the operator preference before implementing.

## AI Implementation Instruction
Choose one: validate `rag_db_path` at `WebCrawler.__init__` and raise a clear error when empty, or make `HttpFetcher.get_conditional_headers` catch configuration errors, log a warning, and return `{}`. Implement only that path; do not touch the successful fetch or cache logic. Add a test for the empty-path case. Run `ruff` and `mypy`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073205
- **Related target files**: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/http_fetcher.py`
