## Goal

Absorb the uncaught `ValueError` raised by `SQLiteHelper._connect` on an empty
`rag_db_path` inside `get_conditional_headers`, and emit a single deduped startup
warning, then return `{}` (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The change described here is **already present in the current source**
  (`scripts/rag/ingestion/http_fetcher.py`): the empty-path guard with the
  `_logged_empty_path` dedupe flag (returns `{}`) and `ValueError` added to the
  caught tuple. It was committed in `03a307158 fix(crawler): surface missing
  rag_db_path at startup...`. `code-implementation` of this procedure is therefore a
  verification pass against `tests/rag/ingestion/test_crawler_integration.py`, not a
  fresh edit.
- The single production caller is `CrawlOrchestrator._process_crawl_url_async`, which
  calls `get_conditional_headers(url)` positionally, so an absorbed error is safe.

## Design decisions
- Add `ValueError` to the `except` tuple alongside
  `sqlite3.OperationalError` / `sqlite3.DatabaseError`; return `{}` on any of them
  (matches `REQ-002`: no uncaught `ValueError` propagates).
- Dedupe the empty-path warning with the instance flag
  `self._logged_empty_path` so a misconfigured path logs once per crawl process, not
  once per fetched URL.

## Alternatives considered
- Raising out of `get_conditional_headers` on empty path — rejected: it crashes every
  per-URL task (the original bug).
- A module-level log flag instead of an instance flag — rejected: an instance flag
  avoids shared cross-instance state across `HttpFetcher` instances.

## Implementation
### Target file
`scripts/rag/ingestion/http_fetcher.py`

### Procedure
In `get_conditional_headers`, keep the early empty-path branch that logs once via
`_logged_empty_path` and returns `{}`; ensure the `try/except` around the
`SQLiteHelper(...).open(...)` lookup includes `ValueError` and returns `{}`.

### Method
Edit `get_conditional_headers` (lines 74-112):
- Empty-path branch (`if not self._rag_db_path:`) logs a single deduped warning and
  returns `{}` (already present).
- Wrap the `SQLiteHelper(...).open(row_factory=True)` lookup in `except
  (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError)` and return `{}`.

### Details
- The caught-tuple edit is the only functional change; the query, `row_factory=True`,
  and header-building logic are unchanged.
- On a valid path with a matching row, `If-None-Match` / `If-Modified-Since` are
  returned exactly as before (`REQ-003`).

## Compatibility considerations
Backward compatible: the signature is unchanged and the only caller passes `url`
positionally. Existing tests that blank `rag_db_path` now see `{}` instead of an
uncaught exception (`REQ-004`).

## Security considerations
N/A: no new input handling or credential access.

## Rollback considerations
N/A: revert the commit that introduced this procedure.

## Validation plan
- Static: `uv run ruff format` and `uv run ruff check` on
  `scripts/rag/ingestion/http_fetcher.py`; `uv run mypy --no-namespace-packages
  scripts/` with no new errors.
- Behavioral: `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` —
  empty-path returns `{}` without raising; valid-path regression still returns cached
  headers.

## Completion criteria
- An empty/missing `rag_db_path` yields `{}` and at most one deduped warning, with no
  `ValueError` escaping `get_conditional_headers`.
- A configured path returns the cached etag/last_modified headers unchanged.

## Out of Scope
Changing the `documents` query/schema, or where `rag_db_path` is read from config.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the `ValueError` safety net + deduped empty-path warning in `get_conditional_headers` (`scripts/rag/ingestion/http_fetcher.py`) | Pending | — | — | Code already present in HEAD 03a307158; verify against tests |
| 2 | Add or update tests per Validation plan | Pending | — | — | Empty-path + valid-path rows in `test_crawler_integration.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blocker | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261106-073205_crawl003_rag-db-path-misconfiguration-handling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094153_crawl003_rag-db-path-misconfiguration-handling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-134321
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`
