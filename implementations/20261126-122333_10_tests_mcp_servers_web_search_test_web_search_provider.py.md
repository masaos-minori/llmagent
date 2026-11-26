## Goal
- Update the provider tests so they pin the new fetch boundary: reverse the HTTP 404 passthrough expectation and add prohibited-address, redirect, content-type, and limit cases at the `fetch_browser` level (REQ-001 to REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tests/mcp_servers/web_search/test_web_search_provider.py`.
- Out of scope: the helper's own unit tests (the bounded fetch and address policy companions) and the service, formatter, and server tests (their companions).

## Assumptions
- Overlap judgment (Plan overlap check): the configuration and audit Plan also modifies this test file, for normalized host matching in `_check_domain`. This document edits the `TestFetchBrowser` class and adds new cases; the other Plan edits the `_check_domain` class. Different classes, compatible; phases rebase onto each other.
- This file is named by two rows of the Plan (the models and provider rows), so it keeps its own document instead of being a companion.
- Implemented after the provider procedure (seq 04); the prohibited-address and redirect tests are written first and must fail on the old code.
- Verified in Step 3a: the current fetch tests use `respx` mocks keyed by hostname and a `_make_browser_config` helper (`test_web_search_provider.py:35-45,222-300`), which no longer match once the request targets a pinned IP; `fetch_browser` gains keyword-only `resolver` and `transport` parameters for tests (seq 04).

## Design decisions
- Replace the `respx` fetch mocks with `httpx.MockTransport` and a fake resolver passed through the new parameters, keeping `respx` for the `search_duckduckgo` tests if they use it.
- Keep one end-to-end test per behavior; detailed network cases live in the helper's tests.

## Alternatives considered
- Keep `respx` with IP-keyed routes: rejected, it ties tests to the pinning implementation and cannot assert the `Host` header and sni_hostname extension as directly.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_provider.py`

### Procedure
1. Add a small fixture or helper that builds a fake resolver returning a given address list and a `MockTransport` handler.
2. Rewrite `test_fetch_returns_extracted_text` and `test_fetch_clamps_caller_max_response_kb_to_server_max` on the new hooks.
3. Reverse `test_fetch_non_2xx_response_passthrough` into a test that a 404 raises the status error and returns no body text; add cases for 301 without `Location`, 403, 429, 500, and 503 with their categories.
4. Add: an allowlisted host resolving to a loopback, a private, a metadata, and an IPv4-mapped address is rejected with the authorization error before any request; a mixed answer is rejected; a resolution failure raises the network error; a redirect to a non-allowlisted host is rejected and a redirect within the allowlist is followed.
5. Add: a PDF, an image, and a missing content type are rejected before the HTML parser (patch `_extract_text` to fail the test if called); `text/plain` is returned without the parser; a download cut sets `download_truncated` while an extracted-text cut sets `truncated`.
6. Keep `test_fetch_disallowed_domain_raises_before_network_call` and `test_fetch_timeout_propagates_raw_httpx_exception`, adapted to the new hooks.

### Method
- The transport handler records each request so tests can assert that no request was sent for the rejected-address cases.

### Details
- Do not weaken any existing `_check_domain` test.

## Compatibility considerations
- Test-only; the reversed 404 test documents the intentional behavior change.

## Security considerations
- Tests use only documentation-range and reserved addresses and never perform a real DNS lookup or network call.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_provider.py`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The 404 passthrough expectation is reversed; each listed case passes; the new tests fail on the pre-change provider; no real network access occurs; all validation commands pass.

## Out of Scope
- Helper unit tests, service, formatter, server tests, and the `_check_domain` normalization tests of the sibling Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the new and reversed tests described in Implementation > Procedure | Pending | — | — | |
| 2 | Confirm the new tests fail on the pre-change provider and pass after seq 04 | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` to `REQ-007` (provider-level behavior of the fetch boundary)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `tests/mcp_servers/web_search/test_web_search_provider.py`
