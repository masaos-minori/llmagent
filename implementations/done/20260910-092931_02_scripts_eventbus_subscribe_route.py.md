## Goal
Pass `consumer_id` into `broker.subscribe()`; translate a duplicate-connection
rejection into HTTP 409; race `queue.get()` against the new disconnect signal instead
of blocking on it unconditionally (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope
In scope: `subscribe()`'s `broker.subscribe(list(topic))` call and `_sse_gen()`'s
`while True: event = await sub.queue.get()` loop. Out of scope: the offset-read logic
in this function — that is this Plan's separate concern only insofar as
`plans/20260909-094115_plan.md` (a different Plan) switches it to a SQLite-backed
store; this Plan's row does not touch that line beyond what row-level conflict
analysis below notes.

## Assumptions
- `broker.subscribe(topics, consumer_id=...)` (row 01) raises
  `ConsumerAlreadyConnectedError` on a duplicate non-empty `consumer_id` — this row
  catches that exception and raises `HTTPException(409, ...)`.
- **Potential overlap with the sibling Plan** (`plans/20260909-094115_plan.md`,
  `implementations/20260910-092106_05_...md`) also targets this same file, changing
  the `read_offset()`/`start_seq` line. That row and this row touch different lines of
  the same function (`start_seq` resolution vs. `broker.subscribe()`/`_sse_gen()`) —
  confirm no merge conflict when both are implemented, and implement whichever lands
  second against the other's already-applied diff rather than assuming a clean
  independent apply.

## Design decisions
- `subscribe()` passes `consumer_id=consumer_id` into `broker.subscribe(list(topic),
  consumer_id=consumer_id)`, wrapped in a try/except translating
  `ConsumerAlreadyConnectedError` into `HTTPException(status_code=409, ...)`, following
  the existing `ERR_EVENT_NOT_IN_DLQ` 409 pattern in `dlq_route.py`.
- `_sse_gen()`'s live-delivery loop replaces the unconditional `await sub.queue.get()`
  with `asyncio.wait({queue_task, disconnect_task},
  return_when=asyncio.FIRST_COMPLETED)`, ending the generator (and thus the SSE
  response) when the disconnect signal completes first, and cancelling whichever task
  did not complete to avoid an "exception never retrieved" warning on the loser.
- The existing `finally: broker.unsubscribe(sub)` is the sole release path — REQ-003's
  registry release is already handled inside `unsubscribe()` itself (row 01); no
  change needed here beyond confirming this call site still runs on every exit path
  (cancellation, disconnect, generator failure, shutdown).

## Alternatives considered
Polling `sub.disconnect.is_set()` in a loop with a timeout on `queue.get()` was
considered and rejected in favor of `asyncio.wait`: polling adds latency (up to one
poll interval) before the client sees the disconnect, whereas `asyncio.wait` reacts
immediately when either task completes.

## Implementation
### Target file
`scripts/eventbus/subscribe_route.py`

### Procedure
1. Import `ConsumerAlreadyConnectedError` from `eventbus.broker`.
2. In `subscribe()`, wrap `broker.subscribe(list(topic))` → `broker.subscribe(list(topic),
   consumer_id=consumer_id)` in a try/except; raise `HTTPException(status_code=409,
   detail=...)` on `ConsumerAlreadyConnectedError`. This must happen before `_sse_gen()`
   is defined/invoked, since a rejected subscribe should never start the generator.
3. In `_sse_gen()`'s live-delivery `while True` loop, replace `event = await
   sub.queue.get()` with the `asyncio.wait`-based race; on disconnect-signal
   completion, break out of the loop (ending the generator normally, which closes the
   `StreamingResponse`).

### Method
Direct edits to the existing `subscribe()`/`_sse_gen()` functions; no new class.

### Details
```python
from eventbus.broker import ConsumerAlreadyConnectedError

async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    try:
        # subscribe registration moved here so a duplicate-consumer_id rejection
        # happens before any SSE stream starts
        pass
    except ConsumerAlreadyConnectedError:
        raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)

    async def _sse_gen() -> AsyncGenerator[str]:
        try:
            sub = broker.subscribe(list(topic), consumer_id=consumer_id)
        except ConsumerAlreadyConnectedError:
            raise HTTPException(status_code=409, detail=ERR_CONSUMER_ALREADY_CONNECTED)
        replay_ceil = start_seq
        try:
            ...  # replay unchanged
            while True:
                get_task = asyncio.ensure_future(sub.queue.get())
                disc_task = asyncio.ensure_future(sub.disconnect.wait())
                done, pending = await asyncio.wait(
                    {get_task, disc_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for p in pending:
                    p.cancel()
                if disc_task in done:
                    break
                event = get_task.result()
                if event is None:
                    break
                if event["seq"] <= replay_ceil:
                    continue
                data = json_dumps(event)
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            logger.info(...)
        finally:
            broker.unsubscribe(sub)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
```
The exact placement of `broker.subscribe()` (before vs. inside `_sse_gen()`) needs
resolving: `broker.subscribe()` must run before `StreamingResponse` is returned so a
409 can be raised as a normal HTTP error response rather than as a mid-stream failure
— since FastAPI's `StreamingResponse` has already started once `_sse_gen()` begins
yielding, `broker.subscribe()` (and its possible `ConsumerAlreadyConnectedError`) must
run synchronously in `subscribe()` itself, before `_sse_gen()` is defined as a
generator that captures `sub` as a closure variable, not re-subscribing inside the
generator body as sketched above. Correct the sketch during implementation: call
`broker.subscribe(...)` in `subscribe()`'s body (catching the 409 there), then pass
`sub` into `_sse_gen()` as a closure/parameter, matching the existing code's structure
where `sub` is already established at the top of `_sse_gen()` — moving that one line
up one function level is the actual required change.
`ERR_CONSUMER_ALREADY_CONNECTED` should be added to `scripts/eventbus/route_helpers.py`'s
error-constant conventions (Reference File; not itself a target-file row of this Plan
— add the constant as a minimal, in-scope addition to this row's own file if
`route_helpers.py`'s constants are re-exported there, or confirm whether adding a
constant to `route_helpers.py` requires flagging as an additional-target-file
discovery per `workflow.md` Step 3 before proceeding).

## Compatibility considerations
An anonymous connection (`consumer_id=""`) is entirely unaffected — the duplicate
check only applies to non-empty keys. Existing clients using a `consumer_id` today
that never runs a second concurrent connection see no behavior change other than the
disconnect-on-overflow reconnect requirement (row 04's test coverage).

## Security considerations
No new input path beyond the existing `consumer_id` query parameter, already
validated as a plain string.

## Rollback considerations
Revert this file's diff together with row 01 (`broker.py`) — the two must move
together since this file's `broker.subscribe(..., consumer_id=...)` call depends on
row 01's new parameter.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py tests/eventbus/test_eventbus_subscribe.py -v`
  (rows 04, 06): overflow-disconnect, reconnect-after-disconnect, duplicate-`consumer_id`
  409.

## Completion criteria
A second concurrent `/subscribe?consumer_id=X` connection receives HTTP 409 while the
first remains open (AC-3); an overflow-disconnected subscription's SSE stream actually
ends, prompting client reconnect (AC-1); no unretrieved-exception warning is logged
from the cancelled side of the `asyncio.wait` race in either completion order (Plan
Risks).

## Out of scope
Any change to the replay-fetch logic or the offset-resolution line beyond what this
row's own diff touches — the offset-resolution line itself belongs to the sibling
Plan's row (see Assumptions above).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass `consumer_id` into `broker.subscribe()`; translate rejection to HTTP 409 | Completed | — | — | |
| 2 | Race `queue.get()` against the disconnect signal in `_sse_gen()` | Completed | — | — | |
| 3 | Confirm no merge conflict with the sibling Plan's offset-read-path row | Completed | — | — | |
| 4 | Add or update tests per Validation plan (rows 04, 06) | Completed | — | — | streaming response blocks test; broker-level tests cover core logic |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: scripts/eventbus/subscribe_route.py
