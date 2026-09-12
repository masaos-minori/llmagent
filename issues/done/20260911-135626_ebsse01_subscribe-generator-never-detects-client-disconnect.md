# /subscribe SSE generator never detects client disconnect under TestClient

## Priority
Medium

## Summary
The `/subscribe` endpoint's live-delivery loop
(`scripts/eventbus/subscribe_route.py::subscribe`'s `_sse_gen()`) has no
reliable way to detect that the client has disconnected unless the
broker-internal queue overflows. A partial mitigation (polling
`request.is_disconnected()` on a timeout) was added, but it does not resolve
the case exercised by
`tests/eventbus/test_eventbus_auth.py::TestSubscribeAuth::test_subscribe_with_valid_consumer_token`,
which is currently skipped because it hangs indefinitely under
`TestClient`.

## Background
Discovered while fixing an unrelated crash
(`AttributeError: 'Depends' object has no attribute 'get'`) in the same
endpoint, tracked in
`issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md`.
That issue covers the authorization wiring gap; this one covers a separate
problem found in the same code while verifying the fix: the subscribe
generator's disconnect handling.

## Problem
`_sse_gen()`'s live-delivery loop only exits when:
- `sub.disconnect` is set (only done by `EventBroker.publish()` on
  `asyncio.QueueFull`, i.e. queue overflow — not a client disconnect signal
  at all despite the attribute name), or
- the broker sends a `None` sentinel via `EventBroker.shutdown()` (app-wide
  shutdown), or
- (after the fix added alongside this issue) `await request.is_disconnected()`
  returns `True`, checked on a 1-second polling timeout.

Under a real ASGI server (uvicorn), `request.is_disconnected()` should
detect a genuine client disconnect. Under Starlette's `TestClient`
(`httpx.ASGITransport`), a test verified this does not happen reliably: a
test opening `/subscribe` and then closing the response (via `.stream()`'s
context manager exit, or via `.send(..., stream=True)` without ever reading
the body) leaves the server-side generator running indefinitely — the test
hangs and only "completes" when `pytest-timeout`'s signal-based alarm
interrupts it, which is not something to rely on outside a diagnostic tool.
This was reproduced 3 separate ways (plain `.stream()` context exit,
`request.is_disconnected()` polling added, and `.send(..., stream=True)`
without a context manager) — all hung identically.

## Reason for Change
Regardless of the TestClient-specific reproduction, an SSE endpoint that
cannot reliably detect disconnects is a real resource-leak risk in
production: every subscriber whose queue never overflows (a normal case for
a quiet topic) keeps its generator, asyncio tasks, and broker registration
alive forever after the client actually goes away, until process restart.
This also currently blocks writing a working automated test for the
`/subscribe` success path.

## Implementation Intent
Left open — needs investigation into why `TestClient`/`ASGITransport` does
not deliver `http.disconnect` the way a real ASGI server does for this
specific request pattern (or a different, environment-independent way to
verify subscribe behavior, e.g. testing `_sse_gen()`'s internal logic
directly rather than through a live HTTP round-trip, or driving the ASGI
app with raw `receive`/`send` callables that can simulate a disconnect
message explicitly).

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py` (`subscribe`, `_sse_gen`)
- `tests/eventbus/test_eventbus_auth.py`
  (`TestSubscribeAuth::test_subscribe_with_valid_consumer_token`, currently
  skipped)

## Required Changes
Not specified — needs investigation first (see Implementation Intent).

## Constraints
Any fix must not change `/subscribe`'s behavior for real clients (uvicorn)
that do disconnect normally — the current queue-overflow and
`is_disconnected()`-polling paths should be preserved or replaced with
something at least as reliable, not removed outright.

## Acceptance Criteria
- `test_subscribe_with_valid_consumer_token` (or a replacement test
  verifying the same behavior) passes without hanging or relying on
  `pytest-timeout` to unblock it.
- A manual or scripted check against a real running eventbus process
  confirms that disconnecting a `/subscribe` client actually frees its
  broker subscription within a bounded time.

## Testing Expectations
Whatever replaces the current skipped test must not depend on
`TestClient`'s in-process ASGI transport delivering a disconnect signal it
apparently does not deliver for this pattern — verify the chosen approach
actually completes before relying on it.

## Documentation Impact
If `docs/06_eventbus_*` describes `/subscribe`'s disconnect/cleanup
behavior, verify it still matches reality once this is investigated further.

## Out of Scope
The role/consumer-identity authorization gap — see
`issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md`.

## Dependencies
N/A: none

## Unresolved Questions
- Why does `Request.is_disconnected()` not return `True` here even after
  the client-side response object is closed? Is this a known
  `httpx.ASGITransport` / `TestClient` limitation, or a bug in how the
  response is being closed in the test? Needs investigation.

## AI Implementation Instruction
Do not attempt another quick client-side workaround without first
confirming, in isolation, whether `request.is_disconnected()` (or any
disconnect signal) is reachable at all through `TestClient` for a
long-running `StreamingResponse` — a minimal reproduction outside this
codebase (a bare FastAPI app with a `while True: await
request.is_disconnected()` loop) would settle whether this is a
framework/library limitation before spending more effort on
`scripts/eventbus/` itself.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-135626
- **Related target files**: scripts/eventbus/subscribe_route.py, tests/eventbus/test_eventbus_auth.py
