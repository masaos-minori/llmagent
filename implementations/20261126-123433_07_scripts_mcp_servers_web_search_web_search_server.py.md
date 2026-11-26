## Goal
- Redact audit targets and details, and emit exactly one audit record for every authenticated `/v1/call_tool` call, including disabled-tool and envelope-validation rejections, without changing provider health counts (REQ-004, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_build_audit_target_and_detail`, the `call_tool` gate and emission structure, and a request-validation handler in `scripts/mcp_servers/web_search/web_search_server.py`, plus the test companions.
- Out of scope: the error-type classification for the fetch-boundary Plan's new errors (a separate, already archived Plan whose server procedure edits `_classify_upstream_error`), health and metrics recording (service only), and the posture and health endpoints.

## Assumptions
- Overlap judgment (Plan overlap check): the fetch-boundary Plan's server procedure edits `_classify_upstream_error` only; this document edits the audit target builder, the `call_tool` structure, and adds one exception handler. Different functions; compatible; the phases rebase onto each other. Both procedures use the guard's `emit` only through this document's structure; the other Plan's classifier is called unchanged inside it.
- Implemented after the audit helper procedure (seq 02).
- Verified in Step 3a: the disabled-tool gate returns before `extract_request_context` and before the audited `try/finally` (`web_search_server.py:265-271`); `_build_audit_target_and_detail` records the raw query and URL with previews (`:208-226`); an unknown tool passes the gate and is audited once through dispatch (`_web_search_tool_availability` returns enabled for unknown names, `:91-95`); FastAPI request-body validation errors never reach the handler and have no handler in this module (`rg RequestValidationError scripts/mcp_servers` found none for web search).
- Open items recorded in the Plan: UNK-02 (result count, status class, and truncation flags are not available at the server layer, so they are not recorded here).

## Design decisions
- One `AuditEmission` wraps the whole handler body; the single `finally` emits, so every return and raise path produces exactly one record (Plan decision D-6).
- The disabled-tool outcome is `rejected` with `error_type="tool_disabled"` and never reaches the service, so health counters stay untouched (Plan decision D-7).
- A RequestValidationError handler scoped to `/v1/call_tool` emits one `rejected` record with `error_type="validation_error"` and returns the framework default response (Plan decision D-8).

## Alternatives considered
- Emit from a middleware: rejected, the outcome and error type are known only inside the handler.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. Import `AuditEmission`, `hash_query_value`, and `redact_url` from `mcp_servers.audit`, and RequestValidationError plus the default request_validation_exception_handler from FastAPI.
2. Rewrite `_build_audit_target_and_detail(name, args, latency_ms)`: for `search_web`, target `sha256:` plus `hash_query_value(query)`, detail `max_results=<n> latency_ms=<ms> query_len=<len>`; for `browser_fetch`, target `redact_url(url)`, detail `latency_ms=<ms> host=<normalized host or ->`; for any other name, target `-` and detail `latency_ms=<ms>`. No preview fields remain.
3. In `call_tool`, extract the request context first, create the `AuditEmission`, then move the disabled-tool check inside the guarded `try`: a disabled tool sets outcome `rejected` and error type `tool_disabled` and returns the existing `Tool disabled: <reason>` response.
4. Replace the direct `_audit_log` call in `finally` with `emission.emit(...)` using the redacted target and detail.
5. Add `@app.exception_handler(RequestValidationError)`: when the request path is `/v1/call_tool`, extract the context, emit one `rejected` record with `validation_error` and target `-`, then return `await request_validation_exception_handler(request, exc)`; for any other path, return the default handler's response without auditing.

### Method
- The host in the browser detail is taken from `urlsplit(url).hostname`, normalized through the normalizer when valid and `-` otherwise; the full URL never appears.
- Keep the audit field removal (steps 2 and 4) and the exactly-once structure (steps 3 and 5) as separate commits or separate tested changes, as the issue instructs.

### Details
- The existing broad `except` ladder stays; only the audit emission and the gate position move.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_audit.py`
  - Procedure: replace the plaintext preview assertions (query preview, URL preview) with redaction assertions; add signed-URL, token, OAuth parameter, and personal-data fixtures for `browser_fetch` and a query containing a secret for `search_web`, asserting none of the fixture values appears in the serialized record; assert exactly one record for each of success, disabled tool, unknown tool, validation error, authorization error, and unexpected failure.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_audit.py`.
- `tests/mcp_servers/web_search/test_web_search_server.py`
  - Procedure: assert the disabled-tool response and its single `rejected` record with the context extracted, assert a malformed `/v1/call_tool` body returns 422 and emits one `validation_error` record when authenticated and none without authentication, and assert other routes keep the default validation response.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py`.

## Compatibility considerations
- The audit `target` and `detail` fields change shape (hash and redacted URL instead of raw values) and previews are removed; no consumer in the repository reads them (Plan UNK-01 covers external readers). The HTTP responses are unchanged.

## Security considerations
- No raw query or URL, no query string, fragment, user information, or token-shaped segment reaches the audit record; rejected attempts become visible to operators. Do not log new sensitive data while debugging.

## Rollback considerations
- N/A: revert the commit; the two parts can be reverted independently if committed separately.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_audit.py tests/mcp_servers/web_search/test_web_search_server.py tests/mcp_servers/web_search/test_web_search_health.py`; `uv run ruff format` and `uv run ruff check` on the files; `uv run mypy`; `wc -c` of the server file below 24576; then the sequence in `rules/toolchain.md`.

## Completion criteria
- No audit record contains raw query or URL content; each outcome category yields exactly one record; the disabled and envelope rejections are audited; health counters are unchanged by rejections; all validation commands pass.

## Out of Scope
- Fetch-boundary error classification, service-side recording, result-metadata plumbing (UNK-02), and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the redacted targets and details (audit field removal) | Pending | — | — | |
| 2 | Implement the exactly-once structure and the envelope handler | Pending | — | — | |
| 3 | Add or update the companion tests per Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (redacted targets and details), `REQ-005` (exactly-once audit for every outcome)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`, `tests/mcp_servers/web_search/test_web_search_audit.py`, `tests/mcp_servers/web_search/test_web_search_server.py`
