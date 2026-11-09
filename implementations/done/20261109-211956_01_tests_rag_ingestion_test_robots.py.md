## Goal

Add the test coverage the Plan requires before the production change (Plan Phase 1): outcome-table unit tests for `RobotsCache`, `ensure_host` (new) idempotence, the per-request redirect flag, the orchestrator start-URL refusal, the external-host robots fetch, and the inverted transport-error test (REQ-001..REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

Row 3 of the frozen target table. `Related Tests` column is `self`. Not treated as a companion document: `tests/rag/ingestion/test_robots.py` is named in `Related Tests` of two target rows (robots.py and orchestrator.py), so it gets its own procedure.

## Assumptions
- Line numbers revalidated 20261109 and re-adversarially-verified 20261110: `test_fetch_host_404_falls_back_allow_all` def at L53, `test_fetch_host_transport_error_falls_back_allow_all` def at L65, `TestOrchestratorEagerFetch` class at L127 — all match the current file.
- The orchestrator class is `CrawlOrchestrator` (`orchestrator.py` L65), not "IngestionOrchestrator" (correction from the 20261110 verification pass).
- ragrev012 has landed (commit 91a807739): `_process_crawl_url_async` already takes `origin` and `robots_cache` parameters; the guard tests must exercise the real `_process_crawl_url_async` body, so they cannot reuse `TestOrchestratorEagerFetch._orchestrator`, which stubs that method with an `AsyncMock`. The new harness mocks `http_fetcher`/`content_extractor`/`persister`/`language_resolver` and leaves `_process_crawl_url_async` real.
- The 404 test stays unmodified: the Plan's outcome table keeps allow-all for 404 and other 4xx except 401/403. Only the transport-error test is renamed and inverted (Plan Assumptions).
- Plan Phase 1 is tests-first: the new outcome/denial tests are expected to fail on HEAD and pass after Phases 2-3 (Validation plan row 2).

## Design decisions
- New tests extend the existing classes and stub style in this file: `MagicMock`/`AsyncMock`-based client stubs as in `TestRobotsCache` (L42-46: `client = MagicMock()`, `client.get = AsyncMock(return_value=resp)`, request counting via `client.get.call_count` at L50) rather than a new fixture layer.
- Orchestrator tests (start-URL refusal, external-host fetch, policy-off) live in this file following the pattern of `TestOrchestratorEagerFetch` (L127+); `tests/rag/ingestion/test_crawler_integration.py` is the secondary integration surface named by the Plan's Validation plan.

## Alternatives considered
- Merging this row as a companion of the robots.py row — rejected by the companion rule (file named in two target rows' `Related Tests`).

## Implementation
### Target file
`tests/rag/ingestion/test_robots.py`

### Procedure
1. Outcome-table unit tests (Plan Tests row 1, AC-1): stubbed-client cases (status code / raised `httpx.RequestError` on the mocked `client.get`) — 401 → disallow-all, 403 → disallow-all, 500 → disallow-all, connection error → disallow-all; 404 → allow-all, 410 → allow-all; 200 with `Disallow: /private` disallows only that path.
2. Idempotence test (AC-2): a second `ensure_host` (new) call for the same host issues no request (`client.get.call_count` assertion, pattern at L50).
3. Redirect-flag test (AC-4): the robots request is issued with `follow_redirects=True` even when the client was created with `follow_redirects=False` — assert `client.get` was called with `follow_redirects=True` via `call_args`.
4. Rename and invert `test_fetch_host_transport_error_falls_back_allow_all` (L65) to assert disallow-all on transport error (Plan Assumptions: deliberate policy change of a pinned contract; rename, not delete).
5. Orchestrator tests (Plan Tests row 2, AC-2/AC-3/AC-5):
   - Start-URL refusal: `respect_robots` on, start host's robots disallow the start URL → the start URL is never requested and a distinct skip log line is emitted.
   - External-host link: a link to a second host triggers exactly one robots fetch for that host before the URL is requested.
   - Policy off: no robots request occurs and behavior is unchanged.
6. Keep `TestOrchestratorEagerFetch` (L127+) and `TestLinkDiscoveryRobots` (L74+) unmodified (AC-5: existing link-filter and eager-fetch tests pass unchanged).

### Method
pytest additions in the existing file style; mock transport reused for status/outcome control; orchestrator cases drive `CrawlOrchestrator.crawl_site` with the real `_process_crawl_url_async` and mocked fetch/persist dependencies (not the `TestOrchestratorEagerFetch._orchestrator` helper, which stubs `_process_crawl_url_async`; stub the cache's `ensure_host`/`fetch_host` to keep the real `httpx.AsyncClient` from issuing network requests, as the eager-fetch spy does).

### Details
- Disallow-all assertions use `is_allowed(url) is False` for representative paths; allow-all assertions use `is_allowed(url) is True`.
- Distinct skip log assertion matches the new guard's log line defined in procedure 03; align wording when both land.

## Compatibility considerations
- New tests fail on HEAD by design (Phase 1 lands before Phases 2-3 in the same cycle); do not land this file alone onto a release branch.

## Security considerations
- Tests pin fail-closed behavior so a future regression to fail-open is caught (Plan Risks row 3).

## Rollback considerations
- Revert with procedures 02 and 03 as one set; reverting this file alone restores the old pinned contract.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_robots.py -q -k "RobotsCache"` — outcome table asserted after Phase 2.
- `uv run pytest tests/rag/ingestion/test_robots.py tests/rag/ingestion/test_crawler_integration.py -q` — new tests fail on HEAD, pass after Phases 2-3.
- `uv run pytest tests/rag/ingestion -q` — green at cycle end.
- Full validation sequence: `rules/toolchain.md`.

## Completion criteria
- All outcome, idempotence, redirect-flag, refusal, external-host, and policy-off tests pass after Phases 2-3; the transport-error test is renamed and inverted; AC-5 existing tests pass unmodified.

## Out of Scope
- Changes to `tests/rag/ingestion/test_crawler_integration.py` beyond any integration case the Plan's Validation plan requires — coordinate with procedure 03.
- Production code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-10 | 2026-11-10 | tests-first per Plan Phase 1; red on HEAD by design outcome/idempotence/redirect-flag/guard tests written; transport-error test renamed+inverted |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-10 | tests-first per Plan Phase 1: red on HEAD (9 predicted failures), green after procedures 02-03 (50 targeted / 324 ingestion pass) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-10 | full suite 12121 passed; diff-cover 100% on changed lines; ruff/mypy/lint-imports/bandit/module-size/docstrings green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-10 | N/A: no documentation in scope for this procedure |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20261108-131232_ragrev014_robots-policy-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170335_ragrev014_robots-policy-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-09 21:19:56
- **Related target files**: tests/rag/ingestion/test_robots.py