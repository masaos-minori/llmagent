## Goal

Own one `SQLiteHelper` per `crawl_site` session: open it once before the BFS loop, reuse
it for every `get_conditional_headers` lookup, and close it on both normal and exception
exit (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `CrawlOrchestrator.crawl_site` owns the `httpx.AsyncClient` lifecycle (line 84) and the
  BFS loop (lines 76-113); `_process_crawl_url_async` calls
  `get_conditional_headers(url)` at line 161. These are the only touch points.
- The eager open happens after `WebCrawler.crawl()` has already run
  `_ensure_rag_db_for_http` (crawl003), so for HTTP targets `rag_db_path` is guaranteed
  non-empty by the time `crawl_site` runs. The guard below is a belt-and-suspenders
  safety net for direct `crawl_site` callers (`UNK-03`).
- `scripts/rag/ingestion/orchestrator.py` is also targeted by `crawl005` (eager
  per-host `robots.txt` fetch) and `raging009` (max-pages). Implement this session-
  connection change first (plan order); keep the `try/finally` connection scope
  independent of any later `crawl_site` additions so the two coexist.

## Design decisions
- Create `SQLiteHelper(db_path=self._rag_db_path, ...)` once before the BFS loop in
  `crawl_site`, `open(reuse_connection=True, row_factory=True)`.
- Thread the helper through `_drain_queue_to_tasks` → `_process_crawl_url_async` and pass
  it as `get_conditional_headers(url, db=helper)`.
- Wrap the BFS `while` loop in `try/finally` and call `helper.close()` in `finally` so
  the connection closes on both normal completion and exception (`REQ-002`).

## Alternatives considered
- Storing the helper on `self` for the session duration — acceptable but adds instance
  state visible across calls; threading it as a method parameter keeps the session scope
  explicit and avoids leaking state between concurrent `crawl_site` runs. Chosen: param
  threading.

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
Introduce a session-scoped `SQLiteHelper` in `crawl_site` and route it into the per-URL
conditional-header lookup, closing it in a `finally`.

### Method
Edit three methods:
- `crawl_site` (lines 76-113): after entering the `httpx.AsyncClient` context and before
  the `while` loop, create and open the helper:
  ```python
  helper = SQLiteHelper(
      db_path=self._rag_db_path,
      sqlite_timeout=self._sqlite_timeout,
      sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
  ).open(reuse_connection=True, row_factory=True)
  try:
      while not queue.empty() or pending:
          ...
  finally:
      helper.close()
  ```
- `_drain_queue_to_tasks`: add a `helper` parameter and forward it to
  `_process_crawl_url_async`.
- `_process_crawl_url_async`: add a `helper` parameter and call
  `self._http_fetcher.get_conditional_headers(url, db=helper)` (line 161).

### Details
- Import `SQLiteHelper` locally inside `crawl_site` (module-level import would risk a
  circular dependency with `scripts.db`; consistent with `http_fetcher.py`'s local
  import pattern).
- Guard the eager open against an empty `rag_db_path` (`UNK-03`): if `not self._rag_db_path`,
  skip the shared connection and fall back to the per-call path (the fetcher already logs
  a deduped warning for the empty path). For the normal HTTP path this branch is never
  taken because crawl003 fails fast first.
- `reuse_connection=True` is a no-op on first open (there is no prior connection) and
  matters only if the same helper were reopened; `row_factory=True` makes
  `row["etag"]` / `row["last_modified"]` valid.

## Compatibility considerations
Behavior-preserving: header values and fetched content are unchanged (`REQ-003`). The
connection is now opened once per session instead of per page; observable results are
identical. Existing callers that do not pass `db=` still work via the fetcher's per-call
path (`REQ-004`).

## Security considerations
N/A: no new credential or input handling. The reused connection carries the same WAL /
busy-timeout pragmas as the per-call connection.

## Rollback considerations
N/A: revert the commit that introduced this procedure.

## Validation plan
- Static: `uv run ruff format` / `uv run ruff check` on
  `scripts/rag/ingestion/orchestrator.py`; `uv run mypy --no-namespace-packages
  scripts/` with no new errors.
- Behavioral: simulate a multi-page crawl and spy on `SQLiteHelper.open` / `close` to
  assert exactly one open and one close per `crawl_site` (`REQ-002`); assert conditional
  headers are identical to the per-call approach (`REQ-003`). Run
  `tests/rag/ingestion/`.

## Completion criteria
- Exactly one SQLite connection is opened per `crawl_site` session regardless of page
  count, and it is closed on both normal and exception exit (`REQ-001`, `REQ-002`).
- Conditional-header values and fetched content are byte-for-byte unchanged (`REQ-003`).

## Out of Scope
Changing the `documents` query/schema, the `httpx.AsyncClient` lifecycle, concurrency of
the BFS loop, or connection pooling beyond one per-session connection.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Own one SQLiteHelper per crawl_site session, thread through, close on exit | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | One-open-one-close per session |
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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261106-073205_crawl004_reuse-sqlite-connection-crawl-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094506_crawl004_reuse-sqlite-connection-crawl-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-134925
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
