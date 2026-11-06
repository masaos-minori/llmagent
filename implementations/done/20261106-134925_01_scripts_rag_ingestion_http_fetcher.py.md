## Goal

Add an optional `db` parameter to `get_conditional_headers` so a session-scoped
`SQLiteHelper` can be passed in and reused across every URL in a `crawl_site` session,
eliminating the per-page connect/disconnect cycle (`REQ-001`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verification (20261106): stale detection passed. Adapted form: in the current source
  `get_conditional_headers` is a method `HttpFetcher.get_conditional_headers(self, url)`
  (lines 74-112) with the crawl003 empty-path guard and `self._logged_empty_path` dedupe
  flag already present; the production caller is
  `self._http_fetcher.get_conditional_headers(url)` (`orchestrator.py` line 161). The
  `db` parameter is therefore added to the method; the crawl003 guard is not disturbed.
- `get_conditional_headers` currently always opens its own
  `SQLiteHelper(...).open(row_factory=True)` and has exactly one production caller:
  `CrawlOrchestrator._process_crawl_url_async` (`scripts/rag/ingestion/orchestrator.py`,
  line 161). Verified via `rg`.
- `SQLiteHelper.open(reuse_connection=True, row_factory=True)` returns the existing
  `self.conn` without reconnecting and skips close in `__exit__` (`scripts/db/helper.py`,
  lines 205-230), so a session-owned helper can be reused safely.
- The crawler runs on a single event-loop thread and the lookup query has no `await`, so
  queries never interleave on the shared connection.
- `scripts/rag/ingestion/http_fetcher.py` was already modified by `crawl003`
  (`03a307158`) to absorb `ValueError` on an empty path; this change layers the `db`
  parameter on top and does not disturb that guard.

## Design decisions
- Add `db: "SQLiteHelper | None = None"` to `get_conditional_headers`. When `db` is
  provided, run the `SELECT etag, last_modified FROM documents WHERE url = ?` query
  against `db.fetchall(...)` (the row factory is already `sqlite3.Row` from open) and
  build the header dict; return `{}` on empty rows.
- When `db` is `None`, keep the existing per-call `SQLiteHelper(...).open(...)` path so
  existing callers and tests are unaffected (`REQ-004`).

## Alternatives considered
- Resolving the session connection inside `HttpFetcher` via lazy shared state — rejected:
  the plan recommends keeping `HttpFetcher` stateless and owning the connection in
  `crawl_site` (`UNK-01`), which matches the "close on session exit" intent.

## Implementation
### Target file
`scripts/rag/ingestion/http_fetcher.py`

### Procedure
Change `get_conditional_headers` to accept an optional `db` and prefer it when present.

### Method
Edit `HttpFetcher.get_conditional_headers` (lines 74-112):
- Signature: add `db: SQLiteHelper | None = None` to the method; annotate via the
  module's `if TYPE_CHECKING:` block (`from db.helper import SQLiteHelper`), keeping the
  function-local runtime import pattern unchanged.
- Signature: add `db: "SQLiteHelper | None = None"`.
- After the empty-path guard, branch on `db`:
  - `if db is not None:` execute the `documents` query via `db.fetchall(...)` inside a
    `try/except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError)`, build the
    header dict from the row, return `{}` on empty/error.
  - else keep the current `with SQLiteHelper(...).open(row_factory=True) as db_local:`
    block unchanged.
- Keep the header-building logic (etag / last_modified → `If-None-Match` /
  `If-Modified-Since`) identical for both paths.

### Details
- The `db` argument is keyword-only in the caller (`get_conditional_headers(url, db=...)`);
  no positional-arg caller changes.
- Row access uses `row["etag"]` / `row["last_modified"]` (sqlite3.Row), unchanged from
  the current code.

## Compatibility considerations
Backward compatible: default `db=None` reproduces the exact current per-call behavior
(`REQ-003`, `REQ-004`). The single positional caller is unaffected until the caller opts
in with `db=`.

## Security considerations
N/A: no new input handling.

## Rollback considerations
N/A: revert the commit that introduced this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on
  `scripts/rag/ingestion/http_fetcher.py`; `uv run mypy --no-namespace-packages
  scripts/` with no new errors.
- Behavioral: call `get_conditional_headers(url)` with `db=None` (returns cached headers
  or `{}`, unchanged) and with a session `SQLiteHelper` (returns byte-identical headers);
  assert an empty path still returns `{}` without raising. Run
  `tests/rag/ingestion/test_crawler_integration.py`.

## Completion criteria
- `get_conditional_headers` accepts `db=` and returns the same header dict whether the
  lookup uses the session connection or the per-call open (`REQ-003`).
- With `db=None` behavior is byte-for-byte unchanged (`REQ-004`).

## Out of Scope
Changing the `documents` query/columns/schema, or the `httpx.AsyncClient` lifecycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add optional `db` parameter to `get_conditional_headers` (`scripts/rag/ingestion/http_fetcher.py`) | Completed | — | 20261106 | Adapted to HttpFetcher method form: db kwarg added to get_conditional_headers |
| 2 | Add or update tests per Validation plan | Completed | — | 20261106 | Session-vs-per-call header equality TestSessionDbParameter (3 tests) in test_crawler_integration.py; ruff/mypy clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261106 | TestSessionDbParameter (3 tests) in test_crawler_integration.py; ruff/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261106 | N/A N/A |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261106-073205_crawl004_reuse-sqlite-connection-crawl-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094506_crawl004_reuse-sqlite-connection-crawl-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-134925
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`