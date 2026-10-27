# Discarded TransportError in HttpTransport.call() RequestError handler

## Priority
Low

## Summary
In `HttpTransport.call()` (`scripts/shared/http_transport.py`), the `except httpx.RequestError` handler computes a `TransportError` via `_transport_error(...)` but neither raises nor returns it; the value is discarded and the retry loop continues by implicit fall-through. Surface the specific transport error instead of relying on silent loop exit.

## Background
`call()` wraps the HTTP POST in a `_RETRY_MAX` (=3) attempt loop. Every handler inside the loop raises immediately except one:

```python
except httpx.RequestError as e:
    # REQ-006: writes are always retried on a non-timeout
    # httpx.RequestError (this handler), exactly like read tools.
    ...
    self._transport_error(name, error_type_tag, str(e))
```

The other handlers (`httpx.TimeoutException`, `httpx.HTTPStatusError`, `ValueError`) each `raise self._transport_error(...)`. The `RequestError` handler is the only one whose `_transport_error` return value is thrown away. The loop's trailing code builds a generic exhaustion message and raises a fresh `TransportError`:

```python
msg = self._build_exhaustion_message(name, last_retryable_status)
logger.error(msg)
raise TransportError(msg)
```

## Problem
- The specific transport failure (its type tag, the underlying `httpx` exception text, and the `/health` hint appended by `_transport_error`) is logged once but never propagated to the caller. After three request errors the caller only sees `[Retry exhausted] tool=<name> after 3 attempts`, which does not say the failures were network/connect errors versus something else.
- Correctness depends on implicit control flow: because the `except` block is the last statement in the loop body, falling off it is equivalent to `continue`. There is no explicit `continue`. If any statement is later added after this `except` block, or the loop body is reordered, the retry behavior changes silently with no compiler or linter signal.
- Asymmetry with sibling handlers: timeout, HTTP-status, and value errors all fail fast with a precise message; only request errors retry-and-discard, so their detail is the only one ever lost.

## Reason for Change
The retry-on-request-error behavior is intentional (REQ-006) and currently correct, so this is not a runtime bug. It is flagged as a maintainability/robustness defect: a discarded return value that the code relies on by accident rather than by declaration invites a future silent regression and hides diagnostic detail.

## Implementation Intent
Make the intended control flow explicit and preserve the specific error. Either (a) add an explicit `continue` after logging so the retry is declared, or (b) raise the specific `TransportError` on the final attempt so the real cause reaches the caller. Choose the option that keeps REQ-006 semantics (non-timeout request errors retry within the loop) intact. Name the responsibility (explicit retry / preserve error detail) rather than a specific line.

## Target Files or Areas
- `scripts/shared/http_transport.py` — `HttpTransport.call()`, `_transport_error()`

## Required Changes
- Replace the discarded `_transport_error(...)` call with either an explicit `continue` or a raise on the last attempt, so behavior is declared rather than implicit.
- Ensure the specific transport error detail (type, message, `/health` hint) reaches the caller when the loop exhausts, rather than only the generic exhaustion message.
- Do not change which errors are retried or the number of attempts.

## Constraints
- Must preserve REQ-006: non-timeout `httpx.RequestError` still retries within the loop; timeouts still fail fast.
- Must not change `_RETRY_MAX` or the per-attempt backoff.
- Must keep the existing handler ordering (`TimeoutException` before `RequestError`).

## Acceptance Criteria
- A sequence of request errors across all attempts still raises a `TransportError` (behavior unchanged).
- The raised/logged message reflects the request-error cause, not only the generic exhaustion text.
- No implicit fall-through remains: an explicit `continue` or `raise` is present in the handler.
- Existing retry/backoff tests still pass.

## Testing Expectations
- Unit test: three consecutive request errors raise `TransportError` and the message mentions the request/network cause.
- Unit test: a request error followed by a success still returns the successful result (retry works).
- Confirm the handler contains an explicit control-flow statement, not a bare discarded call.

## Documentation Impact
Update the REQ-006 comment on the `RequestError` handler to state whether the retry is explicit (`continue`) or the error is raised on the final attempt, and note that the previously-discarded detail is now surfaced.

## Out of Scope
- Changing which transport errors are retried.
- Changing `_RETRY_MAX`, backoff timing, or the health-check suffix behavior for other handlers.
- Any change to read-tool vs write-tool retry asymmetry beyond this handler.

## Dependencies
N/A: none

## Unresolved Questions
- Should the specific request-error detail be raised on the final attempt, or is the generic exhaustion message sufficient once the explicit control flow is in place?
- Does any higher-level caller parse the exhaustion message text, which would constrain how the message is rewritten?

## AI Implementation Instruction
In `scripts/shared/http_transport.py::HttpTransport.call()`, remove the discarded `_transport_error(...)` return value. Add an explicit `continue` after logging, or raise the built `TransportError` on the final attempt so its detail reaches the caller. Preserve REQ-006 retry semantics and current handler ordering. Do not touch other handlers or the retry count.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-001424
- **Related target files**: scripts/shared/http_transport.py

---

**Adversarial Verification** (2026-10-27): verified against current source per `rules/ai-execution.md` Adversarial Verification (Base).

Examined: `scripts/shared/http_transport.py::HttpTransport.call()` (lines 169-223), `_transport_error` (115-132), `_build_exhaustion_message` (134-141).

Claims:

- The `except httpx.RequestError` handler computes a `TransportError` via `_transport_error(...)` but discards the return value (no raise, no explicit `continue`), relying on implicit fall-through — CONFIRMED (line 220; falls through to 221-223).
- Sibling handlers (`TimeoutException`, `HTTPStatusError`, `ValueError`) all `raise self._transport_error(...)` — CONFIRMED (194-211).
- Loop trailing code builds a generic exhaustion message and raises a fresh `TransportError` — CONFIRMED (221-223).

Assessment: All claims hold. Correctly characterized as a maintainability/robustness defect, not a runtime bug (REQ-006 retry behavior is currently correct). The reliance on implicit fall-through is a real latent-regression risk: adding a statement after this `except` block would change retry behavior silently. Recommendation: premise sound; either an explicit `continue` or raise-on-final-attempt preserves REQ-006.
