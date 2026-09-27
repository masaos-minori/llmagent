# Implement Agent to EventBus publish integration

## Priority
Low

## Summary
Implement an Agent-side client capable of publishing events to Event Bus's existing `/publish` HTTP endpoint, closing Known Issue EVENTBUS-005.

## Background
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-005 records that Agent→EventBus publish integration is intentionally unimplemented (Status: deferred, Severity: Low) — a deliberate deferral, not a defect, per its own Current Description. This issue exists to track eventual implementation once the integration is prioritized, per the entry's own Recommended Action.

## Problem
No code path exists anywhere in `scripts/agent/` that calls Event Bus. Confirmed via repository-wide search: `scripts/agent/` contains zero references to `eventbus`/`EventBus`. Event Bus's server side already exposes a working `/publish` endpoint (`scripts/eventbus/publish_route.py`, `scripts/eventbus/app.py::publish()`), but nothing on the Agent side calls it.

## Reason for Change
Without this integration, Agent-driven workflows cannot publish events to Event Bus; the only current workaround is direct MCP tool calls from the Agent, which does not go through Event Bus's durable, ordered event log.

## Implementation Intent
Add an EventBus HTTP client on the Agent side that calls the existing `/publish` endpoint, following the same authentication and error-handling conventions Event Bus's other consumers already use (see `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` for the token model). Keep the client minimal — a thin wrapper around the existing endpoint, not a new protocol.

## Target Files or Areas
- `scripts/agent/` (new client module; exact location not yet decided — Unknown)
- `scripts/eventbus/publish_route.py`, `scripts/eventbus/app.py` (reference only, not modified)
- `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` (reference for the auth token model)

## Required Changes
- Add an Event Bus publish client to the Agent codebase (HTTP call to the existing `/publish` endpoint).
- Wire the client into whichever Agent-side trigger point is decided as the publish source (see Unresolved Questions).
- Handle authentication per the existing per-role token model.
- Handle publish failures without crashing the calling workflow (fail-safe, matching Event Bus's own fail-closed/fail-open conventions where applicable).

## Constraints
- Must not modify Event Bus's server-side `/publish` endpoint or its authentication model — this issue is client-side only.
- Must not introduce a new transport or protocol; use the existing HTTP `/publish` endpoint as-is.

## Acceptance Criteria
- An Agent-side code path exists that successfully calls Event Bus's `/publish` endpoint with a valid auth token and receives a success response.
- A publish failure (e.g. Event Bus unreachable) is handled without crashing the calling Agent workflow.
- EVENTBUS-005 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once implemented and verified.

## Testing Expectations
Unit tests for the new client (request construction, auth header, error handling) and an integration test confirming a published event is retrievable via Event Bus's existing replay/read path.

## Documentation Impact
Update EVENTBUS-005's entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (remove once resolved, per the Current-Specification-Only Policy). If a new Agent-side module is added, document its responsibility boundary in the Agent area's documentation.

## Out of Scope
- EVENTBUS-006 (SSE subscribe) and EVENTBUS-007 (topic management) — tracked as separate issues.
- Any change to Event Bus's server-side publish logic, schema, or authentication model.

## Dependencies
N/A: none

## Unresolved Questions
- Which Agent-side trigger point(s) should publish events (e.g. workflow completion, tool execution, session lifecycle)? Not specified by the existing Known Issue entry — needs owner/architect decision during implementation.

## AI Implementation Instruction
Add the Agent-side publish client only; do not modify Event Bus's server-side code. Do not guess which Agent trigger points should publish — if the specific integration points are not already decided elsewhere, implement the client as a standalone, callable module and stop to report the open question of wiring it into specific trigger points, rather than picking one unilaterally. Keep the change scoped to this one capability — do not also implement SSE subscribe or topic management in the same change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115602
- **Related target files**: scripts/agent/ (new client module, exact path Unknown)
