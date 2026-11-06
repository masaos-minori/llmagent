## Goal
- Remove the per-SQLite-connect/disconnect cycle from the conditional-header lookup hot path by opening one connection per `crawl_site` session and reusing it across all fetched URLs in that session.

## Priority
Low

## Scope
- **In-Scope**:
  - Open the conditional-header lookup connection once per `crawl_site` session.
  - Reuse that connection for every `get_conditional_headers` call within the session.
  - Close the connection on both normal and exception exit paths.
  - Preserve query results, header values, and fetched content exactly.
- **Out-of-Scope**:
  - Changing the `documents` query, columns, or schema.
  - Altering the `httpx.AsyncClient` lifecycle.
  - Connection pooling beyond a single per-session connection.
  - Concurrency changes to the BFS loop.
- **Dependencies**: `N/A: none` (independent optimization; note interaction with crawl003's empty-path safety net)

## Background
`HttpFetcher.get_conditional_headers` opens a connection with `with SQLiteHelper(db_path=..., ...).open(row_factory=True) as db:` and queries `documents` for the URL. `_process_crawl_url_async` calls `get_conditional_headers(url)` before every fetch, so each crawled page opens and closes a fresh SQLite connection.

## Problem
For a multi-page crawl this adds one connect/disconnect cycle per page. It is not a correctness bug, but it is wasteful latency and resource use at scale (hundreds of pages). The `httpx.AsyncClient` is already reused for the whole `crawl_site`; the DB connection is not.

## Reason for Change
As crawls grow, the per-connection overhead compounds. Opening once per session is a small, low-risk efficiency improvement with no behavior change to the fetched content.

## Implementation Intent
Hold one open SQLite connection for the duration of a `crawl_site` run and pass it into the conditional-header lookup, closing it on session exit. `SQLiteHelper` explicitly supports this via `open(reuse_connection=True)` (returns the existing connection instead of reconnecting and skips close in `__exit__`). The reuse is safe here because the crawler runs on a single event-loop thread and the DB query in `get_conditional_headers` is fully synchronous (no `await`), so queries never overlap. If the connection cannot be scoped and cleaned up cleanly within the existing `crawl_site` structure, keep the current per-call behavior and record the trade-off (this is an optional optimization).

## Requirements
- `REQ-001`: The conditional-header lookup opens at most one SQLite connection per `crawl_site` session, regardless of page count.
- `REQ-002`: The connection is closed on both normal completion and exception exit of `crawl_site`.
- `REQ-003`: Conditional-header values and fetched content are byte-for-byte unchanged versus the per-call approach.
- `REQ-004`: `get_conditional_headers` remains callable without an explicit connection argument (backward compatible for existing callers/tests).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Add an optional `db` parameter to `get_conditional_headers` so a session-scoped `SQLiteHelper` can be passed in; when supplied, use it directly (with `row_factory=True`) instead of opening a new connection; keep the per-call open path when `db` is None (REQ-001, REQ-003, REQ-004) | REQ-001 | `get_conditional_headers` currently always opens its own `SQLiteHelper(...).open(...)`; only one production caller at `orchestrator.py:175` (verified) | Existing integration tests | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Own one `SQLiteHelper` per `crawl_site` session: open once with `reuse_connection=True, row_factory=True`, pass it to `get_conditional_headers`, and close it in a `finally` block covering the BFS loop (REQ-001, REQ-002) | REQ-001, REQ-002 | `crawl_site` owns the `httpx.AsyncClient` lifecycle and the BFS loop; `_process_crawl_url_async` calls `get_conditional_headers` per URL (verified) | Existing crawler tests | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | Owns `SQLiteHelper.open(reuse_connection=...)`, `__exit__`, and `close()`; read to confirm the reuse semantics and that `reuse_connection=True` skips reconnect and `__exit__` close (REQ-001, REQ-002) | `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py` |
| `scripts/rag/ingestion/crawler.py` | Owns `WebCrawler.crawl` and `main()`; read to confirm the entry point and that session scoping lives in `orchestrator.crawl_site`, not here (REQ-002) | `scripts/rag/ingestion/orchestrator.py` |

## Acceptance Criteria
- `REQ-001`: A multi-page simulated crawl opens exactly one SQLite connection for the session (asserted via a connection-open counter on a test double).
- `REQ-002`: The connection is closed after `crawl_site` returns, including on an exception raised mid-crawl.
- `REQ-003`: Conditional headers returned for a cached URL match those produced by the previous per-call implementation.
- `REQ-004`: `get_conditional_headers(url)` still works with a single positional argument.

## Tests
- Unit test: a test double for `SQLiteHelper` (or a spy on `open`) asserts the connection is opened once for N URLs in a simulated session, then closed (REQ-001, REQ-002).
- Behavior test: conditional-header values for a cached URL are unchanged (REQ-003).
- Backward-compat test: `get_conditional_headers(url)` with no `db` argument still opens and uses its own connection (REQ-004).
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
`N/A: the connection lifetime is not documented in `docs/*.md``.

## Assumptions
- The crawler runs on a single event-loop thread, so a sqlite3 connection with default `check_same_thread=True` is safe across asyncio tasks as long as queries do not span `await` points (they do not).
- Reads against a WAL database do not contend for locks under the configured busy timeout.
- `rag_db_path` is configured (non-empty); the empty-path case is handled by crawl003's safety net and should not break session connection setup.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Where to own the session connection: `CrawlOrchestrator.crawl_site` (owns the client/BFS lifecycle) versus a lazily-initialized shared connection on `HttpFetcher`. Owning it in the orchestrator matches the issue's "close on session exit" intent and keeps `HttpFetcher` stateless. | None required; both verified feasible. | Recommend orchestrator ownership: create `SQLiteHelper` in `crawl_site`, open once with `reuse_connection=True`, pass to `get_conditional_headers(db=...)`, close in `finally`. Non-blocking. | False |
| UNK-02 | Whether reuse yields measurable benefit for typical crawl sizes (tens of pages) versus added complexity. | No benchmark data available. | This is an explicit Low-priority optional optimization; proceed only if cleanup stays clean. If lifecycle management proves fragile, apply the escape hatch (leave per-call behavior, record trade-off). Non-blocking. | False |
| UNK-03 | Interaction with crawl003's empty-path `ValueError` handling. Opening once at session start would surface an empty path immediately (fail-fast) rather than per-URL. | None required. | Coordinate with crawl003: if the session connection is opened eagerly, an empty `rag_db_path` fails fast at startup (aligned with crawl003's intent); guard the open with the same empty-path check. Non-blocking. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Low (adds optional param; existing single positional-arg caller unaffected) | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Low (session-scoped connection; one production call site) | N/A | N/A | not applicable (rsynced) |

## Design
Current flow: `_process_crawl_url_async` (orchestrator.py) calls
`self._http_fetcher.get_conditional_headers(url)` before every fetch. Each call executes
`SQLiteHelper(db_path=...).open(row_factory=True)` inside a `with`, which connects on
`__enter__` and closes on `__exit__`. For N pages this is N connect/close cycles.

**Reuse feasibility (UNK-01):** `SQLiteHelper.open(reuse_connection=True)` returns the
existing `self.conn` without reconnecting when one is already open, and `__exit__` skips
closing when `reuse_connection` is set. This is a purpose-built mechanism, so reuse is
cleanly supported. Thread-safety is sound because the crawler runs on a single
event-loop thread and the query inside `get_conditional_headers` contains no `await`;
only one coroutine runs at a time, so queries never interleave on the connection.

**Recommended design:**
1. In `get_conditional_headers`, add an optional `db: SQLiteHelper | None = None`
   parameter. When `db` is provided, run the `documents` query against `db` with
   `db.conn.row_factory` already set to `sqlite3.Row` (set at open time) and return the
   header dict. When `db` is `None`, keep the existing per-call open path so existing
   callers and tests are unaffected (REQ-003, REQ-004).
2. In `crawl_site`, own one `SQLiteHelper`: create it once before the BFS loop,
   `open(reuse_connection=True, row_factory=True)`, and pass it to
   `get_conditional_headers(url, db=helper)`. Wrap the loop in `try/finally` and call
   `helper.close()` in `finally` so the connection closes on both normal and exception
   exit (REQ-002).
3. Guard the eager open against an empty `rag_db_path` (UNK-03): if the path is empty,
   either skip the shared connection and fall back to the per-call path, or fail fast
   consistent with crawl003. Coordinate the final choice with crawl003.
4. Escape hatch: if scoping/cleanup cannot be done cleanly within `crawl_site`, leave the
   current per-call behavior and document why (this is an optional optimization).

This preserves all observable behavior while removing the per-page connect/disconnect
overhead.

## Implementation steps
1. **Phase 1: Optional `db` parameter** (`scripts/rag/ingestion/http_fetcher.py`, REQ-003, REQ-004)
   - [ ] Add `db: "SQLiteHelper | None = None"` to `get_conditional_headers`.
   - [ ] When `db` is provided, execute the `documents` query against `db` (row factory already set at open) and build the header dict; return `{}` on empty rows.
   - [ ] Keep the existing per-call `SQLiteHelper(...).open(...)` path when `db` is `None`.
2. **Phase 2: Session-owned connection** (`scripts/rag/ingestion/orchestrator.py`, REQ-001, REQ-002)
   - [ ] In `crawl_site`, create one `SQLiteHelper` and `open(reuse_connection=True, row_factory=True)` before the BFS loop.
   - [ ] Pass it to `get_conditional_headers(url, db=helper)` in `_process_crawl_url_async` (thread it through `_drain_queue_to_tasks` / `_process_crawl_url_async`, or store on the orchestrator instance for the session).
   - [ ] Close the helper in a `finally` block covering the loop (normal and error paths).
   - [ ] Guard the eager open against an empty `rag_db_path` per UNK-03.
3. **Phase 3: Verification & commit** (REQ-001, REQ-002, REQ-004)
   - [ ] Run `uv run ruff format` and `uv run ruff check` on both touched files; confirm clean.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/`; confirm no new errors.
   - [ ] Add a test asserting one connection open per session and proper close; run the crawler/fetcher suite; confirm pass.
   - [ ] Commit, rebase onto `origin/master`, and push via `git-commit-and-sync`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Static: format, lint, type | `uv run ruff format` / `uv run ruff check` / `uv run mypy --no-namespace-packages scripts/` | Clean, no new errors |
| `scripts/rag/ingestion/orchestrator.py` | Behavioral: one connection per session, closed on exit | spy on `SQLiteHelper.open`/`close` in a simulated multi-page crawl | Exactly one open+close per session |
| `scripts/rag/ingestion/http_fetcher.py` | Behavior: conditional headers unchanged | cached-URL header comparison | Headers identical to per-call approach |

## Risks
- **Risk**: A shared sqlite3 connection used across coroutines could raise `sqlite3.ProgrammingError` if a query somehow spans an `await`. → **Mitigation**: the query has no `await`; keep it synchronous and never await between acquiring and releasing the connection within a single lookup.
- **Risk**: Forgetting to close on the exception path leaks the connection for the process lifetime. → **Mitigation**: `try/finally` around the BFS loop guarantees close.
- **Risk**: Changing observable behavior (header values, 304 handling). → **Mitigation**: the reused connection applies the same WAL/busy-timeout pragmas and `row_factory=True`; assert byte-for-byte equality in tests (REQ-003).
- **Risk**: Added complexity for a Low-priority gain. → **Mitigation**: escape hatch permits leaving per-call behavior if cleanup is not clean.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add optional `db` parameter to `get_conditional_headers` (`scripts/rag/ingestion/http_fetcher.py`) | Completed | — | 20261106 |  |
| 2 | Own one session connection in `crawl_site`, pass through, close on exit (`scripts/rag/ingestion/orchestrator.py`) | Completed | — | 20261106 | Depends on UNK-01/UNK-03 UNK-01/UNK-03 resolved: close() exists helper.py:232; empty-path guard skips session helper |
| 3 | Connection-open-count test + format/lint/type/test verification and commit | Completed | — | 20261106 | Connection-open-count tests: TestSessionConnectionLifecycle |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-134925_01_scripts_rag_ingestion_http_fetcher.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261106-134925_02_scripts_rag_ingestion_orchestrator.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073205_crawl004_reuse-sqlite-connection-crawl-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-094506
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / Acceptance Criteria | `scripts/rag/ingestion/orchestrator.py` | Step 2 | REQ-001 acceptance criteria | connection-open-count test | Confirmed by repository evidence |
| REQ-002 | Required Changes / Constraints | `scripts/rag/ingestion/orchestrator.py` | Step 2 | REQ-002 acceptance criteria | exception-path close test | Confirmed by repository evidence |
| REQ-003 | Constraints / Acceptance Criteria | `scripts/rag/ingestion/http_fetcher.py` | Step 1 | REQ-003 acceptance criteria | header-equality test | Confirmed by repository evidence |
| REQ-004 | AI Implementation Instruction | `scripts/rag/ingestion/http_fetcher.py` | Step 1 | REQ-004 acceptance criteria | backward-compat test | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-134925 -->