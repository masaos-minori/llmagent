---
title: "ADR-006: EventBus SQLite Persistence and SSE Delivery"
area: governance
tags:
  - eventbus
  - sqlite
  - sse
decision_scope:
  - eventbus
related:
  - ADR-002-config-isolation.md
  - eventbus_01_system-overview.md
  - eventbus_03_dlq_operations.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_08_configuration-and-operations.md
  - eventbus_09_reference_api.md
  - governance_03_issue-and-uncertainty-management.md
supersedes: []
superseded_by: null
---

# ADR-006: EventBus SQLite Persistence and SSE Delivery

## Keywords

eventbus
sqlite
persistence
sse
delivery
dlq

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

### Assumptions

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
11. Open items confirmed with code and tests, decision finalized:
    - Reject `new_offset <= current_offset` (Monotonicity Invariant); enforced by atomic SQL statement against per-consumer offset table
    - Prohibit concurrent use of same Consumer ID (Conflict Detection Required)
    - Detect Consumer ID collisions
    - ACK persistence failure → error response + no redelivery (Fail-Closed)
    - Unify DLQ promotion paths → inline promotion prioritized; background loop supplements
    - Replay-to-Live switch → Consumers must process idempotently by event_id
12. Resolve Known Issue vs. API Reference contradiction on Offset monotonicity.
13. If authentication not implemented, enforce Loopback/Unix Socket binding, firewall restrictions, and ban on external exposure.
14. The ACK Offset is a high-water mark of acknowledged `seq` values, not a contiguous low-water mark. On resume, the position is the lowest unacknowledged `seq` at or below the stored offset when one exists, otherwise `stored_offset + 1`; no unacknowledged event is skipped, and already-acknowledged events are fast-forwarded. Consumers need not ACK in strict `seq` order.

### Scope

- **Target components**: `EventBroker`, `EventPublisher`, `EventSubscriber`, `OffsetManager`, `DlqService`
- **Target processes**: the EventBus process
- **Target data**: the `events` table, offset files, DLQ state
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
- Authentication must be implemented

### Operational Consequences

Not applicable (EventBus persistence has no RAG-style consistency check or rebuild command)

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
- INV-10: Concurrent use of the same Consumer ID is prohibited.
- INV-11: Consumer ID collisions are detected.
- INV-12: When ACK persistence fails, an error response is returned and the Event is not redelivered.
- INV-13: DLQ promotion prefers inline promotion; the background loop only supplements it.
- INV-14: When switching from Replay to Live, Consumers are required to process idempotently by event_id.
- INV-15: If authentication is not implemented, binding to Loopback or a Unix Socket, Firewall restrictions, and a ban on external exposure are technically enforced.
- INV-16: The Delivery-State UPSERT and the Offset advancement in `ack_event_for_consumer()` are committed within a single transaction, and if either fails, both are rolled back.

## Exceptions

None

## Failure Policy

### Fail-Fast Conditions

- When a SQLite write fails (persistence failure)
- When ACK persistence fails (risk of breaking idempotency)
- When `new_offset <= current_offset` is violated (breaking monotonicity)
- When a Consumer ID collision is detected (security risk)

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists
- A JSONL archive write failure produces only a WARNING log (SQLite is healthy)

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

### Fallback Policy

- Fallback targets: none
- Fallback destination: none
- Conditions that prohibit Fallback: consistency-check mismatches
- Where Fallback reasons are recorded: audit log

## Data Ownership and Persistence

- **System of Record**: the `events` table (SQLite)
- **Derived Data**: the JSONL archive (secondary audit log), offset files
- **Ownership**: EventBus team (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per Event
- **Recovery Source**: SQLite (canonical store)
- **Deletion Rule**: deleted after DLQ promotion (or by TTL-based cleanup)

## Verification

### Automated Tests

- **Test**: Events are stored even when no Subscriber is present
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Un-ACKed Events are Replayed on reconnection
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Offsets do not move backward
  - **Verifies**: INV-05
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: A failure to persist an ACK is not treated as success
  - **Verifies**: INV-12
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Consumers can handle duplicates when switching between Replay and Live
  - **Verifies**: INV-14
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Events move to the DLQ after the Retry limit
  - **Verifies**: INV-13
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Consumer ID collisions are detected
  - **Verifies**: INV-11
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: `new_offset <= current_offset` is rejected
  - **Verifies**: INV-09
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: The Delivery-State UPSERT and the Offset advancement are committed atomically within a single transaction (`tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`)
  - **Verifies**: INV-16
  - **Type**: Regression
  - **Blocking**: Yes

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

Register any Invariant without Verification as an unverified item in an Issue.

## Implementation Notes

- Transaction guarantee: see INV-16 (a single transaction inside `ack_event_for_consumer()`)
- Monotonicity Enforcement: see INV-05, INV-09
- Resume position: the lowest unacked `seq` at or below the stored offset when one exists, otherwise `stored_offset + 1` (see Decision item 14)
- Offset store: `consumer_delivery` tracks per-consumer delivery progress and `consumer_offsets` stores monotonic offsets; `ack_event_for_consumer()` updates both atomically. At startup, `migrate_legacy_offsets()` reads each offset file's `.map` companion to recover the original `consumer_id` and seeds `consumer_offsets`; without a `.map` companion, the sanitized filename is the `consumer_id`.
- INV-07 is enforced by content comparison logic in `insert_event()`: duplicate events cannot corrupt stored data; identical retries return the original seq, conflicting retries return HTTP 409.

## Known Deviations

Record any discrepancy between this ADR and the current implementation, configuration, tests, or documents.

- **Known Issue**: EVENTBUS-008 — tracked in governance_03 Part 1 (authentication model per ADR-013)
- **Known Issue**: EVENTBUS-011 — tracked in governance_03 Part 1 (NACK on a concurrently deleted event)
- **Known Issue**: EVENTBUS-012 — tracked in governance_03 Part 1 (duplicate NACK from the same consumer)
- **Known Issue**: EVENTBUS-013 — tracked in governance_03 Part 1 (ACK/NACK do not enforce Consumer ID exclusivity)

## Review Triggers

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold

Add review conditions specific to this ADR.

- Consumer ID collision detection becomes necessary
- Authentication must be implemented
- Persistent storage moves to something other than files
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

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments
- ADR-013: EventBus Authentication and Authorization

### Specifications

- [EventBus System Overview](../24_eventbus/eventbus_01_system-overview.md) — EventBus architecture overview
- [Event Bus Operations](../24_eventbus/eventbus_03_dlq_operations.md) — Publish/Replay/Subscribe/ACK/NACK/Health/DLQ protocols
- [Persistence Schema and Replay](../24_eventbus/eventbus_06_persistence_schema_and_replay.md) — persistence schema and Replay
- [DLQ Offsets and Delivery Semantics](../24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md) — DLQ offsets and delivery semantics
- [Configuration and Operations](../24_eventbus/eventbus_08_configuration-and-operations.md) — configuration, bind address, health endpoint, Consumer ID, delivery, DLQ operations
- [Reference API](../24_eventbus/eventbus_09_reference_api.md) — core modules, route handlers, Broker/Offsets

### Known Issues

- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md) — EventBus known issues

### Implementation References

- `scripts/eventbus/broker.py` — `EventBroker.publish()`
- `scripts/eventbus/publish_route.py` — `publish()`
- `scripts/eventbus/subscribe_route.py` — `subscribe()`
- `scripts/eventbus/delivery_repo.py` — `ack_event()`, `ack_event_for_consumer()`, `nack_event()`, `get_consumer_offset()`
- `scripts/eventbus/event_repo.py` — `insert_event()`
- `scripts/eventbus/offset_migrator.py` — `migrate_legacy_offsets()`
- `scripts/eventbus/db.py` — facade that re-exports the functions above
- `scripts/eventbus/dlq.py` — `promote_single()`
- `scripts/eventbus/offsets.py` — `write_offset()`, `read_offset()`
- `events` table — `seq`, `event_id`, `topic`, `payload`, `acked_at`, `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`
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
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Migration, or the reason no migration is needed, is recorded
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [ ] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
