# Correct MCP HTTP retry, backoff, and safe error diagnostics

## Priority
Medium

## Summary
The MCP HTTP transport's retry loop currently computes backoff as `2 ** (_RETRY_MAX - attempt - 1)` (confirmed at `scripts/shared/http_transport.py` line 115, comment "# 4, 2, 1"), which decreases with each attempt instead of increasing, and may sleep even after the final attempt; this issue corrects the delay to increasing exponential backoff applied only between actual retries, and separately ensures error diagnostics never expose raw MCP response bodies.

## Background
N/A: covered by Summary — this is a direct code-level finding in the HTTP transport retry loop, not derived from a prior design decision document.

## Problem
With `_RETRY_MAX = 3`, the current backoff formula produces delays of 4, 2, 1 seconds across the three attempts (decreasing), rather than an increasing backoff that would normally follow 1, 2 seconds between two retries after the first attempt. It is also not confirmed whether a sleep occurs after the final (non-retried) attempt, wasting time with no subsequent retry to justify it. Separately, raw response text/bodies may currently be included in transport errors or `ToolCallResult.output`, and secret-redaction may not be applied to server-provided fields before logging.

## Reason for Change
Retry timing and error reporting share the same HTTP failure loop. The current backoff decreases from 4 to 2 to 1 seconds and sleeps after the final attempt, while raw error bodies may be logged or returned. Correcting only one aspect would retain either unnecessary latency or information exposure.

## Implementation Intent
Use increasing exponential backoff only between actual retry attempts and preserve safe, useful diagnostics without exposing raw MCP response bodies.

## Target Files or Areas
- `scripts/shared/http_transport.py`
- `tests/shared/test_tool_executor.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/logger.py`

## Required Changes
- Change the delay calculation to increasing exponential backoff.
- Sleep only when another retry will be attempted.
- For `_RETRY_MAX = 3`, use delays of 1 and 2 seconds.
- Record the last retryable HTTP status before retrying.
- Include the final status and request ID, when available, in the exhausted-retry diagnostic without exposing the raw response body.
- Rename and correct retry tests so they assert increasing delays and exactly two sleeps.
- Remove raw response text from transport errors and tool results.
- Record only safe fields such as status code, request ID, server key, tool name, and a sanitized error code.
- Preserve the last retryable status for retry-exhausted diagnostics.
- Apply the project secret-redaction mechanism before logging any server-provided field.
- Add tests with synthetic secrets and sensitive payload fragments in error responses.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Three total attempts produce exactly two waits.
- The waits occur in the order 1 second, then 2 seconds.
- No sleep occurs after the final failed attempt.
- HTTP 429, 502, 503, and 504 use the same corrected policy.
- Timeouts and non-retryable statuses remain non-retryable unless separately specified.
- Tests assert `TransportError`, not a generic exception.
- Raw MCP response bodies never appear in logs or `ToolCallResult.output`.
- Retry exhaustion reports the final HTTP status safely.
- Request IDs remain available for correlation.
- Redaction tests prove that configured secrets and payload fragments are not emitted.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path (see Acceptance Criteria and Required Changes' test items), including tests with synthetic secrets in error responses. Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to the retry/backoff calculation and error-diagnostic sanitization in `scripts/shared/http_transport.py`; do not rewrite unrelated transport logic. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration — this is the core purpose of this issue's second half, not an incidental check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103224
- **Related target files**: scripts/shared/http_transport.py, tests/shared/test_tool_executor.py, scripts/shared/tool_transport_invoker.py, scripts/shared/logger.py
