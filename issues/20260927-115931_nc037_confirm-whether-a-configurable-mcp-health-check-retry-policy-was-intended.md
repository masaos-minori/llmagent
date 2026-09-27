# Confirm whether a configurable MCP health-check retry policy was intended

## Priority
Low

## Summary
Confirm which MCP-server-unreachable handling path is actually in effect, and obtain an owner ruling on whether a configurable retry policy was ever intended, closing Needs Confirmation item NC-037.

## Background
`docs/10_adr/ADR-004-environment-failure-handling-policy.md`'s Implementation Notes cross-reference NC-037, which asks whether the current single fixed-delay retry (originally cited as `HEALTH_CHECK_RETRY_DELAY_SEC`) on MCP server unreachability is an intentional simplicity choice or a pending configurable Retry Policy.

## Problem
This issue's investigation found NC-037's evidence is stale and the actual situation is more nuanced than "a single fixed-delay retry exists":
- No constant named `HEALTH_CHECK_RETRY_DELAY_SEC` exists anywhere in current source (confirmed via repository-wide search) or in ADR-004's own text.
- `scripts/agent/services/mcp_health.py` (the path that checks RAG/embed-LLM service health via `/health` and logs `unreachable` warnings) performs a **single check with no retry at all** — an `httpx`/`OSError` failure is logged as `Non-Fatal` immediately, once.
- `scripts/agent/http_lifecycle_health_checker.py::HealthChecker.startup_poll()` **does** implement a configurable retry loop (`max_retries`/`interval` parameters, defaulting to `_STARTUP_MAX_RETRIES = 30` / `_STARTUP_INTERVAL = 1.0`), but a repository-wide search found **zero call sites** for `startup_poll` anywhere in `scripts/` or `tests/` — this configurable-retry utility appears to be defined but unused.
- This issue's search was not an exhaustive trace of every MCP-server-unreachable code path in the Agent — only these two modules were checked.

## Reason for Change
NC-037's original question assumed a single retry mechanism exists; the actual state (no retry on one path, an unused configurable-retry utility elsewhere) is different enough that resolving the original question requires first re-establishing what code path ADR-004 actually describes, before an owner can rule on intent vs. gap.

## Implementation Intent
Complete the call-path trace this issue started (confirm whether any other MCP-unreachable-handling code exists beyond `mcp_health.py` and `http_lifecycle_health_checker.py`), then present the owner with the corrected picture for a ruling: is `startup_poll()`'s dead configurable-retry logic meant to be wired into MCP health checks (making it the "pending implementation" case), or was a no-retry, single-check policy always the intended simplicity choice for `mcp_health.py`'s checks specifically?

## Target Files or Areas
- `scripts/agent/services/mcp_health.py`
- `scripts/agent/http_lifecycle_health_checker.py`
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md` (Implementation Notes)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-037 entry)

## Required Changes
- Complete the trace of MCP-server-unreachable handling code paths beyond the two modules this issue checked.
- Present the owner with the corrected evidence and obtain a ruling.
- Update ADR-004's Implementation Notes (and/or `mcp_health.py`'s behavior, per the owner's ruling) to reflect the confirmed intent.
- Remove NC-037 from Active Items once resolved.

## Constraints
- Any behavior change to `mcp_health.py` (e.g. adding retry) requires the owner's explicit ruling first — do not add retry logic speculatively.

## Acceptance Criteria
- The full set of MCP-server-unreachable-handling code paths is confirmed (not just the two modules this issue identified).
- The owner's ruling (retry is/isn't intended for `mcp_health.py`'s checks) is recorded in ADR-004.
- NC-037 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
If the owner's ruling results in a behavior change (e.g. adding retry to `mcp_health.py`), add a unit test covering the new retry behavior. If the ruling confirms no-retry-by-design, no test change is needed.

## Documentation Impact
Update `docs/10_adr/ADR-004-environment-failure-handling-policy.md`'s Implementation Notes to state the confirmed current behavior and the owner's ruling. Remove the NC-037 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Wiring `startup_poll()` into `mcp_health.py` or any other caller, unless the owner's ruling explicitly calls for it.
- Removing `startup_poll()` as dead code — that is a separate concern from this issue's ADR-004/NC-037 scope, even though this issue's evidence noted it has zero callers.

## Dependencies
N/A: none

## Unresolved Questions
- Is `startup_poll()`'s zero-caller status itself worth a separate dead-code issue? Left to the owner to decide; not resolved here to keep this issue's scope on the ADR-004/NC-037 question.

## AI Implementation Instruction
Do not add retry logic to `mcp_health.py`, and do not wire `startup_poll()` into any caller, without the owner's explicit ruling recorded first. Re-confirm both this issue's "no retry" and "zero callers" findings via a fresh search before acting on them, since they may have changed since this issue was filed.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115931
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md, scripts/agent/services/mcp_health.py, scripts/agent/http_lifecycle_health_checker.py
