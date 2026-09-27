# Implement Agent EventBus SSE subscribe integration

## Priority
Low

## Summary
Implement an Agent-side SSE client capable of subscribing to Event Bus's existing replay/subscribe stream, closing Known Issue EVENTBUS-006.

## Background
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-006 records that Agent→EventBus SSE subscribe integration is intentionally unimplemented (Status: deferred, Severity: Low) — a deliberate deferral, not a defect. This issue exists to track eventual implementation once the integration is prioritized, per the entry's own Recommended Action.

## Problem
No SSE client exists anywhere in `scripts/agent/`. Confirmed via repository-wide search: `scripts/agent/` contains zero references to `eventbus`/`EventBus`. Event Bus's server side already exposes a working SSE stream (`scripts/eventbus/replay_route.py::replay()`, `format=sse`) and a `subscribe_route.py` endpoint, but nothing on the Agent side consumes them.

## Reason for Change
Without this integration, the Agent cannot react to Event Bus events in real time; the current workaround (polling via `/replay` or MCP tool calls) adds latency and complexity for any workflow that needs near-real-time event awareness.

## Implementation Intent
Add an SSE client on the Agent side that connects to Event Bus's existing `replay`/`subscribe` stream and dispatches received events into whatever Agent-side handling mechanism is appropriate. Keep the client a thin consumer of the existing stream format — do not change Event Bus's SSE protocol.

## Target Files or Areas
- `scripts/agent/` (new SSE client module; exact location not yet decided — Unknown)
- `scripts/eventbus/replay_route.py`, `scripts/eventbus/subscribe_route.py` (reference only, not modified)

## Required Changes
- Add an Event Bus SSE client to the Agent codebase (long-lived connection to the existing SSE stream).
- Define how received events are dispatched into Agent-side handling (new mechanism or reuse of an existing dispatch pattern — see Unresolved Questions).
- Handle stream disconnection/reconnection gracefully (matching Event Bus's own reconnection guidance, if any exists in its client-facing docs).

## Constraints
- Must not modify Event Bus's server-side SSE/replay endpoints or stream format — this issue is client-side only.
- Must handle long-lived connections without blocking the Agent's other responsibilities (async/non-blocking consumption).

## Acceptance Criteria
- An Agent-side code path exists that successfully opens Event Bus's SSE stream, receives events, and dispatches them without blocking other Agent operations.
- A stream disconnection is handled (reconnect or fail gracefully) without crashing the Agent process.
- EVENTBUS-006 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once implemented and verified.

## Testing Expectations
Unit tests for the SSE client (connection handling, event parsing, disconnection/reconnection) and an integration test confirming an event published to Event Bus is received by the Agent-side subscriber.

## Documentation Impact
Update EVENTBUS-006's entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (remove once resolved). Document the new subscribe client's responsibility boundary in the Agent area's documentation.

## Out of Scope
- EVENTBUS-005 (publish) and EVENTBUS-007 (topic management) — tracked as separate issues.
- Any change to Event Bus's server-side SSE/replay logic or schema.

## Dependencies
N/A: none

## Unresolved Questions
- What Agent-side mechanism should dispatch received events (a new event-handler registry, or reuse of an existing internal dispatch mechanism)? Not specified by the existing Known Issue entry — needs owner/architect decision during implementation.

## AI Implementation Instruction
Add the Agent-side SSE subscribe client only; do not modify Event Bus's server-side code. Do not guess the event-dispatch mechanism — if it is not already decided elsewhere, implement the client as a standalone consumer and stop to report the open question rather than inventing a dispatch design unilaterally. Keep the change scoped to this one capability — do not also implement publish or topic management in the same change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115629
- **Related target files**: scripts/agent/ (new SSE client module, exact path Unknown)
