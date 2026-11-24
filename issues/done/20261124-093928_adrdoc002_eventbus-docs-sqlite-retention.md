Generated at: 20261124-093928

# Rewrite EventBus documentation for SQLite-only persistence and bounded retention

## Priority
High

## Summary
Rewrite the EventBus documentation set so it consistently describes SQLite-only event persistence, derived DLQ artifacts, state-aware retention, replay expiration, capacity monitoring, archive cleanup, and the separation between event persistence and structured security audit logging.

## Background
Source: `memo-issue.md`. The EventBus documents live under `docs/24_eventbus/` (`eventbus_00` to `eventbus_12`, all present). The ADR decisions this issue documents are produced by issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md. Reference inputs exist at `registry/manifests/eventbus_api.yaml` and `registry/manifests/health_contracts.yaml`; the generator is `tools/generate_reference_table.py`.

## Problem
The current EventBus documentation reflects a model being retired:
- It describes `events.jsonl` as an event replica that can permanently diverge from SQLite, plus JSONL append-failure and count-comparison procedures.
- It states or implies that EventBus data grows without automatic retention, and includes manual deletion guidance that can leave `consumer_delivery` rows orphaned.
- It describes `since_seq=0` as complete replay although retained history becomes bounded.
- It defines no persistent retention-participant set, consumer decommission, replay-floor error, archive cleanup, or capacity thresholds, and does not separate the lifecycles of active DLQ artifacts, `requeued/` artifacts, verified database archives, and audit logs.

## Reason for Change
Operators could keep using unsafe manual SQL, assume JSONL is recoverable, or expect data older than the retention floor to remain replayable, even after the ADRs are corrected (wrong-action risk). It cannot start before the ADR decisions exist.

## Implementation Intent
Present one operationally usable EventBus model: SQLite is the only source of truth; security audit records are separate operational logs; DLQ JSON files are derived artifacts; retention is controlled by persisted state and explicit safety predicates; purge is referentially consistent and bounded; replay expiration is explicit and fail-closed; database, WAL, disk, artifacts, audit logs, and archives all have bounded-growth guidance; health output distinguishes warnings from readiness failures. The files describe one lifecycle, so they are updated together.

## Target Files or Areas
- `docs/24_eventbus/eventbus_00_document-guide.md` through `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
- `registry/manifests/eventbus_api.yaml`, `registry/manifests/health_contracts.yaml` (inputs for generated blocks)
- Exact configuration, route, and schema sources to confirm: `config/eventbus.toml`, `scripts/eventbus/schema.sql`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/route_helpers.py`

## Required Changes
A. Guide and overview
- [ ] Point the document guide to the revised persistence, retention, replay, health, and operations documents.
- [ ] State in the system overview that `eventbus.sqlite` is the only system of record; remove `events.jsonl` from diagrams, data flows, recovery descriptions, and storage inventories; distinguish audit logs from event persistence; describe DLQ JSON files as SQLite-derived artifacts.

B. Persistence and publish durability
- [ ] Remove JSONL append steps, failure scenarios, metrics, SQLite/JSONL count comparison, and JSONL repair procedures; define successful SQLite commit as publish success; keep duplicate/conflict behavior and best-effort broker notification semantics.
- [ ] Document the EventBus-generated timestamp used for retention decisions and exclude publisher-supplied `published_at` from retention cutoff calculation.

C. Retention and purge operations
- [ ] Remove unsafe manual deletion SQL from current operations guidance.
- [ ] Define retention participants and explicit consumer decommission; explain why authorization TTL expiry, current connections, offsets, and existing delivery rows are individually insufficient to define the consumer set.
- [ ] Document purge eligibility predicates, purge-blocking states (unacknowledged delivery, `pending` or `failed` outbox, legal hold, incomplete DLQ work, required lineage), purge ordering and referential-integrity expectations, batch size, per-cycle deletion limit, scheduling, and shutdown behavior; state that retention runs in a dedicated task, not in the DLQ repair loop.

D. Replay and subscribe contracts
- [ ] Add `earliest_available_seq` and `latest_available_seq`; document HTTP 410 `replay_position_expired` for both `/replay` and `/subscribe` resume; state that offsets are never silently advanced to the floor; redefine `since_seq=0` as replay from the earliest retained event.

E. DLQ lifecycle
- [ ] Document `events.dlq_at` and `dlq_outbox` as authoritative state, `pending` / `done` / `failed` outbox retention behavior, recovery and reconciliation of missing DLQ artifacts from SQLite, retention of active and `requeued/` artifacts, handling of orphan, mismatched, and temporary files, and where archive or deletion outcomes are recorded.

F. Health and capacity
- [ ] Add database, WAL, archive, DLQ artifact, audit-log size and free-disk measurements; event count, purge-eligible count, retention-blocked count, oldest retained event age, purge lag, last retention run, last result, last deleted count.
- [ ] Document warning and critical thresholds, readiness behavior for critical disk shortage and retention-state inconsistency, and a retention health state separate from the DLQ task and authorization sweep.

G. Backup and archive retention
- [ ] Document SQLite Online Backup API usage where applicable; retention of verified database archives by generation, age, and total size; a minimum number of verified generations; protection of the latest verified recovery candidate; WAL checkpoint requirements around retention and shutdown.

H. API and generated references
- [ ] Update replay/subscribe API documentation with the HTTP 410 response and health response documentation with the retention and capacity fields.
- [ ] Update configuration documentation only after exact configuration keys are confirmed.
- [ ] Update the API manifest and generated-reference inputs instead of editing generated blocks.

## Constraints
- Documented configuration keys and response fields must exist in the implementation or in an approved implementation issue; unconfirmed keys are marked Needs Confirmation, not invented.
- Generated blocks change only through `tools/generate_reference_table.py`.
- Documentation follows `skills/DESIGN.md` "Docs content policy" and is written in English.

## Acceptance Criteria
- [ ] No current EventBus specification describes `events.jsonl` as a replica, backup, recovery source, or audit ledger.
- [ ] Structured audit logging is documented and clearly outside EventBus event persistence; DLQ JSON artifacts are documented as derived and reconstructable.
- [ ] No current operations guide recommends manual SQL that can leave orphan rows.
- [ ] Retention participants, purge predicates, purge blockers, and decommission behavior are unambiguous.
- [ ] Replay and subscribe expired-position behavior is documented.
- [ ] Database, WAL, disk, DLQ artifacts, audit logs, and verified archives all have bounded-growth guidance; warning and critical health behavior is explicit.
- [ ] Generated EventBus references match their source manifest.

## Testing Expectations
Documentation-only: `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/generate_reference_table.py --check`, Markdown/link checks via `uv run pre-commit run --all-files`, and the checkers listed in `rules/tool-gates.md` for `docs/` changes.

## Documentation Impact
Yes. All EventBus documents above. Record intent, boundaries, constraints, failure behavior, operational notes, and Needs Confirmation items for unconfirmed configuration keys.

## Out of Scope
- ADR changes (see issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md).
- Implementation of retention, health fields, replay-floor behavior, or configuration keys.
- Agent and Session DB documentation (see issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md).

## Dependencies
- Depends on issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md (the ADR decisions must exist first).
- Blocks issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md.

## Unresolved Questions
- `不明`: exact retention and capacity configuration keys and thresholds; the memo requires confirmation first.
- `不明`: whether the health response fields are already implemented or covered by an approved implementation issue.
- `不明`: deployment-specific EventBus configuration and logging configuration locations under `config/` or `deploy/` (not located in this pass).

## AI Implementation Instruction
Edit only the EventBus documents and their manifest inputs. Do not edit generated blocks by hand. Do not invent configuration keys or response fields; mark them Needs Confirmation. Do not change code. Stop and report if the ADR decisions from issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md are not yet approved.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-093928
- **Related target files**: `docs/24_eventbus/eventbus_00_document-guide.md` through `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `registry/manifests/eventbus_api.yaml`, `registry/manifests/health_contracts.yaml`
