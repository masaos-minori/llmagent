# Client-side backstop for MCP write idempotency across retries

## Priority
Medium

## Summary
Add a client-side guard so that retrying a side-effecting (write/delete/API-write) MCP tool call over a non-timeout transport error cannot cause the server to execute the same write twice even if the shared in-process dedup cache is ever bypassed. Today double-execution prevention rests solely on one server-side cache keyed by the `X-Idempotency-Key` header.

## Background
`HttpTransport.call()` (`scripts/shared/http_transport.py`) retries a non-timeout `httpx.RequestError` up to `_RETRY_MAX` times, reusing a single per-logical-call `X-Idempotency-Key` emitted once per call. The server side deduplicates writes in `scripts/mcp_servers/dispatch.py` via the module-level `_duplicate_cache` (`OrderedDict`), keyed on that header, with a TTL and a max-entry eviction. The client comment at the retry handler explicitly states "No client-side backstop exists": correctness against double execution depends entirely on the server seeing the same key on every attempt.

## Problem
The entire at-most-once guarantee for side-effecting tools is a single in-process dependency:

- `_duplicate_cache` lives in one server process. A process restart, cache eviction past an expired entry, or a deployment that runs the dispatch layer behind multiple replicas/load balancer without shared state removes the dedup for that window.
- If the `X-Idempotency-Key` header is dropped or rewritten anywhere between the agent and the dispatch layer (a future reverse proxy, a gateway that strips unknown headers, a header-name mismatch), the server sees distinct keys and executes the write on every retry.
- A `ReadTimeout`/`PoolTimeout` means the request may have been processed server-side while the response was lost; the client does not retry on timeout, so this is currently safe, but the asymmetry (timeouts break, request errors retry) means the retry path is the only place a duplicate could ever occur, and it has no defense-in-depth.

## Reason for Change
Writes are the highest-stakes calls in the invocation path (ADR-004 fail-closed on writes). A single-point-of-failure on write idempotency with no second layer is exactly the kind of trust-boundary gap this review flags. The fix is small and additive; it hardens a critical boundary rather than changing current correct behavior.

## Implementation Intent
Introduce a minimal client-side idempotency record co-located with the transport so a given logical call (same `X-Idempotency-Key`) records that a side-effecting call was already dispatched and refuses to send a second identical write. Keep it optional and off by default unless it can be proven not to change current pass behavior, or make it a config toggle. The intent is defense-in-depth, not a replacement for the server cache. Name the responsibility (client-side dedup guard) rather than a specific line.

## Target Files or Areas
- `scripts/shared/http_transport.py` — `HttpTransport.call()`
- `scripts/shared/tool_transport_invoker.py` — `ToolTransportInvoker._run_precall_gates()`
- `scripts/mcp_servers/dispatch.py` — `_duplicate_cache` (read-only reference)

## Required Changes
- Add a client-side record that a side-effecting call for a given `X-Idempotency-Key` has already been sent, and skip re-sending an identical write on a retry.
- Bound the record's lifetime and size consistently with the server cache so it cannot grow unbounded.
- Ensure the guard never blocks a legitimately new call (different key or different args).
- Document the added layer alongside the existing "No client-side backstop exists" comment.

## Constraints
- Must not change behavior for the common case (single successful attempt, or read tools).
- Must not drop or alter the `X-Idempotency-Key`; the server remains the authority.
- Must remain correct under the existing retry loop (one key per logical call).
- Must not introduce blocking I/O in the async path.

## Acceptance Criteria
- A write that times out after the server processed it, then is retried, still executes exactly once end-to-end even if the server cache is cleared between attempts.
- Two writes with different keys or different args both execute.
- Read tools are unaffected.
- The client-side record is bounded in size and lifetime.

## Testing Expectations
- Unit test: a retried write with the same key is dispatched to the transport once.
- Unit test: a write with a different key/args dispatches again.
- Integration test simulating server-cache loss between two client retries confirms single execution.

## Documentation Impact
Update the REQ-006 comment block in `http_transport.py` to describe the new client-side layer and its relationship to the server `_duplicate_cache`.

## Out of Scope
- Changes to the server-side `_duplicate_cache` semantics.
- Changing which transport errors are retried.
- Any change to read-tool behavior.

## Dependencies
N/A: none

## Unresolved Questions
- Is a client-side guard warranted given the server cache is currently well-implemented, or is the existing deliberate single-layer design acceptable?
- Should the guard be always-on or config-toggleable?
- How should the record interact with a process that handles multiple servers (per-server key namespace)?

## AI Implementation Instruction
Add a client-side idempotency guard in `scripts/shared/http_transport.py` that records a side-effecting call's `X-Idempotency-Key` and prevents a second identical write on retry. Do not modify server-side dedup or read-tool paths. Keep the record bounded and non-blocking. If the guard risks changing current pass behavior, gate it behind a config toggle and default it off.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-001245
- **Related target files**: scripts/shared/http_transport.py, scripts/shared/tool_transport_invoker.py

---

**Adversarial Verification** (2026-10-27): verified against current source per `rules/ai-execution.md` Adversarial Verification (Base) — target file → direct dependencies → related tests.

Examined: `scripts/shared/http_transport.py::HttpTransport.call()` (lines 143-223), `scripts/mcp_servers/dispatch.py` idempotency cache (lines 77/105/122-138/186-215), `scripts/shared/tool_transport_invoker.py`.

Claims:

- Single `X-Idempotency-Key` emitted once per logical call and reused across the `_RETRY_MAX=3` retry loop — CONFIRMED (`http_transport.py`:153,159; loop at 169; `RequestError` handler at 212-220).
- Server-side dedup via module-level `_duplicate_cache` (`OrderedDict`), keyed on the header, with TTL (3600s) and max-entry eviction — CONFIRMED (`dispatch.py`:77,102,122-128,186-190). A reuse-with-different-content guard also exists (205-215).
- Client retry-handler comment states "No client-side backstop exists" — CONFIRMED (`http_transport.py`:218-219).
- Timeouts fail fast and are not retried; only non-timeout `RequestError`s retry — CONFIRMED (`TimeoutException` handler raises at 194-197).

Assessment: All factual claims hold. No disconfirming evidence found. This is a defense-in-depth proposal, not a runtime bug. The issue's own Unresolved Questions (whether a client-side guard is warranted, always-on vs config-toggleable, per-server key namespace) remain genuinely open and belong at plan time. Recommendation: premise sound; proceed via issue-to-plan with those questions resolved.
