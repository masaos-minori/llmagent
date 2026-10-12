# Health and lifecycle gates run once per logical call, not per HTTP retry in MCP transport

## Priority

Low

## Summary

Within a single `HttpTransport.call`, up to three HTTP attempts (retryable statuses plus
`httpx.RequestError` retries) execute without re-running the health, lifecycle,
transport, or semaphore gates. Those gates run exactly once in
`ToolTransportInvoker._run_precall_gates` before `call` begins, so a server that fails
mid-call still receives every in-call retry and the circuit breaker trips only after the
whole logical call exhausts its retries.

## Background

`ToolExecutor.execute` -> `ToolTransportInvoker._raw_execute` ->
`_run_precall_gates` performs, in order: health registry check, disabled-server check,
lifecycle `ensure_ready`, transport lookup, and semaphore acquisition. It then calls
`_invoke_and_record`, which runs `HttpTransport.call`. All HTTP-level retries live
inside `call`; none of the gates are re-entered between attempts.

## Problem

The pre-call gate chain is a per-logical-call boundary, but the retry loop is a
per-HTTP-attempt mechanism. When the first attempt fails and the health registry records
a failure, the subsequent attempts inside the same `call` do not re-check health or
re-run `lifecycle.ensure_ready`. Consequences:

- Redundant requests are sent to a server that has already gone unhealthy during the
  call.
- A mid-call crash does not trigger a lifecycle restart until (and unless) the exhausted
  call surfaces a single `TransportError` that `_record_transport_error` turns into one
  health-failure count. Several retryable attempts therefore collapse into one counted
  failure, so reaching the failure threshold takes more wall-clock failures than one might
  expect.

Clarification (adversarial review): these are expected properties of the retry design,
not active defects. The retry loop exists precisely to resend failing requests, and the
health registry is updated only by `record_failure`, which runs after `call` exhausts
(`_record_transport_error`, line 184-194) — so the state cannot flip to unavailable
mid-retry-loop within the same logical call. The "already-unhealthy" window therefore
opens only under concurrent calls whose failures flip the state, and the tail-latency
risk applies to long-timeout servers only. Both the priority (Low) and the Unresolved
Questions already treat the operational harm as theoretical.

## Reason for Change

The asymmetry is easy to misread: `_run_precall_gates` reads like a guard around every
request, but it guards only the first. For a long-timeout server this can mean several
blocked requests against an already-dead endpoint before the breaker trips, degrading
tail latency under partial outages.

## Implementation Intent

Decide explicitly which model is intended and make it unambiguous: either (a) keep
gates per logical call and document/assert that in-call retries intentionally bypass
them, or (b) re-evaluate readiness between attempts (e.g. re-check the health registry
before each retry, or abort the retry loop early once the server is marked
unavailable). Prefer the minimal change that removes the ambiguity; do not redesign the
retry/backoff policy.

Note for the decision: per-logical-call gating is already implied by existing semantics
— the health gate enforces a single HALF_OPEN trial per logical call (`_check_health`,
line 142-169) and the semaphore is acquired per logical call (`_execute_with_semaphore`,
line 212-213), so re-running the gate before each retry (option (b)) would re-enter trial
ownership and is not a minimal change. Unless a deferred-breaker scenario is shown to be
observably harmful, option (a) (document-and-assert) is the lower-risk resolution.

## Target Files or Areas

- `scripts/shared/tool_transport_invoker.py` (`_run_precall_gates`, `_invoke_and_record`)
- `scripts/shared/http_transport.py` (`call`)
- `tests/shared/`

## Required Changes

- State in code/comment whether gates are per-logical-call or per-attempt.
- If per-attempt: re-check health (and optionally lifecycle) before each retry, with a
  bounded, clearly documented cost.
- If per-logical-call: add a test asserting retries bypass the gates, so the behavior is
  deliberate.

## Constraints

- Must not change the retryable-status set or exponential backoff.
- A per-attempt re-check must stay within the existing overall timeout budget.
- Must not alter the health-failure counting semantics already relied on by tests.

## Acceptance Criteria

- The per-call vs per-attempt model is explicit in code or comment.
- A test covers a multi-attempt call and asserts the chosen gate behavior.
- `ruff`, `mypy`, and the shared-module suite pass.

## Testing Expectations

- Test where `call` retries and the health registry flips to unavailable mid-loop,
  asserting the chosen behavior (requests continue, or retries abort early).
- Full `shared` module suite + `ruff check` + `mypy`.

## Documentation Impact

Update the `call` / `_run_precall_gates` docstrings to state when gates are evaluated
relative to retries, if they do not already. No `docs/*.md` update required unless the
transport design doc describes retry/gate interaction.

## Out of Scope

- Changing the retryable-status set, backoff, or `RETRY_MAX`.
- Any change to server-side dedup or idempotency.
- Retry behavior for non-MCP HTTP calls.

## Dependencies

- May be resolved together with `issues/20261012-184834_mcp001_...` (both touch the
  `HttpTransport.call` retry path). No hard ordering required.

## Unresolved Questions

- Is per-logical-call gating an intentional simplification, or an oversight?
- Under current load, is the deferred circuit-breaker tripping observably harmful, or
  purely theoretical?
- If option (b) is chosen, how does re-checking the health registry before each retry
  interact with the single HALF_OPEN trial per logical call and the per-call semaphore?

## AI Implementation Instruction

Do not touch the retry loop arithmetic or backoff. Only resolve the gate-vs-retry
question: re-check readiness between attempts, or pin the current per-logical-call
behavior with a comment and a test. Preserve health-failure counting and the overall
timeout budget. Run `ruff check`, `mypy`, and the shared-module tests before finishing.

## Traceability

- **Workflow phase**: `python-code-review` + `issue-creator`; adversarially reviewed
  20261012 (verdict: core architectural claim valid vs source; framing tempered — retry
  behavior is by-design; added half-open-trial/semaphore composition constraint to
  Implementation Intent)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-185100
- **Related target files**: `scripts/shared/tool_transport_invoker.py`,
  `scripts/shared/http_transport.py`
