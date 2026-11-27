# Implement the EventBus retention-participant registry and safe purge

## Priority
High

## Summary
Record the pending retention-participant decision (only from a maintainer-supplied approval) and implement the persistent registry, explicit consumer lifecycle, legal holds, state-aware purge, replay floor, and an independent retention task.

## Background
Source: bundle item H-04. Verified against master on 2026-11-27:
- `Explicit in code`: `earliest_available_seq` and `replay_position_expired` appear in docs only and have no match under `scripts/` or `tests/`.
- `Documentation only`: Known Issue `EVENTBUS-002` (High, open) and the pending approval `AAL-042` (approver and date `Not recorded`) are in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `AAL-042` covers the registry schema, registration rules, decommission procedure, and ownership.
- This overlaps the open issue `issues/20261125-103310_adrr004_eventbus-retention-replay.md`, which already files the purge, replay floor, HTTP 410, and health signals with a constraint not to implement the registry, purge, or maintenance task before `AAL-042` is approved and not to write approval text. This issue adds the registry lifecycle APIs, legal holds, and the independent retention task.
- Re-verify this issue against current source after that sibling is resolved or merged.

## Problem
EventBus cannot safely delete events without an authoritative, persistent set of retention participants. Connected subscribers, authorization generations, offsets, and delivery rows are incomplete proxies; treating disconnect, token expiry, or authorization TTL expiry as decommission would cause silent event loss.

## Reason for Change
`EVENTBUS-002` is High and open, and storage grows without bound. The registry, schema, lifecycle, purge predicate, replay behavior, health, and tests modify one EventBus boundary, so they are one issue.

## Implementation Intent
Use `eventbus.sqlite` as the source of truth for retention participation. Purge stays fail-closed unless every active participant has acknowledged the event or was explicitly decommissioned and no dead-letter, outbox, legal-hold, or lineage blocker remains.

## Target Files or Areas
- `scripts/eventbus/`, `tests/eventbus/`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `docs/24_eventbus/`, the EventBus API manifest under `registry/manifests/`
- EventBus configuration and deployment files under `config/` and `deploy/` (`Needs confirmation`)

## Required Changes
- Approval and contract: record the approval of a persistent EventBus-owned registry only from a maintainer-supplied decision, never an invented approver or date; define active participants as registered and not explicitly decommissioned; make registration and decommission explicit administrative actions; prohibit consumer-ID reuse; make normal decommission fail while unprocessed events remain; define forced decommission as a separate privileged and audited operation; define fail-closed purge for missing, unreadable, or inconsistent registry state; remove the pending ledger entry only after the ADR Approval Record is complete.
- Schema and implementation: add authoritative registry state (consumer ID, participant flag, registration and decommission time, actor, reason code, update time); keep last-seen and last-ack values derived or non-authoritative; add legal-hold state separately; add retention-task execution state, indexes, and uniqueness constraints; update the schema fingerprint and use archive and recreate on mismatch; implement dedicated registration, decommission, and forced-decommission APIs that do not reuse runtime authorization endpoints; ensure authorization TTL expiry cannot decommission; block purge when any participant or blocker state is uncertain; preserve unacknowledged events, pending or failed outbox rows, incomplete dead-letter work, legal holds, and required lineage; delete events and dependent rows as one referentially consistent unit; run retention independently from the dead-letter repair loop; implement `earliest_available_seq` and `latest_available_seq`; return HTTP 410 `replay_position_expired` for expired replay and subscribe positions; never silently advance consumer offsets; expose registry, retention, purge lag, failure, and readiness state.

## Constraints
- Do not use authorization state as the registry source of truth and do not delete events by age alone.
- Do not close `EVENTBUS-002` before implementation, documentation, and verification are complete.
- Do not implement the registry, purge, or task before the maintainer approves `AAL-042`; persisted-schema changes follow `rules/persisted-schema-change.md`.

## Acceptance Criteria
- The registry decision is approved and recorded correctly, by the maintainer.
- No purge occurs with an uncertain participant set and no orphan EventBus rows remain after a purge.
- Replay expiration is explicit, returns 410, and never changes an offset.
- ADR-006 retention invariants have real automated evidence or remain accurately marked incomplete.

## Testing Expectations
Registry schema and fingerprint; registration, duplicate registration, and ID reuse; normal and forced decommission; disconnect, token expiry, authorization TTL expiry, and restart are not decommission; missing or inconsistent registry fails closed; purge blockers and referential integrity; replay and subscribe 410; offset preservation; retention task lifecycle and shutdown; health and readiness. Run the validation sequence in `rules/toolchain.md`.

## Documentation Impact
ADR-006 evidence, the Approval Ledger, the Known Issue, and EventBus schema, administration, replay, retention, and health documents, handled in issues/20261127-085937_amem009_docs-manifests-sync.md and issues/20261127-085938_amem010_final-validation-gate.md. Follow `skills/DESIGN.md`.

## Out of Scope
- Deciding the registry model (a maintainer decision) and removing `events.jsonl` (issues/20261125-103311_adrr005_eventbus-jsonl-removal.md).

## Dependencies
- Overlaps issues/20261125-103310_adrr004_eventbus-retention-replay.md; fix order: resolve or merge that sibling first, or split ownership at plan time.
- Blocked by the maintainer's approval of `AAL-042`.
- Blocks issues/20261127-085937_amem009_docs-manifests-sync.md.

## Unresolved Questions
- `不明`: whether this issue should be merged into issues/20261125-103310_adrr004_eventbus-retention-replay.md (a user decision).
- `不明`: the approved registry schema, registration timing, decommission transitions, and maintenance boundaries (`AAL-042`).
- `不明`: which `config/` and `deploy/` files carry EventBus retention settings.

## AI Implementation Instruction
Stop before implementation if the `AAL-042` approval is not recorded. Never write approval text, an approver, or a date. Do not implement purge on age alone.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085932
- **Related target files**: `scripts/eventbus/`, `tests/eventbus/`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/24_eventbus/`
