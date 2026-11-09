## Goal
- Make the opt-in robots.txt policy enforce itself: define one outcome table (200, 404 and other 4xx, 401/403, 5xx, network error), fetch robots lazily for every host before its first page request, and refuse a disallowed URL at fetch time (including the start URL), keeping one fetch per host.

## Priority
Medium

## Scope
- **In-Scope**:
  - `RobotsCache` in `scripts/rag/ingestion/robots.py`: one outcome-to-policy mapping (fail-closed for 401, 403, 5xx, and network errors; allow for 404 and other 4xx; parse for 200), an `ensure_host` entry for any host, and an explicit per-request redirect setting for the robots fetch.
  - `scripts/rag/ingestion/orchestrator.py`: before requesting a URL, ensure its host's robots and refuse a disallowed URL (this covers the start URL and hosts reached through external links); the eager start-host preload stays.
  - Tests for each outcome and an external-host orchestrator test; updates of the two documentation places that describe the policy.
- **Out-of-Scope**:
  - Crawl-delay handling, the redirect policy itself (`plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md`), making the policy non-opt-in, cache expiry (see Unknowns).
- **Dependencies**: Related, no required order: the ragrev012 plan (same fetch path; its per-hop robots check can call `ensure_host` once this plan lands).

## Background
Review finding F-014. `RobotsCache.fetch_host` (`scripts/rag/ingestion/robots.py:30-48`) parses an empty rule list (allow all) for every status other than 200 and installs an allow-all parser on `httpx.RequestError` or `ValueError`; `is_allowed` returns `True` when the host has no parser (L50-56); the orchestrator preloads only the start host (`orchestrator.py:128-134`); `LinkDiscovery.should_enqueue_link` consults `is_allowed` synchronously at enqueue time (`link_discovery.py:65-84`) and nothing fetches robots for other hosts or checks the start URL itself. The code parses the body with `RobotFileParser.parse()` instead of `read()`, so the standard library's 401/403 handling is not in effect. Facts found while verifying (checked in Step 3): (1) the existing tests pin the current fail-open behavior for a transport error (`tests/rag/ingestion/test_robots.py:65`, `test_fetch_host_transport_error_falls_back_allow_all`), so changing it is a deliberate policy change of an existing contract; (2) `enqueue_links` is synchronous, so a robots fetch cannot happen there, and the authoritative check has to sit at fetch time in the async orchestrator; (3) `RobotsCache` lives on `WebCrawler` and its `_parsers` dict never expires, so a fail-closed outcome cached for a transient error lasts for the crawler instance; (4) the sibling redirect plan turns the shared client's `follow_redirects` off, so the robots fetch must set `follow_redirects=True` itself per request to keep the standard behavior of following robots redirects.

## Problem
A host answering 401, 403, or 5xx for robots.txt is crawled as if everything were allowed, and hosts reached through external links are crawled without any robots check although the policy is switched on.

## Reason for Change
The policy is opt-in, but when enabled the operator expects it to be enforced; failing open on error contradicts that (RFC 9309 treats an unavailable robots.txt as disallow).

## Implementation Intent
Keep `is_allowed` synchronous for link filtering and add `ensure_host(origin, client)` (async, idempotent per host) that applies the outcome table. In `_process_crawl_url_async`, when a robots cache is configured, `await ensure_host` for the URL's origin and skip the URL with a distinct log when `is_allowed` is false. A fail-closed outcome installs a disallow-all parser, so the host is fetched at most once per cache lifetime.

## Requirements
- `REQ-001`: Outcome table in one place: 200 parses the body; 404 and other 4xx except 401/403 allow all; 401 and 403 disallow all; 5xx and network errors (including timeouts) disallow all; each outcome is logged with its class.
- `REQ-002`: `ensure_host` fetches robots at most once per host (cached), for any host, and is what the orchestrator calls before the first request to that host.
- `REQ-003`: A URL whose path is disallowed (including the start URL) is not requested and is logged distinctly; with no robots cache configured behavior is unchanged.
- `REQ-004`: The robots fetch sets `follow_redirects=True` per request, independent of the client-level setting.
- `REQ-005`: The policy stays opt-in via `respect_robots`; link filtering via `is_allowed` and the eager start-host preload keep working.
- `REQ-006`: The two documentation places describe the per-outcome policy and the fetch-time enforcement.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Modify | Outcome table, `ensure_host`, per-request redirect setting, fail-closed parsers | `REQ-001`, `REQ-002`, `REQ-004` / AC-1, AC-2, AC-4 | Non-200 and errors allow all (L30-48); unknown host returns `True` (L50-56) (checked in Step 3) | `tests/rag/ingestion/test_robots.py` | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Ensure the host's robots and refuse a disallowed URL before the request in `_process_crawl_url_async` | `REQ-002`, `REQ-003`, `REQ-005` / AC-2, AC-3, AC-5 | Preload only at L128-134 (revalidated 20261109: shifted from L127-131 by the landed ragrev011 commit); no per-URL robots check in `_process_crawl_url_async` (checked in Step 3) | `tests/rag/ingestion/test_robots.py` | Verified |
| `tests/rag/ingestion/test_robots.py` | Modify | Tests for 200, 401, 403, 404, 500, and connection error; external-host orchestrator test; start-URL refusal; update the transport-error test | `REQ-001`..`REQ-005` / AC-1..AC-5 | `TestRobotsCache` pins allow-all on 404 and transport error (L53-72); `TestOrchestratorEagerFetch` at L127 (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Robots paragraph (L56-61) and the "Robots.txt Policy" bullet (L75): per-outcome policy and fetch-time enforcement | `REQ-006` / AC-6 | L56-61 describes only the start-host preload and enqueue-time skipping (revalidated 20261109: shifted from L54-59/L73 by the landed ragrev011 commit) | docs gates | Verified |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | `respect_robots` description (L35) | `REQ-006` / AC-6 | L35 states start host only (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/link_discovery.py` | Synchronous `is_allowed` use at enqueue time; unchanged | `REQ-003`, `REQ-005` |
| `scripts/rag/ingestion/crawler.py` | `RobotsCache` creation per `WebCrawler` (L84) and the `respect_robots` flag | `REQ-005` |
| `scripts/rag/ingestion/crawler_utils.py` | `normalize_url` and origin helpers used to derive the host key | `REQ-002` |

## Acceptance Criteria
- AC-1 (`REQ-001`): mock transport returns 401, 403, 500, and a connection error and each host is disallow-all; 404 and 410 allow all; 200 with `Disallow: /private` disallows only that path.
- AC-2 (`REQ-002`): a second call for the same host issues no request; a URL on a second host triggers exactly one robots fetch before that URL is requested.
- AC-3 (`REQ-003`): a disallowed start URL is not requested and a distinct skip is logged; with `respect_robots` off, no robots request occurs.
- AC-4 (`REQ-004`): the robots request is issued with `follow_redirects=True` even when the client was created with `follow_redirects=False`.
- AC-5 (`REQ-005`): the existing link-filtering and eager-fetch tests pass unmodified.
- AC-6 (`REQ-006`): both docs state the outcome table; docs checkers pass.

## Tests
- `REQ-001`/`REQ-002`/`REQ-004`: `RobotsCache` unit tests with a mock transport for each status, idempotence, and the redirect flag.
- `REQ-003`/`REQ-005`: orchestrator tests with a robots-denied start URL, an external-host link (second robots fetch), and the policy-off case.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
Yes (`REQ-006`): `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (also edited by the ragrev011 and ragrev012 plans in other paragraphs) and `docs/21_rag/rag_05_01-configuration-reference.md` (located via `docs/00_index.md` RAG rows), intent and failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- The outcome table follows RFC 9309 section 2.3.1 (unreachable or server-error robots.txt means disallow; client-error other than auth means no restrictions) and the Issue's examples; the owner's open question about other 4xx is resolved here to "allow" (the common convention) and can be overridden by plan amendment (UNK-01).
- Fail-closed on a network error is a deliberate change from the current pinned fail-open behavior (`test_fetch_host_transport_error_falls_back_allow_all` is renamed and inverted in the same change); the consequence is that a transient robots.txt outage skips that host for the crawler instance's lifetime.
- Overlap judgment (Step 8b, revalidated 20261109): `scripts/rag/ingestion/orchestrator.py` (now with the ragrev012, ragrev013, and ragrev018 plans — the ragrev011 overlap closed when ragrev011 landed at commit b2726cf75) and `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` (with the ragrev012 plan) are shared; judged compatible with no required order: this plan edits the per-URL guard at the start of `_process_crawl_url_async` and docs paragraph L56-61/L75, the others edit the fetch result handling, the `save_http` result handling, the client construction, the `crawl_site` loop exit, and other doc paragraphs. If ragrev012 lands first, its per-hop robots check should then call `ensure_host`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner confirmation of the outcome table, notably fail-closed on network errors and allow on other 4xx | Owner decision | Default per RFC 9309 and the Issue; a different rule is a one-function change | False |
| UNK-02 | Whether `RobotsCache` entries should expire (a transient 5xx otherwise disallows a host for the instance lifetime) | Crawler run model (one process per run assumed) | Non-blocking; add an expiry or a per-`crawl_site` reset in a follow-up if long-lived crawlers exist | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Modify | Low (opt-in feature; one cache class) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | High (crawl traversal; `radon`: `_process_crawl_url_async` A (5)) | 5 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_robots.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files; crawl policy change). Architecture: `robots.py` imports only `httpx` and the standard library; the orchestrator already holds the cache through `LinkDiscovery`; `lint-imports` 6 contracts kept at plan time, no new import edges (the orchestrator reads the cache the way it already does via `getattr(self._link_discovery, "_robots_cache", None)` at `orchestrator.py:130`). Dependency graph: `RobotsCache` callers are `crawler.py` (construction), `link_discovery.py` (`is_allowed`), and `orchestrator.py` (`fetch_host`); tests in `test_robots.py`. Complexity: `fetch_host` A (4), `is_allowed` A (2); the outcome table lives in one small mapping function so the methods stay at A.

Alternatives: (a) make `is_allowed` async and fetch on demand, rejected (`enqueue_links` is synchronous and its tests would change); (b) return `False` for unknown hosts at enqueue time, rejected (it would drop every external link before its robots can be fetched). Chosen: synchronous filter plus an authoritative async guard at fetch time.

Persisted schema check: not applicable.

Validation baseline: `radon cc` recorded above; `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Outcome-table tests, idempotence, redirect flag, start-URL refusal, external-host fetch, and the inverted transport-error test (`REQ-001`..`REQ-005`; `tests/rag/ingestion/test_robots.py`)
2. **Phase 2: Policy in the cache**
   - [ ] Outcome table, `ensure_host`, per-request `follow_redirects=True`, fail-closed parsers (`REQ-001`, `REQ-002`, `REQ-004`; `scripts/rag/ingestion/robots.py`)
3. **Phase 3: Fetch-time enforcement**
   - [ ] Ensure the host and refuse a disallowed URL in `_process_crawl_url_async` (`REQ-002`, `REQ-003`, `REQ-005`; `scripts/rag/ingestion/orchestrator.py`)
4. **Phase 4: Documentation**
   - [ ] Per-outcome policy text (`REQ-006`; `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`, `docs/21_rag/rag_05_01-configuration-reference.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/robots.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Unit (mock transport) | `uv run pytest tests/rag/ingestion/test_robots.py -q -k "RobotsCache"` | outcome table asserted |
| `scripts/rag/ingestion/orchestrator.py` | Async integration | `uv run pytest tests/rag/ingestion/test_robots.py tests/rag/ingestion/test_crawler_integration.py -q` | new tests fail on HEAD, pass after |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: fail-closed on 5xx and network errors skips whole hosts after a transient outage → **Mitigation**: logged per outcome; one-function policy; UNK-02 notes cache expiry as a follow-up.
- **Risk**: enabling robots for external hosts adds one request per new host → **Mitigation**: one fetch per host (cached); the policy is opt-in.
- **Risk**: inverting the pinned transport-error test is read as weakening tests → **Mitigation**: the change is a documented policy decision (UNK-01), the test is renamed to the new rule rather than deleted.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | 20261109-211956 | — |  |
| 2 | Phase 2: policy in the cache | In Progress | 20261109-211956 | — |  |
| 3 | Phase 3: fetch-time enforcement | In Progress | 20261109-211956 | — |  |
| 4 | Phase 4: documentation | In Progress | 20261109-211956 | — |  |
| 5 | Phase 5: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-211956_01_tests_rag_ingestion_test_robots.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-211956_02_scripts_rag_ingestion_robots.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-211956_03_scripts_rag_ingestion_orchestrator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261109-211956_04_docs_21_rag_rag_02_02_ingestion_pipeline-crawler.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261109-211956_05_docs_21_rag_rag_05_01-configuration-reference.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131232_ragrev014_robots-policy-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170335
- **Related target files**: `scripts/rag/ingestion/robots.py`, `scripts/rag/ingestion/orchestrator.py`, `tests/rag/ingestion/test_robots.py`, `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`, `docs/21_rag/rag_05_01-configuration-reference.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `robots.py:30-48` | `scripts/rag/ingestion/robots.py` | Phase 2 | AC-1 | outcome-table tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_robots.py` | Phase 1 | AC-1 | outcome-table tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/ingestion/robots.py` | Phase 2 | AC-2 | idempotence and external-host tests | Explicit in issue |
| REQ-002 | Required Changes 2; `orchestrator.py:128-134` | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-2 | external-host orchestrator test | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/rag/ingestion/test_robots.py` | Phase 1 | AC-2 | idempotence and external-host tests | Explicit in issue |
| REQ-003 | Required Changes 3; Acceptance Criteria 3 | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-3 | start-URL refusal test | Explicit in issue |
| REQ-003 | Testing Expectations | `tests/rag/ingestion/test_robots.py` | Phase 1 | AC-3 | start-URL refusal test | Explicit in issue |
| REQ-004 | Step 3 finding: sibling plan turns client redirects off | `scripts/rag/ingestion/robots.py` | Phase 2 | AC-4 | redirect-flag test | Derived from confirmed evidence |
| REQ-004 | Step 3 finding | `tests/rag/ingestion/test_robots.py` | Phase 1 | AC-4 | redirect-flag test | Derived from confirmed evidence |
| REQ-005 | Constraints | `scripts/rag/ingestion/orchestrator.py` | Phase 3 | AC-5 | existing link-filter and eager-fetch tests | Explicit in issue |
| REQ-005 | Constraints | `tests/rag/ingestion/test_robots.py` | Phase 1 | AC-5 | existing link-filter and eager-fetch tests | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` | Phase 4 | AC-6 | docs gates | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/21_rag/rag_05_01-configuration-reference.md` | Phase 4 | AC-6 | docs gates | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-211956 -->