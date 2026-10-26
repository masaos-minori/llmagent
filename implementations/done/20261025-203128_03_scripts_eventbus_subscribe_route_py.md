## Goal

Record the UNK-02 owner decision on delivery-attempt identity for `scripts/eventbus/subscribe_route.py`: the recommended **client-generated key** model requires **no change** to the SSE stream, because a client can derive a stable key from `(consumer_id, event_id)` it already holds. This document verifies the current SSE emission and records the conditional branch that would apply only if the owner later adopts the server-issued model.

## Scope

- **In-Scope** (`scripts/eventbus/subscribe_route.py` only):
  - Verify and record the current SSE emission shape (only `id:{seq}` and `data:{json(payload)}`).
  - Record the UNK-02 decision (client-generated key → no SSE change).
  - Document the conditional server-issued branch (would apply only if UNK-02 selects that model).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - Dedup-scope schema (`scripts/eventbus/schema.sql`, seq 04).
  - Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).

## Assumptions

- UNK-02 recommended = client-generated stable key: the client owns/derives the idempotency key from `(consumer_id, event_id)` (which it already knows from the delivered event) and echoes it on every NACK. No server assistance is required.
- The `/subscribe` SSE stream is consumed externally to this repository; its payload shape is an external contract, not exercised by an internal caller.
- DLQ promotion stays gated on the per-consumer failure count (`INV-13`); this row does not touch it.

## Design decisions

- **Client-generated key (no SSE change).** The recommended UNK-02 model gives the client everything it needs: each SSE event carries `event_id` in its payload, so the client derives a stable attempt key without server help. `subscribe_route.py` is left unchanged.
- **Server-issued variant (conditional, not adopted).** Only if the owner switches UNK-02 to the server-issued model would `subscribe_route.py` emit an `attempt_id` (new) — as a JSON field inside the payload and/or a separate SSE `id:` namespace — which the client then echoes on NACK. This distinguishes sequential attempts but does not by itself dedup a raw HTTP retry (the client must still store it).

## Alternatives considered

- **Server-issued `attempt_id` (UNK-02 server model):** emit an attempt identifier per SSE event. Rejected as the default — it couples clients to a server-owned identity and still requires client-side storage to dedup a raw retry. Kept as a documented conditional branch.
- **Leave the stream as-is unrecorded:** rejected — the one-doc-per-row invariant requires this conditional row to carry a recorded decision with verified current-source evidence.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Verify the current SSE emission (no change required): replay path yields `f"id:{row['seq']}\ndata:{data}\n\n"` at subscribe_route.py:191 and live path yields `f"id:{event['seq']}\ndata:{data}\n\n"` at subscribe_route.py:259, where `data` is `json_dumps(_row_to_dict(row))` (replay, subscribe_route.py:189) / `json_dumps(event)` (live, subscribe_route.py:257).
2. Confirm no delivery-attempt identifier is emitted — the payload carries only `seq, event_id, topic, payload, producer, published_at`; the client derives its key from `event_id`.
3. Record the UNK-02 decision (client-generated key → no modification) and the conditional server-issued branch above.
4. Run the documentation checkers.

### Method

The `_sse_gen()` inner generator (subscribe_route.py:188-266) emits SSE frames on two paths. The replay path (subscribe_route.py:188-192) builds `data = json_dumps(_row_to_dict(row))` and yields `id:{seq}` / `data:{json}` at subscribe_route.py:191. The live path (subscribe_route.py:252-261) builds `data = json_dumps(event)` and yields at subscribe_route.py:259. Neither path includes a delivery-attempt identifier; the returned `StreamingResponse` (subscribe_route.py:277) uses `text/event-stream`. Under the recommended client-key model this is complete as-is.

```python
# subscribe_route.py — replay-path SSE emission (UNCHANGED under recommended UNK-02)
for row in rows:
    data = json_dumps(_row_to_dict(row))
    # REQ-002: Emit id: field alongside data: field
    yield f"id:{row['seq']}\ndata:{data}\n\n"   # subscribe_route.py:191
    last_replayed = row["seq"]
```

```python
# subscribe_route.py — conditional server-issued variant (NOT adopted; UNK-02 = client key)
# Only if UNK-02 selects the server-issued model, add an attempt_id (new) to the payload:
payload = _row_to_dict(row)
payload["attempt_id"] = <server-issued attempt identifier>   # (new)
data = json_dumps(payload)
yield f"id:{row['seq']}\ndata:{data}\n\n"
```

### Details

- **UNK-02 (recommended, client key):** no change. The `event_id` field in `_row_to_dict(row)`'s output lets the client derive a stable key; the stream needs no delivery-attempt identifier.
- **UNK-02 (conditional, server-issued):** would require adding an `attempt_id` (new) to the payload on both the replay (subscribe_route.py:188-192) and live (subscribe_route.py:252-261) paths, and documenting the new field in the contract doc (seq 07). Not implemented — recorded only.
- **No schema/ADR impact:** this row changes nothing under the recommended model; seq 04 (schema) also stays unmodified.

## Compatibility considerations

- No change to the `/subscribe` SSE contract under the recommended model — external subscribers are unaffected.
- If the owner later adopts the server-issued variant, the added `attempt_id` (new) field is additive to the JSON payload (backward compatible for clients that ignore unknown fields).

## Security considerations

- No change under the recommended model; no new secrets or injection surface.
- The conditional server-issued variant would embed a server-issued identifier in the payload — it must not leak consumer-internal state beyond the attempt identity.

## Rollback considerations

- No code change under the recommended model; there is nothing to revert. This document is a decision record.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `subscribe_route.py` unchanged | Current-source verification against this procedure | `uv run python tools/stale_detector.py {this doc}` | All referenced constructs found; emission at :191/:259 matches |
| Decision record integrity | Structure check | `uv run python tools/check_workitem_structure.py {this doc}` | No findings |

## Completion criteria

- The current SSE emission (`id:{seq}` + `data:{json}` at subscribe_route.py:191 and :259) is verified against source with no delivery-attempt identifier.
- The UNK-02 decision (client-generated key → no modification) is recorded, with the conditional server-issued branch documented.
- `stale_detector.py` and `check_workitem_structure.py` pass.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- Dedup-scope schema (`scripts/eventbus/schema.sql`, seq 04).
- Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).
- UNK-02 server-issued variant — recorded as a conditional branch, not implemented.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify current SSE emission; record UNK-02 client-key decision (no modification) + conditional server-issued branch | Done | 2026-10-26 | 2026-10-26 | Verified: replay path at :191 yields `id:{seq}` + `data:{json}`; live path at :259 same; no delivery-attempt identifier emitted |
| 2 | Run the documentation checkers (`stale_detector.py`, `check_workitem_structure.py`) | Done | 2026-10-26 | 2026-10-26 | No code change → no test run needed |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `scripts/eventbus/subscribe_route.py`
