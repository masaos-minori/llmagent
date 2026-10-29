# mcphc001 post-startup MCP health-check retry ignores degraded-but-live liveness predicate

## Priority
Medium

## Summary
`StartupMCPStarter.verify_health` retries on any non-200 HTTP status during the
post-startup health check, but `_verify_single_health` treats every non-200
response as fatal. It never consults the `liveness` field of the JSON body, so a
process that is degraded but still live (HTTP 503 with `"liveness": true`) is
reported as unhealthy and aborts startup. The spawn-phase readiness probe
(`poll_until_ready`) does consult `liveness`. The two phases therefore disagree,
and the disagreement is untested.

## Background
`scripts/agent/startup_mcp_starter.py` starts each MCP server, then polls its
health endpoint until it returns 200 (`verify_health`, lines 104-127). Each poll
calls `_verify_single_health` (lines 130-168), which:
- raises `MCPServerHealthError` on connection errors / timeouts;
- raises `MCPServerHealthError` on any non-200 status;
- otherwise parses JSON and raises if `liveness` is false.

`verify_health` catches `MCPServerHealthError` and retries up to
`max_retries` (default 5) with `retry_delay` (default 2s) sleep between attempts.

`poll_until_ready` (in `scripts/agent/http_lifecycle_health_checker.py`, lines
38-74) is used during process spawn. Its loop (lines 54-73) treats a
non-200 response with `"liveness": true` as a degraded-but-live condition and
keeps polling instead of failing.

## Problem
Startup has two health/readiness gates that use different predicates:

| Phase | Source | Non-200 + liveness=true | Non-200 + liveness=false |
|-------|--------|-------------------------|--------------------------|
| Spawn readiness | `poll_until_ready` | keep polling | fail |
| Post-startup health | `_verify_single_health` | **fail** | fail |

A server that is degraded but live passes the spawn gate but fails the
post-startup gate immediately, with no retry benefit. The retry loop in
`verify_health` therefore spins through all 5 attempts against a degraded-but-live
endpoint and then aborts — wasting ~8s and producing a hard failure where a
degraded-but-live signal should be tolerated.

## Reason for Change
The asymmetry is a latent correctness bug: the post-startup gate contradicts the
spawn gate on the exact signal (`liveness`) that both phases already agree is
meaningful. It is also untested — no test exercises a non-200 + `liveness:true`
body through `_verify_single_health`, so the divergence from `poll_until_ready`
has never been caught.

## Implementation Intent
Make `_verify_single_health` consistent with `poll_until_ready`: a non-200
response whose body indicates `liveness == true` must be treated as
degraded-but-live (retryable / not immediately fatal), matching the spawn-phase
behavior. A non-200 with `liveness == false` (or absent/unparseable body) stays
fatal. Keep the existing retry semantics in `verify_health` intact.

## Target Files or Areas
- `scripts/agent/startup_mcp_starter.py` — `_verify_single_health` (lines 130-168)
- `scripts/agent/http_lifecycle_health_checker.py` — `poll_until_ready` (reference for the correct predicate)
- `tests/agent/test_startup_mcp_starter.py` — add coverage for non-200 + `liveness:true`

## Required Changes
- In `_verify_single_health`, branch on the parsed body's `liveness` field before
  deciding a non-200 is fatal: `liveness == true` => degrade/retry, not raise;
  `liveness == false` or body unusable => raise `MCPServerHealthError` as now.
- Mirror the exact predicate used by `poll_until_ready` so the two phases cannot
  drift again.
- Add a test asserting a non-200 + `liveness:true` response is NOT treated as
  fatal (and that non-200 + `liveness:false` still is).

## Constraints
- Do not change the retry loop, delays, or `max_retries` in `verify_health`.
- Do not alter the spawn-phase `poll_until_ready` behavior; only align the
  post-startup gate to it.
- Preserve `MCPServerHealthError` as the exception type for genuinely dead
  servers.

## Acceptance Criteria
- A server returning HTTP 503 with `"liveness": true` is treated as degraded but
  live by `_verify_single_health`, not raised as fatal.
- A server returning HTTP 503 with `"liveness": false` still raises
  `MCPServerHealthError`.
- Existing tests in `tests/agent/test_startup_mcp_starter.py` still pass.
- New test covers both branches of the non-200 + liveness decision.

## Testing Expectations
- Unit test(s) in `tests/agent/test_startup_mcp_starter.py` for both
  `liveness:true` (tolerated) and `liveness:false` (fatal) under a non-200 status.
- Full suite for `test_startup_mcp_starter.py` passes.

## Documentation Impact
Update any docstring on `_verify_single_health` describing when a non-200 is
fatal, to mention the `liveness`-based degradation path. No external docs.

## Out of Scope
- Changing `verify_health` retry parameters.
- Changing spawn-phase readiness logic.
- Any non-MCP health checks.

## Dependencies
N/A: none

## Unresolved Questions
- Should a degraded-but-live response count toward / reset the retry budget, or
  should it short-circuit to "ok"? Current intent: treat like `poll_until_ready`
  (keep polling until ready or a fatal/dead signal). Confirm whether degraded
  responses should still eventually fail if they never clear to 200 within
  `max_retries`.
- Is the body always JSON here, or could a non-200 return a non-JSON body that
  should be treated as fatal outright?

## AI Implementation Instruction
Align `_verify_single_health`'s non-200 handling with `poll_until_ready`: parse
the JSON body, and if `liveness` is true, treat the non-200 as degraded-but-live
(retryable) rather than raising `MCPServerHealthError`. Raise only when
`liveness` is false or the body cannot be parsed. Add unit tests for both
branches. Do not touch `verify_health` retry parameters or spawn-phase logic.

## Traceability
- **Workflow phase**: `issue-creator` (fed by `python-code-review`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-220520
- **Related target files**: `scripts/agent/startup_mcp_starter.py`, `scripts/agent/http_lifecycle_health_checker.py`, `tests/agent/test_startup_mcp_starter.py`
