# Reuse a single SQLite connection across the crawl session

## Priority
Low

## Summary
Open the conditional-header lookup connection once per crawl session instead of once per fetched URL, to remove a per-page SQLite open/close cycle from the fetch hot path.

## Background
`HttpFetcher.get_conditional_headers` opens a connection with `with SQLiteHelper(db_path=..., ...).open(row_factory=True) as db:` and queries `documents` for the URL. `_process_crawl_url_async` calls `get_conditional_headers(url)` before every fetch, so each crawled page opens and closes a fresh SQLite connection.

## Problem
For a multi-page crawl this adds one connect/disconnect cycle per page. It is not a correctness bug, but it is wasteful latency and resource use at scale (hundreds of pages). The `httpx.AsyncClient` is already reused for the whole `crawl_site`; the DB connection is not.

## Reason for Change
As crawls grow, the per-connection overhead compounds. Opening once per session is a small, low-risk efficiency improvement with no behavior change to the fetched content.

## Implementation Intent
Hold one open SQLite connection (or a short-lived transaction) for the duration of a `crawl_site` run and pass it into the conditional-header lookup, closing it on session exit. Keep the connection scoped to the event-loop task that owns the `httpx.AsyncClient`. This is optional optimization; if the `SQLiteHelper` context does not support reuse cleanly, leave current behavior and record the trade-off.

## Target Files or Areas
`scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`

## Required Changes
- Open the conditional-header connection once per `crawl_site` session rather than per URL, when feasible with the existing `SQLiteHelper` API.
- Ensure the connection is closed on normal and exception exit paths.

## Constraints
- No change to query results, conditional-header values, or fetched content.
- Respect the existing WAL/busy-timeout pragmas and thread-safety rules of `SQLiteHelper`.
- If reuse is not cleanly supported, do not force it; document why.

## Acceptance Criteria
- Conditional-header lookups work correctly with the reused connection.
- The connection is closed on exit (normal and error paths).
- Behavior for 304 / no-cache cases is unchanged.

## Testing Expectations
- Verify conditional-header lookups still return correct headers under a multi-page simulated crawl.
- Confirm the connection is opened once per session, not per URL (e.g., by counting opens in a test double).
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
None required.

## Out of Scope
- Changing the `documents` query or schema.
- Altering the HTTP client lifecycle.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `SQLiteHelper` supports a reusable open connection cleanly enough to justify the change; if not, keep the current per-call behavior.

## AI Implementation Instruction
Only refactor connection lifetime in the conditional-header path. Do not change queries, header values, or HTTP behavior. If `SQLiteHelper` cannot reuse a connection cleanly, leave the code as-is and note why. Run `ruff` and `mypy`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073205
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`
