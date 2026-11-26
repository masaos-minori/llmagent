## Goal
- Make `browser_fetch` a single fail-closed network boundary: an allowlisted hostname is fetched only when every resolved address is public, the connection is bound to the validated address, every redirect is re-authorized, only 2xx text responses reach the parser, and raw, decoded, parser-input, and returned bytes are bounded independently, through a reusable bounded-fetch helper that the CI/CD log retrieval can reuse with its own host policy.

## Priority
High

## Scope
- **In-Scope**:
  - Resolve all A and AAAA addresses of the target host before connecting and reject the request when any answer is loopback, private, link-local, reserved, multicast, unspecified, or an IPv4-mapped form of a prohibited address (mixed answers are rejected as a whole).
  - Connect to the validated address while keeping the TLS server name and the HTTP `Host` value; make no use of environment proxies.
  - Follow redirects with a manual loop of at most 5 hops, repeating scheme, hostname allowlist, DNS, and address validation per hop.
  - Return a normal result only for a 2xx response; classify 3xx without a usable redirect, 4xx, 429, and 5xx as typed errors and never return an upstream error page as content.
  - Stream the body with independent raw, decoded, parser-input, and returned byte limits; accept only `text/html` and `text/plain`; reject other types before the parser.
  - Report download truncation separately from extracted-text truncation; align metrics, health, and the audit error type with the result classification.
  - Provide the address policy and the bounded streaming download as reusable modules with the host policy, limits, and hop count supplied by the caller.
  - Update the `browser_fetch` design documentation.
- **Out-of-Scope**:
  - Configuration normalization, schemas, and audit redaction of the web search server (a sibling issue of the same backlog).
  - The CI/CD log retrieval change itself (it consumes the helper in its own Plan).
  - New configuration keys for the limits: the limits are named constants in this Plan (see UNK-01).
  - Changing `search_web` or its provider.
  - A new third-party dependency (none is needed, see Design D-2).
- **Dependencies**: No blocking dependency. The web search configuration and audit redaction issue may run in parallel and touches the same models module (different symbols; see Assumptions). Archived typing and docstring work on the provider is re-verified against the current source in Background. This Plan blocks the CI/CD log streaming bounds work, which reuses the helper.

## Background
- Source: consolidated Web Search and CI/CD MCP backlog, Issue 1.
- Step 2/3 adversarial verification against current source (all claims in the issue that were checked still hold):
  - `_check_domain` rejects only IP literals (`ipaddress.ip_address(hostname)`, `search_provider.py:90-123`); there is no resolver call anywhere in the web search package (`rg getaddrinfo scripts/mcp_servers/web_search` found no match, checked in Step 3). An allowlisted name resolving to a private or metadata address is fetched.
  - `fetch_browser` performs `client.get(req.url)` with no status check and returns `resp.status_code` (`search_provider.py:168-180`); the existing test expects the 404 body to pass through (`tests/mcp_servers/web_search/test_web_search_provider.py:260-274`).
  - The whole response is read and decoded by httpx before `_extract_text` and `_truncate`, and the limit applies only to the extracted text (`search_provider.py:134-144,171-172`); httpx decodes gzip and deflate automatically, so a compressed body is expanded in memory (httpx 0.28.1, checked in Step 3).
  - Redirects: httpx 0.28.1 does not follow redirects by default (`follow_redirects=False`), so a 3xx response is returned as page content with its status code today; the "redirect escape" is therefore a gap in the future redirect handling and in the content/status handling, not an existing escape. The only `follow_redirects=True` use in the repository is the CI/CD job log request (`scripts/mcp_servers/cicd/cicd_service_github_actions_job.py:85`), which is the consumer of the future helper.
  - Proxies: httpx honors `HTTP_PROXY`/`HTTPS_PROXY` through `trust_env=True` by default; no proxy setting exists in the repository configuration (`rg proxy deploy config scripts/mcp_servers` found no web search match, checked in Step 3). A proxy resolves names itself, so address pinning is meaningless through one.
  - Pinning needs no new dependency: httpx supports a per-request `sni_hostname` extension, and httpcore 1.0.9 uses it as the TLS server name, which is also the certificate-check name; the request can therefore target the validated IP with an explicit `Host` header.
  - The error plumbing already separates caller errors from upstream errors: `BrowserAuthorizationError` (403) and `BrowserValidationError` (422) are handled in the server, while `WebSearchUpstreamError` subclasses map to 502 (`web_search_server.py:111-135,294-310`); metrics and health are recorded only in the service (`web_search_service.py:145-199`) and `browser_fetch` uses separate singletons.
  - `RuntimeError`-based rejection occurs before the handler's `except ValueError` in the dispatcher, which is why the server has an explicit `except BrowserAuthorizationError`; new rejection classes must follow the same hierarchy rules.
  - Reuse candidates: the RAG crawler has a host-is-public check (`scripts/rag/ingestion/crawler_utils.py:140-190`) that resolves once and is not pinned to the connection; it cannot be imported by `mcp_servers` (import contract: `mcp_servers -> db, shared` only, `.importlinter`), so the policy is re-implemented in the `mcp_servers` package.

## Problem
- An allowlisted hostname can resolve to loopback, link-local, private, reserved, or metadata-service addresses (server-side request forgery); HTTP 4xx and 5xx pages and non-HTML content are returned as content; the whole response is downloaded, decompressed, and parsed before the final truncation, so the configured limit bounds only the final text.

## Reason for Change
- Security-sensitive: the backlog states the Web Search MCP server should not be approved for production before this is complete.

## Implementation Intent
- Put the network policy in two reusable modules (address policy, bounded fetch) and make `fetch_browser` a thin caller that supplies the allowlist policy, the limits, and the content types. Keep the existing provider, metrics, and health interfaces, and raise typed errors that the service classifies for metrics and health.

## Requirements
- `REQ-001`: Before connecting, the address policy MUST resolve every A and AAAA address of the host and reject the request when any address is loopback, private, link-local, reserved, multicast, unspecified, or an IPv4-mapped IPv6 form of such an address; an empty answer or a resolution failure MUST fail closed; mixed answers MUST be rejected as a whole.
- `REQ-002`: The connection MUST target a validated address with the original hostname preserved as the TLS server name and the `Host` header, and the client MUST NOT use environment proxies.
- `REQ-003`: Redirects MUST be followed by a bounded loop of at most 5 hops, each hop repeating scheme, hostname allowlist (through the caller's host policy), DNS resolution, and address validation; a hop over the bound or a 3xx without a usable `Location` MUST be an error.
- `REQ-004`: Only a 2xx response MUST be a normal result; 3xx (unresolved), 4xx, 429, and 5xx MUST raise typed errors carrying a category, and no upstream error body MUST be returned as page content.
- `REQ-005`: The body MUST be streamed with four independent limits (raw bytes, decoded bytes, parser-input bytes, returned bytes); a declared `Content-Length` MUST NOT raise any limit, and chunked or falsely declared bodies MUST be stopped by the cumulative count.
- `REQ-006`: Only `text/html` and `text/plain` MUST be accepted, decided from the response headers before any body is read into the parser; other and missing types MUST raise a typed error.
- `REQ-007`: The response MUST carry `download_truncated` separately from `truncated` and the `content_type`; the service MUST classify each new error for metrics (error type per category) and for health (429, 5xx, network, and timeout count as browser failures; caller and content errors do not), and the server MUST report the same error type in the audit record.
- `REQ-008`: The address policy and the bounded streaming download MUST be reusable modules whose host policy, limits, redirect bound, accepted content types, and transport are supplied by the caller, with no web search import.
- `REQ-009`: The `browser_fetch` documentation MUST describe DNS and redirect authorization, the four limits, the supported content types, the status behavior, the proxy rule, and MUST NOT imply that the extracted-text limit is a complete resource control.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/address_policy.py | Create: resolve all A/AAAA answers, classify prohibited addresses, return validated addresses | No resolver step exists; the RAG crawler check is unpinned and not importable by `mcp_servers` | REQ-001, REQ-002, REQ-008; AC-01 | `rg getaddrinfo scripts/mcp_servers/web_search` no match (checked in Step 3); `.importlinter` contract `mcp_servers -> db, shared` (checked in Step 3); `crawler_utils.py:140-190` (checked in Step 3) | tests/mcp_servers/test_address_policy.py | Verified |
| scripts/mcp_servers/bounded_fetch.py | Create: pinned, redirect-bounded, status- and content-type-checked, independently limited streaming download | Reusable helper required by the issue and by the CI/CD log work | REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-008; AC-02, AC-03, AC-04, AC-05 | httpx 0.28.1 `follow_redirects=False` default and `sni_hostname` extension; httpcore 1.0.9 (checked in Step 3); only existing redirect user is `cicd_service_github_actions_job.py:85` (checked in Step 3) | tests/mcp_servers/test_bounded_fetch.py | Verified |
| scripts/mcp_servers/web_search/search_provider.py | Modify: `fetch_browser` calls the helper with the allowlist host policy, limits, and content types; keep `_check_domain` | Current fetch has no resolution, status, type, or stream control | REQ-001 to REQ-007; AC-01 to AC-07 | `search_provider.py:90-123,134-180` (checked in Step 2) | tests/mcp_servers/web_search/test_web_search_provider.py | Verified |
| scripts/mcp_servers/web_search/web_search_models.py | Modify: add typed errors (status category, unsupported content) and `download_truncated`, `content_type` on `BrowserFetchResponse` | Errors and result metadata need typed carriers | REQ-004, REQ-006, REQ-007; AC-04, AC-06, AC-07 | `web_search_models.py:22-46,314-321` (checked in Step 2) | tests/mcp_servers/web_search/test_web_search_provider.py | Verified |
| scripts/mcp_servers/web_search/web_search_service.py | Modify: classify the new errors for metrics and health | `_classify_browser_error` knows three outcomes only | REQ-007; AC-07 | `web_search_service.py:130-199` (checked in Step 2) | tests/mcp_servers/web_search/test_web_search_service.py | Verified |
| scripts/mcp_servers/web_search/formatters.py | Modify: render `download_truncated` and `content_type` next to `truncated` | The text result shows only `truncated` | REQ-007; AC-06 | `formatters.py:42-52` (checked in Step 2) | tests/mcp_servers/web_search/test_web_search_formatters.py | Verified |
| scripts/mcp_servers/web_search/web_search_server.py | Modify: audit `error_type` and HTTP mapping for the new errors | The server enumerates browser error classes explicitly | REQ-007; AC-07 | `web_search_server.py:111-135,191-205,294-310` (checked in Step 2) | tests/mcp_servers/web_search/test_web_search_server.py | Verified |
| tests/mcp_servers/test_address_policy.py | Create: IPv4, IPv6, mapped, mixed, empty, and failed-resolution cases | New module | REQ-001; AC-01 | `tests/mcp_servers/` exists (checked in Step 3) | tests/mcp_servers/test_address_policy.py | Verified |
| tests/mcp_servers/test_bounded_fetch.py | Create: pinning, redirect, status, type, and limit cases with a fake transport and resolver | New module | REQ-002 to REQ-006, REQ-008; AC-02 to AC-05 | `tests/mcp_servers/` exists (checked in Step 3) | tests/mcp_servers/test_bounded_fetch.py | Verified |
| tests/mcp_servers/web_search/test_web_search_provider.py | Modify: reverse the 404 passthrough expectation; adapt respx mocks to the pinned request; add prohibited-address, redirect, type, and limit cases | The 404 test asserts the removed behavior; mocks route by hostname | REQ-001 to REQ-007; AC-01 to AC-07 | `test_web_search_provider.py:222-300` (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_provider.py | Verified |
| tests/mcp_servers/web_search/test_web_search_service.py | Modify: metrics and health classification for every status category | Existing tests cover three outcomes | REQ-007; AC-07 | `test_web_search_service.py:225-325` (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_service.py | Verified |
| tests/mcp_servers/web_search/test_web_search_formatters.py | Modify: truncation metadata rendering | Response gains fields | REQ-007; AC-06 | `test_web_search_formatters.py:60-82` (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_formatters.py | Verified |
| tests/mcp_servers/web_search/test_web_search_server.py | Modify: audit error type and status mapping for the new errors | Server maps the error classes | REQ-007; AC-07 | `test_web_search_server.py` exists (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_server.py | Verified |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify: `browser_fetch` security boundary section | Documents extracted-text truncation only | REQ-009; AC-08 | `mcp_04_01...md:44-55` (checked in Step 3) | `uv run python tools/run_validation_gates.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/rag/ingestion/crawler_utils.py | Existing public-address predicate (`:140-190`) to align the prohibited-address set | REQ-001 |
| scripts/mcp_servers/web_search/health.py | Browser health singleton and failure semantics | REQ-007 |
| scripts/mcp_servers/web_search/metrics.py | Browser metrics singleton (`record_browser_query`) | REQ-007 |
| scripts/mcp_servers/cicd/cicd_service_github_actions_job.py | The consumer of the helper (`follow_redirects=True`, `:85`) | REQ-008 |
| scripts/mcp_servers/dispatch.py | Exception handling order that makes `RuntimeError`-based errors bypass `except ValueError` | REQ-004, REQ-007 |
| config/web_search_mcp_server.toml | Existing browser keys (`browser_max_response_kb`, `browser_timeout_sec`) | REQ-005 |
| .importlinter | Import contracts for the new `mcp_servers` modules | REQ-008 |
| rules/env.md | deploy.sh behavior (`scripts/` rsynced) | Affected areas |

## Acceptance Criteria
- `AC-01` (REQ-001): An allowlisted hostname that resolves to a loopback, private, link-local, metadata, reserved, multicast, unspecified, or IPv4-mapped prohibited address is rejected with `BrowserAuthorizationError` before any connection; an answer set mixing a public and a prohibited address is rejected; an empty answer and a resolution failure are rejected.
- `AC-02` (REQ-002): A request is sent to the validated IP with `Host` and the TLS server name set to the original hostname; a resolver that returns a different address on a second call cannot change the connected address within one hop (rebinding case); no environment proxy is used.
- `AC-03` (REQ-003): A redirect to a non-allowlisted host, to a prohibited address, to a non-http(s) scheme, and a sixth hop are all rejected; a redirect within the allowlist to a public address is followed; each hop re-resolves.
- `AC-04` (REQ-004): 301 (unresolved), 403, 404, 429, 500, and 503 raise typed errors with their categories and return no body text; a 200 returns the text.
- `AC-05` (REQ-005, REQ-006): Binary and unsupported types (PDF, ZIP, image, missing type) are rejected before the parser is called; raw, decoded, parser-input, and returned limits each stop their own stage; gzip expansion, chunked transfer, a false `Content-Length`, and a missing `Content-Length` cannot exceed them; `text/plain` is returned without the HTML parser.
- `AC-06` (REQ-007): A body cut by a download limit reports `download_truncated=true` and an extracted-text cut reports `truncated=true`, independently; both appear in the formatted output with the content type.
- `AC-07` (REQ-007): Each category maps to a distinct metrics `error_type`; 429, 5xx, network, and timeout also record a browser health failure and 4xx, redirect, unsupported content, and authorization errors do not; the audit record carries the same error type.
- `AC-08` (REQ-009): The documentation describes the policy items of REQ-009 and the documentation gates report no finding.

## Tests
- T-01 (REQ-001, AC-01): address policy with a fake resolver for IPv4, IPv6, IPv4-mapped IPv6, mixed, empty, and failing answers.
- T-02 (REQ-002, AC-02): bounded fetch with a recording transport; assert the target IP, the `Host` header, the `sni_hostname` extension, and the rebinding case.
- T-03 (REQ-003, AC-03): redirect chain tests (allowed, off-allowlist, prohibited address, bad scheme, hop bound, missing `Location`).
- T-04 (REQ-004, AC-04): status tests for 301, 403, 404, 429, 500, 503; reverse the existing 404 passthrough test.
- T-05 (REQ-005, REQ-006, AC-05): content-type and limit tests including gzip expansion, chunked transfer, false and missing `Content-Length`, oversized HTML, and binary content.
- T-06 (REQ-007, AC-06, AC-07): service, formatter, and server classification tests for every category.
- T-07 (REQ-009, AC-08): documentation gates from `rules/tool-gates.md`.
- Write the prohibited-address and redirect tests first and confirm they fail on the current code; run ruff, mypy, bandit, and the full test suite.

## Documentation Impact
- Yes. REQ-009 drives an update to the MCP web search section selected through `docs/00_index.md` "Document References by Task" (MCP rows). The docs are written in English.

## Assumptions
- No new dependency is needed for address pinning: the validated IP plus an explicit `Host` header plus the httpx `sni_hostname` request extension keeps SNI and the certificate-check name (verified in httpx 0.28.1 and httpcore 1.0.9 at design time; a test asserts the extension is sent, and the implementation phase stops and reports if the pinned request cannot verify a certificate for the original name).
- `trust_env=False` removes environment proxy use; no repository configuration relies on a proxy for `browser_fetch`.
- The web search configuration and audit redaction Plan will edit configuration symbols of `web_search_models.py`, while this Plan adds exception classes and two response fields; the two are compatible and the implementation phases rebase onto each other.
- Overlap judgment (Step 8b): the web search and file-read document is also modified by the file MCP hardening Plan (mcpai009, file-read symlink and traversal policy) and by the MCP design docs update Plan (mcpai012, GitHub and file-read corrections plus a final sweep). This Plan edits only the `browser_fetch` security boundary section. The three are compatible and edit disjoint sections; the implementation phases rebase onto each other.
- The existing `browser_max_response_kb` (clamped by `HARD_BROWSER_MAX_RESPONSE_KB = 4096`) stays the returned-bytes limit; the other three limits are named constants.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Final values of the raw, decoded, and parser-input limits (this Plan proposes raw 2 MiB, decoded 8 MiB, parser-input 2 MiB as named constants) | No production fetch-size sample | Owner review of the constants during implementation; configuration keys are a follow-up if needed | False |
| UNK-02 | Whether the deployed environment sets `HTTP_PROXY` or `HTTPS_PROXY` for the web search process and expects `browser_fetch` to use it | The deployment environment is outside the repository | Check `/opt/llm` service environment at deploy time; if a proxy is required, a separate decision is needed because pinning does not apply through a proxy | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/address_policy.py | Create | Low (new leaf module, imported by the fetch helper) | N/A (new) | N/A (new) | not applicable (rsynced) |
| scripts/mcp_servers/bounded_fetch.py | Create | Medium (new, later imported by the CI/CD service) | N/A (new) | N/A (new) | not applicable (rsynced) |
| scripts/mcp_servers/web_search/search_provider.py | Modify | Medium (only `fetch_browser` caller path) | 0 | 3 authors | not applicable (rsynced) |
| scripts/mcp_servers/web_search/web_search_models.py | Modify | High (imported by every web search module) | 1 | 3 authors | not applicable (rsynced) |
| scripts/mcp_servers/web_search/web_search_service.py | Modify | Medium | 0 | 1 author (high) | not applicable (rsynced) |
| scripts/mcp_servers/web_search/formatters.py | Modify | Low | 1 | 3 authors | not applicable (rsynced) |
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Medium (HTTP surface) | 4 | 3 authors | not applicable (rsynced) |
| tests/mcp_servers/test_address_policy.py | Create | Low | N/A (new) | N/A (new) | not applicable (rsynced) |
| tests/mcp_servers/test_bounded_fetch.py | Create | Low | N/A (new) | N/A (new) | not applicable (rsynced) |
| tests/mcp_servers/web_search/test_web_search_provider.py | Modify | Low | 0 | 1 author (high) | not applicable (rsynced) |
| tests/mcp_servers/web_search/test_web_search_service.py | Modify | Low | 0 | 1 author (high) | not applicable (rsynced) |
| tests/mcp_servers/web_search/test_web_search_formatters.py | Modify | Low | 0 | 1 author (high) | not applicable (rsynced) |
| tests/mcp_servers/web_search/test_web_search_server.py | Modify | Low | 0 | 1 author (high) | not applicable (rsynced) |
| docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Modify | Low | 3 | 2 authors (high) | not applicable (rsynced) |

## Design
Path B (more than 3 files; a runtime-facing behavior change; two new modules). Baselines (checked in Step 5): `radon cc -n C` reports `_check_domain` at complexity C (12) in `search_provider.py` (the logic stays and the new checks live in the new modules, so its complexity does not grow); `lint-imports` 6 contracts kept; repository-wide `vulture` and `bandit` findings recorded earlier this session are pre-existing and outside the target files; the diff-cover baseline was not measured here (it needs the full coverage run) and the implementation phase records it under `rules/toolchain.md` section 7. `search_provider.py` is 6208 B, `web_search_models.py` 12451 B, `web_search_server.py` 16582 B: all below the 24576 B module size gate; the two new modules are each expected to stay below it.

Decisions (each lists alternatives and compatibility impact):
- **D-1 Mixed-answer policy: reject all.** One prohibited address among the answers rejects the request. Alternative: filter to the public addresses (rejected: a hostile resolver could steer the connection by answer ordering, and fail-closed is the issue's stated intent). Compatibility: a host that publishes a private address next to a public one stops working; allowlisted public sites do not.
- **D-2 Pinning mechanism.** Rewrite the request URL to the validated IP, send `Host` explicitly, and set the httpx `sni_hostname` extension; no new dependency. Alternative: a custom httpcore network backend (rejected: relies on private httpx internals) or a resolver-pinning dependency (rejected: the issue stops on a new dependency).
- **D-3 Proxies.** `trust_env=False` and no proxy. Alternative: honor environment proxies (rejected: the proxy resolves names and defeats pinning). Compatibility: see UNK-02.
- **D-4 Redirects.** A manual loop of at most 5 hops with per-hop revalidation, the caller supplying the host policy. Alternative: `follow_redirects=True` (rejected: unvalidated hops). Only 301, 302, 303, 307, and 308 with a `Location` are followed; a relative `Location` is resolved against the current URL.
- **D-5 Limits.** Four independent named limits: raw bytes 2 MiB (network), decoded bytes 8 MiB (after content-decoding), parser-input bytes 2 MiB (text handed to the parser), returned bytes from `browser_max_response_kb`. Reaching the raw or decoded limit stops the stream and sets `download_truncated`; the parser-input limit caps the text given to the parser; the returned limit keeps setting `truncated`. A declared `Content-Length` is only an early signal and never raises a limit. Values are proposals (UNK-01).
- **D-6 Content types.** `text/html` goes through the HTML parser; `text/plain` is decoded and returned without the parser; everything else, including a missing type and `application/xhtml+xml`, is rejected before reading the body.
- **D-7 Error model.** New typed errors derive from the existing hierarchy so the existing server handlers keep working: status errors and unsupported-content errors derive from `WebSearchUpstreamError` (502), with a `category` attribute used for the metrics `error_type`; prohibited addresses stay `BrowserAuthorizationError` (403). Health failures are 429, 5xx, resolution failure, network, and timeout; 4xx, unresolved 3xx, unsupported content, and authorization errors are metrics-only, matching the existing rule that caller or target problems are not provider-health signals.
- **D-8 Helper placement.** `scripts/mcp_servers/address_policy.py` and `scripts/mcp_servers/bounded_fetch.py`: `mcp_servers` may not import `rag` and `shared` may not import `mcp_servers`, and both consumers are in `mcp_servers`. The helper takes the transport and resolver as parameters so tests inject fakes.

Consumer scan (`tools/scan_change_consumers.py` policy, checked in Step 3): `BrowserFetchResponse` consumers are `formatters.py`, `web_search_service.py`, `web_search_server.py`, and the web search tests (all targets); no persisted schema or shared constant changes. Predictable fallout check (checked in Step 3): module size gate `not affected` (see above); pinned counts `not affected` (no inventory changes); tool inventory `not affected` (no `tools/*.py`); generated blocks `not affected`; the tool schema (`web_search_tools.py`) is unchanged because the request arguments do not change (`not affected: no input schema change`).

Persisted schema check: `not applicable` (no SQLite change).

## Implementation steps
1. **Phase 1: Address policy (REQ-001, REQ-008)**
   - [ ] Write the prohibited-address tests first and confirm they fail on the current code (REQ-001; tests/mcp_servers/test_address_policy.py)
   - [ ] Create the address policy module (REQ-001, REQ-008; scripts/mcp_servers/address_policy.py)
2. **Phase 2: Bounded fetch helper (REQ-002 to REQ-006, REQ-008)**
   - [ ] Write the pinning, redirect, status, type, and limit tests first (REQ-002 to REQ-006; tests/mcp_servers/test_bounded_fetch.py)
   - [ ] Create the helper (REQ-002 to REQ-006, REQ-008; scripts/mcp_servers/bounded_fetch.py)
3. **Phase 3: Wire `browser_fetch` and classify results (REQ-004, REQ-006, REQ-007)**
   - [ ] Add the typed errors and response fields (REQ-004, REQ-006, REQ-007; scripts/mcp_servers/web_search/web_search_models.py)
   - [ ] Call the helper from `fetch_browser` with the allowlist policy; reverse the 404 test and adapt the mocks (REQ-001 to REQ-007; scripts/mcp_servers/web_search/search_provider.py, tests/mcp_servers/web_search/test_web_search_provider.py)
   - [ ] Classify metrics and health, audit type, and formatted output (REQ-007; scripts/mcp_servers/web_search/web_search_service.py, scripts/mcp_servers/web_search/web_search_server.py, scripts/mcp_servers/web_search/formatters.py, tests/mcp_servers/web_search/test_web_search_service.py, tests/mcp_servers/web_search/test_web_search_server.py, tests/mcp_servers/web_search/test_web_search_formatters.py)
4. **Phase 4: Documentation (REQ-009)**
   - [ ] Update the `browser_fetch` boundary section (REQ-009; docs/22_mcp/mcp_04_01_web-search-file-read-github.md)
5. **Phase 5: Deployment & Verification**
   - [ ] Run `uv run python tools/run_validation_gates.py --full`, `lint-imports`, bandit, and the documentation gates; record the diff-cover number (REQ-001 to REQ-009; all rows)
   - [ ] Hand off to `skills/deploy/SKILL.md` once the change is committed and pushed; deploying is the user's decision and has an approval gate. `scripts/` is rsynced and no config file changes, so `deploy.sh` needs no change; confirm UNK-02 on the host before the restart (REQ-002; scripts/mcp_servers/bounded_fetch.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/address_policy.py | Unit with a fake resolver | `uv run pytest tests/mcp_servers/test_address_policy.py` | Fails first on the old code path, then passes |
| scripts/mcp_servers/bounded_fetch.py | Unit with a fake transport and resolver | `uv run pytest tests/mcp_servers/test_bounded_fetch.py` | Pass |
| scripts/mcp_servers/web_search/*.py | Unit and service-level classification | `uv run pytest tests/mcp_servers/web_search` | Pass |
| All changed Python | Format, lint, type, architecture, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | No new finding |
| Full suite and coverage | Regression | `uv run python tools/run_validation_gates.py --full`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass, changed-line coverage at or above 90% |
| docs/22_mcp file | Documentation consistency | `rules/tool-gates.md` "When to run which tool" checkers | No finding |

## Risks
- **Risk**: The IP-pinned request fails TLS certificate verification for the original hostname (likelihood: medium) → **Mitigation**: the test asserts the `sni_hostname` extension, a live smoke test against an allowlisted public site runs in the implementation phase, and the phase stops and reports (no silent fallback to an unpinned request) if verification fails.
- **Risk**: A legitimate allowlisted site publishes a private address and is now rejected (likelihood: low) → **Mitigation**: fail-closed is the intended policy (D-1); the rejection message names the host and category without echoing the address list.
- **Risk**: Existing respx tests route by hostname and break on the pinned request (likelihood: high) → **Mitigation**: the helper accepts an injected transport and resolver; provider tests use them.
- **Risk**: The proposed limits reject or truncate legitimate pages (likelihood: low-medium) → **Mitigation**: limits are named constants (UNK-01), truncation is reported separately instead of failing, and the owner reviews them.
- **Risk**: A proxy-dependent deployment loses `browser_fetch` (likelihood: low) → **Mitigation**: UNK-02 check before deployment.
- **Risk**: Streaming decode bounds are implemented incorrectly and a decompression bomb passes (likelihood: low) → **Mitigation**: dedicated gzip-expansion, chunked, and false-length tests (AC-05).
- **Risk**: `web_search_models.py` has high blast radius (likelihood: medium) → **Mitigation**: additive classes and defaulted response fields only; the full suite runs.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Address policy | Pending | — | — | |
| 2 | Bounded fetch helper | Pending | — | — | |
| 3 | Wire `browser_fetch` and classify results | Pending | — | — | |
| 4 | Documentation | Pending | — | — | |
| 5 | Deployment & Verification | Pending | — | — | |

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
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-114539
- **Related target files**: scripts/mcp_servers/address_policy.py, scripts/mcp_servers/bounded_fetch.py, scripts/mcp_servers/web_search/search_provider.py, scripts/mcp_servers/web_search/web_search_models.py, scripts/mcp_servers/web_search/web_search_service.py, scripts/mcp_servers/web_search/formatters.py, scripts/mcp_servers/web_search/web_search_server.py, tests/mcp_servers/test_address_policy.py, tests/mcp_servers/test_bounded_fetch.py, tests/mcp_servers/web_search/test_web_search_provider.py, tests/mcp_servers/web_search/test_web_search_service.py, tests/mcp_servers/web_search/test_web_search_formatters.py, tests/mcp_servers/web_search/test_web_search_server.py, docs/22_mcp/mcp_04_01_web-search-file-read-github.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `search_provider.py:90-123` | scripts/mcp_servers/address_policy.py | Phase 1 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1; `search_provider.py:168-169` | scripts/mcp_servers/web_search/search_provider.py | Phase 3 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; httpx `sni_hostname` extension | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-02 | T-02 | Derived from confirmed evidence |
| REQ-003 | Required Changes bullet 3; httpx `follow_redirects=False` default | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-03 | T-03 | Derived from confirmed evidence |
| REQ-004 | Required Changes bullet 4; `search_provider.py:178` | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-004 | Required Changes bullet 4; `web_search_models.py:22-46` | scripts/mcp_servers/web_search/web_search_models.py | Phase 3 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 5; `search_provider.py:134-144,171-172` | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-006 | Required Changes bullet 6 | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-05 | T-05 | Explicit in issue |
| REQ-006 | Required Changes bullet 6 | scripts/mcp_servers/web_search/web_search_models.py | Phase 3 | AC-05 | T-05 | Explicit in issue |
| REQ-007 | Required Changes bullet 7; `web_search_service.py:130-199` | scripts/mcp_servers/web_search/web_search_service.py | Phase 3 | AC-07 | T-06 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 7; `formatters.py:42-52` | scripts/mcp_servers/web_search/formatters.py | Phase 3 | AC-06 | T-06 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 7; `web_search_server.py:294-310` | scripts/mcp_servers/web_search/web_search_server.py | Phase 3 | AC-07 | T-06 | Confirmed by repository evidence |
| REQ-007 | Required Changes bullet 7; `web_search_models.py:314-321` | scripts/mcp_servers/web_search/web_search_models.py | Phase 3 | AC-06 | T-06 | Confirmed by repository evidence |
| REQ-008 | Required Changes bullet 8; `cicd_service_github_actions_job.py:85` | scripts/mcp_servers/address_policy.py | Phase 1 | AC-01 | T-01 | Explicit in issue |
| REQ-008 | Required Changes bullet 8 | scripts/mcp_servers/bounded_fetch.py | Phase 2 | AC-03 | T-03 | Explicit in issue |
| REQ-009 | Documentation Impact; `mcp_04_01...md:44-55` | docs/22_mcp/mcp_04_01_web-search-file-read-github.md | Phase 4 | AC-08 | T-07 | Explicit in issue |
