## Goal

Add cross-references to canonical delivery spec in subscribe route description in `06_eventbus_06` and link each invariant to an automated test or an explicitly identified missing test.

## Scope

Modify `docs/06_eventbus_06_reference-api.md`:
- Add cross-reference to canonical delivery spec in subscribe route description in `06_eventbus_06` (REQ-001; `docs/06_eventbus_06_reference-api.md`).
- Update related documents section in all chapters to include cross-references (REQ-001; all Target Files).
- Identify Known Deviations in ADR-006 that require updates (REQ-006; `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`).
- Identify Known Deviations in ADR-008 that require updates (REQ-006; `docs/adr/ADR-008-sqlite-4db-separation.md`).

## Assumptions

- Contradictions between documents should be resolved by aligning with the most recent authoritative source (the ADRs, particularly ADR-006, are the highest authority for design decisions).
- The `06_eventbus_04` chapter is the best candidate for consolidation because it already covers DLQ, offsets, and delivery semantics — the core of the delivery lifecycle.

## Design decisions

1. **Contradiction resolution (REQ-005)**: Resolve contradictions by aligning with the most recent authoritative source:
   - ADR-006 is the highest authority for design decisions.
   - For operational details not covered by ADRs, prefer the more detailed document.
   - Document each contradiction and its resolution in the "Known Deviations" section of the affected ADR.

2. **Invariant linking (REQ-006)**: Link each invariant in ADR-006 to either:
   - An automated test (with test file path and function name).
   - An explicitly identified missing test (documented as a gap).

3. **Documentation update order**: Update in this order to minimize intermediate inconsistency:
   - First: `06_eventbus_04` (canonical delivery spec)
   - Second: `06_eventbus_03` (recovery runbook)
   - Third: Correct contradictions in `06_eventbus_01`, `06_eventbus_02`, `06_eventbus_05`
   - Fourth: Update cross-references in `06_eventbus_06`
   - Fifth: Identify Known Deviations in ADR-006 and ADR-008

## Alternatives considered

- Starting from scratch instead of consolidating: would lose existing content and require more effort.
- Using a different document as the base for consolidation: `06_eventbus_04` is the best fit because it already covers DLQ, offsets, and delivery semantics.
- Writing the recovery runbook at the developer level: less useful for operators who need to execute the procedure.
- Resolving contradictions by aligning with the least detailed document: would introduce inconsistencies.

## Implementation
### Target file
`docs/06_eventbus_06_reference-api.md`

### Procedure
1. Phase 1: Preparation — Read all documents and identify contradictions
2. Phase 2: Core Logic — Create canonical delivery-semantics section
3. Phase 3: Core Logic — Complete recovery runbook
4. Phase 4: Documentation — Correct contradictions
5. Phase 5: Documentation — Update cross-references
6. Phase 6: Documentation — Identify Known Deviations

### Method
#### Phase 1: Preparation
- [ ] Read all 8 target files and identify contradictions between them (REQ-005; all Target Files)
- [ ] Map each invariant in ADR-006 to existing tests or identify gaps (REQ-006; `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`)
- [ ] Map each invariant in ADR-008 to existing tests or identify gaps (REQ-006; `docs/adr/ADR-008-sqlite-4db-separation.md`)

#### Phase 2: Core Logic
- [ ] Add consumer identity section to `06_eventbus_04` (consumer ID stability, collision risk, monotonicity) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add ordering section to `06_eventbus_04` (per-topic ordering, seq-based ordering) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add ACK/NACK rules section to `06_eventbus_04` (preconditions, postconditions, error responses) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add offset semantics section to `06_eventbus_04` (monotonicity guarantee, resume behavior) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add replay section to `06_eventbus_04` (since_seq precedence, consumer offset precedence, Last-Event-ID precedence) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add backpressure section to `06_eventbus_04` (queue overflow behavior, slow consumer detection) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add DLQ promotion/requeue section to `06_eventbus_04` (inline vs background loop, requeue semantics) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)
- [ ] Add retention section to `06_eventbus_04` (TTL policy, cleanup procedure) (REQ-002; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`)

#### Phase 3: Core Logic
- [ ] Convert "SQLite/JSONL Consistency Check and Recovery Procedure" in `06_eventbus_03` from detection-only to executable runbook (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add WAL file integrity check procedure (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add sequence validation procedure (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add consumer progress check procedure (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add DLQ state consistency check procedure (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add controlled restart procedure (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)

#### Phase 4: Documentation
- [ ] Correct offset monotonicity claim in `06_eventbus_01` (align with EVENTBUS-001 Known Issue) (REQ-005; `docs/06_eventbus_01_system-overview.md`)
- [ ] Correct duplicate/conflicting entries in ACK/NACK state transition table in `06_eventbus_02` (REQ-005; `docs/06_eventbus_02_operations.md`)
- [ ] Correct slow-consumer threshold values in `06_eventbus_05` (align with config centralization plan) (REQ-005; `docs/06_eventbus_05_configuration-and-operations.md`)

#### Phase 5: Documentation
- [ ] Add cross-reference to canonical delivery spec in subscribe route description in `06_eventbus_06` (REQ-001; `docs/06_eventbus_06_reference-api.md`)
- [ ] Update related documents section in all chapters to include cross-references (REQ-001; all Target Files)

#### Phase 6: Documentation
- [ ] Identify Known Deviations in ADR-006 that require updates (REQ-006; `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`)
- [ ] Identify Known Deviations in ADR-008 that require updates (REQ-006; `docs/adr/ADR-008-sqlite-4db-separation.md`)

### Details

**Phase 1: Preparation**

Read all 8 target files and identify contradictions between them. Map each invariant in ADR-006 to existing tests or identify gaps. Map each invariant in ADR-008 to existing tests or identify gaps.

**Phase 2: Core Logic**

Extend `06_eventbus_04` with the following sections:

```markdown
## Consumer Identity

Consumer IDs are specified by the client and are not automatically generated by the server. Use stable IDs that persist across restarts. If multiple consumers use the same ID, the last write wins.

### Consumer ID Collision Risk

When two consumers use the same ID, the last write wins. The server does not detect conflicts. This means:
- The first consumer's offset may be overwritten by the second consumer's offset.
- The first consumer may receive events intended for the second consumer.
- The second consumer may miss events intended for the first consumer.

To avoid collisions, use unique consumer IDs per instance (e.g., PID + topic combination).

### Monotonicity Guarantee

The offset value is monotonically non-decreasing — older-or-equal seq values cannot move a consumer's offset backward. This is enforced by the SQL statement:

```sql
INSERT INTO consumer_offsets(consumer_id, offset) VALUES (?, ?) ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset
```

This ensures monotonic enforcement: an older-or-equal seq value cannot move a consumer's offset backward.

## Ordering

### Per-Topic Ordering

Events within a single topic are delivered in ascending order of `seq`. This is guaranteed by the `ORDER BY seq` clause in the SQLite query used by `fetch_events_since()`.

### Seq-Based Ordering

The `seq` field is globally monotonic across all topics. Each event is assigned a unique, incrementing `seq` value at publish time. This ensures:
- Events are always delivered in the correct order within a topic.
- Consumers can use `seq` to determine if they have received all events up to a given point.
- Replay operations can resume from any `seq` value without missing events.

## ACK/NACK Rules

### ACK Preconditions

- The event must exist in the `events` table.
- The event must not have been previously ACKed (`acked_at IS NULL`).

### ACK Postconditions

- `acked_at` is set to the current timestamp.
- If a `consumer_id` is provided, the offset is updated using the SQL statement above.
- The response body includes `{event_id, acked: true, seq: <int>}`.

### ACK Error Responses

- HTTP 404 if the event is not found.
- HTTP 409 if the event was already ACKed (idempotent duplicate ACK).

### NACK Preconditions

- The event must exist in the `events` table.
- The event must not have been previously ACKed (`acked_at IS NULL`).

### NACK Postconditions

- `delivery_failure_count` is incremented.
- If `delivery_failure_count >= max_retry`, the event is promoted to the DLQ.
- The response body includes `{event_id, delivery_failure_count}`.

### NACK Error Responses

- HTTP 404 if the event is not found.

### Duplicate NACK Behavior

No idempotency guard exists in `nack_event`; `delivery_failure_count` increases with every call. This is **Implementation fix required**.

### NACK followed by ACK

`ack_event`'s `WHERE acked_at IS NULL` check remains true (NACK does not set `acked_at`). ACK succeeds, `delivery_failure_count` remains at the value from NACK — No readjustment.

### ACK followed by NACK

No `acked_at` check in `nack_event`. Even if already ACKed, NACK succeeds and `delivery_failure_count` increases — **Implementation fix required**.

## Offset Semantics

### Monotonicity Guarantee

Offsets advance ONLY when a consumer explicitly calls `POST /events/{event_id}/ack?consumer_id={consumer_id}`. They do not advance automatically during streaming. Idempotent duplicate ACKs do not update the offset.

**Note:** Offsets only advance based on the `seq` value provided during ACK. If ACKs are not received in `seq` order, the offset may become non-monotonic (skipped `seq` values will not be re-acquired later).

### Resume Behavior

Reconnecting with a `consumer_id` resumes from the last acknowledged offset. If no offsets have been acknowledged, it starts from `seq=0`. It is also possible to start from a specific position using `since_seq=N`.

## Replay Semantics

### since_seq Precedence

When `since_seq=N` is provided, the replay operation returns events where `seq > N` in ascending order of `seq`. This takes precedence over any consumer offset.

### Consumer Offset Precedence

When no `since_seq` is provided but a `consumer_id` is provided, the replay operation resumes from the last acknowledged offset stored in the `consumer_offsets` table.

### Last-Event-ID Precedence

When a `Last-Event-ID` header is provided, the replay operation uses it as a fallback for `EventSource`-based clients. The precedence order is: `since_seq` > consumer offset > `Last-Event-ID`.

## Backpressure

### Queue Overflow Behavior

A process queue exceeding `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration (default: `100`).

If a consumer is slow, events are discarded from the queue. The consumer must reconnect and replay from SQLite.

### Slow Consumer Detection

Slow consumer detection can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

**Threshold validation rules:**
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`
- `backlog_health_threshold` must be less than or equal to `subscriber_queue_maxsize`

Invalid combinations fail startup with actionable error messages naming both conflicting values.

## DLQ Promotion and Requeue

### Inline Promotion Path

When a NACK occurs and `delivery_failure_count` reaches `>= max_retry`, the event is immediately promoted to the DLQ. The background DLQ loop (every 60 seconds) serves as a safety net to catch any events missed during inline processing.

### Background Loop Promotion

The background DLQ loop runs every 60 seconds and promotes events that were missed during inline processing. It checks each event's `delivery_failure_count` against `max_retry` and promotes events that meet the criteria.

### Requeue Semantics

`POST /dlq/{event_id}/requeue` clears `dlq_at` and increments `dlq_requeue_count` (`delivery_failure_count` is not reset). If `delivery_failure_count >= max_retry`, it will be re-promoted during the next DLQ loop.

## Retention

### TTL Policy

Events are retained in SQLite until they are explicitly deleted or the database is truncated. There is no automatic TTL-based cleanup.

### Cleanup Procedure

To clean up old events, use the following SQL command:

```sql
DELETE FROM events WHERE seq <= ?;
```

Replace `?` with the desired cutoff sequence number. After deletion, run `VACUUM` to reclaim disk space.

### JSONL Archive Retention

JSONL archive files are appended to `{storage_dir}/events.jsonl` as a secondary storage. SQLite is the primary store; failures in appending to JSONL do not prevent a 200 response. Do NOT read primary data from JSONL; use SQLite queries instead.
```

**Phase 3: Core Logic — Complete recovery runbook**

Convert the detection-only section in `06_eventbus_03` into an executable runbook:

```markdown
## SQLite/JSONL Consistency Check and Recovery Procedure

### Step 1: Verify WAL file integrity

Run the following command to verify the SQLite WAL file integrity:

```bash
sqlite3 /path/to/eventbus.db "PRAGMA integrity_check;"
```

Expected output: `ok`

If the output is not `ok`, the database may be corrupted. Proceed to Step 5 (controlled restart) before continuing.

### Step 2: Validate sequence continuity

Check for gaps in the sequence numbers:

```bash
sqlite3 /path/to/eventbus.db "SELECT seq FROM events ORDER BY seq LIMIT 1;"
sqlite3 /path/to/eventbus.db "SELECT MAX(seq) FROM events;"
```

Compare the minimum and maximum `seq` values. If there are gaps (i.e., `MAX(seq) - MIN(seq) != COUNT(*) - 1`), some events may have been lost.

### Step 3: Check consumer progress

Verify that consumer offsets are consistent with the latest event:

```bash
sqlite3 /path/to/eventbus.db "SELECT consumer_id, offset FROM consumer_offsets ORDER BY consumer_id;"
```

For each consumer, compare the offset with the maximum `seq` in the `events` table. If a consumer's offset is greater than the maximum `seq`, it indicates a potential inconsistency.

### Step 4: Verify DLQ state consistency

Check that events marked for DLQ promotion match the DLQ directory:

```bash
sqlite3 /path/to/eventbus.db "SELECT event_id FROM events WHERE dlq_at IS NOT NULL;"
ls -la /path/to/deadletter_dir/
```

Compare the list of event IDs from the database with the list of files in the DLQ directory. Any discrepancies indicate a potential inconsistency.

### Step 5: Controlled restart procedure

If inconsistencies are detected, follow this controlled restart procedure:

1. Stop the EventBus process gracefully:
   ```bash
   kill -TERM $(pgrep -f "uvicorn scripts.eventbus.app:app")
   ```

2. Wait for the process to stop completely:
   ```bash
   sleep 5
   ```

3. Run the checkpoint command to flush WAL to the main database:
   ```bash
   sqlite3 /path/to/eventbus.db "PRAGMA wal_checkpoint(TRUNCATE);"
   ```

4. Start the EventBus process again:
   ```bash
   uvicorn scripts.eventbus.app:app --host 127.0.0.1 --port 8080 &
   ```

5. Verify the process started successfully:
   ```bash
   curl http://127.0.0.1:8080/health
   ```

6. Re-run Steps 1–4 to confirm consistency.
```

**Phase 4: Documentation — Correct contradictions**

Correct the slow-consumer threshold values in `06_eventbus_05_configuration-and-operations.md`:

```markdown
The Client specifies the Consumer ID via the `consumer_id` parameter; it is not automatically generated by the server. Use a stable ID that persists across restarts. Do not use volatile IDs like PIDs. If multiple consumers use the same ID, the last write wins, and the server does not detect conflicts.

See `06_eventbus_02_operations.md` for the Subscribe/Ack protocol and `06_eventbus_03_persistence_schema_and_replay.md` for offset persistence details.

---

## Delivery Operations

### Verifying Delivery

Verify live push using `GET /subscribe?consumer_id=test`. Events should be received within one loop tick after publishing.

### Monitoring Slow Consumers

A process queue exceeding `slow_consumer_threshold` events is considered slow. This value is configurable via the `slow_consumer_threshold` field in the Event Bus TOML configuration (default: `100`). This can be verified via the health endpoint:

- `slow_consumers > 0` → `degraded`
- `max_queue_depth >= backlog_health_threshold` → `broker_queue_backlog_high`

If a consumer is slow, events are discarded from the queue. The consumer must reconnect and replay from SQLite.

**Threshold validation rules:**
- `slow_consumer_threshold` must be strictly less than `subscriber_queue_maxsize`
- `backlog_health_threshold` must be less than or equal to `subscriber_queue_maxsize`

Invalid combinations fail startup with actionable error messages naming both conflicting values.

### Recovery on Reconnection

Reconnecting with a `consumer_id` resumes from the last acknowledged offset. If no offsets have been acknowledged, it starts from `seq=0`. It is also possible to start from a specific position using `since_seq=N`.

### Subscriber Count

When the count is 0, the broker is idle. Events remain in SQLite and are available for replay upon the next connection.
```

**Phase 5: Documentation — Update cross-references**

Add cross-references to canonical delivery spec in subscribe route description in `06_eventbus_06_reference-api.md`:

```markdown
### scripts/eventbus/dlq_route.py

`dlq_list(request, limit=100, offset=0)`: `GET /dlq`. `dlq_requeue(request, event_id)`: `POST /dlq/{event_id}/requeue`. If `failure_count >= max_retry`, it may be re-moved to the DLQ. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for DLQ semantics.

### scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: `GET /replay`. SSE stream or paginated JSON. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for replay semantics.

### scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: `GET /subscribe`. SSE streaming + replay+push. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for delivery semantics, offset semantics, and backpressure behavior.

### scripts/eventbus/health_route.py

`health_check(request)`: `GET /health`. See `06_eventbus_05_configuration-and-operations.md` for monitoring thresholds.
```

**Phase 6: Documentation — Identify Known Deviations**

Identify Known Deviations in ADR-006 and ADR-008 that require updates. Link each invariant to either:
- An automated test (with test file path and function name).
- An explicitly identified missing test (documented as a gap).

## Compatibility considerations

- Changing `EventBroker.__init__` signature breaks any external callers beyond `app.py`. Verify all call sites before merging; `EventBroker` is an internal class (no public API contract), but confirm no third-party code imports it directly.
- Existing TOML configs that lack the new threshold fields will use defaults (backward compatible).
- No changes needed to callers — `EventBusConfig` construction remains the same.

## Security considerations

- The validation rules prevent misconfiguration that could hide operational issues (e.g., slow-consumer threshold above queue capacity would make health check unreachable).
- Invalid combinations fail startup with actionable errors rather than silently producing misleading health status.

## Rollback considerations

- Reverting the threshold fields requires reverting the validation logic and `load_config()` updates simultaneously.
- If reverted during runtime, the dataclass defaults ensure behavior reverts to original hardcoded values.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All docs | Quality check | `uv run python tools/check_docs_quality.py` | Clean |
| All docs | Structure check | `uv run python tools/check_docs_structure.py` | Clean |
| All docs | Consistency check | `uv run python tools/check_docs_consistency.py --domain eventbus` | Clean (if domain option exists) |
| All docs | Manual review | Human inspection | No unresolved contradictions |

## Completion criteria

- Each operation has documented preconditions, postconditions, and error responses — REQ-002
- The specification identifies the canonical source for schema, API contract, and runtime behavior — REQ-001
- The recovery runbook is executable by an operator and includes verification and rollback steps (not only detection, unlike the current `06_eventbus_03` section) — REQ-004
- Documentation checks report no unresolved contradiction introduced or left by this work — REQ-005

## Out of scope

- Deriving threshold values from load-test measurement (EB-M05).
- Backpressure disconnect behavior itself (EB-H02).
- Changing the DLQ sweep interval (`_DLQ_INTERVAL = 60.0` in `app.py`).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all documents and identify contradictions | Pending | — | — | |
| 2 | Map each invariant in ADR-006 to existing tests or identify gaps | Pending | — | — | |
| 3 | Map each invariant in ADR-008 to existing tests or identify gaps | Pending | — | — | |
| 4 | Add consumer identity section to 06_eventbus_04 | Pending | — | — | |
| 5 | Add ordering section to 06_eventbus_04 | Pending | — | — | |
| 6 | Add ACK/NACK rules section to 06_eventbus_04 | Pending | — | — | |
| 7 | Add offset semantics section to 06_eventbus_04 | Pending | — | — | |
| 8 | Add replay section to 06_eventbus_04 | Pending | — | — | |
| 9 | Add backpressure section to 06_eventbus_04 | Pending | — | — | |
| 10 | Add DLQ promotion/requeue section to 06_eventbus_04 | Pending | — | — | |
| 11 | Add retention section to 06_eventbus_04 | Pending | — | — | |
| 12 | Convert recovery procedure to executable runbook | Pending | — | — | |
| 13 | Correct contradictions in related documents | Pending | — | — | |
| 14 | Update cross-references in related documents | Pending | — | — | |
| 15 | Identify Known Deviations in ADRs | Pending | — | — | |
| 16 | Run documentation quality checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20260907-125042_eb_l03_canonical_eventbus_delivery_recovery_spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-073543_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-071615
- **Related target files**: docs/06_eventbus_06_reference-api.md
