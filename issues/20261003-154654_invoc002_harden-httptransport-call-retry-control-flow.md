# Harden HttpTransport.call retry control flow

## Priority
Low

## Summary
`shared/http_transport.py::HttpTransport.call()` uses a `for...else` loop whose control flow has two defects: a malformed `/v1/call_tool` response is retried up to three times despite being deterministic, and the trailing `raise last_exc or TransportError(...)` is unreachable. Simplify the loop so non-transient failures fail immediately and the exit paths are explicit.

## Background
`call()` is the single HTTP entry point for every MCP tool invocation. It retries on a fixed set of retryable status codes (`{429, 502, 503, 504}`) and classifies other failures via a `for...else` construct: timeout and non-retryable `HTTPStatusError` raise inside their `except` block, retryable statuses `continue`, and the loop's `else` clause raises a retry-exhaustion message on completion.

## Problem
Two related control-flow weaknesses exist in `call()`:

1. A malformed response (`result` missing/non-str, `is_error` non-bool, or invalid JSON) raises `ValueError` inside `_parse_http_response()`. That `ValueError` is caught by `except (httpx.RequestError, ValueError)`, which does not set `break_flag` and does not `continue`/`return`/`raise` — so the loop simply iterates again and re-issues the request. Because a malformed body is deterministic, all three attempts fail identically, wasting up to `2**0 + 2**1` seconds of exponential backoff plus network time for a failure that can never succeed on retry.

2. The final `raise last_exc or TransportError(f"call failed: {name}")` line is unreachable. Every iteration either returns (success), raises inside an `except` block (timeout / non-retryable status), `continue`s (retryable status), or falls through to the `for...else` clause, which already raises the exhaustion message. Nothing ever reaches the trailing statement.

## Reason for Change
The malformed-response retry adds latency with zero recovery value on every persistent server misconfiguration or schema mismatch, and the fragile `for...else` + shadowed `last_exc` pattern is a footgun: a future edit that introduces another `break_flag=False` path would expect `last_exc` to surface but would instead be swallowed by the `else` clause, producing confusing "call failed" errors instead of the real cause.

## Implementation Intent
Make non-transient failures fail fast and make exit paths explicit. On a `ValueError` from response parsing, return/raise immediately rather than looping. Collapse the `for...else` + trailing-raise into a clear structure where retryable statuses loop and everything else resolves to a single, well-defined error. Preserve the current retryable-status set, the `2**attempt` exponential backoff, the retry-exhaustion message wording, and the distinction between `transport` and `tool` error surfaces downstream.

## Target Files or Areas
- `scripts/shared/http_transport.py`
- `tests/shared/test_tool_executor.py` (`TestHttpTransportRetry`)
- `tests/shared/test_tool_executor_routing.py` (`TestHttpTransportErrors`)

## Required Changes
- On `ValueError` raised by `_parse_http_response()`, fail immediately (do not retry) — a malformed body is non-transient.
- Remove or replace the unreachable `raise last_exc or TransportError(...)` statement so the loop has exactly one explicit failure-exit per non-retryable path.
- Keep retryable-status handling (`429/502/503/504`, exponential sleep, exhaustion message) unchanged.

## Constraints
- Do not change which status codes are retryable, the retry count, or the backoff schedule.
- Do not change the `ToolCallResult`/`TransportError` shapes observed by callers.
- Preserve redaction/logging behavior (no response bodies or secrets in logs).

## Acceptance Criteria
- A persistently malformed response now fails after a single attempt instead of three.
- Retryable statuses still retry the configured number of times and then raise the exhaustion message.
- Non-retryable HTTP errors still raise `TransportError` with the same `[HTTPStatusError]` prefix and `status=` detail.
- No unreachable code remains in `call()`.

## Testing Expectations
- Add/adjust a test asserting a malformed body raises `TransportError` after exactly one `post` call (not three).
- Re-run `TestHttpTransportRetry` and `TestHttpTransportErrors` unchanged for the retryable/non-retryable paths.
- Confirm `ruff check` / `mypy` / `bandit` pass on `http_transport.py`.

## Documentation Impact
None required.

## Out of Scope
- Changing the retryable-status set or retry/backoff policy.
- Adding client-side response-size limits or new validation beyond the current schema checks.
- Refactoring other methods in the module.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Behavior-preserving cleanup of `HttpTransport.call()`. Make malformed-response (`ValueError`) fail fast instead of retrying, and remove the unreachable trailing `raise`. Do NOT touch the retryable-status set, retry count, backoff, or error shapes. Add a regression test asserting a malformed body fails after one attempt. Stop and report if the current `for...else` semantics hide a retry path you cannot map precisely.

## Traceability
- **Workflow phase**: python-code-review via issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-154654
- **Related target files**: scripts/shared/http_transport.py
