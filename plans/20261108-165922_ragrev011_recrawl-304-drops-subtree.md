## Goal
- Make a re-crawl keep discovering a page's subtree when the page answers 304 Not Modified: `fetch_html` returns a typed result that separates fetched, not-modified, and failed outcomes, and for a not-modified page above the depth limit the orchestrator fetches the body unconditionally, discovers links from it, and does not re-persist the page.

## Priority
High

## Scope
- **In-Scope**:
  - A typed fetch result in `scripts/rag/ingestion/http_fetcher.py` (`fetched` / `not_modified` / `failed`) replacing the `tuple | None` return of `fetch_html`, with every caller and test updated (the repository has a no-compatibility-shim policy, so no parallel old-shape function is kept).
  - In `scripts/rag/ingestion/orchestrator.py`, handling of `not_modified`: when `depth < max_depth`, fetch the page unconditionally (no validator headers), run `enqueue_links` on that body, and skip extraction, persistence, and the persisted-page budget count; `failed` is reported distinctly (log level and message).
  - A crawl-level test with a 304 start page and a new child, and updates of the existing fetch tests; the crawler documentation.
- **Out-of-Scope**:
  - Redirect handling (sibling `issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md`), robots policy, adding a stored link table or persisting HTML, and the other early returns before `enqueue_links` (see Unknowns).
- **Dependencies**: Related, no required order: the ragrev012 work (same fetch path in `http_fetcher.py` and the orchestrator; coordinate when both are implemented).

## Background
Review finding F-005. In `_process_crawl_url_async` (`scripts/rag/ingestion/orchestrator.py:216-265`) `if result is None: return` precedes `enqueue_links`; `fetch_html` returns `None` for a 304 and for retry exhaustion (`scripts/rag/ingestion/http_fetcher.py:42-70`); `get_conditional_headers` sends `If-None-Match` / `If-Modified-Since` for stored pages (L72-122), so on the second crawl the start page answers 304 and the crawl ends after one page. Corrections found while verifying (checked in Step 3): (1) the Issue's "enqueue links from the stored page content" is not possible with what is persisted: the crawl JSON written by `CrawlPersister.save_http` carries only extracted text and code blocks (`content_extractor.extract_content` returns `(title, text, code_blocks)`), `documents` stores only `etag`, `last_modified`, `fetched_at`, and chunks hold text, so no stored artifact contains the page's anchors; (2) two further early returns precede `enqueue_links` and also hide a subtree: empty extracted content (L243-246) and an unsupported language (L248-252). Existing tests assert the tuple/`None` shape (`tests/rag/ingestion/test_crawler_integration.py:55-152` call `fetch_html` directly; L615-620 mocks it with `None`).

## Problem
Pages added or changed deeper in a site are never discovered after the first crawl whenever an ancestor page is unchanged, and a transient fetch failure of an index page hides its subtree for that run.

## Reason for Change
Incremental crawling is the normal operating mode, so the discovery loss affects every site that supports conditional requests.

## Implementation Intent
Keep persisted data unchanged and pay the cost only where discovery needs it: a not-modified page that can still enqueue links (`depth < max_depth`) is fetched once more without validator headers, its HTML is used for `enqueue_links` only, and nothing is persisted. The typed result makes the three outcomes explicit so the orchestrator never infers meaning from `None`.

## Requirements
- `REQ-001`: `fetch_html` returns a typed result that distinguishes fetched (html, etag, last_modified), not-modified, and failed; every caller and test uses it.
- `REQ-002`: For a not-modified page with `depth < max_depth`, the orchestrator fetches the body without conditional headers and enqueues its links; for `depth >= max_depth` it does no extra request.
- `REQ-003`: A not-modified page is not extracted, not persisted, and does not increment the persisted-page budget; the scheduled-URL bound, depth limit, link filtering (origin, nofollow), and robots policy still apply to the discovered links.
- `REQ-004`: A failed fetch is reported distinctly from a 304 (separate log message and level, distinct result kind) and enqueues nothing.
- `REQ-005`: A second crawl whose start page answers 304 still reaches and ingests a changed child page.
- `REQ-006`: The crawler documentation states that a not-modified page is re-fetched for link discovery only and is not persisted.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Typed `fetch_html` result with `fetched` / `not_modified` / `failed` | `REQ-001`, `REQ-004` / AC-1, AC-4 | `fetch_html` returns `None` for 304 (L55-61) and for retry exhaustion (L70) (checked in Step 3) | `tests/rag/ingestion/test_crawler_integration.py` | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Branch on the typed result; unconditional discovery fetch for not-modified pages; distinct failed handling | `REQ-002`..`REQ-005` / AC-2..AC-5 | `if result is None: return` at L237-238 before `enqueue_links` at L265 (checked in Step 3) | `tests/rag/ingestion/test_crawler_integration.py` | Verified |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Update the direct `fetch_html` tests (L55-152) and the `None` mock (L615-620) to the typed result; add the 304-parent crawl test, depth-limit test, failed-vs-304 test | `REQ-001`..`REQ-005` / AC-1..AC-5 | Tests at L103-125 (304) and L600-625 assert the old shape (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Correct "If a 304 response is received, saving the file is skipped" (L72) and the non-persisting-outcomes note (L42) | `REQ-006` / AC-6 | L42 and L72 describe 304 as skipped (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/link_discovery.py` | `enqueue_links` (`depth >= max_depth` early return, origin/nofollow/robots filtering); unchanged | `REQ-002`, `REQ-003` |
| `scripts/rag/ingestion/crawl_persister.py` | `save_http` persists extracted text only, no links | Scope |
| `scripts/rag/ingestion/content_extractor.py` | `extract_content` output (no anchors) | Scope |
| `scripts/rag/ingestion/crawler.py` | `WebCrawler` wiring of the orchestrator | `REQ-001` |
| `tests/rag/ingestion/test_robots.py` | Orchestrator tests that patch `_process_crawl_url_async`; must stay green | `REQ-003` |

## Acceptance Criteria
- AC-1 (`REQ-001`): the three outcomes are distinct result kinds; no remaining `result is None` check on `fetch_html`.
- AC-2 (`REQ-002`): with a start page at depth 0 and `max_depth >= 1`, a 304 start page triggers one unconditional GET of the same URL and its links are enqueued; at `depth == max_depth` no second request is made.
- AC-3 (`REQ-003`): no `save_http` call and no persisted-count increment for the 304 page; link filters, robots, and the scheduling bound apply to the enqueued links (test asserts a cross-origin link is not enqueued).
- AC-4 (`REQ-004`): a failed fetch logs a distinct message and enqueues nothing; a 304 logs the not-modified message.
- AC-5 (`REQ-005`): the mock-transport crawl test ingests the changed child.
- AC-6 (`REQ-006`): the doc states the behavior; docs checkers pass.

## Tests
- `REQ-001`/`REQ-004`: direct `HttpFetcher.fetch_html` tests for 200, 304, and retry exhaustion returning the typed kinds.
- `REQ-002`/`REQ-003`/`REQ-005`: async orchestrator test with a mock transport (304 conditional response for the start page, 200 for the unconditional repeat, new child page 200) asserting persisted pages, request sequence, and budget counts; depth-limit variant.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
Yes (`REQ-006`): `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (located via `docs/00_index.md` RAG rows), intent and failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- An unconditional second GET of an unchanged page above the depth limit is acceptable (bandwidth only; no re-embedding): the alternative that avoids it needs a persisted link list or HTML, a schema or storage change that belongs in its own Plan (UNK-01).
- The unconditional discovery fetch uses the same crawl delay and concurrency semaphore as any fetch and counts toward the scheduled-URL bound only through the links it enqueues, not as a new page.
- The typed result changes the signature of a public method of `HttpFetcher`; callers are the orchestrator and tests only (rg of `fetch_html` in `scripts/` and `tests/`, checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner prefers persisting a link list (new storage) over a second GET per unchanged index page | Owner preference and request-volume tolerance | Default is the second GET; a stored link list would be a separate persisted-schema Plan | False |
| UNK-02 | Empty-content and unsupported-language pages also return before `enqueue_links` (orchestrator L243-252), hiding their subtrees | Intended behavior unknown | Reported to the owner; candidate separate Issue; not changed here | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Medium (fetch result contract; one production caller) | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | High (crawl traversal; `radon`: `crawl_site` C (11)) | 5 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_integration.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files; a method return contract changes). Architecture: `orchestrator` imports `http_fetcher` and `link_discovery` (already present); no new edges; `lint-imports` 6 contracts kept at plan time. Dependency graph: `fetch_html` has one production caller (`orchestrator.py:236`) and test callers in `test_crawler_integration.py`; `_process_crawl_url_async` is only scheduled by `_drain_queue_to_tasks`. Historical: `orchestrator.py` is among the highest-churn RAG ingestion files in 30 days (5 commits), so the diff is kept to the function and one helper. Complexity: `fetch_html` B (8), `_process_crawl_url_async` A (5); the discovery fetch goes into a small private method to keep the main function at A.

Alternatives: (a) persist a link list or the HTML for later discovery, rejected here (storage change; UNK-01); (b) always fetch without conditional headers and compare validators locally, rejected (gives up the bandwidth benefit for leaf pages and changes the conditional-GET contract); (c) keep the `tuple | None` return and add a second function, rejected (no-compat-shim policy). Chosen: typed result plus targeted unconditional discovery fetch.

Persisted schema check: not applicable (no DDL).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Update the existing `fetch_html` and `None`-mock tests to the typed result and add the 304-parent, depth-limit, failed-vs-304 tests (`REQ-001`..`REQ-005`; `tests/rag/ingestion/test_crawler_integration.py`)
2. **Phase 2: Typed fetch result**
   - [ ] Typed result with the three outcomes (`REQ-001`, `REQ-004`; `scripts/rag/ingestion/http_fetcher.py`)
3. **Phase 3: Orchestrator discovery for not-modified pages**
   - [ ] Branch on the outcome, unconditional discovery fetch, distinct failed handling (`REQ-002`..`REQ-005`; `scripts/rag/ingestion/orchestrator.py`)
4. **Phase 4: Documentation**
   - [ ] Update the conditional-GET and budget description (`REQ-006`; `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/orchestrator.py`)

### Release units
**Unit**: ragrev011-core | **Phases**: 2, 3 | **Reason**: the typed result breaks the orchestrator and tests until the orchestrator branches on it.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Unit | `uv run pytest tests/rag/ingestion/test_crawler_integration.py -q -k "fetch or 304 or retry"` | typed kinds asserted |
| `scripts/rag/ingestion/orchestrator.py` | Async integration (mock transport) | `uv run pytest tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q` | 304-parent test fails on HEAD, passes after |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: the discovery GET doubles requests for unchanged index pages on every re-crawl → **Mitigation**: limited to `depth < max_depth`; same delay and concurrency control; UNK-01 records the alternative.
- **Risk**: an unconditional GET returns changed content that is then not persisted this run (the next run's conditional header still matches the stale stored validators, so the page is re-fetched normally and persisted then) → **Mitigation**: acceptable lag of one run; the Plan keeps "do not re-persist unchanged documents" as the Issue requires.
- **Risk**: changing a return type breaks unseen callers → **Mitigation**: rg shows only the orchestrator and tests; mypy covers the rest.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Pending | — | — | |
| 2 | Phase 2: typed fetch result | Pending | — | — | |
| 3 | Phase 3: orchestrator discovery for not-modified pages | Pending | — | — | |
| 4 | Phase 4: documentation | Pending | — | — | |
| 5 | Phase 5: deployment and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165922
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/test_crawler_integration.py`, `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `http_fetcher.py:55-70` | `scripts/rag/ingestion/http_fetcher.py` | Phase 2 | AC-1 | typed-kind fetch tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-1 | typed-kind fetch tests | Explicit in issue |
| REQ-002 | Required Changes 2 (corrected: no stored links exist) | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-2 | 304-parent and depth-limit tests | Derived from confirmed evidence |
| REQ-002 | Testing Expectations | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-2 | 304-parent and depth-limit tests | Explicit in issue |
| REQ-003 | Constraints | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-3 | persisted-count and filter assertions | Explicit in issue |
| REQ-003 | Constraints | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-3 | persisted-count and filter assertions | Explicit in issue |
| REQ-004 | Acceptance Criteria 2 | `scripts/rag/ingestion/http_fetcher.py` | Phase 2 | AC-4 | failed-vs-304 test | Explicit in issue |
| REQ-004 | Acceptance Criteria 2 | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-4 | failed-vs-304 test | Explicit in issue |
| REQ-004 | Acceptance Criteria 2 | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-4 | failed-vs-304 test | Explicit in issue |
| REQ-005 | Acceptance Criteria 1 | `tests/rag/ingestion/test_crawler_integration.py` | Phase 1 | AC-5 | 304-parent crawl test | Explicit in issue |
| REQ-006 | Documentation Impact; doc L42, L72 | `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Phase 4 | AC-6 | docs gates | Confirmed by repository evidence |
