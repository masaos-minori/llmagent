# Crawler redirects bypass the origin filter, robots.txt and internal-host checks

## Priority
High

## Summary
The crawler client is created with `follow_redirects=True`, while the origin and robots checks are applied only to links before they are enqueued, so a same-origin link that redirects to another host or to an internal address is fetched and its body is ingested under the requested URL.

## Background
Review finding F-012 (Confidence Medium: reading of the code, no live redirect was exercised). Evidence (Explicit in code): `scripts/rag/ingestion/orchestrator.py` builds `httpx.AsyncClient(..., follow_redirects=True)`; `LinkDiscovery.should_enqueue_link` applies `skip_external` and the robots check to enqueued URLs only; `fetch_html` returns the final response body without comparing the final URL to the allowed origin. Crawl targets come from the operator configuration, but the content of crawled pages (and therefore their links and redirects) is untrusted.

## Problem
An open redirect or a malicious page can make the crawler request an internal service (loopback or link-local addresses) or a disallowed host, and the response is written into the RAG corpus.

## Reason for Change
Fetching attacker-influenced URLs from inside the host is a trust-boundary weakness (SSRF-class) even for a read-only crawler.

## Implementation Intent
Validate every redirect hop and the final URL against the same origin, robots and address policy used for links, and refuse private, loopback and link-local destinations unless explicitly allowed.

## Target Files or Areas
- `scripts/rag/ingestion/orchestrator.py` (client construction)
- `scripts/rag/ingestion/http_fetcher.py` (`fetch_html`)
- `scripts/rag/ingestion/link_discovery.py`
- `scripts/rag/ingestion/robots.py`
- `tests/rag/ingestion/`

## Required Changes
- Disable automatic redirects or follow them manually with a per-hop policy check.
- Apply origin, robots and address checks to each hop and to the final URL.
- Store the document under the final accepted URL or reject the page.
- Add tests with a redirect to another host and to a loopback address.

## Constraints
- Keep ordinary same-origin redirects (for example http to https) working.
- No new third-party dependency without need.

## Acceptance Criteria
- A redirect to a different host or to a loopback or link-local address is refused and logged.
- A same-origin redirect is followed and stored under the final URL.
- Existing crawl tests pass.

## Testing Expectations
- Mock-transport tests for cross-host, internal-address and same-origin redirects.
- `uv run bandit -r scripts/rag -c pyproject.toml -ll`, ruff and mypy.

## Documentation Impact
Document the crawler trust boundary (what is fetched and what is refused) in the ingestion description.

## Out of Scope
- Authentication for crawled sites.
- file:// target restrictions (operator-controlled).

## Dependencies
Related, no required order: `issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md` (same fetch path).

## Unresolved Questions
Whether an internal host is ever a legitimate crawl target in this deployment is `Needs confirmation` (owner decision on an allowlist).

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131127
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`, `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/link_discovery.py`, `scripts/rag/ingestion/robots.py`, `tests/rag/ingestion/`
