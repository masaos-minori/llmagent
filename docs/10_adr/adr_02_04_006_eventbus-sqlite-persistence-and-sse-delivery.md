---
title: "ADR-006: EventBus SQLite Persistence and SSE Delivery"
area: governance
tags:
  - eventbus
  - sqlite
  - sse
related:
  - adr_02_01_002_platform-config-isolation.md
  - eventbus_01_system-overview.md
  - eventbus_03_dlq_operations.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_07_configuration-and-operations.md
  - eventbus_08_reference_api.md
  - governance_03_issue-and-uncertainty-management.md
  - adr_02_01_004_platform-environment-failure-handling-policy.md
  - adr_02_04_013_eventbus-authentication-authorization.md
  - adr_02_05_008_db-sqlite-4db-separation.md
  - governance_01_documentation-policy.md
---

# ADR-006: EventBus SQLite Persistence and SSE Delivery

## Keywords

- eventbus
- sqlite
- persistence
- sse
- delivery
- dlq

## Status

Accepted

## Summary

Canonicalizes SQLite (`eventbus.sqlite`) as the sole persistent store and system of record of Events and SSE as the Live delivery channel, with At-Least-Once Delivery (duplicates tolerated, losses not, except under the ADR-008 schema-mismatch rule), offset monotonicity, Consumer ID conflict detection, state-aware bounded retention, and explicit replay expiration (see Decision).

## Context

### Problem

The EventBus has one system of record, `eventbus.sqlite`, plus derived DLQ artifacts. SQLite is the canonical store of Events; SSE delivery is independent as a low-latency channel. Replay of unprocessed Events on Subscriber reconnection must be guaranteed, and delivery guarantees for ACK/NAK/DLQ must be clarified. Without a retention contract, Events, delivery rows, DLQ outbox rows, write-ahead log files, and archives grow without bound, and without a replay floor a consumer cannot tell that its start position has been purged.

### Constraints

- EventBus events are managed in a dedicated SQLite database (`eventbus.sqlite`) under the ADR-008 per-process database separation
- SSE delivery: real-time only to connected Subscribers
- No `events.jsonl`: the EventBus writes no event replica outside `eventbus.sqlite`; structured security audit records are operational logs, not an EventBus data store
- Consumer IDs: client-specified, not server-generated
- Offsets advance by ACK; no automatic advancement

## Assumptions

- Single host; the EventBus owns `eventbus.sqlite` among the six per-process SQLite databases defined by ADR-008
- Limited concurrency
- Privileges are enforced at the EventBus HTTP authentication layer defined by ADR-013, not within SQLite
- No external dependencies (SQLite is local)
- Items to re-evaluate if the assumptions no longer hold: distributed execution, integration with an external event store

## Decision

### Decision Details

1. SQLite is the canonical store of Events, and SSE is the low-latency delivery channel.
2. The Publisher persists an Event to SQLite via `POST /publish` and delivers it over SSE to connected Subscribers.
3. Events are stored even when no Subscriber is present.
4. On Subscriber reconnection, the Consumer ID and ACK Offset are checked, unprocessed Events are Replayed from SQLite, and the Subscriber returns to SSE Live delivery.
5. Successful SSE delivery is not a substitute for successful persistence; when a SQLite write fails, a success response is not returned.
6. Consumer IDs stay fixed across restarts, and ACK Offsets are persisted.
7. Moving an ACKed Offset backward is not permitted.
8. Event IDs are assigned so that Consumers can process idempotently.
9. At-Least-Once Delivery is the baseline: duplicates are tolerated but losses are not. The guarantee holds when the Consumer initiates delivery from a start position the Consumer itself selected, either a `since_seq` greater than zero or a `Last-Event-ID` header. Events that are not carried over when the database is archived and recreated under the ADR-008 schema-mismatch rule are outside the guarantee (Decision Detail #22).
10. The state, count, and history of NAK, Retry, DLQ, and Requeue are persisted.
11. The following delivery rules apply:
    - 11a. An ACK with `new_offset <= current_offset` is accepted, offset unchanged (Monotonicity Invariant); enforced atomically in SQL on the per-consumer offset table.
    - 11b. A non-empty Consumer ID may have only one active `GET /subscribe` connection at a time; a second concurrent connection is rejected (Conflict Detection Required). Exclusivity on `POST /events/{event_id}/ack` and `POST /nack` is enforced by admitting only an authenticated Consumer principal whose explicit `consumer_id` and topic authorizations cover the request; admin and shared credentials have no Consumer-route bypass (ADR-013). It is not provided by binding the call to a live connection.
    - 11c. When ACK persistence fails, an error response is returned and neither the delivery state nor the offset advances; the event therefore remains eligible for redelivery (At-Least-Once).
    - 11d. DLQ promotion paths are unified: inline promotion is prioritized and the background loop supplements it.
    - 11e. On the Replay-to-Live switch, Consumers must process idempotently by `event_id`.
12. Authentication and authorization of EventBus callers follow ADR-013. Independently of authentication, the EventBus accepts only a loopback bind address; a non-loopback host fails configuration validation. (Explicit in code — `scripts/eventbus/config.py` `EventBusConfig.__post_init__`)
13. The ACK Offset is a high-water mark of acknowledged `seq` values, not a contiguous low-water mark. On resume, the position is the lowest unacknowledged `seq` at or below the stored offset when one exists, otherwise `stored_offset + 1`; no unacknowledged event is skipped, and already-acknowledged events are fast-forwarded. Consumers need not ACK in strict `seq` order.
14. The EventBus service is kept (planned future integration), per the repository owner instruction of 2026-11-09; it currently has no defined producers or consumers, and that absence is intentional. The producer and consumer model is not yet defined (NC-003): the defining component and integration timing are left as a marked pending item for the maintainer to complete through `governance_03_issue-and-uncertainty-management.md`.
15. `eventbus.sqlite` is the sole source of truth for the EventBus: Events, consumer delivery state, consumer offsets, DLQ state, the `dlq_outbox` durable promotion record, requeue lineage, retention-participant state, and retention-maintenance state. The EventBus does not create `events.jsonl`. Structured security audit records are operational logs: they are not EventBus replicas, backups, replay sources, or recovery sources. Deadletter JSON files are derived artifacts that can be reconstructed from SQLite.
16. A publish succeeds when its SQLite transaction commits. Broker notification is a best-effort live-delivery side effect that follows the commit and cannot roll back a committed Event.
17. `events.dlq_at` and the `dlq_outbox` table are the authoritative DLQ state. A `dlq_outbox` row whose status is `pending` or `failed` is never deleted automatically.
18. Consumers that take part in retention safety (retention participants) need a persistent source of truth in `eventbus.sqlite`. Authorization generations, connected subscribers, consumer offsets, and existing `consumer_delivery` rows are each insufficient alone to identify the complete participant set. The model of that persistent source (a consumer registry) is not yet approved; this is an open owner decision, and no purge may run until it is approved.
19. Retention never deletes by Event age alone. An Event is purge-eligible only when every active retention participant has acknowledged it or has been explicitly decommissioned, and no blocker applies: incomplete DLQ processing, a `dlq_outbox` row in `pending` or `failed` status, a legal hold, or requeue lineage that must be retained. An Event and its dependent `consumer_delivery` and `dlq_outbox` rows are deleted as one referentially consistent purge unit. Any age condition uses a timestamp generated by the EventBus, never the publisher-supplied `published_at`.
20. Retention runs as a dedicated maintenance task, separate from the DLQ repair loop. The capacity signals are database size, WAL size, free disk, purge lag, retention-blocked count, oldest retained Event age, and the last retention result, each with a warning and a critical level. A critical disk shortage and a retention-invariant failure make readiness false; a warning does not.

### Replay Contract

- **`/replay` is Operator-only.** Only a caller holding the `Operator` role may read through `/replay` (`scripts/eventbus/replay_route.py`). It reads any `seq` range and advances no Consumer offset: a replay is a read-only view, so repeated replays never move a stored position.
- **`/subscribe` start position.** The start `seq` is `since_seq` when it is non-zero, then the Consumer's stored resume position, then the `Last-Event-ID` header (`scripts/eventbus/subscribe_route.py`). `since_seq=0` means unspecified, so a `consumer_id` with a stored offset resumes from that offset and cannot replay from the start through `/subscribe`; `since_seq` greater than zero overrides the stored position. Reading from the earliest retained Event uses `/replay` with `since_seq=0`.
- **Retained history bounds.** `earliest_available_seq` is the lowest `seq` still retained and `latest_available_seq` is the highest. On `/replay`, `since_seq=0` means the earliest retained Event.
- **Expired position.** A `/replay` request or a `/subscribe` resume whose start position is before `earliest_available_seq` fails with HTTP 410 and the error code `replay_position_expired`. The EventBus never advances a Consumer offset silently to the retention floor.
- **Open decision.** Whether `/subscribe` should support replay from the start for a Consumer with a stored offset is not decided; this ADR records the current behavior and `/replay` as the alternative.

### Scope

- **Target components**: `EventBroker`, the publish, subscribe and ACK/NACK routes, offset handling (`delivery_repo.py`), and DLQ handling (`dlq.py`, `dlq_repo.py`, `dlq_route.py`), and the retention maintenance task
- **Target processes**: the EventBus process
- **Target data**: the `events` table, the `consumer_delivery` and `consumer_offsets` tables, DLQ state (`events.dlq_at`, the `dlq_outbox` durable promotion record, and deadletter files), retention-participant state, and retention-maintenance state
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `POST /publish`, `GET /subscribe`, `POST /events/{event_id}/ack`, `POST /nack`, `POST /dlq/{event_id}/requeue`

### Out of Scope

- Detailed implementation of security authentication (handled by a separate ADR)
- Detailed configuration of metrics collection
- Detailed logging format
- Performance benchmark thresholds

## Rationale

### 1. Primary Reason for Adoption — Data Integrity

Making SQLite the canonical store of Events prevents Event loss, except when the database is archived and recreated under the ADR-008 schema-mismatch rule. Because an SSE delivery failure is not confused with a persistence failure, Event reliability is ensured.

### 2. Second Reason for Adoption — Operability

Making At-Least-Once Delivery explicit unifies error handling on the Consumer side. Because duplicates are tolerated, Consumers only need to implement idempotent processing.

### 3. Third Reason for Adoption — Security

Guaranteeing Offset monotonicity prevents offsets from moving backward through an invalid ACK. Detecting Consumer ID collisions prevents unintended Event reception.

### 4. Fourth Reason for Adoption — Bounded Growth

A single system of record with state-aware retention keeps storage bounded without discarding an Event that a participant still needs. An explicit replay floor lets a consumer detect purged history instead of silently missing Events.

## Alternatives Considered

### Alternative A: SSE Delivery as a Substitute for Persistence

- **Description:** Attempt SSE delivery before writing to SQLite.
- **Advantages:** Low-latency delivery takes priority; Simple implementation
- **Disadvantages:** Risk of Event loss; Recovery is difficult when delivery fails; Unclear responsibility between persistence and delivery
- **Reason for Rejection:** Data Integrity requires preventing Event loss.
- **Reconsideration Conditions:** SSE delivery becomes 100% reliable; Event loss becomes acceptable

### Alternative B: No offset monotonicity guarantee

- **Description:** Permit ACKed Offsets to move backward.
- **Advantages:** More flexible Consumer implementation; Parallel ACKs are possible
- **Disadvantages:** Unpredictable movement of Offsets; Risk of data loss; Reduced reproducibility
- **Reason for Rejection:** Data Integrity prevents data loss from backward-moving offsets. Out-of-order ACKs are already permitted without backward offset movement (Decision Detail 13).
- **Reconsideration Conditions:** Consumers implement fully idempotent processing; Parallel ACKs become necessary

### Alternative C: No consumer ID conflict detection

- **Description:** Permit concurrent use of the same Consumer ID, with the last write winning.
- **Advantages:** Simple implementation; Adding Consumers is easy
- **Disadvantages:** Unintended Event reception; Offset conflicts; Risk of data loss
- **Reason for Rejection:** Security requires preventing unintended Event reception.
- **Reconsideration Conditions:** Consumer IDs are guaranteed to be fully unique; Unintended Event reception becomes acceptable

## Consequences

### Positive Consequences

- Event loss is prevented, except when the database is archived and recreated under the ADR-008 schema-mismatch rule
- At-Least-Once Delivery becomes explicit
- Unprocessed Events are reliably Replayed on Consumer reconnection
- Offset monotonicity is guaranteed
- Consumer ID collisions are detected
- DLQ promotion paths are unified
- ACK state and Offset tracking are independent per consumer, and the ACK write and Offset advancement are committed or rolled back within a transaction
- The intentional-keep status is now explicit, so reviews can distinguish it from abandonment
- Storage growth is bounded by state-aware retention, and purged history is reported through HTTP 410 instead of being missed silently

### Negative Consequences

- Duplicate Events must be handled
- Cost of detecting Consumer ID collisions
- Overhead of verifying Offset monotonicity
- Authentication and authorization are a separate concern (ADR-013) that must stay consistent with this ADR
- A replay or resume position before the retention floor fails and the Consumer must handle HTTP 410
- Retention needs a persistent participant source and a dedicated maintenance task

### Operational Consequences

- DLQ promotion happens inline on `POST /nack`, with a periodic background sweep as a safety net; a DLQ event is returned to delivery through `POST /dlq/{event_id}/requeue`. Promotion is gated per consumer (see INV-13).
- Health state (database availability, DLQ task state) is exposed through the health endpoint.
- Capacity signals and the retention task state are defined by Decision Detail 20; critical disk shortage and a retention-invariant failure make readiness false.

### Security Consequences

- Trust boundary: privileges are enforced at the EventBus HTTP authentication layer defined by ADR-013, not within SQLite
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: SQLite is the canonical store of Events.
- INV-02: Successful SSE delivery is not a substitute for successful persistence.
- INV-03: Events are stored even when no Subscriber is present.
- INV-04: Consumer IDs stay fixed across restarts, and ACK Offsets are persisted.
- INV-05: Moving an ACKed Offset backward is not permitted.
- INV-06: Event IDs are assigned so that Consumers can process idempotently.
- INV-07: At-Least-Once Delivery is the baseline: duplicates are tolerated but losses are not. The guarantee holds when the Consumer initiates delivery from a start position the Consumer itself selected, either a `since_seq` greater than zero or a `Last-Event-ID` header. Events that are not carried over when the database is archived and recreated under the ADR-008 schema-mismatch rule are outside the guarantee (Decision Detail #22).
- INV-08: The state, count, and history of NAK, Retry, DLQ, and Requeue are persisted.
- INV-09: An ACK with `new_offset <= current_offset` never updates the offset.
- INV-10: A non-empty Consumer ID has at most one active `GET /subscribe` connection. On Subscribe, ACK, and NACK, a caller may use only the `consumer_id` and topic values explicitly bound to its authenticated Consumer principal; no superuser bypass exists (ADR-013 INV-02).
- INV-11: A second concurrent `GET /subscribe` with an active Consumer ID is detected and rejected with HTTP 409.
- INV-12: When ACK persistence fails, an error response is returned, the delivery state and offset are not advanced, and the Event stays eligible for redelivery.
- INV-13: DLQ promotion prefers inline promotion; the background loop only supplements it. An Event promotes only when every attempting consumer's failure count (`consumer_delivery_failure_count`) has reached max_retry (`>= max_retry`) and none has ACKed, so one consumer's NACKs never promote an Event shared by others; `events.dlq_at` stays event-level.
- INV-14: When switching from Replay to Live, Consumers are required to process idempotently by event_id.
- INV-15: The EventBus binds only to a loopback address (this ADR owns the decision; ADR-013 layers authentication on top); a non-loopback host fails configuration validation.
- INV-16: The Delivery-State UPSERT and the Offset advancement in `ack_event_for_consumer()` are committed within a single transaction, and if either fails, both are rolled back.
- INV-17: `eventbus.sqlite` is the sole system of record; a publish succeeds only when its SQLite transaction commits, and broker notification cannot roll back a committed Event.
- INV-18: The EventBus creates no `events.jsonl`; structured security audit records are not an EventBus replica, backup, replay source, or recovery source.
- INV-19: No Event is deleted by age alone; an Event is purged only when every active retention participant has acknowledged it or been decommissioned and no purge blocker applies, and the Event and its dependent `consumer_delivery` and `dlq_outbox` rows are deleted as one unit.
- INV-20: A `/replay` request or `/subscribe` resume before `earliest_available_seq` fails with HTTP 410 `replay_position_expired`, and no Consumer offset is advanced silently to the retention floor.
- INV-21: A `dlq_outbox` row in `pending` or `failed` status is never deleted automatically.
- INV-22: Retention runs in a dedicated maintenance task separate from the DLQ repair loop, and a critical disk shortage or a retention-invariant failure makes readiness false.

## Failure Policy

### Fail-Fast Conditions

- When a SQLite write fails (persistence failure)
- When ACK persistence fails (risk of breaking idempotency)
- When an offset update fails to persist, the whole ACK transaction (delivery state and offset) is rolled back and the request fails; an ACK whose `seq` is not above the current offset is not a failure, it is accepted with delivery state updated and the offset left unchanged (Decision 11a, INV-09)
- When a second concurrent `GET /subscribe` uses a Consumer ID that is already connected (rejected with HTTP 409)
- When a replay or resume position is before the retention floor (rejected with HTTP 410, offset not advanced)
- When free disk is critically low or the retention-state invariant fails (readiness is false)

### Fail-Open or Degraded Conditions

- No environment-specific downgrade exists: ADR-004 defines a single common failure-handling policy, and a failed SQLite write is never downgraded
- Permitted degradation after the SQLite commit has succeeded: a failure of a secondary path does not fail the request or roll back the Event; the Event stays persisted in SQLite (System of Record) and is delivered by Replay. This is not a Fallback
  - A broker notification failure is logged and counted (Explicit in code — `scripts/eventbus/publish_route.py` `publish()`)

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

### Fallback Policy

Not applicable (no Fallback exists: neither structured audit logs nor SSE delivery may stand in for a failed SQLite write)

## Data Ownership and Persistence

- **System of Record**: `eventbus.sqlite` as a whole: the `events` table, consumer delivery state, consumer offsets, DLQ state (`events.dlq_at` and `dlq_outbox`), requeue lineage, retention-participant state, and retention-maintenance state
- **Derived Data**: deadletter files (copies of DLQ-promoted Events, reconstructable from SQLite); structured security audit records are operational logs, not EventBus data
- **Ownership**: EventBus (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per Event
- **Recovery Source**: SQLite (canonical store)
- **Durable promotion record**: the `dlq_outbox` table (`scripts/eventbus/schema.sql`) records each Event promoted to the DLQ with its request time, `status` (`pending`, `done`, or `failed`), attempt count, and next attempt time; it is the outbox the background loop consumes to generate deadletter files. `done` rows are kept as the generation record; `pending` and `failed` rows are never deleted automatically.
- **Deletion Rule**: DLQ promotion marks the `events` row (`dlq_at`) and writes a deadletter file (Explicit in code — `scripts/eventbus/dlq.py` `promote_single()`). Events are deleted only by the state-aware retention purge of Decision Details 18 to 20, as one unit with their dependent delivery and outbox rows; ADR-008 refers to this ADR for the EventBus retention rule

## Verification

### Automated Tests

| Test | Verifies | Type | Blocking | Implementation |
|---|---|---|---|---|
| Events are stored even when no Subscriber is present | INV-03 | Integration | Yes | `tests/eventbus/test_eventbus_publish.py::test_publish_inserts_event` |
| A Consumer resumes from its persisted ACK Offset under the same Consumer ID after a restart | INV-04 | Integration | Yes | `tests/eventbus/test_eventbus_restart_resume.py::test_same_consumer_id_resumes_from_last_acked_offset`, `tests/eventbus/test_eventbus_restart_resume.py::test_resume_from_sqlite_offset` |
| Un-ACKed Events are Replayed on reconnection | INV-07 | Integration | Yes | `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_unacked_event_replayed_on_reconnect` |
| Offsets do not move backward | INV-05 | Regression | Yes | `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq` |
| A failure to persist an ACK is not treated as success | INV-12 | Integration | Yes | `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state` (the failure raises and nothing is committed; no HTTP-level test exists) |
| Consumers can handle duplicates when switching between Replay and Live | INV-14 | Integration | Yes | `tests/eventbus/test_eventbus_subscribe_transition.py::TestReplayToLiveTransition::test_event_published_during_replay_delivered_via_live_push` (server-side Replay-to-Live transition; consumer-side idempotency is not testable here) |
| Events move to the DLQ after the Retry limit | INV-13 | Integration | Yes | `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPromotionSemantics::test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`, `tests/eventbus/test_eventbus_dlq.py::test_inline_dlq_promotion_on_nack`, `tests/eventbus/test_eventbus_dlq_promotion.py::TestMultiConsumerPromotion` (multi-consumer rule, sweep and inline paths) |
| Consumer ID collisions are detected | INV-11 | Integration | Yes | `tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409`, `tests/eventbus/test_eventbus_broker.py::test_duplicate_consumer_id_rejected` |
| A lower-`seq` ACK leaves the offset unchanged | INV-09 | Regression | Yes | `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`, `tests/eventbus/test_eventbus_ack_nack.py::TestAckHttpBehavior::test_ack_lower_seq_keeps_offset` |
| The Delivery-State UPSERT and the Offset advancement are committed atomically within a single transaction | INV-16 | Regression | Yes | `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state` |
| Identical retries return the original seq and conflicting retries are rejected without modifying stored data | INV-06 | Integration | Yes | `tests/eventbus/test_eventbus_publish.py::test_identical_content_retry_returns_same_seq`, `tests/eventbus/test_eventbus_publish.py::test_conflicting_content_retry_returns_409` |
| NACK counters are persisted per Event; Requeue history is persisted as the `redelivered_from` descendant lineage | INV-08 | Integration | Yes | `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPromotionSemantics::test_nack_increments_consumer_delivery_failure_count`, `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPromotionSemantics::test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count` |
| A non-loopback host is rejected at configuration validation | INV-15 | Unit | Yes | `tests/eventbus/test_eventbus_config.py::test_non_loopback_host_raises_value_error` |
| A SQLite insert or commit failure on `POST /publish` returns a non-success response, leaves no committed Event, and triggers no SSE broker notification | INV-02, INV-17 | Integration | Yes | `tests/eventbus/test_eventbus_publish.py::test_publish_sqlite_write_failure_reports_failure_without_side_effects` |
| DLQ promotion records a durable outbox row whose attempts are bounded and end in a terminal `failed` status, and pending rows survive a restart | INV-13 | Integration | Yes | `tests/eventbus/test_eventbus_dlq_outbox.py::test_terminal_failed_after_bound`, `tests/eventbus/test_eventbus_dlq_outbox.py::test_restart_with_pending_rows` |
| `/subscribe` starts from `since_seq`, then the stored resume position, then `Last-Event-ID`; `/replay` rejects a caller without the Operator role | Replay Contract | Integration | Yes | `tests/eventbus/test_eventbus_subscribe.py::test_since_seq_takes_precedence_over_consumer_offset`, `tests/eventbus/test_eventbus_subscribe.py::test_consumer_offset_used_when_since_seq_is_zero`, `tests/eventbus/test_eventbus_subscribe.py::test_last_event_id_fallback_when_since_seq_and_offset_are_zero`, `tests/eventbus/test_eventbus_auth.py::test_replay_with_publisher_token_is_rejected` (no automated test asserts that `/replay` leaves Consumer offsets unchanged) |

### Startup Validation

- DB connectivity is confirmed at startup

### Deployment Validation

- Check the DB Schema before and after deployment

### Runtime Monitoring

- Health Check: DB connection state, DLQ task state, authorization sweep task state, Broker queue backlog, Slow Consumer detection
- Metrics: Event publish count, ACK count, NACK count, DLQ promotion count
- Logs: Event publish events, ACK events, NACK events, DLQ events
- Capacity signals and the retention task state (Decision Detail 20) are Not verified: no implementation exists yet (see Known Deviations)
- Alert conditions: `db_unavailable`, `dlq_task_stopped`, `authz_sweep_task_stopped`, `authz_sweep_failing`, `broker_queue_backlog_high`, `slow_consumers_detected`
- Degraded condition: failure of a dependency

### Manual Review

- Investigation of DLQ promotions
- DB Schema verification before deployment
- INV-10 connection exclusivity is verified for `GET /subscribe`; its consumer binding is governed by ADR-013 INV-02 and verified by the ADR-013 Verification tests
- INV-18 to INV-22 are Not verified: no implementation or automated test exists yet (see Known Deviations). Expected evidence: a test that no `events.jsonl` is written (INV-18), purge-eligibility and purge-unit tests (INV-19), an HTTP 410 `replay_position_expired` test on `/replay` and `/subscribe` (INV-20), an outbox-retention test (INV-21), and a readiness test for the retention task (INV-22). Cadence: CI once the implementation lands. INV-17 is Not verified as a whole: the publish-failure test in the Automated Tests table covers only the failure side of commit-decides-success, and no test covers broker notification after a commit
- INV-01 has no dedicated automated test (it is exercised indirectly by every persistence test); INV-06 has dedicated tests in the Automated Tests table and is bounded by the envelope schema's `event_id` format check in `tests/eventbus/test_eventbus_publish_contract.py::TestPublishEnvelopeSchemaContract`

## Implementation Notes

- Offset store: `consumer_delivery` tracks per-consumer delivery progress and `consumer_offsets` stores monotonic offsets; `ack_event_for_consumer()` updates both atomically.
- INV-06 is enforced by content comparison logic in `insert_event()`: duplicate events cannot corrupt stored data; identical retries return the original seq, conflicting retries return HTTP 409.
- DLQ promotion threshold (INV-13): an Event promotes when every attempting consumer's `consumer_delivery_failure_count` has reached `max_retry` (`>= max_retry`, i.e. its retry budget is exhausted) and none has ACKed. This `>=` boundary is enforced in `ack_route.py` and `dlq.py` and confirmed by `test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`.
- NACK idempotency: the per-consumer `consumer_delivery_failure_count` is incremented once per distinct delivery-attempt key; a NACK that repeats the same `consumer_last_nack_attempt` key is a no-op. Deduplication is latest-key-only (one remembered key per `(consumer_id, event_id)`); a non-latest key counts as a new attempt. The route passes the caller-supplied key unchanged (no per-request UUID), so genuine network/proxy retries of one attempt deduplicate rather than double-count.
- DLQ requeue commits or rolls back as one unit, and the route runs all SQLite access inside the global database lock (INV-08, INV-16).
- Redelivery uniqueness is enforced by the database: the partial unique index `idx_events_redelivered_from` on `events(redelivered_from)` permits at most one redelivery descendant per original; `redeliver_event()` maps the index violation to `already_redelivered`, which the requeue API returns as HTTP 409 with the error text `event is not in DLQ` (the same text as for an Event that is not in the DLQ), and the pre-insert check only classifies the sequential case. Existing databases are recreated on this schema change per ADR-008.
- Startup validates the database against the shared canonical schema shape by fingerprint and refuses a mismatch; deployment applies the same check and reports started only after a passing health check.
- Shutdown closes the shared connection only after acquiring the global database lock within a bounded wait, and refuses to close it otherwise (INV-01).

## Known Deviations

- **Known Issue:** EVENTBUS-001 — `scripts/eventbus/publish_route.py` still appends `events.jsonl` and exposes the `eventbus_jsonl_append_failure_total` metric, which this ADR no longer permits (INV-18).
- **Known Issue:** EVENTBUS-002 — no retention task, purge, capacity signal, retention configuration, replay-floor check, or HTTP 410 response exists, and the retention-participant registry model is not approved (INV-19 to INV-22).

## Review Triggers

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- The EventBus authentication model (ADR-013) changes
- Persistent storage moves away from a single local SQLite database
- A change from At-Least-Once Delivery to Exactly-Once Delivery becomes necessary
- The retention-participant registry model is approved, or the retention rules or capacity thresholds change

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Current Decision Approval**: Task-level approval decision (repository owner) covers the current decision (2026-10-15).
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text as of 2026-11-09, including the keep decision and the producer/consumer model stated as not yet defined; individual reviewer names are not recorded.
- **Current Decision Approval (pending)**: The addition of the `dlq_outbox` durable promotion record to the Scope and Data Ownership is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-006. No approval is recorded here.
- **Current Decision Approval (pending)**: The Replay Contract (`/replay` Operator-only and offset-preserving; `/subscribe` start position order) is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-007. No approval is recorded here.
- **Current Decision Approval (pending)**: The INV-13 wording (`>= max_retry`), the re-mapping of the INV-04, INV-06, and INV-07 verification rows, and the requeue error text are decision-text changes awaiting maintainer approval; the approver, date, and scope are not recorded, and they are tracked by AAL-008. No approval is recorded here.
- **Current Decision Approval (pending)**: Adding ADR-008 to the front matter `related` and Related ADRs and stating in INV-15 that ADR-006 owns the loopback-binding decision (ADR-013 layers authentication on top) is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-009. No approval is recorded here.
- **Current Decision Approval (pending)**: Stating the no-loss claims (Decision Detail 9, INV-07, and the Rationale and Consequences statements) as holding under the ADR-008 schema-mismatch rule is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-029. No approval is recorded here.
- **Current Decision Approval (pending)**: Stating the start position of the At-Least-Once delivery guarantee as a start position the Consumer itself selected (`since_seq` greater than zero or a `Last-Event-ID` header) in Decision Detail 9 and INV-07 is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-037. No approval is recorded here.
- **Current Decision Approval**: Task-level approval decision by the repository owner acting as `@lead`, given in the task `memo-issue.md` (Part 1, AAL-040), covers Decision Details 15 to 17 and INV-17, INV-18, INV-21: `eventbus.sqlite` is the sole EventBus system of record; publish success is determined by the SQLite transaction commit; broker notification is a best-effort side effect after the commit; the EventBus does not create `events.jsonl`; structured security audit records are not EventBus replicas, backups, replay sources, or recovery sources; Deadletter JSON files are derived artifacts reconstructable from SQLite. No approval date is recorded because the task context gives none; individual reviewer names are not recorded.
- **Current Decision Approval**: Task-level approval decision by the repository owner acting as `@lead`, given in the task `memo-issue.md` (Part 1, first approval unit split from AAL-041), covers the retention and replay principles: Event age alone never authorizes deletion; incomplete DLQ work, `pending` or `failed` outbox state, a legal hold, and required requeue lineage block purge; Events and dependent state are deleted as one referentially consistent purge unit; a replay or subscribe before the retention floor returns HTTP 410 with `replay_position_expired`; Consumer offsets are never silently advanced; a critical disk shortage or a retention-invariant failure makes readiness false. No approval date is recorded because the task context gives none; individual reviewer names are not recorded.
- **Current Decision Approval (pending)**: The persistent retention-participant registry (Decision Detail 18), the participant acknowledgement and decommission clause of Decision Detail 19 and INV-19, and the dedicated-task and capacity-signal-list wording of Decision Detail 20 and INV-22 that the approved principles do not enumerate are decision-text changes awaiting maintainer approval; the registry schema, registration rules, decommission procedure, and ownership are not decided, the approver, date, and scope are not recorded, and they are tracked by AAL-042. No approval is recorded here.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments
- ADR-008: Separation and Lifecycle Policy for Six SQLite Stores
- ADR-013: EventBus Authentication and Authorization

## Implementation References

- `scripts/eventbus/broker.py` — `EventBroker.publish()`, `EventBroker.subscribe()`
- `scripts/eventbus/publish_route.py` — `publish()`
- `scripts/eventbus/subscribe_route.py` — `subscribe()`
- `scripts/eventbus/delivery_repo.py` — `ack_event_for_consumer()`, `nack_event()`, `get_consumer_offset()`
- `scripts/eventbus/event_repo.py` — `insert_event()`
- `scripts/eventbus/db.py` — facade that re-exports the functions above
- `scripts/eventbus/dlq.py` — `promote_single()`, `sweep_orphans()`
- `scripts/eventbus/config.py` — `EventBusConfig.__post_init__()`
- `events` table — `seq`, `event_id`, `topic`, `payload`, `producer`, `published_at`, `redelivered_from`, `dlq_at` (no event-level `acked_at` column; ACK state is per-consumer in `consumer_delivery`)
- `consumer_delivery` table — `consumer_id`, `event_id`, `acked`, `consumer_delivery_failure_count`, `consumer_last_nack_attempt`, PRIMARY KEY `(consumer_id, event_id)`
- `consumer_offsets` table — `consumer_id` PRIMARY KEY, `offset INTEGER NOT NULL DEFAULT 0`
- DLQ promotion paths — inline promotion (on `POST /nack`) and the periodic background loop
- Tests — `tests/eventbus/`, `tests/db/test_create_schema.py`

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification (gaps: Verification > Manual Review)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
