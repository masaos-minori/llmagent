## Goal

Move the existing `fetch_html` tests and the `None` mock to the typed result and add the crawl-level tests that pin the new behavior: a 304 parent still reaches a changed child, no extra request at the depth limit, and a failed fetch distinct from a 304 (`REQ-001`: typed kinds asserted; `REQ-002`: unconditional discovery fetch and depth limit; `REQ-003`: 304 page not persisted, link filters still apply; `REQ-004`: failed distinct from 304; `REQ-005`: changed child ingested after a 304 parent).

## Scope
**Release unit**: ragrev011-core

- In scope: `tests/rag/ingestion/test_crawler_integration.py` (updates of the four direct `fetch_html` tests and the `AsyncMock(return_value=None)` test, plus one new test class).
- Out of scope: production code (documents `01` and `02`), `tests/rag/ingestion/test_robots.py` (patches `_process_crawl_url_async` and must stay green unmodified), and the other test classes of this file.
- Plan: `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` (Plan step 1); the file is not a companion because two other rows name it in `Related Tests`.

## Assumptions

- Re-verified at generation time (by symbol): `TestHttpRetryOnTransientFailure` asserts `result is None` after retry exhaustion and unpacks a tuple after a retry success; `TestResponseSkippingContentFetch` asserts `result is None` for a 304 and unpacks a tuple for the header test; `TestSessionConnectionLifecycle.test_headers_lookup_uses_session_connection` mocks `fetcher.fetch_html = AsyncMock(return_value=None)` and asserts a single awaited call plus the conditional headers.
- Names created by documents `01` and `02` (`Fetched`, `NotModified`, `FetchFailed`, the log messages) come from earlier-`seq` siblings; this document runs after them in `seq` order, so the old-shape tests are updated together with the production change inside the release unit.
- `TestMaxPagesBoundaryCondition::test_max_pages_warning_logged` serves 304 children at `depth == max_depth` and stays valid unmodified (no discovery request at the limit).
- `TestSessionConnectionLifecycle._seed_documents` seeds `documents(url, etag, last_modified)` with one row for `http://example.com/page` (`etag-1`, `Mon, 01 Jan 2024 00:00:00 GMT`) and is reusable as a static method; its sibling `_rag_config` shows how to point `rag_db_path` and `rag_src_dir` at `tmp_path`.
- Overlap: this file is also a target of ragrev013 (an in-flight budget-stop test) and ragrev018 (a `None` `save_http` caller test); compatible, each adds its own class or test. Locate tests by name, not line number.

## Design decisions

- Keep every existing assertion's intent and change only the shape: `FetchFailed()`/`NotModified()` instances (`isinstance` or equality, since they are frozen dataclasses) and `Fetched` attributes in place of tuple unpacking.
- For the mocked-`fetch_html` header test, return `FetchFailed()`, not `NotModified()`: a `NotModified` below the depth limit would trigger the discovery fetch and break its single-await assertion.

## Alternatives considered

- Add the crawl tests to `TestMaxPagesBoundaryCondition`: rejected; a separate class keeps the 304-discovery cases and their helper together.

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_integration.py`

### Procedure
1. Import `FetchFailed`, `Fetched`, and `NotModified` from `rag.ingestion.http_fetcher` where the tests use them (local imports, matching the file's style).
2. In `TestHttpRetryOnTransientFailure`, assert `result == FetchFailed()` after retry exhaustion and read `Fetched` attributes (`result.html`, `result.etag`) after the retry success, asserting `isinstance(result, Fetched)` first.
3. In `TestResponseSkippingContentFetch`, assert `result == NotModified()` for the 304 test, and `isinstance(result, Fetched)` with `result.etag == "abc123"` in the conditional-headers test.
4. In `TestSessionConnectionLifecycle.test_headers_lookup_uses_session_connection`, change the mock to `AsyncMock(return_value=FetchFailed())`.
5. Add `TestNotModifiedLinkDiscovery` (new) with the crawl tests listed under Method.

### Method
- `TestNotModifiedLinkDiscovery` (new): a `_page` helper like `TestMaxPagesBoundaryCondition._page`; seed the start URL `http://example.com/page` with `TestSessionConnectionLifecycle._seed_documents`; build the config with `rag_db_path` and `rag_src_dir` under `tmp_path`, `max_depth = 1`, `skip_external = True`.
  - 304 parent: a `respx` route for the start URL whose side effect returns 304 when the request carries `If-None-Match` and a 200 page linking to `/child` and to a cross-origin URL otherwise; a 200 route for `/child`. Assert the request sequence (conditional GET, unconditional GET, child GET), that exactly one file is persisted and it is the child's, that the start page was not persisted, and that the cross-origin link was not requested (`REQ-002`, `REQ-003`, `REQ-005`).
  - Depth limit: the same setup with `max_depth = 0`; assert exactly one request (the conditional GET) and no persisted file (`REQ-002`).
  - Failed versus 304: a start route that raises `httpx.ConnectError` with `fetch_retry = 1`; assert no link is requested, a warning containing `fetch failed, subtree not discovered` is logged, and in the 304 case an info record containing `not modified` is logged instead (`REQ-004`), using `caplog` at the `rag.ingestion.orchestrator` logger.
- Assert on counts and paths read from `respx.calls` and `tmp_path`, not on private orchestrator state.

### Details
- The 304 parent test must fail on the unmodified code (the crawl ends after one request); confirm once before applying document `02`, if the Plan's tests-first order is followed, by running the new class against HEAD.
- Run `uv run python tools/check_mock_patch_targets.py` after the edit.

## Compatibility considerations

N/A: test-only change; no public test helper or fixture is renamed.

## Security considerations

N/A: test-only change; all HTTP is mocked with `respx`.

## Rollback considerations

N/A: revert the commit (together with documents `01` and `02`, since the old-shape tests would fail against the typed result).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q`, then `uv run pytest tests/rag/ingestion -q`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria

- No test in the file asserts `result is None` for `fetch_html`; the typed kinds are asserted for 200, 304, and retry exhaustion.
- The 304-parent crawl test ingests the changed child and persists nothing for the parent; the depth-limit test makes no second request; the failed-versus-304 test distinguishes the two log messages.
- `test_robots.py` and the rest of `tests/rag/ingestion` pass unmodified.

## Out of Scope

- Production code and documentation, the empty-content and language early returns, and tests for redirect or robots behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the four direct `fetch_html` tests and the `None` mock to the typed result | Pending | — | — | |
| 2 | Add `TestNotModifiedLinkDiscovery` (new) (304 parent, depth limit, failed versus 304) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) together with documents `01` and `02` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (typed kinds asserted), `REQ-002` (discovery fetch and depth limit), `REQ-003` (304 page not persisted), `REQ-004` (failed distinct from 304), `REQ-005` (changed child ingested)
- **Source issue**: issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-143141
- **Related target files**: `tests/rag/ingestion/test_crawler_integration.py`
