# HttpTransport retries non-retryable HTTP statuses and loses HTTPStatusError context in the final exception message

## Priority
High

## Summary
`HttpTransport.call()` in `scripts/shared/http_transport.py` retries HTTP status errors that
are outside its retryable set (e.g. 400/500), contradicting the "non-retryable" classification,
and the final raised `TransportError` message is a generic `"[Retry exhausted]"` string that
does not mention the originating `HTTPStatusError` or status code.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/http_transport.py`
(2026-08-13). Two pre-existing tests fail and were confirmed unrelated to that refactor by
reproducing them identically before and after the change:
- `tests/shared/test_tool_executor.py::TestHttpTransportRetry::test_non_retryable_http_status_not_retried`
- `tests/shared/test_tool_executor_routing.py::TestHttpTransportErrors::test_http_status_error_raises_transport_error`

Root cause (Evidence label: Strongly implied by code — confirmed by the two failing tests'
actual vs. expected behavior): `resp.raise_for_status()` raises `httpx.HTTPStatusError` for
*any* non-2xx status, but the surrounding exception handling in `call()` treats it like any
other retryable failure and re-runs the loop for the full `_RETRY_MAX` attempt count regardless
of status code, then raises a generic `"[Retry exhausted] tool=... url=... after N attempts"`
message that drops the `HTTPStatusError`/status-code context.

This is a correctness issue: callers relying on `tool_executor.py`/`tool_transport_invoker.py`
retry semantics may retry requests that should fail fast (e.g. 400 Bad Request), and error
messages surfaced to logs/audits lose the actual failure reason.

## Implementation Intent
Classify `HTTPStatusError` by status code before deciding whether to retry (reuse or align with
the existing retryable-status-code set already used elsewhere in `scripts/shared/llm_retry.py`'s
`_TRANSIENT_HTTP_STATUS_CODES` pattern, if applicable to this module's own retry policy).
Preserve the original `HTTPStatusError`'s status code and message in the exception raised when
retries are exhausted or when a non-retryable status is hit immediately.

## Target Files or Areas
- `scripts/shared/http_transport.py` (`HttpTransport.call`)
- `tests/shared/test_tool_executor.py`
- `tests/shared/test_tool_executor_routing.py`

## Required Changes
- Determine the intended retryable-status-code set for this module (may already be documented
  in test names/expectations — see the two failing tests above).
- Short-circuit (no retry loop) when a non-retryable `HTTPStatusError` is hit.
- Include the status code and/or original exception type in the final `TransportError` message
  raised on both the non-retryable and retry-exhausted paths.

## Acceptance Criteria
- `test_non_retryable_http_status_not_retried` and `test_http_status_error_raises_transport_error`
  pass without weakening their assertions.
- No new retry-loop iteration occurs for a non-retryable status code.
- Existing retryable-status tests (429/503) continue to retry as before.

## Testing Expectations
Unit tests covering: non-retryable status (e.g. 400/404/500 if outside the retryable set) fails
immediately with context-preserving message; retryable status (429/503) still retries up to the
existing limit; retry-exhaustion message still names the originating error.

## Documentation Impact
None expected beyond the code itself — this is an internal retry-classification bug, not a
documented public contract change.

## Out of Scope
- Do not change the retry loop's backoff timing/formula.
- Do not change `tool_executor.py`/`tool_transport_invoker.py` call sites unless the exception
  message format they depend on changes.

## AI Implementation Instruction
Read `scripts/shared/http_transport.py::HttpTransport.call` and the two failing tests in full
before changing anything. Keep the change scoped to status-code classification and message
content; do not restructure the retry loop's control flow beyond what's needed. Run
`uv run pytest tests/shared/test_tool_executor.py tests/shared/test_tool_executor_routing.py -v`
before and after to confirm only the two named tests change from fail to pass.
