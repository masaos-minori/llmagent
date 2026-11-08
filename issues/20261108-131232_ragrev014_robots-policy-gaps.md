# robots.txt handling treats errors as allow-all and only checks the start host

## Priority
Medium

## Summary
`RobotsCache.fetch_host` allows everything for any non-200 robots response and for network errors, `is_allowed` returns True for hosts that were never fetched, and the orchestrator loads robots only for the start host, so with external links enabled other hosts are not checked.

## Background
Review finding F-014. Evidence (Explicit in code): `scripts/rag/ingestion/robots.py` `fetch_host` calls `parser.parse([])` for every status other than 200 and installs an allow-all parser on `httpx.RequestError`/`ValueError`; `is_allowed` returns `True` when `self._parsers.get(host)` is `None`; `scripts/rag/ingestion/orchestrator.py` calls `robots_cache.fetch_host(origin, client)` once for the start origin before the loop; `LinkDiscovery.should_enqueue_link` consults `is_allowed` but nothing fetches robots for other hosts. The standard-library `RobotFileParser.read()` treats 401 and 403 as disallow-all, and RFC 9309 treats server errors as "assume disallow" for the crawl duration. The start URL itself is not checked with `is_allowed`.

## Problem
A host that answers 401, 403 or 5xx for robots.txt is crawled as if everything were allowed, and hosts reached through external links are crawled with no robots check although the policy is switched on.

## Reason for Change
The robots policy is opt-in, but when enabled the operator expects it to be enforced; fail-open on error contradicts that.

## Implementation Intent
Define the policy for each robots outcome (200, 4xx, 401/403, 5xx, network error) in one place, fetch robots lazily for every host before its first request, and check the start URL.

## Target Files or Areas
- `scripts/rag/ingestion/robots.py` (`RobotsCache.fetch_host`, `is_allowed`)
- `scripts/rag/ingestion/orchestrator.py` (start-host preload)
- `scripts/rag/ingestion/link_discovery.py`
- `tests/rag/ingestion/`

## Required Changes
- Map each response class to allow or disallow per the chosen policy and document it.
- Fetch robots on first use for any host and cache the result.
- Check the start URL against the policy.
- Add tests for 401, 403, 404, 500 and a connection error.

## Constraints
- Keep the policy opt-in as today.
- Keep one robots fetch per host (cached).

## Acceptance Criteria
- A 5xx or 401/403 robots response disallows crawling that host (per the documented rule) and a 404 allows it.
- A link to a second host triggers a robots fetch for that host before the page is requested.
- The start URL is refused when disallowed.

## Testing Expectations
- Unit tests for `RobotsCache` with a mock transport for each status; an orchestrator test with an external-host link.
- ruff and mypy.

## Documentation Impact
Document the robots policy for each outcome (intent and failure behavior) in the ingestion description.

## Out of Scope
- Crawl-delay handling.
- Redirect policy (separate issue).

## Dependencies
Related, no required order: `issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md` (same fetch path).

## Unresolved Questions
Whether 4xx other than 401/403 should allow all (the common convention) is accepted as the rule is `Needs confirmation` (owner decision).

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131232
- **Related target files**: `scripts/rag/ingestion/robots.py`, `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/link_discovery.py`, `tests/rag/ingestion/`
