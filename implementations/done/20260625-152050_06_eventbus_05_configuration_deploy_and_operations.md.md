# Implementation: docs/06_eventbus_05_configuration_deploy_and_operations.md — multiple updates (req #40 + #45)

## Goal

Update the config table to mark deprecated fields, add Push-Mode Operations section.

## Scope

### req #40: Config table
- Mark `poll_interval_ms` as `[deprecated]` in the config table
- Mark `offset_checkpoint_interval` as `[deprecated]` in the config table
- No removal — fields still exist for backward compat

### req #45: Push-Mode Operations section
- Add "Push-Mode Delivery Operations" section after the existing Delivery Operations section
- Document: how to verify delivery, slow consumer detection, broker queue monitoring, reconnect recovery

## Assumptions

- Config table is in an existing section of this doc
- req #34 added a Delivery Operations section; req #45 adds a follow-up Push-Mode section

## Implementation

### Target file

`docs/06_eventbus_05_configuration_deploy_and_operations.md`

### Procedure

1. Find `poll_interval_ms` row in config table → append `[deprecated]` to description
2. Find `offset_checkpoint_interval` row → append `[deprecated]` to description
3. Add Push-Mode Operations section after Delivery Operations

### Method

Edit config table rows + append new section.

### Details

**Config table edits:**

| Field | Before | After |
|---|---|---|
| `poll_interval_ms` | `Subscribe polling interval (ms)` | `[deprecated] Subscribe polling interval — no longer used; push-mode delivery via EventBroker` |
| `offset_checkpoint_interval` | `Checkpoint every N events` | `[deprecated] Mid-stream offset checkpoint interval — removed; ack-only model in place` |

**New section to add (after Delivery Operations):**

---

## Push-Mode Delivery Operations

### Verifying delivery

After enabling the in-memory broker, confirm live push is working:

```bash
# Terminal 1: subscribe (hold connection open)
curl -N "http://localhost:8010/subscribe?consumer_id=test-consumer"

# Terminal 2: publish
curl -X POST http://localhost:8010/publish \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test-001","topic":"test","payload":{},"producer":"ops","published_at":"2026-06-25T12:00:00Z"}'
```

The event should appear in Terminal 1 within one event-loop tick (< 1 ms typical latency on localhost).

### Monitoring slow consumers

Slow consumers are those whose in-process queue depth reaches >= 100 events. Check via health endpoint:

```bash
curl http://localhost:8010/health | jq '.slow_consumers, .max_queue_depth, .active_subscribers'
```

**Thresholds:**
- `slow_consumers > 0` → `degraded_reasons` includes `slow_consumers_detected`
- `max_queue_depth >= 500` → `degraded_reasons` includes `broker_queue_backlog_high`

When a consumer is slow, events are dropped from the in-process queue (logged as WARNING). The consumer must reconnect to replay missed events from SQLite.

### Reconnect recovery

If a subscriber disconnects, it can resume without missing events:

```bash
# Reconnect with consumer_id — replays from last acked offset automatically
curl -N "http://localhost:8010/subscribe?consumer_id=my-consumer"
```

If the consumer has never acked any events, replay starts from seq=0 (all events). To start from a specific point:

```bash
curl -N "http://localhost:8010/subscribe?consumer_id=my-consumer&since_seq=100"
```

### Checking subscriber count

```bash
curl http://localhost:8010/health | jq '.active_subscribers'
```

Zero subscribers means the broker is idle. Events are still persisted to SQLite and available for replay on next connect.

---

## Validation plan

| Check | Target |
|---|---|
| poll_interval_ms deprecated | `grep "poll_interval_ms" docs/06_eventbus_05*.md` → `[deprecated]` |
| offset_checkpoint deprecated | `grep "offset_checkpoint" docs/06_eventbus_05*.md` → `[deprecated]` |
| Push-Mode section present | Section "Push-Mode Delivery Operations" exists |
| curl examples valid | Commands match actual endpoint signatures |
