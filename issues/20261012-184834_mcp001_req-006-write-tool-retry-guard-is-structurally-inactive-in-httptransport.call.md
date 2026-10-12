# REQ-006 write-tool retry guard is structurally inactive in `HttpTransport.call`

## Priority

Low

## Summary

The `HttpTransport.call` retry path contains a guard that is meant to prevent blind
retries of state-mutating (write) tools when no idempotency key is present, but the
guard's condition can never be true. Every write tool is therefore retried on a
non-timeout `httpx.RequestError` just like a read tool. This is a dead-code /
misleading-comment defect (the documented client-side protection does not exist), not
an active write-safety hazard: the key is always sent, so `dispatch.py`'s server-side
deduplication is always engaged and is the real backstop.

## Background

Commit `c433c3c68` added per-call idempotency handling to the MCP transport layer
(REQ-005, REQ-006): one UUID is emitted per logical call, sent as the
`X-Idempotency-Key` header on every retry, and write-tool post-send retries are gated
on key presence. The server side deduplicates via `dispatch.py`'s `_duplicate_cache`
(keyed on `(idempotency_key, tool name, normalized-args hash)`, 1h TTL, oldest-first
eviction past 1024 entries).

## Problem

In `HttpTransport.call`, `idempotency_key` is assigned once as `str(uuid.uuid4())`,
which is always a non-empty 36-character string. The write guard is written as
`if name in _WRITE_TOOLS and not idempotency_key:`. Because `idempotency_key` is never
empty, `not idempotency_key` is always `False`, so the `raise ... break_flag=True`
branch is unreachable. Control always falls through to the non-breaking
`_transport_error(...)` call, which discards its return value and lets the retry loop
continue. Write tools are retried on a non-timeout `httpx.RequestError`, exactly like
read tools. (`httpx.TimeoutException`, a `RequestError` subclass, is caught earlier at
line 188 and breaks without retry.) The guard that was supposed to stop blind write
retries never runs. This has been true since the guard was introduced in commit
`c433c3c68` — the key is always sent (line 159), so the guard was unreachable from
its inception.

## Reason for Change

The guard documents a safety property (REQ-006: a write must not be retried without a
server-side dedup key) that the code does not actually enforce. Anyone reading
`http_transport.py` concludes that writes are protected from double execution by this
guard; that conclusion is wrong. The defect is therefore a misleading comment plus dead
code, not an active vulnerability: because the key is always sent, `dispatch.py`
deduplicates every write for this transport, so server-side `_duplicate_cache` is the
real (and always-engaged) backstop. The residual question — whether the dedup cache's
TTL/eviction could allow a double execution for a retry arriving after eviction — is
open (see Unresolved Questions), not an established current hazard. The maintenance
risk is that future edits may rely on a client-side backstop that does not exist and
make the write path blindly retriable.

## Implementation Intent

Adopt option (b): the design is intentionally "key always present, always safe to
retry," so replace the dead branch with an explicit comment stating that writes are
always retried on a non-timeout `httpx.RequestError` and that safety rests on the
always-active server-side `_duplicate_cache`, plus a test asserting writes are retried,
so the behavior is deliberate rather than accidental. Do not adopt option (a) (emitting
the key only for write tools) unless the `X-Idempotency-Key` header contract is changed
in a coordinated, separately-scoped change — option (a) conflicts with the Constraint
that forbids altering that header contract. Note: option (a) is ruled out by the
Constraint "Must not change the `X-Idempotency-Key` header contract"; only elimination
of the dead branch is viable. Do not leave a `raise` branch that cannot be reached.

## Target Files or Areas

- `scripts/shared/http_transport.py` (`HttpTransport.call`)
- `scripts/shared/dispatch.py` (`_duplicate_cache`) — reference only, to confirm the
  server-side dedup contract the client relies on
- `tests/shared/` — new or updated tests for the retry path

## Required Changes

- Eliminate the unreachable `not idempotency_key` branch, or make it reachable and
  correct.
- Document the actual write-retry policy in the surrounding comment so it matches the
  implementation.
- Add a test asserting the observed write-retry behavior (whichever policy is chosen).

## Constraints

- Must not change the `X-Idempotency-Key` header contract already relied on by
  `dispatch.py` server-side dedup.
- Must not reduce write-safety below the current (safe) behavior.
- Keep one idempotency key per logical call reused across retries.

## Acceptance Criteria

- No unreachable `raise` branch remains in `HttpTransport.call`'s `RequestError`
  handler.
- A test exercises a write tool under a non-timeout `httpx.RequestError` and asserts the
  retry policy (3 attempts for both write and read tools); a timeout variant asserts
  1 attempt.
- `ruff`, `mypy`, and the shared-module test suite pass.

## Testing Expectations

- Unit test on `HttpTransport.call` with a mocked `httpx.AsyncClient` that raises a
  non-timeout `httpx.RequestError` (e.g. `httpx.ConnectError`), for both a write tool
  and a read tool, asserting the exact number of attempts.
- Full `shared` module suite + `ruff check` + `mypy`.

## Documentation Impact

If the intent is (b) above, update the REQ-005/REQ-006 comment in
`http_transport.py` to state that writes are always retried because the key is always
present, and that safety depends on server-side dedup. No `docs/*.md` update required
unless the transport design doc describes this guard.

## Out of Scope

- Any change to `dispatch.py` server-side dedup semantics.
- Changes to the retryable-status set (`429/502/503/504`) or exponential backoff.
- Retry behavior for non-MCP HTTP calls (LLM, embedding, history).

## Dependencies

- `N/A: none`

## Unresolved Questions

- Was the intent that the idempotency key be emitted only for write tools (making the
  guard reachable), or always for all tools (making the guard intentionally inert)?
- Does the server-side `_duplicate_cache` TTL/eviction introduce a real double-execution
  window for a retry that arrives after eviction, and is that window acceptable?
  (Within a single retry loop the window is bounded by the max ~3s backoff period; the
  1h TTL makes eviction during this window extremely unlikely unless the cache is under
  extreme cardinality pressure.)

## AI Implementation Instruction

Do not rewrite the retry loop or backoff. Only resolve the unreachable guard: either
make `not idempotency_key` reachable by controlling when the key is emitted, or replace
the dead branch with an explicit comment plus a test pinning the always-retry behavior.
Preserve the single-per-call idempotency key and the `X-Idempotency-Key` header. Run
`ruff check`, `mypy`, and the shared-module tests before finishing.

## Traceability

- **Workflow phase**: `python-code-review` + `issue-creator`; adversarially reviewed
  20261012 (verdict: core finding valid; severity corrected Medium→Low; implementation
  intent resolved to option (b))
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-184834
- **Related target files**: `scripts/shared/http_transport.py`, `scripts/shared/dispatch.py`
