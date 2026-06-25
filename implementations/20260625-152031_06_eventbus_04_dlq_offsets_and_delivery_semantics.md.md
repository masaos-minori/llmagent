# Implementation: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md — offset hybrid model (req #43)

## Goal

Update the offset semantics section to document the ack-only model with hybrid subscribe reconnect behavior.

## Scope

- Remove references to mid-stream `write_offset()` checkpointing
- Update offset semantics: offset advanced only via `POST /events/{id}/ack`
- Document reconnect resume: `consumer_id` + `since_seq` default = last acked offset
- Note: `offset_checkpoint_interval` deprecated

## Assumptions

- Current doc describes mid-stream checkpointing that was removed in req #29
- Hybrid subscribe adds `consumer_id` resume from stored offset on reconnect

## Implementation

### Target file

`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure

1. Find the offset semantics / consumer offsets section
2. Remove mid-stream checkpoint description
3. Add reconnect resume semantics

### Method

Edit offset section.

### Details

**Remove (mid-stream checkpoint description):**
> The subscribe endpoint automatically checkpoints the consumer offset every `offset_checkpoint_interval` events. This allows consumers to resume from a recent point rather than from the start on reconnect.

**Replace with:**
> **Ack-only offset model**
>
> Consumer offsets advance only when the consumer explicitly acknowledges an event via `POST /events/{event_id}/ack?consumer_id={consumer_id}`. Offsets are never advanced automatically during streaming.
>
> **Reconnect resume**
>
> On reconnect, provide `consumer_id` (without `since_seq`) to resume from the last acknowledged offset. The subscribe handler calls `read_offset(offsets_dir, consumer_id)` at connect time and uses the stored seq as `start_seq` for the SQLite replay query.
>
> Example reconnect flow:
> 1. Consumer connects: `GET /subscribe?consumer_id=svc-A`
> 2. Receives events seq=1..10, acks seq=10: `POST /events/{id}/ack?consumer_id=svc-A`
> 3. Disconnects
> 4. Reconnects: `GET /subscribe?consumer_id=svc-A` → replay starts from seq=11
>
> **Deprecated**: `offset_checkpoint_interval` config field is no longer used.

## Validation plan

| Check | Target |
|---|---|
| No checkpoint language | `grep "checkpoint" docs/06_eventbus_04*.md` → 0 matches |
| Ack-only model documented | Section describes ack endpoint advancing offsets |
| Reconnect example present | Step-by-step reconnect flow documented |
