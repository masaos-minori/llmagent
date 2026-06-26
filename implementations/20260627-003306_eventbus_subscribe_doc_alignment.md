# Design: /subscribe Documentation Alignment — Remove Stale Polling Description

## Goal

Align `/subscribe` documentation with the actual replay-plus-push runtime model by removing the stale "polling-based" description and confirming the implementation matches the documented behavior.

The `/subscribe` endpoint uses a hybrid model: replay from SQLite followed by live EventBroker push. The known-issues doc incorrectly describes it as "Polling-based internally (not push)", which contradicts both the HTTP API doc and the actual implementation.

## Scope

**In-Scope**:
- Verify actual `/subscribe` implementation confirms hybrid model (replay from SQLite + live EventBroker push)
- Remove stale "polling-based internally (not push)" description from known-issues doc
- Document replay-to-live transition behavior consistently
- Add tests for: replay phase, live push phase, event published during replay, dedup against replay ceiling
- Mark the polling-based known issue as resolved

**Out-of-Scope**:
- Replacing SSE with WebSocket
- Adding durable per-subscriber queues

## Requirements

### Functional Requirements
1. Remove incorrect "Polling-based internally (not push)" entry from `06_eventbus_90_inconsistencies_and_known_issues.md`
2. Clarify system overview doc to mention push model alongside replay for `/subscribe`
3. Document the replay-to-live transition behavior explicitly
4. Add tests covering replay-to-live transition scenarios

### Non-Functional Requirements
- Documentation must match actual runtime behavior
- No behavioral changes — only documentation and test additions

## Assumptions

1. `/subscribe` uses a hybrid model: replay from SQLite followed by live EventBroker push (confirmed in app.py lines 269-314)
2. The known-issues doc entry "Polling-based internally (not push)" is stale and incorrect
3. The HTTP API doc correctly describes the replay-plus-push model (no changes needed)

## Architecture

### Current `/subscribe` Implementation (confirmed via code inspection)

```
Step 1: Register with broker BEFORE replay
    sub = broker.subscribe(list(topic))   # app.py:271

Step 2: Replay from SQLite
    rows = await asyncio.to_thread(_fetch_replay)  # app.py:288
    for row in rows:
        yield f"data: {data}\n\n"              # SSE framing
        replay_ceil = row["seq"]               # track ceiling

Step 3: Live delivery from broker queue
    while True:
        event = await sub.queue.get()          # async get — not polling
        if event is None:                       # shutdown sentinel
            break
        if event["seq"] <= replay_ceil:         # dedup against replay ceiling
            continue
        yield f"data: {data}\n\n"               # SSE framing

Cleanup:
    broker.unsubscribe(sub)                     # app.py:312
```

### EventBroker push mechanism (confirmed via code inspection)

```python
# broker.py:46 — push-based, not polling
sub.queue.put_nowait(event)   # async Queue.push_nowait

# broker.py:58-62 — shutdown sends None sentinels
sub.queue.put_nowait(None)    # unblocks subscriber queue.get()
```

**No polling fallback logic exists.** The `await sub.queue.get()` is an async await on asyncio.Queue, not a polling loop. Events are pushed via `put_nowait()` in `EventBroker.publish()`.

### Race-free transition design

1. Broker subscription registered **before** replay query (app.py:271 before app.py:288)
2. Any event published during replay is queued by broker and deduplicated against `replay_ceil` at the start of the live phase (app.py:300-301)
3. No events are lost or duplicated

## Module Design

### Affected Files

| File | Change Type | Description |
|---|---|---|
| `docs/06_eventbus_90_inconsistencies_and_known_issues.md` | Edit (remove) | Remove stale "Polling-based internally (not push)" entry; add resolved item |
| `docs/06_eventbus_01_system-overview.md` | Edit (clarify) | Update line 12 to mention push model alongside replay for `/subscribe` |
| `tests/test_eventbus_subscribe_transition.py` | New file | Replay-to-live transition tests |

### Test Design

**File**: `tests/test_eventbus_subscribe_transition.py`

| Test | Target | Verification |
|---|---|---|
| `test_replay_phase_delivers_events` | Replay phase | Events with seq > start_seq are yielded via SSE during replay |
| `test_live_push_phase_delivers_after_replay` | Live push phase | Events published after replay completes arrive via EventBroker push |
| `test_event_published_during_replay_not_lost` | Race-free transition | Event published during replay is delivered in live phase (not lost) |
| `test_dedup_against_replay_ceil` | Dedup logic | Event with seq <= replay_ceil is discarded, not duplicated |
| `test_slow_consumer_queue_full_during_transition` | Slow consumer behavior | Queue full causes drop with WARNING log during replay-to-live transition |

## Test Strategy

### Unit Tests (new file: `tests/test_eventbus_subscribe_transition.py`)

- Use the existing `client` fixture pattern from `test_eventbus_subscribe.py` (TestClient + monkeypatch)
- Use `_event()` helper from `test_eventbus_replay_subscribe.py` for event creation
- Test replay phase via direct DB query + `_row_to_dict` transformation (same approach as `test_subscribe_yields_matching_event`)
- Test live push phase via EventBroker unit tests (same pattern as `test_eventbus_broker.py`)

### Integration Tests

- Test the full `/subscribe` SSE stream with a producer publishing during replay
- Verify dedup behavior by publishing an event, triggering replay, then publishing the same seq again

### Validation Commands

| Target | Command | Expected Outcome |
|---|---|---|
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Grep for "Polling-based" | No matches found |
| `06_eventbus_01_system-overview.md` | Grep for "push" or "EventBroker" alongside "/subscribe" | Match found |
| `tests/test_eventbus_subscribe_transition.py` | `uv run pytest tests/test_eventbus_subscribe_transition.py -v` | All 5 tests pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Removing the polling-based description may break existing documentation that operators rely on for latency expectations | Low | The HTTP API doc already correctly describes the push model. This is a bug fix — docs should match runtime behavior. |
| Slow consumer queue full behavior during replay-to-live transition may cause unexpected event drops | Medium | Document the slow consumer threshold (100 items) and drop behavior in the system overview doc. This is existing behavior, not a change. |
