---
title: "ADR-006: EventBus SQLite Persistence and SSE Delivery"
area: governance
tags:
  - eventbus
  - sqlite
  - sse
related:
  - ADR-002-config-isolation.md
  - eventbus_01_system-overview.md
  - eventbus_03_dlq_operations.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_07_configuration-and-operations.md
  - eventbus_08_reference_api.md
  - governance_03_issue-and-uncertainty-management.md
  - ADR-004-environment-failure-handling-policy.md
  - ADR-013-eventbus-authentication-authorization.md
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

This ADR canonicalizes SQLite as the persistent canonical store of Events and SSE as the Live delivery channel, and clarifies delivery guarantees for reconnection, Replay, ACK, NAK, and DLQ. At-Least-Once Delivery is the baseline: duplicates tolerated, losses not. Offset monotonicity and Consumer ID conflict policy are finalized.

## Context

### Problem

The EventBus has multiple data stores (SQLite, JSONL archive, offset files) with different roles. SQLite is the canonical store of Events; SSE delivery is independent as a low-latency channel. Replay of unprocessed Events on Subscriber reconnection must be guaranteed, and delivery guarantees for ACK/NAK/DLQ must be clarified.

### Constraints

- Events managed in a single SQLite database
- SSE delivery: real-time only to connected Subscribers
- JSONL archive: secondary audit log, not Primary Store
- Consumer IDs: client-specified, not server-generated
- Offsets advance by ACK; no automatic advancement

## Assumptions

- Single host, single SQLite database
- Limited concurrency
- Privileges granted only within SQLite
- No external dependencies (SQLite is local)
- Items to re-evaluate if the assumptions no longer hold: multi-DB configuration, distributed execution, integration with an external event store

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
9. At-Least-Once Delivery is the baseline: duplicates are tolerated but losses are not.
10. The state, count, and history of NAK, Retry, DLQ, and Requeue are persisted.
11. The following delivery rules apply:
    - 11a. Reject `new_offset <= current_offset` (Monotonicity Invariant); enforced by an atomic SQL statement against the per-consumer offset table.
    - 11b. A non-empty Consumer ID may have only one active `GET /subscribe` connection at a time; a second concurrent connection is rejected (Conflict Detection Required). Exclusivity on `POST /events/{event_id}/ack` and `POST /nack` is provided by binding the caller's token to its permitted `consumer_id` values (ADR-013), not by binding the call to a live connection.
    - 11c. When ACK persistence fails, an error response is returned and neither the delivery state nor the offset advances; the event therefore remains eligible for redelivery (At-Least-Once).
    - 11d. DLQ promotion paths are unified: inline promotion is prioritized and the background loop supplements it.
    - 11e. On the Replay-to-Live switch, Consumers must process idempotently by `event_id`.
12. Authentication and authorization of EventBus callers follow ADR-013. Independently of authentication, the EventBus accepts only a loopback bind address; a non-loopback host fails configuration validation. (Explicit in code — `scripts/eventbus/config.py` `_validate_deployment_mode()`)
13. The ACK Offset is a high-water mark of acknowledged `seq` values, not a contiguous low-water mark. On resume, the position is the lowest unacknowledged `seq` at or below the stored offset when one exists, otherwise `stored_offset + 1`; no unacknowledged event is skipped, and already-acknowledged events are fast-forwarded. Consumers need not ACK in strict `seq` order.

### Scope

- **Target components**: `EventBroker`, `EventPublisher`, `EventSubscriber`, `OffsetManager`, `DlqService`
- **Target processes**: the EventBus process
- **Target data**: the `events` table, the `consumer_delivery` and `consumer_offsets` tables, DLQ state (`events.dlq_at` and deadletter files)
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `POST /publish`, `GET /subscribe`, `POST /events/{event_id}/ack`, `POST /nack`, `POST /dlq/{event_id}/requeue`

### Out of Scope

- Detailed implementation of security authentication (handled by a separate ADR)
- Detailed configuration of metrics collection
- Detailed logging format
- Performance benchmark thresholds

## Rationale

### 1. Primary Reason for Adoption — Data Integrity

Making SQLite the canonical store of Events prevents Event loss. Because an SSE delivery failure is not confused with a persistence failure, Event reliability is ensured.

### 2. Second Reason for Adoption — Operability

Making At-Least-Once Delivery explicit unifies error handling on the Consumer side. Because duplicates are tolerated, Consumers only need to implement idempotent processing.

### 3. Third Reason for Adoption — Security

Guaranteeing Offset monotonicity prevents offsets from moving backward through an invalid ACK. Detecting Consumer ID collisions prevents unintended Event reception.

## Alternatives Considered

### Alternative A: SSE Delivery as a Substitute for Persistence

#### Description

Treat successful SSE delivery as a substitute for successful persistence, attempting SSE delivery before writing to SQLite.

#### Advantages

- Low-latency delivery takes priority
- Simple implementation

#### Disadvantages

- Risk of Event loss
- Recovery is difficult when delivery fails
- Unclear responsibility between persistence and delivery

#### Reason for Rejection

Data Integrity requires preventing Event loss.

#### Reconsideration Conditions

- SSE delivery becomes 100% reliable
- Event loss becomes acceptable

### Alternative B: No offset monotonicity guarantee

#### Description

Permit ACKed Offsets to move backward so that Consumers can ACK in any order.

#### Advantages

- More flexible Consumer implementation
- Parallel ACKs are possible

#### Disadvantages

- Unpredictable movement of Offsets
- Risk of data loss
- Reduced reproducibility

#### Reason for Rejection

Data Integrity prevents data loss from backward-moving offsets.

#### Reconsideration Conditions

- Consumers implement fully idempotent processing
- Parallel ACKs become necessary

### Alternative C: No consumer ID conflict detection

#### Description

Permit concurrent use of the same Consumer ID, with the last write winning.

#### Advantages

- Simple implementation
- Adding Consumers is easy

#### Disadvantages

- Unintended Event reception
- Offset conflicts
- Risk of data loss

#### Reason for Rejection

Security requires preventing unintended Event reception.

#### Reconsideration Conditions

- Consumer IDs are guaranteed to be fully unique
- Unintended Event reception becomes acceptable

## Consequences

### Positive Consequences

- Event loss is prevented
- At-Least-Once Delivery becomes explicit
- Unprocessed Events are reliably Replayed on Consumer reconnection
- Offset monotonicity is guaranteed
- Consumer ID collisions are detected
- DLQ promotion paths are unified
- ACK state and Offset tracking are independent per consumer, and the ACK write and Offset advancement are committed or rolled back within a transaction

### Negative Consequences

- Duplicate Events must be handled
- Cost of detecting Consumer ID collisions
- Overhead of verifying Offset monotonicity
- Authentication and authorization are a separate concern (ADR-013) that must stay consistent with this ADR

### Operational Consequences

- DLQ promotion happens inline on `POST /nack`, with a periodic background sweep as a safety net; a DLQ event is returned to delivery through `POST /dlq/{event_id}/requeue`.
- Health state (database availability, DLQ task state) is exposed through the health endpoint.

### Security Consequences

- Trust boundary: privileges are granted only within SQLite
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: SQLite is the canonical store of Events.
- INV-02: Successful SSE delivery is not a substitute for successful persistence.
- INV-03: Events are stored even when no Subscriber is present.
- INV-04: Consumer IDs stay fixed across restarts, and ACK Offsets are persisted.
- INV-05: Moving an ACKed Offset backward is not permitted.
- INV-06: Event IDs are assigned so that Consumers can process idempotently.
- INV-07: At-Least-Once Delivery is the baseline: duplicates are tolerated but losses are not.
- INV-08: The state, count, and history of NAK, Retry, DLQ, and Requeue are persisted.
- INV-09: `new_offset <= current_offset` is rejected.
- INV-10: A non-empty Consumer ID has at most one active `GET /subscribe` connection. On ACK and NACK, a caller may use only the `consumer_id` values bound to its token (ADR-013 INV-02).
- INV-11: A second concurrent `GET /subscribe` with an active Consumer ID is detected and rejected with HTTP 409.
- INV-12: When ACK persistence fails, an error response is returned, the delivery state and offset are not advanced, and the Event stays eligible for redelivery.
- INV-13: DLQ promotion prefers inline promotion; the background loop only supplements it.
- INV-14: When switching from Replay to Live, Consumers are required to process idempotently by event_id.
- INV-15: The EventBus binds only to a loopback address; a non-loopback host fails configuration validation.
- INV-16: The Delivery-State UPSERT and the Offset advancement in `ack_event_for_consumer()` are committed within a single transaction, and if either fails, both are rolled back.

## Failure Policy

### Fail-Fast Conditions

- When a SQLite write fails (persistence failure)
- When ACK persistence fails (risk of breaking idempotency)
- When `new_offset <= current_offset` is violated (breaking monotonicity)
- When a second concurrent `GET /subscribe` uses a Consumer ID that is already connected (rejected with HTTP 409)

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists
- A JSONL archive write failure produces only a WARNING log and a failure metric (the Event is already committed to SQLite)
- A broker notification failure after the commit is logged and counted; the Event stays persisted and is delivered by Replay (Explicit in code — `scripts/eventbus/publish_route.py` `publish()`)

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

### Fallback Policy

Not applicable (no Fallback exists: the JSONL archive is an audit log, not an alternative store, and neither it nor SSE delivery may stand in for a failed SQLite write)

## Data Ownership and Persistence

- **System of Record**: the `events` table (SQLite)
- **Derived Data**: the JSONL archive (secondary audit log), deadletter files (copies of DLQ-promoted Events)
- **Ownership**: EventBus (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per Event
- **Recovery Source**: SQLite (canonical store)
- **Deletion Rule**: the EventBus does not delete Events; DLQ promotion marks the `events` row (`dlq_at`) and writes a deadletter file (Explicit in code — `scripts/eventbus/dlq.py` `promote_single()`)

## Verification

### Automated Tests

- **Test**: Events are stored even when no Subscriber is present
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_publish.py::test_publish_inserts_event`

- **Test**: Un-ACKed Events are Replayed on reconnection
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_unacked_event_replayed_on_reconnect`, `tests/eventbus/test_eventbus_restart_resume.py::TestOutOfOrderAckNoSkipOnReconnect::test_out_of_order_ack_no_skip_on_reconnect`

- **Test**: Offsets do not move backward
  - **Verifies**: INV-05
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`

- **Test**: A failure to persist an ACK is not treated as success
  - **Verifies**: INV-12
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state` (the failure raises and nothing is committed; no HTTP-level test exists)

- **Test**: Consumers can handle duplicates when switching between Replay and Live
  - **Verifies**: INV-14
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_subscribe_transition.py::TestReplayToLiveTransition::test_event_published_during_replay_delivered_via_live_push` (server-side Replay-to-Live transition; consumer-side idempotency is not testable here)

- **Test**: Events move to the DLQ after the Retry limit
  - **Verifies**: INV-13
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_promotion_when_delivery_failure_count_gte_max_retry`, `tests/eventbus/test_eventbus_dlq.py::test_inline_dlq_promotion_on_nack`

- **Test**: Consumer ID collisions are detected
  - **Verifies**: INV-11
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409`, `tests/eventbus/test_eventbus_broker.py::test_duplicate_consumer_id_rejected`

- **Test**: `new_offset <= current_offset` is rejected
  - **Verifies**: INV-09
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`

- **Test**: The Delivery-State UPSERT and the Offset advancement are committed atomically within a single transaction
  - **Verifies**: INV-16
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`

- **Test**: Identical retries return the original seq and conflicting retries are rejected without modifying stored data
  - **Verifies**: INV-07
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_publish.py::test_identical_content_retry_returns_same_seq`, `tests/eventbus/test_eventbus_publish.py::test_conflicting_content_retry_returns_409`

- **Test**: NACK counters and requeue counters are persisted per Event
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_nack_increments_delivery_failure_count`, `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count`

- **Test**: A non-loopback host is rejected at configuration validation
  - **Verifies**: INV-15
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_config.py::test_non_loopback_host_raises_value_error`

- **Test**: A publish whose JSONL append fails still succeeds after the SQLite commit (persistence precedes the secondary paths)
  - **Verifies**: INV-02 (partial: no test injects a SQLite write failure on `POST /publish`)
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/eventbus/test_eventbus_publish_contract.py::TestPublishContract::test_publish_succeeds_if_jsonl_append_fails`

### Startup Validation

- DB connectivity is confirmed at startup

### Deployment Validation

- Check the DB Schema before and after deployment

### Runtime Monitoring

- Health Check: DB connection state, DLQ task state, Broker queue backlog, Slow Consumer detection
- Metrics: Event publish count, ACK count, NACK count, DLQ promotion count
- Logs: Event publish events, ACK events, NACK events, DLQ events
- Alert conditions: `db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`
- Degraded condition: failure of a dependency

### Manual Review

- Investigation of DLQ promotions
- DB Schema verification before deployment
- INV-10 is verified for `GET /subscribe` only (EVENTBUS-013 tracks ACK/NACK)
- INV-01 and INV-06 have no dedicated automated test (INV-01 is exercised indirectly by every persistence test; INV-06 is bounded by the envelope schema's `event_id` format check in `tests/eventbus/test_eventbus_publish_contract.py::TestPublishEnvelopeSchemaContract`)

## Implementation Notes

- Transaction guarantee: see INV-16 (a single transaction inside `ack_event_for_consumer()`)
- Monotonicity Enforcement: see INV-05, INV-09
- Resume position: the lowest unacked `seq` at or below the stored offset when one exists, otherwise `stored_offset + 1` (see Decision item 13)
- Offset store: `consumer_delivery` tracks per-consumer delivery progress and `consumer_offsets` stores monotonic offsets; `ack_event_for_consumer()` updates both atomically. At startup, `migrate_legacy_offsets()` reads each offset file's `.map` companion to recover the original `consumer_id` and seeds `consumer_offsets`; without a `.map` companion, the sanitized filename is the `consumer_id`.
- INV-07 is enforced by content comparison logic in `insert_event()`: duplicate events cannot corrupt stored data; identical retries return the original seq, conflicting retries return HTTP 409.

## Known Deviations

- **Known Issue**: EVENTBUS-008 — tracked in governance_03 Part 1 (a principal without a `consumer_id` allowlist is unrestricted, namely the CONSUMER token when `consumer_authorization` is an empty mapping and the shared `auth_token`/`admin_token`, so the ACK/NACK binding of INV-10 is not enforced for it)
- **Known Issue**: EVENTBUS-011 — tracked in governance_03 Part 1 (NACK on a concurrently deleted event)
- **Known Issue**: EVENTBUS-012 — tracked in governance_03 Part 1 (duplicate NACK from the same consumer)
- **Known Issue**: EVENTBUS-013 — tracked in governance_03 Part 1 (ACK and NACK are not bound to the active subscription of a `consumer_id`; they check only the principal allowlist)
- **Known Issue**: EVENTBUS-014 — tracked in governance_03 Part 1 (`events.acked_at` is never written but is still read)

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

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Decision Change (2026-10-08)**: The reinterpretation of INV-12 (a failed ACK is not treated as success and the event stays eligible for redelivery, consistent with INV-07) and the narrowed scope of INV-10 and INV-11 were approved as a task-level approval decision (repository administrator instruction); individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments
- ADR-013: EventBus Authentication and Authorization

## Implementation References

- `scripts/eventbus/broker.py` — `EventBroker.publish()`, `EventBroker.subscribe()`
- `scripts/eventbus/publish_route.py` — `publish()`
- `scripts/eventbus/subscribe_route.py` — `subscribe()`
- `scripts/eventbus/delivery_repo.py` — `ack_event()`, `ack_event_for_consumer()`, `nack_event()`, `get_consumer_offset()`
- `scripts/eventbus/event_repo.py` — `insert_event()`
- `scripts/eventbus/offset_migrator.py` — `migrate_legacy_offsets()`
- `scripts/eventbus/db.py` — facade that re-exports the functions above
- `scripts/eventbus/dlq.py` — `promote_single()`, `sweep_orphans()`
- `scripts/eventbus/config.py` — `_validate_deployment_mode()`
- `scripts/eventbus/offsets.py` — `write_offset()`, `read_offset()`
- `events` table — `seq`, `event_id`, `topic`, `payload`, `acked_at` (event-level column; not written by the ACK route), `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`
- `consumer_delivery` table — `consumer_id`, `event_id`, `acked_at`, PRIMARY KEY `(consumer_id, event_id)`
- `consumer_offsets` table — `consumer_id` PRIMARY KEY, `offset INTEGER NOT NULL DEFAULT 0`
- Offset files — `{offsets_dir}/{sanitized_consumer_id}` (read only by `migrate_legacy_offsets()` at startup)
- DLQ promotion paths — inline promotion (on `POST /nack`) and the periodic background loop
- Tests — `tests/eventbus/`, `tests/db/test_create_schema.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

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
- [ ] Each Invariant has a corresponding Verification (INV-01, INV-02, INV-06, and INV-10 lack a complete automated test; INV-10 is enforced on `GET /subscribe` only, see EVENTBUS-013)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
