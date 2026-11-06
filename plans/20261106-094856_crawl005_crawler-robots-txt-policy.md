## Goal
- Add an explicit, opt-in (disabled by default) robots.txt policy so external-site crawling respects `Disallow` rules per host, without changing any behavior when the policy is disabled.

## Priority
Low

## Scope
- **In-Scope**:
  - Add a config flag to enable/disable robots.txt respect (default off).
  - Create an isolated `RobotsCache` component that fetches and parses `robots.txt` per host and answers `can_fetch(user_agent, url)` queries.
  - Filter out disallowed URLs before they are enqueued in the BFS loop.
  - Fetch each host's `robots.txt` at most once per crawl.
  - Document the new config flag and its default.
- **Out-of-Scope**:
  - Changing nofollow / cross-origin filtering semantics.
  - Crawl-rate tuning beyond the existing `crawl_delay`.
  - Per-host concurrency limits or politeness parsing beyond `robots.txt`.
  - Caching `robots.txt` across separate crawl runs (in-memory per session only).
- **Dependencies**: `N/A: none`

## Background
The BFS crawler (`CrawlOrchestrator` + `LinkDiscovery`) filters links by `nofollow` and cross-origin rules and applies a constant `crawl_delay`. There is no robots.txt fetching or parsing anywhere in `scripts/rag/ingestion/`.

## Problem
Crawling external sites without respecting robots.txt can violate site policy, Terms of Service, or legal expectations. The current fixed delay alone does not address path-level disallow rules.

## Reason for Change
The configured targets are currently well-known documentation sites, but adding an explicit, toggleable policy now prevents future exposure when new targets are added and makes the politeness stance deliberate rather than accidental.

## Implementation Intent
Introduce an optional, disabled-by-default robots.txt layer that, when enabled, fetches and caches `robots.txt` per host and skips disallowed paths before enqueueing. Gate it behind a config flag so existing behavior is unchanged unless opted in. Keep it isolated from the core BFS loop.

## Requirements
- `REQ-001`: A config flag `respect_robots` controls whether robots.txt is honored; default is `false`.
- `REQ-002`: When the flag is off, no `robots.txt` request is issued and crawling behavior is identical to today.
- `REQ-003`: When the flag is on, `robots.txt` is fetched at most once per host and disallowed paths are skipped while allowed paths are crawled.
- `REQ-004`: Existing nofollow / cross-origin filtering is unchanged.
- `REQ-005`: The new config flag and its default are documented in the crawler config notes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Create | New isolated `RobotsCache`: async per-host fetch of `/robots.txt`, parse with stdlib `urllib.robotparser.RobotFileParser`, cache per host, expose `is_allowed(url)` using the crawler user agent (REQ-003) | REQ-003 | No existing robots handling exists in `scripts/rag/ingestion/` (verified); `RobotFileParser.can_fetch` returns correct allow/deny for sample `Disallow` rules (verified) | New test file below | Verified |
| `scripts/rag/ingestion/link_discovery.py` | Modify | Add an optional `robots_cache` parameter and, when set, skip enqueuing URLs that `robots_cache.is_allowed` returns False for; keep all existing nofollow/cross-origin logic intact (REQ-002, REQ-003, REQ-004) | REQ-002, REQ-003, REQ-004 | `should_enqueue_link` is the single enqueue decision point; `enqueue_links` is the choke point (verified) | Existing + new tests | Verified |
| `scripts/rag/ingestion/orchestrator.py` | Modify | When a robots cache is present, fetch the start host's `robots.txt` once before the BFS loop using the shared `httpx.AsyncClient`; do nothing when absent (REQ-003) | REQ-003 | `crawl_site` owns the `httpx.AsyncClient` lifecycle and is called per target host (verified) | Existing crawler tests | Verified |
| `scripts/rag/ingestion/crawler.py` | Modify | Read `respect_robots` via `cfg.get("respect_robots", False)`; construct and inject a `RobotsCache` into `LinkDiscovery` when enabled (REQ-001, REQ-005) | REQ-001 | Config is read via `cfg.get(...)` with defaults; adding a key cannot break existing configs (verified) | Existing crawler tests | Verified |
| `config/crawler.toml` | Modify | Document the new `respect_robots = false` flag and its default (REQ-005) | REQ-005 | `config/crawler.toml` documents `skip_nofollow`, `skip_external`, etc. (verified) | N/A | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/crawler_utils.py` | Owns `normalize_url` and `same_origin`; read to build host keys and confirm same-origin scoping for robots lookups (REQ-003) | `scripts/rag/ingestion/robots.py`, `scripts/rag/ingestion/link_discovery.py` |
| `scripts/rag/ingestion/http_fetcher.py` | Owns the `HttpFetcher` user-agent convention and fetch patterns; read to reuse a consistent user agent and fetch style (REQ-003) | `scripts/rag/ingestion/robots.py` |
| `scripts/rag/ingestion/crawler.py` | Owns `WebCrawler.__init__` construction order and `main()`; read to wire config and component injection correctly (REQ-001, REQ-005) | `scripts/rag/ingestion/crawler.py` (target) |

## Acceptance Criteria
- `REQ-002`: With the flag off, a simulated crawl issues zero `robots.txt` requests and produces the same output as without the feature.
- `REQ-003`: With the flag on, a sample `robots.txt` with a `Disallow` rule causes disallowed URLs to be skipped and allowed URLs to be crawled; each host's `robots.txt` is fetched exactly once.
- `REQ-004`: nofollow / cross-origin filtering behavior is unchanged when the flag is on or off.
- `REQ-005`: `config/crawler.toml` documents `respect_robots` and its default.

## Tests
- Flag-off test: with `respect_robots = false`, assert no `robots.txt` HTTP request is made (spy on the fetch) and behavior is unchanged (REQ-002).
- Flag-on test: with `respect_robots = true` and mocked `robots.txt` responses, assert a `Disallow` rule blocks the disallowed path and allows the allowed path (REQ-003).
- Once-per-host test: assert `robots.txt` is fetched at most once per host across a multi-URL same-origin crawl (REQ-003).
- Regression test: nofollow / cross-origin filtering still works with the flag on (REQ-004).
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
- Document `respect_robots` and its default in `config/crawler.toml` (REQ-005).
- If `docs/*.md` contains crawler config notes, add the flag there too (verify against `docs/` first; update only if such notes exist).

## Assumptions
- The crawl is same-origin (`skip_external = true` by default), so only the start host's `robots.txt` is needed per `crawl_site`; multiple targets mean multiple hosts, each fetched once.
- In-memory per-session caching is sufficient; cross-run caching is out of scope.
- `urllib.robotparser.RobotFileParser` (stdlib) is adequate for parsing; no third-party robots library is required or available in deps.
- The crawler user agent (`_USER_AGENT`) is used as the robots user-agent token.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Integration location for the filter: inside `LinkDiscovery.should_enqueue_link` (synchronous, single choke point) versus a pre-crawl fetch-and-filter pass in the orchestrator. | None required; both verified feasible. | Recommend injecting an optional `RobotsCache` into `LinkDiscovery` and checking `is_allowed` synchronously in `should_enqueue_link`, with eager per-host fetch in `orchestrator.crawl_site`. This keeps the check at the single enqueue decision point and avoids awaiting inside the sync filter. Non-blocking. | False |
| UNK-02 | Whether to refuse to start a crawl when the start URL itself is disallowed by robots.txt. | None required. | Optional enhancement: after fetching the start host's robots.txt, if `is_allowed(start_url)` is False, log a clear message and skip that target. Non-blocking. | False |
| UNK-03 | Behavior when `robots.txt` is missing (404) or non-2xx. | None required. | `RobotFileParser` treats a missing/empty robots.txt as "allow all"; fetch failures should fall back to allow-all and log once per host. Non-blocking. | False |
| UNK-04 | Task-size classification (Path A vs B) for the plan-to-impl-procedure step. | None required. | New isolated module + opt-in wiring across ≤4 files with no shared-contract or DB schema change; classify as Path A (contained). If a reviewer deems the new subsystem larger, promote to a dedicated implementation procedure. Non-blocking. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Create | Low (new isolated module; no existing references) | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/link_discovery.py` | Modify | Low (additive optional param; default preserves behavior) | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/orchestrator.py` | Modify | Low (optional pre-loop fetch; no-op when disabled) | N/A | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/crawler.py` | Modify | Low (additive config read with default) | N/A | N/A | not applicable (rsynced) |

## Design
Current flow: `LinkDiscovery.enqueue_links` → `should_enqueue_link` is the single
decision point for what gets queued; it applies `nofollow` and cross-origin filters and
then calls `queue.put_nowait`. There is no robots.txt awareness anywhere.

**New component (`scripts/rag/ingestion/robots.py`):**
- `RobotsCache` holds the crawler user agent and a `{host -> RobotFileParser}` map.
- `async fetch_host(host, client)`: GET `{scheme}://{host}/robots.txt`; on 2xx, call
  `parser.parse(lines)`; on 404/non-2xx/transport error, keep a permissive parser (allow
  all) and log once; store the parser keyed by host. Idempotent — a second call for an
  already-fetched host is a no-op, guaranteeing at-most-once per host.
- `is_allowed(url)`: parse the URL host, return `parser.can_fetch(USER_AGENT, url)`;
  return True (allow) for unknown hosts.
- Uses stdlib `urllib.robotparser.RobotFileParser` (available; `can_fetch` verified to
  return correct allow/deny). No third-party dep.

**Wiring:**
1. `crawler.py`: read `respect_robots = cfg.get("respect_robots", False)`; when True,
   construct `self.link_discovery = LinkDiscovery(..., robots_cache=RobotsCache(_USER_AGENT))`.
2. `link_discovery.py`: add optional `robots_cache: RobotsCache | None = None`; in
   `should_enqueue_link`, after existing checks, if `self._robots_cache is not None` and
   not `self._robots_cache.is_allowed(next_url)`, return False. All other paths unchanged
   (REQ-004).
3. `orchestrator.py`: in `crawl_site`, if `self._link_discovery` exposes a robots cache,
   `await cache.fetch_host(start_host, client)` once before the BFS loop. No-op when the
   cache is absent (REQ-002).
4. `config/crawler.toml`: document `respect_robots = false` with a comment (REQ-005).

When disabled, `robots_cache` is `None` everywhere: no fetch, no check, identical behavior.

## Implementation steps
1. **Phase 1: New `RobotsCache` module** (`scripts/rag/ingestion/robots.py`, REQ-003)
   - [ ] Implement `RobotsCache(user_agent)` with a `{host -> RobotFileParser}` cache.
   - [ ] Implement `async fetch_host(host, client)` (idempotent per host, permissive fallback on error).
   - [ ] Implement `is_allowed(url)` via `RobotFileParser.can_fetch`.
2. **Phase 2: Filter integration** (`scripts/rag/ingestion/link_discovery.py`, REQ-002, REQ-003, REQ-004)
   - [ ] Add optional `robots_cache` parameter; add the `is_allowed` check in `should_enqueue_link` after existing filters.
3. **Phase 3: Eager per-host fetch** (`scripts/rag/ingestion/orchestrator.py`, REQ-003)
   - [ ] In `crawl_site`, fetch the start host's `robots.txt` once before the BFS loop when a cache is present.
4. **Phase 4: Config wiring & docs** (`scripts/rag/ingestion/crawler.py`, `config/crawler.toml`, REQ-001, REQ-005)
   - [ ] Read `respect_robots` with default `False`; inject `RobotsCache` into `LinkDiscovery` when enabled.
   - [ ] Document the flag and default in `config/crawler.toml`.
5. **Phase 5: Verification & commit** (REQ-002, REQ-003, REQ-004)
   - [ ] Run `uv run ruff format` and `uv run ruff check` on touched files; confirm clean.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/`; confirm no new errors.
   - [ ] Add flag-off and flag-on tests; run the crawler suite; confirm pass.
   - [ ] Commit, rebase onto `origin/master`, and push via `git-commit-and-sync`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/robots.py` | Unit: can_fetch allow/deny, once-per-host fetch | `uv run pytest tests/rag/ingestion/test_robots.py -v` | New tests pass |
| `scripts/rag/ingestion/link_discovery.py` | Behavioral: filter respects robots when on, no-op when off | spy on fetch; compare queued URLs | Disallowed skipped; zero fetches when off |
| `scripts/rag/ingestion/orchestrator.py` | Behavioral: one fetch per host | multi-URL simulated crawl | Exactly one fetch per host |
| `config/crawler.toml` | Static: documented flag | manual/doc check | Flag + default documented |

## Risks
- **Risk**: Adding robots logic to the hot enqueue path adds latency per link. → **Mitigation**: the check is an in-memory dict lookup on an already-parsed parser; robots.txt is fetched once per host before the crawl.
- **Risk**: A wrong `RobotFileParser` usage could over- or under-block. → **Mitigation**: use stdlib `can_fetch` (battle-tested) and cover it with flag-on tests using a sample `Disallow` rule.
- **Risk**: Changing behavior when the feature is off. → **Mitigation**: `robots_cache` defaults to `None`; all existing code paths are byte-for-byte unchanged when disabled (REQ-002, REQ-004).
- **Risk**: Fetching `robots.txt` could fail and hang the crawl. → **Mitigation**: bounded by the shared `httpx` timeout; transport errors fall back to allow-all and log once per host (UNK-03).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `RobotsCache` module (`scripts/rag/ingestion/robots.py`) | Pending | — | — | |
| 2 | Inject filter into `LinkDiscovery.should_enqueue_link` | Pending | — | — | |
| 3 | Eager per-host fetch in `orchestrator.crawl_site` | Pending | — | — | |
| 4 | Config wiring (`crawler.py`) + docs (`config/crawler.toml`) | Pending | — | — | |
| 5 | Format/lint/type/test verification and commit | Pending | — | — | |

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
- **Source issue**: `issues/20261106-073206_crawl005_crawler-robots-txt-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-094856
- **Related target files**: `scripts/rag/ingestion/robots.py`, `scripts/rag/ingestion/link_discovery.py`, `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/crawler.py`, `config/crawler.toml`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / Constraints | `scripts/rag/ingestion/crawler.py` | Step 4 | REQ-001 acceptance criteria | config-flag test | Confirmed by repository evidence |
| REQ-002 | Constraints / Testing Expectations | `scripts/rag/ingestion/link_discovery.py` | Step 2 | REQ-002 acceptance criteria | zero-fetch flag-off test | Confirmed by repository evidence |
| REQ-003 | Required Changes / Acceptance Criteria | `scripts/rag/ingestion/robots.py` | Steps 1-3 | REQ-003 acceptance criteria | flag-on + once-per-host tests | Confirmed by repository evidence |
| REQ-004 | Constraints / Out of Scope | `scripts/rag/ingestion/link_discovery.py` | Step 2 | REQ-004 acceptance criteria | nofollow/external regression test | Confirmed by repository evidence |
| REQ-005 | Documentation Impact | `config/crawler.toml` | Step 4 | REQ-005 acceptance criteria | doc check | Confirmed by repository evidence |
