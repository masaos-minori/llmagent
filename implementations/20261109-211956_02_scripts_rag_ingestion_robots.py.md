## Goal

Turn `RobotsCache` into the single owner of the robots.txt outcome policy (Plan Phase 2): one outcome table (fail-closed for 401/403, 5xx, network errors; allow-all for 404 and other 4xx except 401/403; parse on 200), a new `ensure_host` (new) entry usable for any host, and an explicit per-request `follow_redirects=True` on the robots fetch (REQ-001, REQ-002, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

Row 1 of the frozen target table.

## Assumptions
- Line numbers revalidated 20261109 against the current file: `fetch_host` L30-48 (non-200 → `parser.parse([])` allow-all at L41-43; `httpx.RequestError`/`ValueError` → allow-all fallback with "allowing all" log at L44-48), `is_allowed` L50-55 (unknown host → `True` at L53-54). The Plan cites `is_allowed` at L50-56 — one line of overshoot, behavior claims accurate.
- `ValueError` is not in the Plan's outcome table (it is a client-side parse error, not a fetch outcome): its current allow-all fallback is kept unchanged and logged with its class; owner confirmation falls under UNK-01.
- Fail-closed parsers are cached for the cache lifetime (Plan Background fact 3); no expiry in this cycle (UNK-02).

## Design decisions
- Outcome table lives in one small mapping function (Plan Design complexity note) so `fetch_host` (A 4) and `is_allowed` (A 2) stay at grade A; mapping: 200 → parse body; 401/403 → disallow-all; 404 and other 4xx → allow-all; 5xx and `httpx.RequestError` (timeouts included) → disallow-all; each outcome logged with its class.
- Disallow-all is expressed as a `RobotFileParser` parsed from `["User-agent: *", "Disallow: /"]` (via a new private helper `_disallow_all_parser` (new)), so `is_allowed` remains the single synchronous query API unchanged.
- `ensure_host` (new) — confirmed absent from scripts/ — is the new async entry: `(self, origin: str, client: httpx.AsyncClient) -> None`, idempotent per host (cache hit returns before any request), usable for any host, applies the outcome table. `fetch_host` (L30-48) keeps its signature and delegates to `ensure_host` (new) so existing callers (orchestrator preload L134, tests) are untouched (REQ-005: eager preload keeps working).
- The robots request becomes `client.get(robots_url, timeout=..., follow_redirects=True)` per request (REQ-004), independent of the shared client's `follow_redirects` setting (Plan Background fact 4: the sibling ragrev012 plan turns the client-level setting off).
- No retry logic and no cache expiry in this cycle (Out-of-Scope: cache expiry; UNK-02).

## Alternatives considered
- Making `is_allowed` async — rejected by the Plan (Design alternatives (a): `enqueue_links` is synchronous).
- Returning `False` for unknown hosts — rejected by the Plan (Design alternatives (b): would drop every external link before its robots fetch).

## Implementation
### Target file
`scripts/rag/ingestion/robots.py`

### Procedure
1. Add the outcome mapping: a small function mapping status code / exception class to one of three parser outcomes (parse body, allow-all parser, disallow-all parser), with one log line per outcome carrying the outcome class and host (REQ-001).
2. Rewrite `fetch_host` (L30-48) to delegate to the new `ensure_host` (new), keeping its public signature; remove the current "every status other than 200 → `parse([])`" branch and the allow-all fallback on `httpx.RequestError` (fail-open), replacing them with the outcome mapping (REQ-001).
3. Add `ensure_host(origin, client)` (new): cache-hit short-circuit on `self._parsers` (one fetch per host per cache lifetime, REQ-002); fetch `robots.txt` with per-request `follow_redirects=True`; apply the outcome mapping and cache the resulting parser (REQ-001, REQ-004).
4. Leave `is_allowed` (L50-55) behaviorally unchanged (synchronous, unknown host → `True`); only docstring updates.
5. Update module docstring (L2-10) to state the outcome table and the fail-closed semantics.

### Method
In-place edit; no new import edges (`httpx` and stdlib only — Plan Design: `lint-imports` 6 contracts kept).

### Details
- Keep the existing user-agent handling and `self._parsers` dict; do not introduce new public types (the Plan expresses outcomes as parser installs, not new symbols beyond `ensure_host`).
- 401/403 distinction from other 4xx happens before the allow-all branch (RFC 9309 mapping, Plan Assumptions).

## Compatibility considerations
- Callers keep their shape: `orchestrator.py` preload (L128-134), `link_discovery.py` `is_allowed` (L80-82), `crawler.py` construction (L84) — the orchestrator guard change lands in procedure 03.
- Related Tests (from the Plan row): `tests/rag/ingestion/test_robots.py` — owned by procedure 01 (outcome tests, `ensure_host` idempotence, redirect flag, inverted transport-error test; `test_fetch_host_404_falls_back_allow_all` stays unmodified).

## Security considerations
- Fail-closed on 401/403/5xx/network error is the fix: an unreachable or access-restricted host is not crawled without rules (Plan Reason for Change, RFC 9309).

## Rollback considerations
- Single-file revert; must be reverted together with procedures 01 and 03 (test and guard coupling).

## Validation plan
- `uv run pytest tests/rag/ingestion/test_robots.py -q -k "RobotsCache"` — outcome table asserted.
- `uv run pytest tests/rag/ingestion -q` — regression net.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` — clean.
- Full validation sequence: `rules/toolchain.md`.

## Completion criteria
- One outcome mapping exists; 401/403/5xx/network outcomes install disallow-all parsers and are logged; 404/other 4xx allow all; `ensure_host` (new) fetches at most once per host for any host; robots requests carry `follow_redirects=True` regardless of client setting; AC-1, AC-2, AC-4 green.

## Out of Scope
- Cache expiry for fail-closed entries (UNK-02, follow-up).
- Crawl-delay handling, the redirect policy itself (ragrev012), making the policy non-opt-in (Plan Out-of-Scope).
- `crawler.py` wiring changes.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20261108-131232_ragrev014_robots-policy-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170335_ragrev014_robots-policy-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-09 21:19:56
- **Related target files**: scripts/rag/ingestion/robots.py
