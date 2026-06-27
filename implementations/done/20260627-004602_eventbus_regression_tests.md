# Goal

Add operational regression tests for Event Bus delivery, health, offsets, and DLQ behavior to lock down invariants discovered during require processing. These tests target 5 specific gaps in current test coverage that were identified by code analysis of the Event Bus implementation.

# Scope

**In-Scope**:
- Add 6 new test files targeting specific behavioral gaps:
  - crash-before-ack replay (consumer disconnects before acking)
  - replay-to-live transition (event published during replay phase)
  - slow consumer queue overflow (broker.publish drops on full)
  - unsafe public bind guard (0.0.0.0 with allow_public_bind=False)
  - concurrent publish/replay/ack stress
  - DLQ re-promotion edge case (requeue then retry-exhausted again)
- Keep tests deterministic and isolated using temporary directories
- Encode delivery and recovery invariants directly

**Out-of-Scope**:
- Large-scale load testing
- Distributed multi-node tests
- Benchmarking throughput
- Code changes to Event Bus implementation (tests only)

# Assumptions

1. Current test coverage has gaps for crash-before-ack, replay-to-live transition, slow consumer overflow, public bind guard, and concurrent stress — confirmed by grep search showing zero matches for these patterns in existing tests
2. Existing tests cover: /health status mapping, ack-only offset advancement, DLQ promotion/requeue, publish idempotency, replay pagination, fan-out/topic filtering/unsubscribe
3. The Event Broker queue maxsize=1000 and slow threshold=100 are fixed values in the implementation
4. The broker.publish() method drops events when queue is full (line 78 in broker.py) with WARNING log
5. The subscribe handler CancelledError handling logs but does not write offset (line 305 in app.py)
6. ack_event doesn't write offset (lines 78-88 in db.py), so unacked events will be replayed

# Implementation

## Target files

### File 1: tests/test_eventbus_crash_ack.py

**Procedure**: Add crash-before-ack regression test

**Method**: Use the existing TestClient + tmp_path fixture pattern from test_eventbus_dlq.py. Publish events, subscribe to them, then simulate disconnect without acking by terminating the subscription. On reconnect with same consumer_id, verify replay from seq=0 (offset not found).

**Details**:
- Create a subscriber that receives events via SSE but never sends ack/nack
- Use httpx.ASGITransport directly (not TestClient) to control connection lifecycle
- After disconnecting subscriber, verify offset file does not exist for unacked events by checking offsets_dir
- Reconnect with same consumer_id and verify events are replayed from seq=0
- Key invariant: unacked events must be replayed on reconnect

### File 2: tests/test_eventbus_subscribe_transition.py

**Procedure**: Add replay-to-live transition race test

**Method**: Use asyncio.Event for deterministic synchronization instead of time.sleep() based assertions. Test two scenarios:
1. Event published during replay phase is delivered via live push (not lost)
2. Event with seq <= replay_ceil is deduped against replay ceiling

**Details**:
- Start a /subscribe SSE connection
- Immediately publish an event while the subscriber is in replay phase
- Verify the event appears in the live push stream (seq > replay_ceil)
- Verify no duplicate delivery of events within replay range
- Use asyncio.Event to signal when replay phase ends, then verify live push works

### File 3: tests/test_eventbus_slow_consumer.py

**Procedure**: Add slow consumer queue overflow test

**Method**: Subscribe with a slow consumer (consume from queue slowly), verify health endpoint reports slow_consumer_count > threshold. Then publish an event and verify it is dropped.

**Details**:
- Subscribe to /subscribe, then only read from the queue every 100ms
- Verify /health returns slow_consumer_count >= 100 after consuming enough events
- Publish an event while queue depth >= queue.maxsize (1000) and verify delivery failure
- Verify WARNING log is emitted for dropped event

### File 4: tests/test_eventbus_startup.py

**Procedure**: Add unsafe public bind guard test

**Method**: Test that Event Bus fails-fast or logs critical warning when bind address is 0.0.0.0 with allow_public_bind=False. Also verify startup succeeds with 127.0.0.1.

**Details**:
- Create EventBusConfig with bind="0.0.0.0" and allow_public_bind=False
- Verify startup fails or raises ValidationError
- Create EventBusConfig with bind="127.0.0.1" and allow_public_bind=False
- Verify startup succeeds without errors

### File 5: tests/test_eventbus_concurrent_stress.py

**Procedure**: Add concurrent publish/replay/ack stress test

**Method**: Use asyncio.gather to run multiple concurrent operations. Test three scenarios:
1. Concurrent publish requests (10+ simultaneous) — no SQLite lock errors
2. Concurrent ack requests on same event_id — idempotent, no corruption
3. Concurrent replay with overlapping time ranges — no duplicate delivery

**Details**:
- Publish 15 events sequentially first to have a known set
- Run asyncio.gather with 15 concurrent /publish requests — verify all succeed without SQLite lock errors
- Run asyncio.gather with 10 concurrent /ack requests on same event_id — verify idempotent response each time
- Run asyncio.gather with 3 concurrent /replay requests with overlapping since_seq ranges — verify no duplicate event_ids in combined results

### File 6: tests/test_eventbus_dlq_repromote.py

**Procedure**: Add DLQ re-promotion edge case test

**Method**: Extend the existing DLQ requeue test pattern from test_eventbus_dlq.py. Test two scenarios:
1. Requeue of event at delivery_failure_count >= max_retry — requeue succeeds but next DLQ loop tick will re-promote
2. dlq_requeue_count increments on each requeue (not reset)

**Details**:
- Publish event, exhaust retries to promote to DLQ
- Requeue the event — verify requeue succeeds
- Set delivery_failure_count back to >= max_retry via DB update
- Verify next DLQ loop tick will promote again (check dlq_at is set again)
- Verify dlq_requeue_count increments on each requeue call

# Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/test_eventbus_crash_ack.py (new) | Verify crash-before-ack replay passes | `uv run pytest tests/test_eventbus_crash_ack.py` | Test passes, offset not written for unacked events, replay from seq=0 on reconnect |
| tests/test_eventbus_subscribe_transition.py (new) | Verify replay-to-live transition tests pass | `uv run pytest tests/test_eventbus_subscribe_transition.py` | All transition tests pass, no lost events during replay-to-live |
| tests/test_eventbus_slow_consumer.py (new) | Verify slow consumer queue overflow test passes | `uv run pytest tests/test_eventbus_slow_consumer.py` | Slow consumer threshold triggers correctly, event dropped when queue full |
| tests/test_eventbus_startup.py (new) | Verify unsafe bind guard tests pass | `uv run pytest tests/test_eventbus_startup.py` | Public bind detected and handled, startup fails with 0.0.0.0 allow_public_bind=False |
| tests/test_eventbus_concurrent_stress.py (new) | Verify concurrent stress tests pass | `uv run pytest tests/test_eventbus_concurrent_stress.py` | No SQLite errors, no data corruption, idempotent acks, no duplicate replay |
| tests/test_eventbus_dlq_repromote.py (new) | Verify DLQ re-promotion edge cases pass | `uv run pytest tests/test_eventbus_dlq_repromote.py` | dlq_requeue_count increments, re-promotion after requeue works |

# Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Timing-based tests for replay-to-live transition may be flaky | High | Use deterministic synchronization (asyncio.Event, asyncio.Queue) instead of time.sleep() based assertions. Test the replay_ceil dedup logic directly rather than relying on timing. |
| Concurrent stress tests may require long runtime for reliable results | Medium | Use a moderate number of concurrent requests (10-20) rather than hundreds. Focus on SQLite lock errors and data corruption rather than throughput metrics. |
| Slow consumer test may hang if queue never fills | Low | Set a timeout on the test and verify queue depth explicitly before asserting slow_consumer_count. Use asyncio.wait_for to bound the test. |
| Test isolation — shared app state between tests | Medium | Use tmp_path fixtures for all file-based state (db, offsets, deadletter). Re-initialize app.state between tests via monkeypatch and _init_state pattern from test_eventbus_app_isolation.py. |
