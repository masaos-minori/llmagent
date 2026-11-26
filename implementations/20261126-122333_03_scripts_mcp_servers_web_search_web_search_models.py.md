## Goal
- Add the typed carriers the fetch boundary needs: errors for non-2xx outcomes and unsupported content (REQ-004, REQ-006), and result metadata that separates download truncation from extracted-text truncation (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: two exception classes and two defaulted fields on `BrowserFetchResponse` in `scripts/mcp_servers/web_search/web_search_models.py`.
- Out of scope: configuration parsing, request models, and allowlist validation (the sibling configuration and audit Plan edits other symbols of this file).

## Assumptions
- Overlap judgment (Plan overlap check): the configuration and audit Plan also modifies this file, on configuration and request-model symbols. This document adds exception classes and response fields only, so the two are compatible; implementation phases rebase onto each other.
- This document is implemented before the search provider procedure (seq 04), which imports the new classes; the filename order encodes that dependency (the Plan rows were reordered in Step 3a so the models row precedes the provider row).
- Verified in Step 3a: `WebSearchUpstreamError` is a `RuntimeError` mapped to HTTP 502 by the server handler (`web_search_server.py:111-119`); `BrowserAuthorizationError` is a `RuntimeError` (403) and `BrowserValidationError` a `ValueError` (422) (`web_search_models.py:22-46`).

## Design decisions
- Both new errors derive from `WebSearchUpstreamError`: they describe the upstream site's answer, not caller input, so the existing 502 handler applies and the dispatcher's `except ValueError` does not swallow them (Plan decision D-7).
- New response fields have defaults, so existing constructions (including test fixtures) stay valid.

## Alternatives considered
- Derive the status error from `BrowserValidationError`: rejected, it is a `ValueError` that the dispatcher converts to a validation result and the server would report it as a 422 caller error.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_models.py`

### Procedure
1. After `BrowserValidationError`, add `BrowserHttpStatusError` (new), a subclass of `WebSearchUpstreamError`, with attributes status_code (int) and category (str) (one of `redirect`, client_error, rate_limited, `server_error`, `other`); its constructor takes `(message, status_code, category)` and passes the message to the base class.
2. Add `BrowserUnsupportedContentError` (new), a subclass of `WebSearchUpstreamError`, with attribute content_type (str); constructor `(message, content_type)`.
3. In `BrowserFetchResponse` add `download_truncated` (new), a bool defaulting to false, and `content_type` (new), a string defaulting to empty, after `elapsed_sec`; keep `truncated` meaning "the extracted text was cut".
4. Update the class docstrings to state those meanings.

### Method
- Plain classes; no behavior beyond storing the attributes. The status category vocabulary matches the bounded fetch helper's `category` values (seq 02) plus `redirect` for unresolved or over-bound redirects.

### Details
- Field order and defaults keep `BrowserFetchResponse(text=..., truncated=..., url=..., status_code=..., elapsed_sec=...)` valid for the existing formatter and service tests.

## Compatibility considerations
- Additive: a caller that ignores the new fields and errors is unaffected; the new errors surface through the existing 502 handler.

## Security considerations
- Error messages must not carry the upstream body; they carry the status code, category, and content type only.

## Rollback considerations
- N/A: revert the commit (later procedures import these names, so revert them together).

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py tests/mcp_servers/web_search/test_web_search_formatters.py tests/mcp_servers/web_search/test_web_search_service.py` still pass; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `uv run lint-imports`; then the sequence in `rules/toolchain.md`. New behavior is covered by the provider test procedure (seq 10).

## Completion criteria
- Both classes exist with the stated bases and attributes; `BrowserFetchResponse` carries the two defaulted fields; existing tests of these modules pass unchanged; all validation commands pass.

## Out of Scope
- Raising the errors (seq 04), classifying them (seq 05, 07), formatting the fields (seq 06), configuration and request-model changes, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Confirm the existing tests listed in Validation plan still pass | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (typed status error), `REQ-006` (unsupported-content error), `REQ-007` (truncation metadata)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/web_search/web_search_models.py`
