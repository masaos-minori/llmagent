# Implementation Procedure: Replace offset-based pagination with keyset pagination in subscribe_route.py

## Goal

Replace the offset-based replay query in `scripts/eventbus/subscribe_route.py` with keyset pagination based on the last emitted sequence number, ensuring deterministic ordering and eliminating duplicate or skipped events across reconnect boundaries.

## Scope

- Modify the replay loop in `scripts/eventbus/subscribe_route.py` to use keyset pagination (`WHERE seq > start_seq AND seq <= replay_ceil + batch_size`) instead of offset-based pagination (`WHERE seq > start_seq ... OFFSET ?`).
- Update the replay loop state tracking to use `start_seq` (next-to-read convention) instead of `start_offset` (row-count offset).
- Align the live-delivery deduplication boundary (`event["seq"] <= replay_ceil`) with the new keyset pagination semantics.

## Assumptions

- A: The `seq` column in the `events` table is monotonically increasing and gap-free (confirmed by db.py INSERT logic).
- B: The `consumer_offsets` table exists and is maintained by existing acknowledgment logic.
- C: The `replay_batch_size` config parameter remains valid for keyset pagination (no change needed).
- D: The current `replay_ceil` capture mechanism (line 105: `replay_ceil = start_seq`) is correct and does not need adjustment.

## Design decisions

- Use keyset pagination with two bounds: `seq > start_seq` (exclusive lower bound) and `seq <= replay_ceil + batch_size` (inclusive upper bound). This eliminates the OFFSET clause entirely and ensures deterministic ordering regardless of concurrent inserts.
- Maintain the `replay_ceil` variable as the highest sequence number covered by replay. Events with `seq > replay_ceil` are handled by the live-delivery path.
- After each batch, set `start_seq = replay_ceil + 1` for the next iteration. This follows the "next to read" resume-position convention defined in REQ-003/REQ-004.

## Alternatives considered

- **Pre-pass ceiling calculation**: Calculate `replay_ceil` before entering the replay loop by querying `SELECT MAX(seq) FROM events`. This would eliminate the incremental ceiling update but adds a separate DB round-trip and could miss events published between the pre-pass and the first replay batch. Current approach captures ceiling incrementally, which is simpler and handles concurrent publishes correctly.
- **Single-query replay**: Fetch all events in one query with `WHERE seq > start_seq ORDER BY seq`. This avoids pagination complexity but risks memory exhaustion for large datasets. Keyset pagination is safer for production deployments with large event histories.

## Compatibility considerations

- The SQL query structure changes from `WHERE seq > ? ... OFFSET ?` to `WHERE seq > ? AND seq <= ?`. Topic-filtered queries (lines 114-124) require updating placeholder generation to include the new `seq <= ?` bound.
- The `start_offset` variable (currently used for row-count offset) is replaced by `start_seq` (sequence-number-based cursor). No external API contract changes — the `/subscribe` endpoint's query parameters remain unchanged.
- The `event["seq"] <= replay_ceil` deduplication check in the live-delivery phase (line 196) continues to work correctly because `replay_ceil` is updated incrementally during replay.

## Security considerations

- The new SQL query uses parameterized placeholders (`?`) for both bounds, maintaining the same security posture as the current code. No SQL injection risk introduced.
- The `replay_ceil + batch_size` upper bound prevents unbounded queries while allowing the final batch to extend slightly beyond the initial ceiling to catch events published during replay.

## Rollback considerations

- If the keyset pagination introduces regressions, reverting to offset-based pagination requires restoring the original query structure and the `start_offset` variable. The revert is straightforward: replace the two-bound WHERE clause with the original single-bound + OFFSET pattern.
- The `start_seq` vs `start_offset` naming change is cosmetic; the functional difference is in how the cursor advances between batches.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Replace the offset-based replay query with keyset pagination in both the filtered and unfiltered paths.
2. Replace `start_offset` with `start_seq` for cursor advancement.
3. Update the replay loop termination condition to use `start_seq > replay_ceil`.
4. Ensure the live-delivery deduplication boundary aligns with the new keyset semantics.

### Method

#### Step 1: Replace the unfiltered replay query (lines 126-134)

Current code:
```python
rows = await run_with_db_lock(
    lambda: list(
        db.execute(
            "SELECT seq, event_id, topic, payload, producer, published_at"
            " FROM events WHERE seq > ?",
            (start_seq,),
        ).fetchall()
    )
)
```

New code:
```python
rows = await run_with_db_lock(
    lambda: list(
        db.execute(
            "SELECT seq, event_id, topic, payload, producer, published_at"
            " FROM events WHERE seq > ? AND seq <= ?"
            " ORDER BY seq LIMIT ?",
            (start_seq, replay_ceil + batch_size, batch_size),
        ).fetchall()
    )
)
```

Key changes:
- Add `AND seq <= ?` bound using `replay_ceil + batch_size`
- Remove `OFFSET ?` — keyset pagination replaces it
- Add `ORDER BY seq` for deterministic ordering (REQ-008)
- Parameter tuple changes from `(start_seq,)` to `(start_seq, replay_ceil + batch_size, batch_size)`

#### Step 2: Replace the filtered replay query (lines 113-124)

Current code:
```python
if topic:
    placeholders = ",".join("?" for _ in topic)
    rows = await run_with_db_lock(
        lambda: list(
            db.execute(
                f"SELECT seq, event_id, topic, payload, producer, published_at"
                f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq LIMIT ? OFFSET ?",  # nosec B608 — all values bound via ? placeholders
                (start_seq, *topic, batch_size, start_offset),
            ).fetchall()
        )
    )
```

New code:
```python
if topic:
    placeholders = ",".join("?" for _ in topic)
    rows = await run_with_db_lock(
        lambda: list(
            db.execute(
                f"SELECT seq, event_id, topic, payload, producer, published_at"
                f" FROM events WHERE seq > ? AND seq <= ? AND topic IN ({placeholders}) ORDER BY seq LIMIT ?",
                (start_seq, replay_ceil + batch_size, *topic, batch_size),
            ).fetchall()
        )
    )
```

Key changes:
- Add `AND seq <= ?` bound after `seq > ?`
- Remove `OFFSET ?` from the query string
- Remove `OFFSET ?` from the `nosec` comment
- Parameter tuple changes from `(start_seq, *topic, batch_size, start_offset)` to `(start_seq, replay_ceil + batch_size, *topic, batch_size)`

#### Step 3: Replace `start_offset` with `start_seq` for cursor advancement

Current code (line 145):
```python
start_offset += len(rows)
```

New code:
```python
start_seq = replay_ceil + 1
```

This follows the "next to read" convention: after emitting events up to `replay_ceil`, the next batch starts from `replay_ceil + 1`.

#### Step 4: Verify replay loop termination conditions

Current termination logic (lines 136-150):
```python
if not rows:
    break

for row in rows:
    data = json_dumps(_row_to_dict(row))
    yield f"id:{row['seq']}\ndata:{data}\n\n"
    replay_ceil = row["seq"]

start_offset += len(rows)

# If we got a full batch, more data may exist; release lock between batches
if len(rows) == batch_size:
    continue
break
```

No structural changes needed here — the termination conditions remain:
1. Zero rows returned → break (end of data)
2. Partial batch (< batch_size rows) → break (last batch)
3. Full batch (batch_size rows) → continue (more data may exist)

The `replay_ceil` update inside the for-loop (line 143) continues to track the highest emitted sequence number.

#### Step 5: Verify live-delivery deduplication alignment

Current code (line 196):
```python
if event["seq"] <= replay_ceil:
    continue  # duplicate from replay; discard
```

No change needed. The `replay_ceil` variable is updated incrementally during replay (line 143), so this deduplication check correctly excludes events that were already delivered during the replay phase.

### Details

- REQ-001: Keyset pagination replaces offset-based pagination in both filtered and unfiltered paths.
- REQ-007: Replay loop termination conditions remain unchanged — zero rows, partial batch, or `start_seq > replay_ceil` (implicit via the `seq <= replay_ceil + batch_size` bound).
- REQ-008: `ORDER BY seq` is added to the unfiltered path (already present in the filtered path).
- REQ-010: The `event["seq"] <= replay_ceil` deduplication check in the live-delivery phase ensures no event is lost or duplicated across reconnect boundaries.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters (`since_seq`, `consumer_id`, `Last-Event-ID`) remain unchanged.
- The SSE response format (`id:`, `data:` fields) remains unchanged.
- The `replay_ceil` variable scope and lifecycle remain unchanged — captured at subscription start (line 105), updated during replay (line 143), used in live-delivery deduplication (line 196).

## Security considerations

- All SQL parameters remain bound via `?` placeholders — no SQL injection risk.
- The `replay_ceil + batch_size` upper bound prevents unbounded queries.

## Rollback considerations

- Revert requires restoring the original query strings and the `start_offset` variable.
- The revert is a mechanical replacement — no semantic changes to rollback.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py | Unit: verify keyset pagination query correctness | uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -v | Existing transition tests pass |
| scripts/eventbus/subscribe_route.py | Integration: multi-batch replay with no duplicates | uv run pytest tests/eventbus/test_eventbus_subscribe.py -v | Existing subscribe tests pass |
| scripts/eventbus/subscribe_route.py | Static analysis: parameter binding verification | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/subscribe_route.py | Type checking | uv run mypy scripts/eventbus/subscribe_route.py | No new type errors |

## Completion criteria

- [ ] The replay query in both filtered and unfiltered paths uses keyset pagination (`WHERE seq > ? AND seq <= ? ORDER BY seq LIMIT ?`) instead of offset-based pagination.
- [ ] The `start_offset` variable is replaced by `start_seq` for cursor advancement.
- [ ] The `start_seq` value advances as `start_seq = replay_ceil + 1` after each batch.
- [ ] The `event["seq"] <= replay_ceil` deduplication check in the live-delivery phase continues to work correctly.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-009).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace offset-based pagination with keyset pagination in subscribe_route.py | Completed | 20260915-001102 | 20260915-001102 |  |
| 2 | Verify replay loop termination conditions | Completed | 20260915-001112 | 20260915-001112 |  |
| 3 | Verify live-delivery deduplication alignment | Completed | 20260915-001113 | 20260915-001113 |  |
| 4 | Run validation suite | Completed | 20260915-001113 | 20260915-001113 |  |

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
- **Requirement ID**: REQ-001, REQ-007, REQ-008, REQ-010
- **Source issue**: issues/20260914-102225_eventbus01_subscription-replay-boundaries-batching.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-170207_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-192422
- **Related target files**: scripts/eventbus/subscribe_route.py