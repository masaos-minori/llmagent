## Goal

Enforce the robots policy at fetch time in the orchestrator (Plan Phase 3): before any URL is requested, ensure its host's robots rules via `ensure_host` (new) and refuse a disallowed URL (including the start URL) with a distinct log; keep the eager start-host preload and unchanged behavior when no robots cache is configured (REQ-002, REQ-003, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

Row 2 of the frozen target table.

## Assumptions
- Line numbers revalidated 20261109: preload block at L128-134 (Plan cited L127-131; shifted by the landed ragrev011 commit b2726cf75); cache access `getattr(self._link_discovery, "_robots_cache", None)` at L130; `_process_crawl_url_async` def at L219 with `client: httpx.AsyncClient` parameter at L226; no per-URL robots check exists in the method. Behavior claims accurate.
- `ensure_host` (new) from procedure 02 exists before this change lands (Plan Phase 3 follows Phase 2).
- Overlap judgment (Plan Assumptions): `orchestrator.py` is shared with the open ragrev012/ragrev013/ragrev018 plans; compatible, no required order — this row edits only the guard at the start of `_process_crawl_url_async` and keeps the preload; if ragrev012 lands first, its per-hop robots check calls `ensure_host` (its own procedure set).

## Design decisions
- Guard placement: at the start of `_process_crawl_url_async` inside `async with sem:`, before `get_conditional_headers`/`fetch_html` — `enqueue_links` is synchronous, so the authoritative check must sit at fetch time in the async orchestrator (Plan Background fact 2).
- Cache lookup stays `getattr(self._link_discovery, "_robots_cache", None)` — the pattern the file already uses at L130; no new import edges (`lint-imports` 6 contracts kept, Plan Design).
- Host/origin derivation reuses `crawler_utils.normalize_url` / urlparse helpers (Plan Reference Files); host key = scheme + netloc, matching `ensure_host`'s (new) origin key.
- A disallowed URL (or a host whose fetch outcome installed a disallow-all parser) is skipped with a distinct log line — separate from the existing domain-scope skip logs — and `return` before any HTTP request (REQ-003).
- The start URL flows through the queue into `_process_crawl_url_async`, so the guard covers it automatically (Plan Intent: "refuse a disallowed URL (including the start URL)").

## Alternatives considered
- Enforcing at enqueue time in `link_discovery.should_enqueue_link` — rejected by the Plan (Design alternatives (b) and Background fact 2: fetch cannot happen in the synchronous enqueue path).

## Implementation
### Target file
`scripts/rag/ingestion/orchestrator.py`

### Procedure
1. At the start of `_process_crawl_url_async` (L219, after `async with sem:`): resolve `robots_cache = getattr(self._link_discovery, "_robots_cache", None)`; when it is not `None`, derive the URL's origin and await `ensure_host` (new) with `(origin, client)` (REQ-002: covers hosts reached through external links, one fetch per host).
2. Immediately after: when the cache is configured and `robots_cache.is_allowed(url)` is `False`, log a distinct skip line carrying url and host, and `return` without requesting the URL (REQ-003).
3. Leave the eager preload block (L128-134, `fetch_host` call) in place unchanged — after procedure 02 it delegates to `ensure_host` internally (REQ-005).
4. When `robots_cache` is `None` (policy off via `respect_robots`, wired in `crawler.py` L73/L84), take no robots action: behavior identical to today (REQ-003, REQ-005).
5. Keep method complexity acceptable: the guard is a two-branch check; `radon` baseline for `_process_crawl_url_async` is A (5) (Plan Affected areas).

### Method
In-place edit of one method plus reuse of existing helpers; no signature changes, no new imports.

### Details
- Distinct log wording (e.g. `robots disallowed: url=%s host=%s`) is fixed here and asserted by the start-URL refusal test in procedure 01; align on landing.
- The guard runs before the conditional-headers lookup so a disallowed URL issues zero HTTP requests.

## Compatibility considerations
- Related Tests (from the Plan row): `tests/rag/ingestion/test_robots.py` — orchestrator cases (start-URL refusal, external-host second fetch, policy-off) owned by procedure 01; Validation plan also runs `tests/rag/ingestion/test_crawler_integration.py` (async integration; add a case there only if the test-robots.py coverage duplicates an existing integration harness pattern).
- `link_discovery.py` stays unchanged (Plan Reference Files: synchronous `is_allowed` use at enqueue time remains as a pre-filter).

## Security considerations
- Fetch-time enforcement is the security fix: hosts reached through external links are no longer crawled without a robots check while the policy is enabled (Plan Problem).

## Rollback considerations
- Revert together with procedures 01 and 02 as one set; reverting this file alone leaves the new orchestrator tests red.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_robots.py tests/rag/ingestion/test_crawler_integration.py -q` — new tests fail on HEAD, pass after (Plan Validation plan row 2).
- `uv run pytest tests/rag/ingestion -q` — regression net, AC-5 existing tests unmodified.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` — clean.
- Full validation sequence: `rules/toolchain.md`.

## Completion criteria
- Every crawl URL (start URL included) gets `ensure_host` before its first request when a cache is configured; disallowed URLs are skipped with a distinct log and zero HTTP requests; policy-off behavior unchanged; AC-2, AC-3, AC-5 green.

## Out of Scope
- `link_discovery.py` changes.
- `robots.py` internals (procedure 02).
- Client-level redirect policy (ragrev012).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005
- **Source issue**: issues/20261108-131232_ragrev014_robots-policy-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170335_ragrev014_robots-policy-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-09 21:19:56
- **Related target files**: scripts/rag/ingestion/orchestrator.py
