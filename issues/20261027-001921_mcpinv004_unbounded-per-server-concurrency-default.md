# Add a sane default per-server concurrency cap

## Priority
Low

## Summary
Introduce a bounded default for concurrent calls to a single MCP server. Today `ToolTransportInvoker` applies a per-server semaphore only when `concurrency_limits` contains a positive entry for that server; with the default (no config) every call uses a null semaphore, so an unbounded number of concurrent requests can fan out to one server.

## Background
`ToolTransportInvoker.__init__` copies `concurrency_limits` into `self._concurrency_limits` (empty when the caller passes `None`) and leaves `self._semaphores` as `None` until `_ensure_semaphores()` runs. That method only builds semaphores for keys whose limit is positive:

```python
self._semaphores = {
    key: asyncio.Semaphore(n)
    for key, n in self._concurrency_limits.items()
    if n > 0
}
```

In `_run_precall_gates()` the semaphore is resolved and passed to `_invoke_and_record`, which wraps the call in `_maybe_semaphore(sem)`. When `sem` is `None` (the default path) `_maybe_semaphore` returns `contextlib.nullcontext()`, i.e. no concurrency limit at all. The docstring of `_ensure_semaphores` documents this deliberately: a `0`/negative limit, and by extension an omitted key, means "unlimited".

## Problem
- With no `tool_concurrency_limits` configured, a single logical request path can dispatch an arbitrary number of concurrent HTTP calls to one MCP server. There is no ceiling on in-flight requests per server.
- All transports share one `httpx.AsyncClient` (`ToolTransportInvoker.__init__` receives a single `http` client). Unbounded per-server concurrency can exhaust that client's connection pool or overwhelm a single server that tolerates few simultaneous connections.
- The health registry's HALF_OPEN logic permits only one recovery trial at a time, but it does not bound ordinary concurrent load, so it provides no protection here.
- The current behavior is correct for the documented "unlimited by default" design, so this is a guardrail gap rather than a runtime defect.

## Reason for Change
The invocation path is the single choke point through which every MCP tool call flows. A missing default ceiling means the first workload that issues many concurrent calls to one server hits no backpressure, and the only lever available is an operator-configured `concurrency_limits` map that may simply never be set. Adding a sane default bounds the blast radius without removing the existing opt-out.

## Implementation Intent
Add a process-wide default cap applied when a server has no explicit positive limit, while preserving the documented semantics: an explicit `0`/negative limit still means unlimited. Apply the cap inside `_maybe_semaphore` or `_ensure_semaphores` so it covers both the unconfigured default and any server omitted from the config. Name the responsibility (default concurrency ceiling) rather than a specific line. Make the default value a named constant so it is tunable and visible.

## Target Files or Areas
- `scripts/shared/tool_transport_invoker.py` — `_ensure_semaphores()`, `_maybe_semaphore()`, `_run_precall_gates()`

## Required Changes
- Apply a bounded default semaphore to every server that lacks an explicit positive limit, including servers never mentioned in `concurrency_limits`.
- Preserve the existing meaning of an explicit `0`/negative limit as "unlimited" (no semaphore).
- Expose the default as a named constant (and ideally a constructor/`__init__` parameter with a documented default) so it can be tuned without editing code.
- Keep the existing warning for unknown server keys and for known keys set to `0`/negative.

## Constraints
- Must not change behavior when a positive per-server limit is already configured.
- Must not remove the "explicit 0/negative = unlimited" semantics.
- The default must be large enough not to throttle legitimate sequential agent usage, but small enough to bound pool exhaustion.
- Must remain correct under the shared `httpx.AsyncClient` (one semaphore per server, not a global cap that would over-restrict across servers) unless a global cap is explicitly intended.

## Acceptance Criteria
- With no `concurrency_limits` configured, concurrent calls to a single server are capped at the default and never exceed it.
- An explicit positive limit still caps at that value.
- An explicit `0`/negative limit still allows unlimited concurrency.
- Existing concurrency-limit tests still pass.

## Testing Expectations
- Unit test: N concurrent calls to an unconfigured server never exceed the default in flight simultaneously.
- Unit test: an explicit positive limit overrides the default.
- Unit test: an explicit `0`/negative limit bypasses the default (unlimited).

## Documentation Impact
Update the `_ensure_semaphores` docstring and the `concurrency_limits` parameter docstring in `ToolExecutor.__init__` to state the new default ceiling and how it interacts with explicit `0`/negative limits.

## Out of Scope
- Changing which servers get a semaphore beyond adding the default.
- Restructuring the pre-call gate chain.
- Adding a global cross-server cap (unless the maintainer explicitly wants one instead of a per-server default).

## Dependencies
N/A: none

## Unresolved Questions
- Should the default be a per-server cap or a single global cap across all servers? A per-server cap is safer against exhausting one server but allows a larger total fan-out.
- What value is appropriate as the default, and should it be configurable via env var or config file?
- Does the shared `httpx.AsyncClient` already impose a connection-pool limit that partially covers this, and if so what headroom should the default leave?

## AI Implementation Instruction
In `scripts/shared/tool_transport_invoker.py`, apply a bounded default semaphore to any server lacking an explicit positive limit, including servers absent from `concurrency_limits`. Keep explicit `0`/negative limits as unlimited. Define the default as a named constant and document it in `_ensure_semaphores` and the `concurrency_limits` param docstring. Do not restructure the gate chain or alter configured positive limits.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-001921
- **Related target files**: scripts/shared/tool_transport_invoker.py
