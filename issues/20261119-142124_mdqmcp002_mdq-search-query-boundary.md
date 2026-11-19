# Move MDQ search authorization, filtering, error classification, and cancellation into one query boundary

## Priority
High

## Summary
Refactor MDQ search so authorization, counting, limiting, path and tag filtering, FTS5 error classification, and SQLite cancellation are handled in one query boundary before response construction.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 2).

Evidence (`Explicit in code`, by `rg` on `scripts/mcp_servers/mdq/search.py`): path, heading-path, and tag filters use `LIKE ?` (lines 218-227, tags on `tags_json`); `sqlite3.OperationalError` is caught at line 192; the call uses `asyncio.wait_for(asyncio.to_thread(...))` (lines 51-52); `COUNT(*)` is computed without `LIMIT` (line 149). Whether authorization is applied in SQL or in Python after `LIMIT`, and what the `OperationalError` branch returns, are backlog claims and `Needs confirmation`.

## Problem
Counts and limits may include unauthorized rows (count leakage, authorized results hidden by unauthorized rows); `LIKE` metacharacters broaden path filters; tag filtering is substring-based; generic SQLite errors may become successful zero-result responses; a timeout stops the caller, not the SQLite query.

## Reason for Change
Authorization and information-disclosure risk plus a resource leak on timeouts.

## Implementation Intent
Apply authorized-source constraints in SQL before `COUNT`, ranking, and `LIMIT`; make `matched_count` an authorized count; use exact path and tag semantics; classify errors by cause; use a dedicated cancellable connection per search.

## Target Files or Areas
- `scripts/mcp_servers/mdq/search.py`; `scripts/db/helper.py` (shared progress-handler cancellation)
- Search request and result models
- `tests/mcp_servers/mdq/test_search.py`, `test_mdq_search_counts.py`, `test_mdq_search_limits.py`, `test_mdq_search_modes.py`, `test_mdq_read_authorization.py`

## Required Changes
- Authorize and canonicalize `path_prefix` before query construction; escape `LIKE` metacharacters or use a non-`LIKE` comparison; match tags exactly with `json_each()`.
- Convert malformed FTS syntax to a validation error, interruption to timeout, busy or locked to a retryable consistency error, and missing table, corruption, or schema mismatch to non-retryable consistency errors; success only for a completed zero-result query; no raw SQLite or query text in responses.
- Dedicated connection per search; progress-handler cancellation; set a stop event on async timeout and wait for the worker before closing; never reuse an interrupted connection; bounded active-search semaphore; non-sensitive timeout and cancellation metrics.

## Constraints
- Unauthorized counts never appear in text, metadata, or audit.
- Use the error codes defined by `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`.

## Acceptance Criteria
- [ ] Unauthorized rows never affect visible counts or limits and cannot suppress authorized results.
- [ ] Path wildcard characters do not broaden scope; tags match exact values.
- [ ] Malformed FTS syntax is not reported as zero results.
- [ ] Timed-out queries stop within a bounded interval; repeated timeouts do not leak threads or connections.

## Testing Expectations
- Mixed authorized and unauthorized roots; unauthorized rows ranked above authorized rows; `%`, `_`, and escape characters in path filters; exact and similar tags.
- Syntax, timeout, busy, missing table, corruption, and genuine zero-result cases; repeated-timeout resource-leak tests; update count, limit, and mode characterization tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. `matched_count` as authorized count; path and tag filter semantics; error codes and cancellation behavior.

## Out of Scope
- Server error contract and audit (`issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`); schema identity (`issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`).

## Dependencies
- Depends on `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`. Can run in parallel with `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md` once the error contract exists.

## Unresolved Questions
- `不明`: whether the shared `scripts/db/helper.py` progress handler can be reused as is.
- `不明`: semaphore size and timeout bounds.

## AI Implementation Instruction
Write the unauthorized-rows-ranked-first test and the repeated-timeout leak test first. Keep changes inside the search path and tests. Stop and report if the shared helper must change in a way that affects other databases.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142124
- **Related target files**: `scripts/mcp_servers/mdq/search.py`, `scripts/db/helper.py`, `tests/mcp_servers/mdq/test_search.py`
