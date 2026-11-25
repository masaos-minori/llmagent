# Implement EventBus retention, the replay floor, and the retention health signals

## Priority
High

## Summary
Implement ADR-006 Decision Details 18 to 20 and INV-19 to INV-22: state-aware purge in one transaction, a persisted replay floor with HTTP 410, and the retention and capacity health signals. Implementation is blocked until the maintainer approves the retention-participant registry (ledger entry `AAL-042`).

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issues 005, 006, 010, 011):
- Confirmed: no retention task, purge, replay-floor check, HTTP 410, or capacity signal exists under `scripts/eventbus/` (the only registry reference is the subscriber registry in `broker.py`). This is Known Issue `EVENTBUS-002` (High, open) in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, whose recommended action is the implementation issue this document files.
- Confirmed: `scripts/eventbus/schema.sql:3,24,49` states "no row is deleted automatically; growth is an accepted risk", which contradicts ADR-006 (state-aware retention, no unbounded growth accepted by ADR-008 Decision Detail 23).
- Partly refuted: the note says a degraded health payload with HTTP 503 and readiness true is a defect. `is_ready()` documents that a capacity-only degraded reason does not change readiness (`scripts/eventbus/health_route.py:65-70`), and ADR-006 Decision Detail 20 says only a critical disk shortage or a retention-invariant failure makes readiness false, a warning does not. The missing part is the critical level and the retention signals, not the existing 503 behavior.
- Not found: a direct test that `/replay` never changes a consumer offset (`replay_route.py` reads through `fetch_events_since`, and `offset` there is a pagination parameter); the existing replay tests do not assert offset invariance. Not exhaustively verified across all EventBus tests.
- Blocking: ADR-006 Decision Detail 18 says the registry model "is not yet approved; this is an open owner decision, and no purge may run until it is approved"; `AAL-042` is pending with approver and date `Not recorded`; `AAL-007` (Replay Contract) is pending.

## Problem
EventBus storage grows without bound, a purged position cannot be detected, and readiness does not reflect retention or critical capacity.

## Reason for Change
ADR-006 INV-19 to INV-22 are Not verified and unimplemented; this is the High-severity gap EVENTBUS-002.

## Implementation Intent
Deliver one coherent lifecycle: participant registry and maintenance state from the approved model, one purge transaction over events, delivery state, and outbox state, a persisted replay floor enforced by replay and subscribe, and health results that use the same retention state. Purge stays disabled until the approval exists.

## Target Files or Areas
- `scripts/eventbus/schema.sql`, `scripts/eventbus/schema.py`
- `scripts/eventbus/replay_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/app.py`
- a new retention module under `scripts/eventbus/`
- `tests/eventbus/`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_01_index.md`, `registry/manifests/invariant_coverage.yaml`
- `docs/24_eventbus/` operations documents

## Required Changes
- Persist the participant registry and maintenance state as approved; add state-aware purge in one transaction that is blocked by pending or failed outbox work, legal hold, required lineage, or unacknowledged active participants.
- Persist and enforce the replay floor; return 410 `replay_position_expired` below it without advancing any offset.
- Add the capacity and retention signals and the critical levels that set readiness false; keep warning semantics as ADR-006 states them.
- Correct the `schema.sql` comments to describe the unbounded growth as an implementation gap.
- Add replay offset-invariance coverage and register evidence in ADR-006, the index, and the manifest; close `EVENTBUS-002` only after implementation and evidence.

## Constraints
- Do not implement purge, the registry schema, or the maintenance task before the maintainer approves `AAL-042`; do not write approval text or an approver.
- Keep the existing 503 and readiness behavior for warning-level capacity reasons.
- Persisted-schema changes follow `rules/persisted-schema-change.md` (the EventBus schema is recreated on mismatch per ADR-008).

## Acceptance Criteria
- ADR-006 INV-19 to INV-22 have automated evidence.
- Purge never removes protected evidence or splits a purge unit; replay and subscribe return 410 below the floor and keep current behavior above it; replay never changes any consumer offset.
- Each degraded reason has an explicit HTTP, status, liveness, and readiness result; critical retention or disk conditions give readiness false.
- The schema comments no longer present unbounded growth as accepted design.

## Testing Expectations
Schema and transition tests, protected-evidence and atomic-purge tests, floor 410 tests for replay and subscribe, a multi-consumer offset invariance test, crash and rollback tests, a health outcome matrix, and the ADR cited-test and manifest checks.

## Documentation Impact
ADR-006, the ADR index, the manifest, the governance Known Issue, and the EventBus operations documents.

## Out of Scope
- Deciding the registry model (a maintainer decision); removal of `events.jsonl` (issues/20261125-103311_adrr005_eventbus-jsonl-removal.md).

## Dependencies
- Blocked by the maintainer's approval of `AAL-042` and the status of `AAL-007` in the governance ledger (not issues).
- Coordinate with issues/20261125-103311_adrr005_eventbus-jsonl-removal.md where both edit the governance evidence.

## Unresolved Questions
- `不明`: the approved registry schema, registration timing, decommission transitions, and maintenance task boundaries (the maintainer's decision, `AAL-042`).
  The decision to be recorded by the maintainer covers: the registry schema and its canonical owner; the registration timing and the responsible component; the active and decommissioned states and their legal transitions; who may authorize a decommission and what producer or consumer removal does; the acknowledgement and purge transaction boundaries; and the dedicated maintenance task with the required capacity and retention signals. The result is recorded as an approval in ADR-006 and the governance ledger (or the change is reverted); ADR-006, the ledger, and EventBus operations documents must then use the same terminology and state model, and purge stays prohibited until that record exists. The retention design document under `docs/24_eventbus/` was not identified in this verification.
- `不明`: the approved Replay Contract (`AAL-007`).
- `不明`: deployment probe configuration that consumes readiness.

## AI Implementation Instruction
Stop before implementation if the `AAL-042` approval is not recorded; report the missing record; never invent the decision.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103310
- **Related target files**: `scripts/eventbus/schema.sql`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/app.py`
