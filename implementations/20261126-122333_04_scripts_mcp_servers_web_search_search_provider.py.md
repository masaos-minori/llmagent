## Goal
- Make `fetch_browser` a thin caller of the bounded fetch helper: allowlist host policy, address validation and pinning, redirect bound, 2xx-only results, text types only, independent limits, and separate truncation metadata (REQ-001 to REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `fetch_browser` and its module-level constants in `scripts/mcp_servers/web_search/search_provider.py`.
- Out of scope: `_check_domain` normalization (the sibling configuration and audit Plan edits that function), metrics and health classification, and formatting.

## Assumptions
- Overlap judgment (Plan overlap check): the configuration and audit Plan also modifies this file, in `_check_domain` (host normalization). This document keeps `_check_domain` unchanged and uses it as the host policy, so the edits are on different symbols and compatible; `_check_domain` stays the allowlist policy the helper calls.
- Implemented after the address policy (seq 01), the bounded fetch helper (seq 02), and the models procedure (seq 03), whose names it imports.
- Verified in Step 3a: the current `fetch_browser` does one `client.get`, no status check, parses the whole body, and truncates only extracted text (`search_provider.py:147-180`); httpx raised exceptions propagate raw today and the service classifies them as `fetch_error` (existing tests `test_fetch_timeout_propagates_raw_httpx_exception`).
- The web search `_extract_text` and `_truncate` helpers stay in this module.

## Design decisions
- Limits are module constants (Plan decision D-5, values adjustable by the owner): raw 2 MiB, decoded 8 MiB, parser input 2 MiB, returned bytes from the existing clamped `max_response_kb`.
- Error translation happens here, not in the helper, so the helper stays free of web search types: a prohibited address becomes `BrowserAuthorizationError`; a failed resolution becomes `WebSearchNetworkError`; helper status and redirect errors become `BrowserHttpStatusError`; type and encoding errors become `BrowserUnsupportedContentError`.

## Alternatives considered
- Let helper errors propagate raw: rejected, the service and server classify by the web search hierarchy.

## Implementation
### Target file
`scripts/mcp_servers/web_search/search_provider.py`

### Procedure
1. Add imports from `mcp_servers.address_policy` (the error type), `mcp_servers.bounded_fetch` (the fetch function, limits, result, and its four error types), and the two new web search errors from `web_search_models`.
2. Add constants for the three fixed limits and the allowed media types (`text/html`, `text/plain`).
3. Rewrite the body of `fetch_browser`: keep the domain check call for early rejection, keep the `max_response_kb` clamp, then call the helper with a host policy that runs `_check_domain` against the same allowlist set, the limits (returned bytes = clamped value times 1024), the allowed types, and `cfg.timeout_sec`.
4. Translate the helper's exceptions as in Design decisions; let `httpx` timeout and connection errors propagate raw.
5. Decode the body with the reported charset (default UTF-8, `errors="replace"`); for `text/html` call `_extract_text`, for `text/plain` use the decoded text stripped; apply `_truncate` with the returned-bytes limit.
6. Build `BrowserFetchResponse` with `truncated` from `_truncate`, `download_truncated` from the helper result, `content_type`, `url` as requested, `status_code`, and `elapsed_sec` from the helper.
7. Update the module and function docstrings (steps list and raises).

### Method
- The host policy is a small closure over the allowlist set; it returns the validated hostname as `_check_domain` does, so every redirect hop is checked against the same allowlist.
- The status code in the response is always the 2xx code of the final hop.

### Details
- The existing test that expects a 404 body to pass through is reversed in the provider test procedure (seq 10); respx hostname mocks there are replaced by the helper's injectable transport and resolver, which `fetch_browser` exposes to tests as keyword-only parameters `resolver` and `transport`, both defaulting to `None` (production callers never pass them; the service calls `fetch_browser(req, cfg)` unchanged).

## Compatibility considerations
- Behavior change by design: 3xx, 4xx, 429, and 5xx now raise instead of returning page text; non-text types are rejected; large bodies are cut at the download limits. The response model stays constructible as before.

## Security considerations
- Closes the DNS-resolved SSRF gap and bounds network, decompression, and parser input before parsing. Messages from the translated errors must not include the resolved address list or the upstream body.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_provider.py tests/mcp_servers/test_bounded_fetch.py tests/mcp_servers/test_address_policy.py`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `uv run bandit -r scripts/mcp_servers/web_search/search_provider.py -c pyproject.toml`; a live smoke test against one allowlisted public HTTPS site confirms certificate verification with the pinned address; then the sequence in `rules/toolchain.md`.

## Completion criteria
- `fetch_browser` returns text only for a 2xx text response from an allowlisted host whose answers are all public; each error class listed in Design decisions is raised for its trigger; the returned limit still clamps to the server maximum; the provider tests (seq 10) pass; all validation commands pass.

## Out of Scope
- Metrics, health, and audit classification (seq 05, 07), formatted output (seq 06), `_check_domain` normalization, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the provider tests of the seq 10 procedure against the change | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (address validation), `REQ-002` (pinned connection), `REQ-003` (redirects), `REQ-004` (status), `REQ-005` (limits), `REQ-006` (content types), `REQ-007` (truncation metadata)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/web_search/search_provider.py`
