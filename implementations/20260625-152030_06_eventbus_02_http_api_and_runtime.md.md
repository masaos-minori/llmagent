# Implementation: docs/06_eventbus_02_http_api_and_runtime.md — subscribe section rewrite (req #43)

## Goal

Update the `/subscribe` endpoint documentation to reflect hybrid replay+live push-mode delivery. Remove all polling-model descriptions.

## Scope

- Rewrite the `/subscribe` section description
- Remove "Polls the DB every poll_interval_ms ms" text
- Replace with hybrid model: immediate SQLite replay + broker queue live delivery
- Update behavioral notes: latency, reconnect semantics

## Assumptions

- Current doc describes subscribe as polling-based
- No changes to endpoint parameters (`topic`, `since_seq`, `consumer_id`) — those stay

## Implementation

### Target file

`docs/06_eventbus_02_http_api_and_runtime.md`

### Procedure

1. Find the `/subscribe` section in the doc
2. Replace poll-model description with push-mode description

### Method

Edit the subscribe section only.

### Details

**Remove:**
> Polls the DB every `poll_interval_ms` ms for new events matching the filter. Streams each matching event as an SSE `data:` line. Continues until client disconnects.

**Replace with:**
> Streams events to the caller using a hybrid replay+push model:
>
> **Phase 1 — Replay**: On connect, queries SQLite for all events with `seq > start_seq` matching the topic filter. Each event is yielded as a `data:` SSE line immediately.
>
> **Phase 2 — Live push**: After replay completes, the connection subscribes to the in-process `EventBroker`. New events published via `POST /publish` are pushed to the SSE stream within one event loop tick — no polling delay.
>
> **Reconnect semantics**: Provide `consumer_id` to resume from the last acknowledged offset. The handler reads the stored offset as `start_seq`, ensuring missed events during a disconnect are replayed automatically.
>
> **Race-free transition**: The broker subscription is registered *before* the replay query. Any event published during the replay phase is queued and deduplicated against `replay_ceil` (last seq from replay) at the start of the live phase — no events are lost or duplicated.

**Update the query parameter table entry for `poll_interval_ms`:**

Remove `poll_interval_ms` from any query parameter table or config table in this doc (deprecated in req #40).

## Validation plan

| Check | Target |
|---|---|
| No "poll" language | `grep -i "poll" docs/06_eventbus_02_http_api_and_runtime.md` → 0 matches |
| Hybrid model described | Section describes both replay and live phases |
| race-free note present | `replay_ceil` deduplication documented |
