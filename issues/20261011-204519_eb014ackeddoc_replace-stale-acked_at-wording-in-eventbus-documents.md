# Replace stale acked_at wording in eventbus documents

## Priority
Medium

## Summary
Several eventbus documents still describe ACK state as a timestamp column `acked_at`, including a documented event-level `events.acked_at` column and a `consumer_delivery` column of the same name. The schema stores per-consumer ACK state as the boolean `consumer_delivery.acked`, and the `events.acked_at` column has been dropped. Correct the documents so they describe the current schema.

## Background
- A schema change replaced `acked_at` with an `acked` boolean on `consumer_delivery` and removed the event-level `events.acked_at` column (a migration drops it). The repository function `ack_event()` that wrote the event-level column was removed at the same time; the remaining `ack_event` symbols under `scripts/eventbus/` are HTTP route handlers.
- The ACK/NACK endpoint reference and the ADR-006 data-model note already describe the new state (`consumer_delivery.acked`, no event-level `acked_at`).
- The delivery-semantics document (`eventbus_05_dlq_offsets_and_delivery_semantics.md`) still states in several places that ACK sets `consumer_delivery.acked_at` to a timestamp, that "unset `acked_at`" means not ACKed, and that the ACKed state is `consumer_delivery.acked_at IS NOT NULL`.
- The persistence-schema document (`eventbus_06_persistence_schema_and_replay.md`) still lists `acked_at` among the `events` key columns (annotated as an unused event-level column) and describes `consumer_delivery(consumer_id, event_id, acked_at)` with an upsert that sets `acked_at`.
- The reference API document (`eventbus_08_reference_api.md`) still lists a repository function `ack_event(conn, event_id, now)` described as setting `acked_at` on an event.
- This was first noticed as a single sentence (UNK-02 of `plans/done/20261011-201351_plan.md`) and widened after grepping the documents.

## Problem
- A reader following the delivery-semantics or persistence-schema document looks for a timestamp column that does not exist, and cannot tell that ACK state is a boolean.
- The state-transition tables in the delivery-semantics document define "ACKed" with a predicate (`acked_at IS NOT NULL`) that does not match the actual column.
- The reference API lists a repository function that no longer exists.
- Evidence (`Explicit in code`): the `consumer_delivery` table has an `acked` integer column and no `acked_at`; a migration drops `events.acked_at`; the ACK repository function writes `acked`. Evidence (`Explicit in documentation`): the three documents above still say `acked_at`; the endpoint reference and ADR-006 already say otherwise.

## Reason for Change
- Documentation/code mismatch on persisted state and on a removed function, in documents that implementers use as the source for ACK semantics.
- The documents contradict the endpoint reference and ADR-006 on the same topic.

## Implementation Intent
- Describe the current model: per-consumer ACK state is the boolean `consumer_delivery.acked`; there is no event-level ACK column; the repository's ACK function is `ack_event_for_consumer`.
- Replace predicates such as "`acked_at IS NOT NULL`" with the boolean equivalent, and describe the first-ACK idempotency without a timestamp.
- Remove or replace the reference API row for the removed `ack_event` repository function; keep the HTTP route entries untouched.
- Follow the docs content policy: describe behavior and intent, not line numbers or implementation counts.

## Target Files or Areas
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
- `docs/24_eventbus/eventbus_08_reference_api.md`

## Required Changes
- Replace `acked_at` wording with the boolean `acked` state in the three documents wherever it describes current behavior.
- Correct the schema description of `consumer_delivery` and the `events` key-column list.
- Correct the reference API entry for the removed repository function.
- Keep the wording consistent with `eventbus_12_ack_nack_endpoints.md` and ADR-006.

## Constraints
- Documentation only; do not change code, tests, schema, or migrations.
- Do not edit ADR-006 or the endpoint reference unless a check shows a contradiction.
- Do not rewrite unrelated parts of these documents.

## Acceptance Criteria
- None of the three documents describes a current `acked_at` column, an event-level ACK column, or a repository function that no longer exists.
- The delivery-semantics state tables define the ACKed state with the boolean `acked` column.
- The three documents agree with `eventbus_12_ack_nack_endpoints.md` and ADR-006.
- The documentation checkers named in `routing.md` "When to run which tool" report no findings for each edited document.

## Testing Expectations
- Documentation-only; run the documentation checkers and a search for `acked_at` across `docs/` to confirm the only remaining mentions are intentional historical or migration notes.
- Manual verification against the `consumer_delivery` table definition and the ACK repository function.

## Documentation Impact
Update the three eventbus documents above (ACK state model, schema description, reference API entry). Record behavior and boundaries, not implementation counts or line numbers.

## Out of Scope
- Any code, schema, or migration change.
- The duplicate-ACK response field name (already handled by the plan that fixed it).
- Other eventbus documentation clean-up not about ACK state.

## Dependencies
- Follows `plans/done/20261011-201351_plan.md` (UNK-02). No blocking dependency.

## Unresolved Questions
- Should historical mentions of `acked_at` (for example in a migration note) be kept? `Needs confirmation`; default is to keep only explicitly historical notes.
- Is the `ack_event` row in the reference API intended to describe the HTTP handler instead of the removed repository function? `Needs confirmation`; the row's signature and description describe the repository function.

## AI Implementation Instruction
- Resolve the Unresolved Questions with the user or by checking the code before editing.
- Edit only the three listed documents and only the passages that describe ACK state or the removed function.
- Do not change code or tests; run the documentation checkers before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261011-201351_plan.md` (Unknown UNK-02)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261011-204519
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_08_reference_api.md`
