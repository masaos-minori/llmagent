# Apply one bounded security policy to crawler requests, redirects, robots.txt, and bodies

## Priority
Medium

## Summary
Validate the initial URL, every redirect hop (including same-host hops), robots.txt retrieval, and response bodies under one network policy, with bounded and content-typed bodies.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` M-02):
- Confirmed: robots.txt is fetched with `follow_redirects=True` (`scripts/rag/ingestion/robots.py:56`), outside the hop policy.
- Confirmed: the public-address check `host_is_public` is used only in `_hop_policy` for hops to a host other than the crawl start host (`scripts/rag/ingestion/http_fetcher.py:151-180`); a same-host hop checks only the scheme downgrade, and no use of `host_is_public` for the initial URL was found in `scripts`.
- Confirmed: DNS is resolved by `getaddrinfo` in `host_is_public` (`scripts/rag/ingestion/crawler_utils.py:160-183`) and the connection is made separately, so there is no IP pinning.
- Confirmed: no content-type or body-size limit exists in the fetch path; `_build_fetched` uses `response.text` (`http_fetcher.py:195`).
- Not a defect by itself: `config/crawler.toml` sets `respect_robots = false`, and `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md:56-66` documents that opt-in design (default disabled). Changing the default is a policy decision, not drift.

## Problem
Initial and same-host requests and robots.txt can reach destinations the policy was meant to block, a rebinding race exists between validation and connection, and oversized or non-HTML bodies reach the parser.

## Reason for Change
The crawler fetches attacker-influenced URLs; the policy must hold on every request path.

## Implementation Intent
One guarded fetcher for pages and robots.txt; validate the initial URL and resolved IPs before the first request and every hop; pin validated IPs (preserving Host and SNI) or enforce equivalent egress control; allow only supported HTML content types; enforce compressed and decompressed size limits.

## Target Files or Areas
- `scripts/rag/ingestion/http_fetcher.py`, `crawler_utils.py`, `robots.py`, `orchestrator.py`, `crawler.py`
- `config/crawler.toml`
- `tests/rag/ingestion/`

## Required Changes
- Validate initial URL and every hop, same-host included; route robots.txt through the guarded fetcher without automatic redirects.
- Block loopback, RFC1918, link-local, IPv6 ULA, and metadata destinations unless explicitly allowlisted; pin validated IPs with Host and SNI preserved, or document the egress control that replaces pinning.
- Restrict content types to supported HTML types; enforce body-size limits before parsing.
- Make malformed or unavailable robots.txt behavior match the documented policy; define the User-Agent and a host-level request-rate policy.
- Decide and record the `respect_robots` default for public-site configuration.

## Constraints
- Keep the documented opt-in robots design unless the maintainer changes it.
- An allowlist for intentionally allowed private hosts must be explicit configuration.

## Acceptance Criteria
- Private and metadata destinations are blocked for initial and redirected requests; a rebinding test cannot reach a newly returned private address.
- Cross-host robots.txt redirects are subject to the same policy.
- Binary and oversized responses are rejected before HTML parsing.
- Tests cover IPv4, IPv6, same-host and cross-host redirects, malformed robots.txt, and body-size limits.

## Testing Expectations
Unit tests with a stub resolver and transport for each case; whole-suite run and changed-path gates including bandit.

## Documentation Impact
Update the crawler pipeline and configuration documents for the policy, limits, and the robots default decision.

## Out of Scope
- Deployment firewall or proxy changes.

## Dependencies
- N/A: none (independent of the other remediation issues).

## Unresolved Questions
- `不明`: whether the maintainer wants `respect_robots` enabled by default for public sites (currently documented opt-in).
- `不明`: whether a custom transport or an egress firewall already exists in deployment.
- `不明`: the operational policy for intentionally allowed private hosts.

## AI Implementation Instruction
Do not change the robots default without the recorded decision; keep the change inside the listed modules and tests.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093153
- **Related target files**: `scripts/rag/ingestion/http_fetcher.py`, `scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/robots.py`, `config/crawler.toml`
