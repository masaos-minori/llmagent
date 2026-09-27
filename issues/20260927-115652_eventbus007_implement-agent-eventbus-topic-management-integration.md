# Implement Agent EventBus topic management integration

## Priority
Low

## Summary
Define and implement an Agent-side capability for managing Event Bus topics, closing Known Issue EVENTBUS-007.

## Background
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-007 records that Agent→EventBus topic management integration is intentionally unimplemented (Status: deferred, Severity: Low) — a deliberate deferral, not a defect. This issue exists to track eventual implementation once the integration is prioritized, per the entry's own Recommended Action.

## Problem
Unlike EVENTBUS-005/006, Event Bus currently has no server-side concept of a manageable "topic" entity. Confirmed via reading `scripts/eventbus/broker.py`, `scripts/eventbus/config.py`, and `scripts/eventbus/auth.py`: `topic` is only a free-form string field on each event (`event.get("topic", "")`), used for subscription filtering (`_Subscriber.topics`) and static per-consumer authorization (`consumer_authorization`/`topic_authorization` in config). There is no create/list/rename/delete API for topics as a distinct entity — a topic exists only as whatever string values have been used on published events or configured in the authorization maps. `scripts/agent/` has zero references to `eventbus`/`EventBus`.

## Reason for Change
Administrative workflows currently require direct MCP tool calls or manual config edits to manage topic-based access; an Agent-side capability would let these workflows be automated. However, since no server-side topic-management concept exists yet, this issue's scope is broader than EVENTBUS-005/006 — it may require server-side design work in addition to an Agent-side client.

## Implementation Intent
Before writing any code, first decide what "topic management" concretely means for Event Bus (see Unresolved Questions) — there is no existing server-side API this issue can simply wrap, unlike EVENTBUS-005/006. Once that scope is decided (e.g. dynamic `topic_authorization` updates via a new admin endpoint), implement the minimal server-side API needed plus a thin Agent-side client for it.

## Target Files or Areas
- `scripts/eventbus/` (potential new admin endpoint for topic/authorization management — exact scope Unknown, depends on the design decision below)
- `scripts/agent/` (new client module; exact location Unknown)
- `scripts/eventbus/config.py`, `scripts/eventbus/broker.py`, `scripts/eventbus/auth.py` (reference for current topic/authorization model)

## Required Changes
- Decide the concrete scope of "topic management" (see Unresolved Questions) before implementation begins.
- If server-side work is in scope: add the decided management API (e.g. dynamic authorization updates) to `scripts/eventbus/`.
- Add an Agent-side client for whatever server-side API results.

## Constraints
- Must not change the existing per-event `topic` field's meaning or format — any new management capability layers on top of it, not replaces it.
- Must preserve the existing static `consumer_authorization`/`topic_authorization` config-file model as a valid configuration path, if a dynamic management API is added alongside it.

## Acceptance Criteria
- A concrete definition of "topic management" is documented and agreed before implementation (this issue's Unresolved Question is resolved).
- An Agent-side code path exists that exercises the resulting management capability end-to-end.
- EVENTBUS-007 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items once implemented and verified.

## Testing Expectations
Unit and integration tests scoped to whatever management API results from the design decision below; cannot be fully specified until that decision is made.

## Documentation Impact
Update EVENTBUS-007's entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (remove once resolved). If a new server-side concept is introduced, document its design intent and boundaries in the EventBus area's documentation, and record the design decision in an ADR if it changes EventBus's authorization model.

## Out of Scope
- EVENTBUS-005 (publish) and EVENTBUS-006 (SSE subscribe) — tracked as separate issues.
- Changing the existing static `consumer_authorization`/`topic_authorization` config-file model, unless the design decision below explicitly requires it.

## Dependencies
N/A: none

## Unresolved Questions
- What does "topic management" concretely mean here — creating/listing/renaming topics as first-class entities, or dynamically updating the existing `consumer_authorization`/`topic_authorization` config at runtime instead of only at config-load time? The existing Known Issue entry does not specify, and no existing server-side concept answers this. This must be resolved by owner/architect decision before implementation, not assumed by an implementer.

## AI Implementation Instruction
Do not start implementation before the Unresolved Question above is explicitly answered by the owner — this issue's scope is undefined until then. If asked to implement without that decision having been made, stop and report the open question rather than inventing a topic-management design unilaterally. Keep the change scoped to this one capability — do not also implement publish or SSE subscribe in the same change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115652
- **Related target files**: scripts/eventbus/ (scope Unknown), scripts/agent/ (new client module, exact path Unknown)
