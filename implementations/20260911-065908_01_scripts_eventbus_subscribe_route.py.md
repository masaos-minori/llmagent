## Goal

Add SSE-standard features to the EventBus subscription protocol so idle connections stay alive through heartbeats, clients can auto-reconnect using the standard `Last-Event-ID` header, and event delivery includes monotonic sequence IDs. These additions improve interoperability with `EventSource`-based clients without changing the existing `since_seq`/`consumer_id` resume mechanism.

## Scope

Modify `scripts/eventbus/subscribe_route.py`:
- Modify `_sse_gen()` to emit `id:<seq>` field: `yield f"id:{row['seq']}\ndata:{data}\n\n"` (REQ-002; `scripts/eventbus/subscribe_route.py`).
- Modify live-phase event emission similarly: `yield f"id:{event['seq']}\ndata:{data}\n\n"` (REQ-002; `scripts/eventbus/subscribe_route.py`).
- Add `sse_heartbeat_interval` parameter to `_sse_gen()` signature (REQ-001; `scripts/eventbus/subscribe_route.py`).
- Create heartbeat `asyncio.Task` in the `try` block after entering the live phase (REQ-001; `scripts/eventbus/subscribe_route.py`).
- Cancel heartbeat task in the `finally` block (REQ-005; `scripts/eventbus/subscribe_route.py`).
- Parse `request.headers.get("last-event-id", "")` in `subscribe_route.subscribe()` (REQ-003; `scripts/eventbus/subscribe_route.py`).
- Implement precedence: `since_seq` > consumer offset > `Last-Event-ID` (REQ-004; `scripts/eventbus/subscribe_route.py`).
- Add stale reconnect rejection: if `Last-Event-ID` seq > current max seq, return HTTP 412 (REQ-003; `scripts/eventbus/subscribe_route.py`).

## Assumptions

- The heartbeat interval should be configurable via `EventBusConfig` (defaulting to a reasonable value like 30 seconds if absent from TOML).
- The `Last-Event-ID` header should be parsed as an integer representing the last received `seq` value.
- The `id:` field should contain the event's `seq` number, which is monotonic across all events regardless of topic.
- The heartbeat should be an SSE comment line (`: heartbeat\n\n`), not a `data:` event, so it does not appear as a delivered event to `EventSource`-based clients.
- The `replay_ceil`-based duplicate-discard logic in `subscribe_route.py` should remain unchanged when adding the `id:` field.

## Design decisions

1. **Heartbeat implementation (REQ-001)**: Spawn an `asyncio.Task` in `_sse_gen()` that periodically yields `: heartbeat\n\n` during the live phase. The task is cancelled in the `finally` block alongside subscriber unregistration. Default interval: 30 seconds (documented as half of common 60s proxy timeout).

2. **Event ID emission (REQ-002)**: In both `_sse_gen()` functions, yield `f"id:{row['seq']}\ndata:{data}\n\n"` instead of just `f"data:{data}\n\n"`. This preserves backward compatibility — `EventSource`-based clients will use the `id:` field for auto-reconnect, while other clients can ignore it.

3. **Last-Event-ID parsing (REQ-003)**: In `subscribe_route.subscribe()`, read `request.headers.get("last-event-id", "")` and parse as int. Used only when `since_seq == 0` AND no persisted consumer offset exists. Precedence: `since_seq` > consumer offset > `Last-Event-ID`.

4. **Precedence definition (REQ-004)**: Define explicitly in documentation:
    - Priority 1: Explicit `since_seq` query parameter (highest)
    - Priority 2: Persisted consumer offset (from `consumer_id`)
    - Priority 3: `Last-Event-ID` header (lowest — fallback for `EventSource` clients)

5. **Task lifecycle (REQ-005)**: The heartbeat task is created in the `try` block before entering the live phase and cancelled in the `finally` block. This follows the existing pattern of `broker.unsubscribe(sub)` in the `finally` block.

6. **Stale reconnect rejection (UNK-02 decision)**: Reject `Last-Event-ID` reconnects where the requested `seq` exceeds the current max seq in SQLite. Return HTTP 412 Precondition Failed with the current max seq in the response body. This prevents clients from requesting events that have already been garbage-collected.

## Alternatives considered

- Using `time.sleep()` instead of `asyncio.sleep()` for heartbeat intervals: would block the event loop; `asyncio.sleep()` is non-blocking.
- Adding heartbeat as a separate endpoint rather than embedding in the generator: adds unnecessary complexity for a simple keepalive mechanism.
- Accepting all `Last-Event-ID` values without validation: risks returning stale or non-existent events.
- Raising `ValueError` for invalid `Last-Event-ID` values: less user-friendly than silently ignoring them.

## Implementation
### Target file
`scripts/eventbus/subscribe_route.py`

### Procedure
1. Phase 1: Preparation — Add config import and Last-Event-ID parsing
2. Phase 2: Core Logic — Add event IDs to subscribe route
3. Phase 3: Core Logic — Add heartbeat to subscribe route
4. Phase 4: Core Logic — Implement precedence order

### Method
#### Phase 1: Preparation
- [ ] Read `request.headers.get("last-event-id", "")` in `subscribe_route.subscribe()` (REQ-003; `scripts/eventbus/subscribe_route.py`)
- [ ] Parse `Last-Event-ID` header as int, handle non-integer values gracefully (REQ-003; `scripts/eventbus/subscribe_route.py`)

#### Phase 2: Core Logic
- [ ] Modify `_sse_gen()` in `subscribe_route.py` to emit `id:<seq>` field: `yield f"id:{row['seq']}\ndata:{data}\n\n"` (REQ-002; `scripts/eventbus/subscribe_route.py`)
- [ ] Modify live-phase event emission similarly: `yield f"id:{event['seq']}\ndata:{data}\n\n"` (REQ-002; `scripts/eventbus/subscribe_route.py`)

#### Phase 3: Core Logic
- [ ] Add `sse_heartbeat_interval` parameter to `_sse_gen()` signature (REQ-001; `scripts/eventbus/subscribe_route.py`)
- [ ] Create heartbeat `asyncio.Task` in the `try` block after entering the live phase (REQ-001; `scripts/eventbus/subscribe_route.py`)
- [ ] Cancel heartbeat task in the `finally` block (REQ-005; `scripts/eventbus/subscribe_route.py`)

#### Phase 4: Core Logic
- [ ] Implement precedence: `since_seq` > consumer offset > `Last-Event-ID` (REQ-004; `scripts/eventbus/subscribe_route.py`)
- [ ] Add stale reconnect rejection: if `Last-Event-ID` seq > current max seq, return HTTP 412 (REQ-003; `scripts/eventbus/subscribe_route.py`)

### Details

**Phase 1: Preparation**

Read `Last-Event-ID` header in `subscribe_route.subscribe()`:

```python
# After cfg = request.app.state.config
# Before start_seq = since_seq

# REQ-003: Read Last-Event-ID header as additional resume-position input
last_event_id_str = request.headers.get("last-event-id", "")
last_event_id: int | None = None
if last_event_id_str:
    try:
        last_event_id = int(last_event_id_str, 10)
    except ValueError:
        # Invalid Last-Event-ID value — silently ignore per design decision
        logger.warning("Invalid Last-Event-ID header: %r", last_event_id_str)

# REQ-003: Stale reconnect rejection
if last_event_id is not None:
    def _get_max_seq() -> int:
        """Get the current maximum seq in SQLite."""
        row = db.execute("SELECT MAX(seq) FROM events").fetchone()
        return int(row[0]) if row else 0
    
    max_seq = await run_with_db_lock(_get_max_seq)
    if last_event_id > max_seq:
        raise HTTPException(
            status_code=412,
            detail=f"Last-Event-ID ({last_event_id}) exceeds current max seq ({max_seq})",
        )
```

**Phase 2: Core Logic**

Modify `_sse_gen()` to emit `id:<seq>` field:

```python
async def _sse_gen() -> AsyncGenerator[str]:
    """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
    # Subscriber registration already done above, before this generator starts
    # must be set before any await below, so the except CancelledError handler
    # below always has a value, even if cancelled during the replay fetch
    replay_ceil = start_seq
    try:
        # Step 2: replay from SQLite
        def _fetch_replay() -> list[Any]:
            """Fetch replay events from SQLite filtered by topic and sequence."""
            if topic:
                placeholders = ",".join("?" for _ in topic)
                return list(
                    db.execute(
                        f"SELECT seq, event_id, topic, payload, producer, published_at"
                        f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",  # nosec B608 — all values bound via ? placeholders
                        (start_seq, *topic),
                    ).fetchall()
                )
            return list(
                db.execute(
                    "SELECT seq, event_id, topic, payload, producer, published_at"
                    " FROM events WHERE seq > ? ORDER BY seq",
                    (start_seq,),
                ).fetchall()
            )

        rows = await run_with_db_lock(_fetch_replay)
        for row in rows:
            data = json_dumps(_row_to_dict(row))
            # REQ-002: Emit id: field alongside data: field
            yield f"id:{row['seq']}\ndata:{data}\n\n"
            replay_ceil = row["seq"]

        # Step 3: live delivery from broker queue, racing against disconnect signal
        while True:
            # Race between receiving an event and the disconnect signal
            done, pending = await asyncio.wait(
                [
                    asyncio.ensure_future(sub.queue.get()),
                    asyncio.ensure_future(sub.disconnect_signal.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            # Cancel the losing task(s) to avoid "exception never retrieved" warnings
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check which task completed first
            if sub.disconnect_signal in done:
                # Disconnect signal fired — end the stream
                logger.info(
                    "subscribe disconnected overflow consumer=%s seq=%d",
                    consumer_id,
                    replay_ceil,
                )
                break

            # queue.get() completed — process the event
            event = done.pop().result()
            if event is None:  # shutdown sentinel
                break
            if event["seq"] <= replay_ceil:
                continue  # duplicate from replay; discard
            data = json_dumps(event)
            # REQ-002: Emit id: field alongside data: field
            yield f"id:{event['seq']}\ndata:{data}\n\n"

    except asyncio.CancelledError:
        logger.info(
            "subscribe disconnected consumer=%s seq=%d",
            consumer_id,
            replay_ceil,
        )
    finally:
        broker.unsubscribe(sub)
```

**Phase 3: Core Logic**

Add heartbeat implementation:

```python
async def _sse_gen() -> AsyncGenerator[str]:
    """Generate Server-Sent Events by replaying from SQLite and streaming live broker events."""
    # Subscriber registration already done above, before this generator starts
    # must be set before any await below, so the except CancelledError handler
    # below always has a value, even if cancelled during the replay fetch
    replay_ceil = start_seq
    heartbeat_task: asyncio.Task[None] | None = None
    try:
        # Step 2: replay from SQLite
        def _fetch_replay() -> list[Any]:
            """Fetch replay events from SQLite filtered by topic and sequence."""
            if topic:
                placeholders = ",".join("?" for _ in topic)
                return list(
                    db.execute(
                        f"SELECT seq, event_id, topic, payload, producer, published_at"
                        f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq",  # nosec B608 — all values bound via ? placeholders
                        (start_seq, *topic),
                    ).fetchall()
                )
            return list(
                db.execute(
                    "SELECT seq, event_id, topic, payload, producer, published_at"
                    " FROM events WHERE seq > ? ORDER BY seq",
                    (start_seq,),
                ).fetchall()
            )

        rows = await run_with_db_lock(_fetch_replay)
        for row in rows:
            data = json_dumps(_row_to_dict(row))
            # REQ-002: Emit id: field alongside data: field
            yield f"id:{row['seq']}\ndata:{data}\n\n"
            replay_ceil = row["seq"]

        # Step 3: live delivery from broker queue, racing against disconnect signal
        # REQ-001: Start heartbeat task when entering live phase
        async def _heartbeat_loop(interval: float) -> None:
            """Periodically emit SSE comment heartbeats."""
            while True:
                await asyncio.sleep(interval)
                yield ": heartbeat\n\n"
        
        heartbeat_task = asyncio.create_task(_heartbeat_loop(cfg.sse_heartbeat_interval))
        
        while True:
            # Race between receiving an event and the disconnect signal
            done, pending = await asyncio.wait(
                [
                    asyncio.ensure_future(sub.queue.get()),
                    asyncio.ensure_future(sub.disconnect_signal.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            # Cancel the losing task(s) to avoid "exception never retrieved" warnings
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check which task completed first
            if sub.disconnect_signal in done:
                # Disconnect signal fired — end the stream
                logger.info(
                    "subscribe disconnected overflow consumer=%s seq=%d",
                    consumer_id,
                    replay_ceil,
                )
                break

            # queue.get() completed — process the event
            event = done.pop().result()
            if event is None:  # shutdown sentinel
                break
            if event["seq"] <= replay_ceil:
                continue  # duplicate from replay; discard
            data = json_dumps(event)
            # REQ-002: Emit id: field alongside data: field
            yield f"id:{event['seq']}\ndata:{data}\n\n"

    except asyncio.CancelledError:
        logger.info(
            "subscribe disconnected consumer=%s seq=%d",
            consumer_id,
            replay_ceil,
        )
    finally:
        # REQ-005: Cancel heartbeat task on disconnect/shutdown
        if heartbeat_task is not None and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        broker.unsubscribe(sub)
```

**Phase 4: Core Logic**

Implement precedence order:

```python
# In subscribe_route.subscribe(), after reading Last-Event-ID header:
# REQ-004: Implement precedence: since_seq > consumer offset > Last-Event-ID
start_seq = since_seq
if consumer_id and start_seq == 0:
    # Try SQLite-backed offset first, then fall back to legacy file-based
    start_seq = _get_offset_from_sqlite(db, consumer_id)
    if start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)

# REQ-003: Fallback to Last-Event-ID only if both since_seq and consumer offset are unavailable
if start_seq == 0 and last_event_id is not None:
    start_seq = last_event_id + 1
```

## Compatibility considerations

- Adding `id:` fields changes the SSE frame format — existing clients that parse exact frame shapes may need updates.
- The `Last-Event-ID` header is case-insensitive in HTTP — need to handle both `Last-Event-ID` and `last-event-id` variants.
- The default heartbeat interval should be shorter than typical proxy/LB timeouts (30s is half of the common 60s default).
- The `id:` field must be monotonic — using `seq` ensures this since `seq` is globally increasing.

## Security considerations

- The stale reconnect rejection prevents clients from requesting events that have already been garbage-collected.
- Invalid `Last-Event-ID` values are silently ignored rather than causing request failures.

## Rollback considerations

- Reverting the `id:` field emission restores backward compatibility but loses SSE-standard auto-reconnect support.
- Reverting the heartbeat task removes idle connection keepalive but simplifies the generator loop.
- Reverting the `Last-Event-ID` parsing restores the original resume mechanism without standard SSE support.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/subscribe_route.py` | Integration — heartbeat + id field | `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -k "heartbeat or id" -v` | Heartbeat emitted, id field present |
| `scripts/eventbus/subscribe_route.py` | Integration — Last-Event-ID precedence | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -k "resume or last-event" -v` | Correct precedence applied |
| `scripts/eventbus/subscribe_route.py` | Integration — disconnect cleanup | `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -k "disconnect" -v` | No leaks after disconnect |
| `scripts/eventbus/replay_route.py` | Integration — replay id field | `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py -k "id" -v` | Replay frames include id field |
| `scripts/eventbus/config.py` | Unit — config validation | `uv run pytest tests/eventbus/test_eventbus_config.py -v` | All config tests pass |
| `scripts/eventbus/*.py` | Lint | `uv run ruff check scripts/eventbus/subscribe_route.py scripts/eventbus/replay_route.py scripts/eventbus/config.py` | Clean |
| `scripts/eventbus/*.py` | Type check | `uv run mypy scripts/eventbus/subscribe_route.py scripts/eventbus/replay_route.py scripts/eventbus/config.py` | Pass |

## Completion criteria

- Idle subscriptions emit heartbeats at the configured interval — REQ-001
- Heartbeat frames do not alter offsets or delivery state — REQ-005
- Reconnect with `Last-Event-ID` resumes after that sequence according to the documented precedence — REQ-003
- No task or subscriber registration leaks after disconnect — REQ-005
- Each event carries an `id:` field with the event's `seq` value — REQ-002

## Out of scope

- Changing the underlying event ordering or offset-persistence mechanism (EB-H01).
- Backpressure/duplicate-connection handling (EB-H02).
- Deriving threshold values from load-test measurement (EB-M05).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Last-Event-ID parsing and stale reconnect rejection | Pending | — | — | |
| 2 | Add event IDs to subscribe route | Pending | — | — | |
| 3 | Add heartbeat to subscribe route | Pending | — | — | |
| 4 | Implement precedence order | Pending | — | — | |
| 5 | Add or update tests per Validation plan | Pending | — | — | |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260907-125042_eb_l01_sse_heartbeat_event_id_resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-072908_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-065908
- **Related target files**: scripts/eventbus/subscribe_route.py
