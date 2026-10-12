# Concurrency limit of zero silently disables the per-server semaphore in `ToolTransportInvoker`

## Priority

Low

## Summary

In `ToolTransportInvoker._ensure_semaphores`, concurrency limits with a value of `0`
(or negative) are filtered out when building the per-server semaphores. A server
configured with a limit of `0` therefore gets no semaphore and allows unbounded
concurrent tool calls, which contradicts the intent of setting a limit.

## Background

`ToolExecutor` accepts `concurrency_limits: dict[str, int] | None`, keyed by server key,
to bound how many tools run concurrently per MCP server. Semaphores are created lazily in
`_ensure_semaphores` and acquired in `_execute_with_semaphore` around each transport
call.

## Problem

```python
self._semaphores = {
    key: asyncio.Semaphore(n)
    for key, n in self._concurrency_limits.items()
    if n > 0          # <-- 0 and negatives are dropped here
}
```

A config entry such as `{ "server": 0 }` produces no semaphore for that server, so
`_execute_with_semaphore` acquires nothing and concurrency is unlimited. There is no
warning for a known server key whose limit is `0` (the existing warning only fires for
keys absent from `server_configs`). So `0` is an ambiguous, silent "no limit" rather
than an error or an explicit "1" cap.

Clarification (adversarial review): the resulting behavior is self-consistent rather
than silently wrong — a `0` limit resolves to exactly the same state as omitting the
key entirely (no semaphore, unbounded), which is the documented default for
unconfigured servers, and matches the common `0` = "unlimited" convention. The defect
is therefore narrow: an operator who sets `0` receives no feedback about which meaning
applied, and `0` cannot be used to express "serial only". It is a clarity / config-convention
gap, not a correctness, safety, or crash defect.

## Reason for Change

`0` is a natural value to type when someone wants "no concurrency" or "serial only", and
either reading yields the opposite of the other. Under high fan-out this can let far more
parallel requests hit a server than operators assumed, defeating the backpressure the
config exists to provide.

## Implementation Intent

Pick and document one semantics for `0` and enforce it consistently: either treat `0`
as "unlimited" (explicitly, with a clear default and no silent filtering), or coerce it
to a minimum of `1` (serial) and warn on `0`/negative. Make the chosen behavior visible
in config validation or a warning rather than a silent filter. Keep the change minimal
and backward compatible with existing passing tests.

The two options carry asymmetric risk: coercing `0` to `1` can regress a deployed config
that currently relies on `0` meaning "unlimited" by capping that server at a single
in-flight call, whereas documenting "unlimited" cannot cause a throughput regression.
Absent an established serial-only convention, prefer documenting "unlimited" (with a
warning when a `0`/negative limit is seen) and reserve coerce-to-1 for when such a
convention is confirmed.

## Target Files or Areas

- `scripts/shared/tool_transport_invoker.py` (`_ensure_semaphores`,
  `_maybe_semaphore`)
- Config loading for `tool_concurrency_limits`
- `tests/shared/`

## Required Changes

- Define the meaning of a `0`/negative limit explicitly.
- Either cap at `1` (with a warning) or record "unlimited" explicitly; remove the silent
  drop that leaves the key without a semaphore.
- Add a test asserting the chosen behavior for a `0` limit.

## Constraints

- Must not change the semantics of a positive limit.
- Must not break servers that currently have no entry in `concurrency_limits` (those
  remain uncapped by design).
- Preserve the existing "unknown server key" warning for keys outside `server_configs`.

## Acceptance Criteria

- A `0` limit resolves to a defined, documented behavior (not a silently dropped
  semaphore).
- A test asserts the behavior for a `0` limit and for a positive limit.
- `ruff`, `mypy`, and the shared-module suite pass.

## Testing Expectations

- Test `_ensure_semaphores` with a `0` limit and assert the resulting semaphore behavior
  for the chosen semantics.
- Full `shared` module suite + `ruff check` + `mypy`.

## Documentation Impact

If `tool_concurrency_limits` is documented, note the `0` semantics. Otherwise update the
code comment in `_ensure_semaphores` to state the chosen meaning. No `docs/*.md` update
required unless the config reference doc covers this key.

## Out of Scope

- Changes to positive concurrency-limit handling or semaphore acquisition order.
- Any change to how unknown server keys are warned about.
- Non-MCP concurrency controls.

## Dependencies

- `N/A: none`

## Unresolved Questions

- Should `0` mean "unlimited" or "serial only (1)"? This is a config-convention choice,
  not derivable from the code alone.
- Is any currently-deployed config relying on `0` meaning "unlimited"?
- Is a serial-only (`0` -> 1) convention established anywhere in config/tooling, or is
  "unlimited" the prevailing convention? This determines which option is lower-risk.

## AI Implementation Instruction

Do not touch positive-limit handling or semaphore acquisition. Only define and enforce a
meaning for `0`/negative limits in `_ensure_semaphores` (cap at 1 with a warning, or
explicit unlimited), and pin it with a test. Run `ruff check`, `mypy`, and the
shared-module tests before finishing.

## Traceability

- **Workflow phase**: `python-code-review` + `issue-creator`; adversarially reviewed
  20261012 (verdict: core claim valid vs source; framing tempered — `0`→unbounded is
  self-consistent with the unconfigured default; added asymmetric-risk guidance to
  Implementation Intent)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-185224
- **Related target files**: `scripts/shared/tool_transport_invoker.py`
