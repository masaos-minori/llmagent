## Goal
- Put a trust boundary on crawler redirects: stop following redirects automatically, follow them hop by hop in `fetch_html` with a per-hop policy (same host with an http-to-https upgrade allowed, robots check, and refusal of private, loopback, link-local, and other non-public destinations outside the operator-configured start host), and persist an accepted page under its final URL.

## Priority
High

## Scope
- **In-Scope**:
  - The crawler `httpx.AsyncClient` is built with `follow_redirects=False`; `HttpFetcher.fetch_html` follows redirects manually up to a bounded hop count, applying the hop policy to every hop and to the final URL.
  - Policy helpers in `scripts/rag/ingestion/crawler_utils.py` (redirect-allowed rule, non-public-address check using `ipaddress` and asynchronous name resolution), using the standard library only.
  - The orchestrator passes the start origin and the robots cache into the fetch, marks the final URL visited, and persists under the final accepted URL; refused redirects are logged distinctly.
  - Mock-transport tests (cross-host, loopback, link-local, same-origin upgrade, redirect loop and hop limit) and the crawler trust-boundary documentation.
- **Out-of-Scope**:
  - Authentication for crawled sites, `file://` target restrictions, a new allowlist configuration key (UNK-01), robots policy gaps beyond the per-hop check (`issues/20261108-131232_ragrev014_robots-policy-gaps.md`), a connection-level DNS pinning transport (see Risks).
- **Dependencies**: Fix order against the sibling fetch-path plan:
  - **Depends on**: plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md | phase 2 | both change `HttpFetcher.fetch_html` and the `_process_crawl_url_async` result handling; land the typed fetch result first so the redirect loop is written against it.

## Background
Review finding F-012 (the Issue records Confidence Medium: reading of the code, no live redirect exercised; Step 3 below confirms the code facts but did not run a live redirect either). `CrawlOrchestrator.crawl_site` builds `httpx.AsyncClient(..., follow_redirects=True)` (`scripts/rag/ingestion/orchestrator.py:109-113`); `LinkDiscovery.should_enqueue_link` applies `skip_external` and the robots check to enqueued URLs only (`scripts/rag/ingestion/link_discovery.py:63-84`); `HttpFetcher.fetch_html` returns the final response body without inspecting `resp.url` (`http_fetcher.py:42-70`); `save_http` is called with the requested `url` (`orchestrator.py:254-263`). Facts found while verifying (checked in Step 3): (1) `RobotsCache.is_allowed` returns `True` for any host without a loaded parser, and only the start host is loaded (`orchestrator.py:127-131`, `robots.py:50-56`), so a robots check per hop is effective only for the start host; the robots.txt fetch itself also uses the redirect-following client; (2) `same_origin` compares scheme and `netloc` (`crawler_utils.py:107-110`), so applying it unchanged to redirect hops would refuse an ordinary http-to-https upgrade, which the Issue requires to keep working; (3) `config/crawler.toml` sets `skip_external = true` and `respect_robots = false` by default, so with defaults a cross-host redirect is the only way off the origin and robots enforcement is off; with `skip_external = false` any link, not only a redirect, can point at an internal address. Crawl targets come from operator configuration; the pages, their links and their redirects are untrusted.

## Problem
An open redirect or a malicious page can make the crawler request another host or an internal service (loopback or link-local addresses), and the response is written into the RAG corpus under the requested URL.

## Reason for Change
Fetching attacker-influenced destinations from inside the host is a trust-boundary weakness of the SSRF class even for a read-only crawler.

## Implementation Intent
Take redirect following out of httpx and into `fetch_html`, where each hop is validated before it is requested. The hop policy is: the same hostname as the crawl's start URL (scheme upgrade http to https allowed, downgrade refused, default ports normalized) when `skip_external` is on; otherwise any host whose resolved addresses are all public, with the operator-configured start host always allowed even if internal. Persist under the final accepted URL and mark it visited so the BFS does not fetch it twice.

## Requirements
- `REQ-001`: The crawler client does not follow redirects automatically; `fetch_html` follows at most a fixed number of hops and refuses a loop or an over-long chain with a distinct log.
- `REQ-002`: Every hop and the final URL are checked: same-host rule (with http-to-https upgrade) when external crawling is off; for any non-start host, all resolved addresses must be public (not private, loopback, link-local, reserved, multicast, or unspecified); a refused hop returns a `failed` kind and is logged with the reason.
- `REQ-003`: The per-hop robots check (`is_allowed`) applies when a robots cache is configured; its limitation to hosts with a loaded parser is documented, not changed.
- `REQ-004`: A same-host redirect (including http to https) is followed and the page is persisted under the final accepted URL; the final URL is added to the visited set.
- `REQ-005`: The 304 and conditional-header behavior, retry behavior, and link discovery from fetched pages are unchanged.
- `REQ-006`: Mock-transport tests cover cross-host, loopback (literal and by name), link-local, same-host upgrade, https-to-http downgrade, loop, and hop-limit cases.
- `REQ-007`: The crawler documentation states what is fetched and what is refused, including the DNS-resolution limitation.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Manual redirect loop with per-hop policy in `fetch_html`; final URL in the result | `REQ-001`..`REQ-005` / AC-1..AC-5 | `fetch_html` returns the body without checking `resp.url` (L42-70) (checked in Step 3) | `tests/rag/ingestion/test_crawler_redirects.py` | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | `follow_redirects=False`, pass start origin and robots cache to the fetch, persist under the final URL, mark it visited | `REQ-001`, `REQ-004` / AC-1, AC-4 | Client at L109-113; `save_http(url, ...)` at L254-263 (checked in Step 3) | `tests/rag/ingestion/test_crawler_redirects.py` | Verified |
| `scripts/rag/ingestion/crawler_utils.py` | Modify | Add the redirect-allowed rule and the non-public-address check next to `same_origin` | `REQ-002` / AC-2 | `same_origin` L107-110 compares scheme and netloc (checked in Step 3) | `tests/rag/ingestion/test_crawler_redirects.py` | Verified |
| `tests/rag/ingestion/test_crawler_redirects.py` | Create | New file: mock-transport redirect tests; policy unit tests | `REQ-001`..`REQ-006` / AC-1..AC-6 | New file; the directory `tests/rag/ingestion/` exists (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Crawler trust boundary: what is fetched, what is refused, and the DNS limitation | `REQ-007` / AC-7 | Doc describes conditional GET and robots policy at L72-73, no redirect statement (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/link_discovery.py` | Link-time origin, nofollow, and robots checks the hop policy must stay consistent with | `REQ-002`, `REQ-003` |
| `scripts/rag/ingestion/robots.py` | `RobotsCache.fetch_host` / `is_allowed` semantics (parser only for loaded hosts) | `REQ-003` |
| `scripts/rag/ingestion/crawler.py` | `WebCrawler` wiring and config keys (`skip_external`, `respect_robots`) | `REQ-002` |
| `config/crawler.toml` | Defaults (`skip_external = true`, `respect_robots = false`); not modified | `REQ-002` |
| `tests/rag/ingestion/test_crawler_integration.py` | Existing crawl tests that must pass unchanged | `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`): the client is created with `follow_redirects=False`; a redirect chain longer than the hop limit and a loop both end as `failed` with a distinct log.
- AC-2 (`REQ-002`): a redirect to another host (external crawling off), to `127.0.0.1`, to `localhost` resolving to loopback, to `169.254.169.254`, and to a private range is refused and logged; the start host is never refused for being internal.
- AC-3 (`REQ-003`): with a robots cache that disallows the hop path for the start host, the hop is refused.
- AC-4 (`REQ-004`): an http-to-https redirect on the same host is followed; `save_http` receives the final URL; the final URL is in `visited`; an https-to-http downgrade is refused.
- AC-5 (`REQ-005`): existing `test_crawler_integration.py`, `test_robots.py`, and `test_crawler_retry_boundary.py` pass unmodified (apart from the typed-result updates of the sibling plan).
- AC-6 (`REQ-006`): the new tests fail on HEAD for the refused cases.
- AC-7 (`REQ-007`): the doc states the boundary and limitation; docs checkers pass.

## Tests
- `REQ-001`: loop and hop-limit mock-transport tests.
- `REQ-002`: parametrized cross-host, literal-IP, named-loopback (resolver stubbed), link-local, and private-range tests; start-host-internal allowed.
- `REQ-003`: robots-denied hop.
- `REQ-004`: same-host upgrade persisted under the final URL; downgrade refused.
- `REQ-005`: existing suites unmodified.
- Static: `uv run bandit -r scripts/rag -c pyproject.toml -ll`, `uv run ruff check`, `uv run mypy`.

## Documentation Impact
Yes (`REQ-007`): `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (located via `docs/00_index.md` RAG rows); the sibling `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` also edits this file in different paragraphs. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- With `skip_external` on (the default), allowing only the start hostname (plus the http-to-https upgrade) is the intended reading of "the same origin policy used for links"; a redirect from a bare domain to `www.` is therefore refused and logged, and the operator updates the target URL (UNK-02).
- The operator-configured start host is trusted even if it resolves to a private address; only other hosts face the address check, so internal-docs crawls keep working without a new configuration key.
- Name resolution for the address check happens before the request and is not pinned to the connection, so a DNS-rebinding attacker is not fully excluded; the plan accepts this documented limitation rather than adding a custom transport.
- Overlap judgment (Step 8b): `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`, and `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` are also targets of `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md`; judged a sequencing dependency (ragrev011 first, recorded under Scope Dependencies), compatible otherwise because the changes are to different parts of the same functions and different doc paragraphs.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any non-start internal host is a legitimate crawl target (an allowlist configuration key would be needed) | Owner decision | Default refuses; an allowlist key would be a separate Plan (config, reference table, deploy) | False |
| UNK-02 | Whether redirects between apex and `www.` (or other same-site hostnames) must be accepted | Owner decision and the production target list | Default is the strict same hostname; relaxing it is a one-function change after the owner decides | False |
| UNK-03 | Whether a live redirect from a production target currently occurs | No live request was made | Owner-side log check of the refused-redirect messages after deploy | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Modify | Medium (every crawled fetch; one production caller) | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | High (crawl traversal; `radon`: `crawl_site` C (11)) | 5 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler_utils.py` | Modify | Low (new pure helpers) | 0 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_crawler_redirects.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files, a new test module, runtime-facing crawl behavior). Architecture: `http_fetcher` gains a dependency on the new `crawler_utils` helpers (same package, no cycle: `crawler_utils` imports no crawler component); the orchestrator already imports both; `lint-imports` 6 contracts kept at plan time. Dependency graph: `fetch_html` has one production caller (the orchestrator) and `follow_redirects=True` appears only at `orchestrator.py:112`, so no other client in `scripts/rag` follows redirects (the `RobotsCache` fetch uses the same client). Security design: standard library `ipaddress` and `loop.getaddrinfo`, no new dependency (Issue constraint); a redirect hop is requested only after its policy check; `bandit -ll` is part of validation. Complexity: `fetch_html` B (8) and `crawl_site` C (11); the hop loop and the policy go into small helpers so neither grows past its current band.

Alternatives: (a) an httpx request event hook that raises for a refused hop, kept as an implementation option but not chosen because the final-URL and visited bookkeeping needs the loop anyway; (b) a custom transport that pins resolved addresses to the connection, rejected here as disproportionate (stated limitation); (c) checking only the final URL, rejected (intermediate hops are also requests from inside the host). Chosen: manual per-hop loop with stdlib policy helpers.

Persisted schema check: not applicable. Storing under the final URL changes which `documents.url` is written for redirected pages (a requested URL that redirects is later looked up under the requested URL for conditional headers, so such pages are fetched unconditionally and then deduplicated by the freshness check; recorded in Risks).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Policy unit tests and mock-transport redirect tests, including the refused cases (`REQ-001`..`REQ-006`; `tests/rag/ingestion/test_crawler_redirects.py`)
2. **Phase 2: Policy helpers**
   - [ ] Redirect-allowed rule and non-public-address check (`REQ-002`; `scripts/rag/ingestion/crawler_utils.py`)
3. **Phase 3: Fetch and orchestrator**
   - [ ] Manual redirect loop with the per-hop policy and robots check (`REQ-001`..`REQ-003`, `REQ-005`; `scripts/rag/ingestion/http_fetcher.py`)
   - [ ] `follow_redirects=False`, final-URL persistence, visited marking (`REQ-001`, `REQ-004`; `scripts/rag/ingestion/orchestrator.py`)
4. **Phase 4: Documentation**
   - [ ] State the trust boundary and limitation (`REQ-007`; `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, bandit, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/http_fetcher.py`)

### Release units
**Unit**: ragrev012-core | **Phases**: 2, 3 | **Reason**: turning off automatic redirects without the hop loop would make every redirecting page fail, and the loop needs the helpers.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/crawler_utils.py` | Unit | `uv run pytest tests/rag/ingestion/test_crawler_redirects.py -q -k policy` | policy matrix passes |
| `scripts/rag/ingestion/http_fetcher.py`, `orchestrator.py` | Async integration (mock transport) | `uv run pytest tests/rag/ingestion/test_crawler_redirects.py tests/rag/ingestion/test_crawler_integration.py tests/rag/ingestion/test_robots.py -q` | refused cases fail on HEAD, pass after |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| security | Static | `uv run bandit -r scripts/rag -c pyproject.toml -ll`, `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | no new findings |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: legitimate redirects are refused (apex to `www.`, regional hostnames), shrinking crawls → **Mitigation**: distinct refusal log with the reason; UNK-02 decision; the rule is one function.
- **Risk**: pages that redirect are stored under the final URL, so the next run's conditional-header lookup (by requested URL) misses and the page is fetched unconditionally → **Mitigation**: the freshness check deduplicates by validators; acceptable cost for redirected pages only.
- **Risk**: DNS rebinding between the check and the connection → **Mitigation**: documented limitation; same-host crawls are unaffected; a pinned transport is a separate hardening Plan.
- **Risk**: name resolution inside the event loop blocks → **Mitigation**: use the loop's asynchronous `getaddrinfo` and treat resolution failure as a refusal.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — |  |
| 2 | Phase 2: policy helpers | In Progress | — | — |  |
| 3 | Phase 3: fetch and orchestrator | In Progress | — | — |  |
| 4 | Phase 4: documentation | In Progress | — | — |  |
| 5 | Phase 5: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_04_tests_rag_ingestion_test_crawler_redirects.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-205004_03_scripts_rag_ingestion_crawler_utils.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-205004_01_scripts_rag_ingestion_http_fetcher.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261109-205004_02_scripts_rag_ingestion_orchestrator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261109-205004_05_docs_21_rag_rag_02_02_ingestion_pipeline-crawler.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170101
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/crawler_utils.py`, `tests/rag/ingestion/test_crawler_redirects.py`, `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `orchestrator.py:112` | `scripts/rag/ingestion/http_fetcher.py` | Phase 3 | AC-1 | loop and hop-limit tests | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; `orchestrator.py:112` | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-1 | loop and hop-limit tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_crawler_redirects.py` | Phase 1 | AC-1 | loop and hop-limit tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/ingestion/http_fetcher.py` | Phase 3 | AC-2 | cross-host and internal-address tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/ingestion/crawler_utils.py` | Phase 2 | AC-2 | policy matrix | Explicit in issue |
| REQ-002 | Testing Expectations | `tests/rag/ingestion/test_crawler_redirects.py` | Phase 1 | AC-2 | cross-host and internal-address tests | Explicit in issue |
| REQ-003 | Required Changes 2 (robots); `robots.py:50-56` | `scripts/rag/ingestion/http_fetcher.py` | Phase 3 | AC-3 | robots-denied hop test | Confirmed by repository evidence |
| REQ-003 | Required Changes 2 (robots) | `tests/rag/ingestion/test_crawler_redirects.py` | Phase 1 | AC-3 | robots-denied hop test | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; Acceptance Criteria 2 | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-4 | same-host upgrade test | Explicit in issue |
| REQ-004 | Acceptance Criteria 2 | `tests/rag/ingestion/test_crawler_redirects.py` | Phase 1 | AC-4 | same-host upgrade test | Explicit in issue |
| REQ-005 | Constraints; Acceptance Criteria 3 | `scripts/rag/ingestion/http_fetcher.py` | Phase 3 | AC-5 | existing crawl suites | Explicit in issue |
| REQ-006 | Required Changes 4; Testing Expectations | `tests/rag/ingestion/test_crawler_redirects.py` | Phase 1 | AC-6 | new redirect tests | Explicit in issue |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Phase 4 | AC-7 | docs gates | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-205004 -->