## Goal
- Classify every `browser_fetch` outcome for metrics and health so the recorded error type matches the result category: 429, 5xx, resolution failure, network, and timeout count as browser health failures; caller, redirect, 4xx, and content errors are metrics-only (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_classify_browser_error` and the exception handling of `fetch_browser` in `scripts/mcp_servers/web_search/web_search_service.py`, plus its test companion.
- Out of scope: the audit `error_type` of the server (seq 07), formatting (seq 06), and `search_web` handling.

## Assumptions
- Implemented after the models procedure (seq 03) and the provider procedure (seq 04), which define and raise the new errors.
- Verified in Step 3a: validation and authorization errors are metrics-only and every other exception is both a metrics failure and a browser health failure (`web_search_service.py:145-199`); health and metrics are recorded only in this module.
- Plan overlap check: this file overlaps no other Frozen Plan.

## Design decisions
- Error-type vocabulary (stable, lowercase snake): `authorization_error`, `validation_error`, `http_redirect`, `http_client_error`, `http_rate_limited`, `http_server_error`, `http_other`, unsupported_content, `network_error`, `fetch_error` (everything else, including httpx timeouts and connection errors, as today).
- Health-neutral set: authorization, validation, `http_redirect`, `http_client_error`, unsupported_content. All other types also call the browser health failure hook.

## Alternatives considered
- N/A: lightweight row; the vocabulary follows the existing `search_web` classification style.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_service.py`

### Procedure
1. Import the two new errors (status and unsupported content) and keep `WebSearchNetworkError` (already imported).
2. Extend `_classify_browser_error` to return the vocabulary above, using the status error's `category` attribute for the `http_*` names.
3. Add a small predicate `_is_health_neutral(error_type)` over the health-neutral set.
4. Restructure the exception handling in `fetch_browser`: one `except` for the broad failure path that records the metrics failure, and calls the health failure hook only when `_is_health_neutral` (new) is false; the validation and authorization branch stays as is.
5. Update the docstrings of `_classify_browser_error` and `fetch_browser` (raises and recording rules).

### Method
- The broad `except Exception` branch already records metrics and health; the change is only the neutral-type check before the health call, so there is exactly one metrics record per call and no change to the success path.

### Details
- The type strings are the contract that the server audit mapping (seq 07) reproduces.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_service.py`
  - Procedure: patch `_provider_fetch_browser` to raise each error type (status with each category, unsupported content, network error, authorization, validation, an httpx timeout) and assert the recorded metrics `error_type` and whether `health.record_browser_failure` was called; assert a success records neither a failure nor changes `last_error_type`.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_service.py`.

## Compatibility considerations
- Metrics `last_error_type` gains new values; no consumer enumerates the old three values (`rg last_error_type scripts tests` shows `/health` details passthrough and tests only).

## Security considerations
- N/A: classification only; messages and bodies are not logged here.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_service.py tests/mcp_servers/web_search/test_web_search_health.py tests/mcp_servers/web_search/test_web_search_metrics.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Each category records its documented `error_type`; health failures are recorded for exactly the non-neutral types; existing service tests pass; all validation commands pass.

## Out of Scope
- Server audit mapping, formatting, the provider, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-133732 | 20261126-133732 | Changed: scripts/mcp_servers/web_search/web_search_service.py |
| 2 | Add the companion test cases first, then confirm they pass | Completed | 20261126-133732 | 20261126-133732 | Changed: tests/mcp_servers/web_search/test_web_search_service.py (the success test now patches the provider instead of a hostname-keyed respx mock that performed a real DNS lookup) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-133732 | 20261126-133732 | ruff format/check, mypy (CI invocation), lint-imports, bandit, module size, docstring, reference table, validation gates passed; full suite (parallel, coverage): 26 failed and 88 errors in tests/agent/* and tests/docs/test_command_docs_sync.py from a pre-existing NameError in scripts/agent/commands/cmd_mcp.py, unrelated to this change; no failing test touches a changed file; diff-cover 95% on the changed tracked files; targeted tests pass |

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
- **Requirement ID**: `REQ-007` (metrics and health classification)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/web_search/web_search_service.py`, `tests/mcp_servers/web_search/test_web_search_service.py`
