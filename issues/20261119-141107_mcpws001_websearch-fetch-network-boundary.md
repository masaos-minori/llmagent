# Harden Web Search MCP network authorization, HTTP handling, and resource limits

## Priority
High

## Summary
Implement one fail-closed `browser_fetch` boundary covering DNS-resolved destination validation, redirect authorization, HTTP status handling, content-type validation, and bounded streaming.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 1).

Evidence (`Explicit in code`, by `rg` and reading): `scripts/mcp_servers/web_search/search_provider.py` rejects only IP literals (`ipaddress.ip_address(hostname)`, lines 107-114); no `getaddrinfo` or resolution step exists in the web search package. The fetch returns `status_code=resp.status_code` (line 178) without a status check, and truncation applies to the extracted text (`_truncate`, line 172). Redirect handling, decompression, and streaming claims are from the backlog and `Needs confirmation`.

## Problem
An allowlisted hostname can resolve to loopback, link-local, private, reserved, or metadata-service addresses (server-side request forgery). HTTP 4xx and 5xx pages can be returned as content. The whole response is downloaded, decompressed, and parsed before truncation, so the configured limit bounds only the final text.

## Reason for Change
Security-sensitive; the backlog states Web Search MCP should not be approved for production use before this is complete.

## Implementation Intent
Only allowlisted hostnames resolving to approved public addresses are fetched; every redirect is re-authorized; only supported text content from 2xx responses reaches the parser; network, decompression, parser, and output use are bounded independently. Bind the connection to validated addresses to prevent DNS rebinding.

## Target Files or Areas
- `scripts/mcp_servers/web_search/search_provider.py`, `web_search_service.py`, response models, `formatters.py`
- `tests/mcp_servers/web_search/test_web_search_provider.py`, `test_web_search_service.py`
- MCP design document sections (location of `22_mcp_all.md` is `不明`; the file is not tracked)

## Required Changes
- Resolve all A and AAAA addresses before connecting; reject loopback, private, link-local, reserved, multicast, unspecified, and IPv4-mapped prohibited IPv6 addresses; define a fail-closed policy for mixed answers.
- Bind the connection to the validated addresses, preserving TLS SNI and the HTTP `Host` value.
- Disable redirects or implement a bounded loop (at most 5) repeating scheme, hostname, allowlist, DNS, and IP validation per hop; document outbound proxy behavior.
- Treat only 2xx as normal results; classify 3xx, 4xx, 429, and 5xx separately; never return upstream error pages as page content.
- Stream with separate limits for raw, decompressed, parser-input, and returned bytes; check `Content-Length` and still enforce cumulative limits.
- Permit only `text/html` and approved `text/plain`; reject PDF, ZIP, image, and other binary types before parsing.
- Return metadata distinguishing download truncation from extracted-text truncation; keep health and metrics aligned with result classification.

## Constraints
- Legitimate allowlisted public HTML pages remain fetchable.
- The change must work with the existing provider and metrics interfaces.

## Acceptance Criteria
- [ ] An allowlisted hostname resolving to a prohibited address is rejected; mixed answers follow the explicit policy.
- [ ] Redirects cannot escape the hostname and IP authorization boundary.
- [ ] HTTP 403, 404, 429, 500, and 503 are not reported as successful fetches.
- [ ] Binary and unsupported types are rejected before parser invocation.
- [ ] Raw, decompressed, parser-input, and final-output limits are enforced independently; chunked transfer and false or missing `Content-Length` cannot bypass them.

## Testing Expectations
- DNS, IPv4, IPv6, mixed-answer, rebinding, and redirect cases in `test_web_search_provider.py`; reverse the existing HTTP 404 passthrough expectation.
- 301, 403, 404, 429, 500, and 503 cases; gzip or brotli expansion, chunked transfer, false `Content-Length`, oversized HTML, and binary content.
- Metrics and health classification for every status category.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. DNS and redirect authorization, the four distinct limits, supported content types, and HTTP status behavior; remove any implication that the extracted-text limit is a complete resource control.

## Out of Scope
- Configuration normalization, schemas, and audit redaction (`issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md`).

## Dependencies
- No blocking dependency. Can run in parallel with `issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md`. Archived `issues/done/20260816-160000_web_search_provider_typing_and_docstring.md` touched the provider; re-verify against current source.

## Unresolved Questions
- `不明`: mixed-answer policy (reject all versus filter to public).
- `不明`: how to pin validated addresses with the HTTP client in use while keeping SNI.
- `不明`: limit values, approved `text/plain` scope, and outbound proxy behavior.

## AI Implementation Instruction
Write the prohibited-address and redirect tests first. Keep changes inside the web search package and its tests. Stop and report if address pinning needs a new dependency.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141107
- **Related target files**: `scripts/mcp_servers/web_search/search_provider.py`, `scripts/mcp_servers/web_search/web_search_service.py`, `scripts/mcp_servers/web_search/formatters.py`, `tests/mcp_servers/web_search/test_web_search_provider.py`, `tests/mcp_servers/web_search/test_web_search_service.py`
