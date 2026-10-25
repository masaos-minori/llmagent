## Goal

Make `_nack_and_promote()` (`scripts/eventbus/ack_route.py`) pass a caller-supplied NACK idempotency key through to `nack_event()` instead of minting a fresh `uuid.uuid4()` per request (`REQ-002`), and enforce the UNK-01 keyless-NACK contract (`REQ-006`).

## Scope

- **In-Scope** (`scripts/eventbus/ack_route.py` only):
  - Add an `idempotency_key` query parameter to `nack()`.
  - Enforce the UNK-01 keyless handling (reject 400 when absent) before calling the repository.
  - Replace the per-request `uuid.uuid4()` in `_nack_and_promote()` with the caller key, passed unchanged as `last_nack_attempt` to `_nack_event()`.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The repository guard live-ification and `consumer_id=None` handling (`scripts/eventbus/delivery_repo.py`, seq 02).
  - The dedup-scope schema decision (`scripts/eventbus/schema.sql`, seq 04).
  - Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).

## Assumptions

- The client owns a stable idempotency key for a delivery attempt (UNK-02, client-generated model) and echoes it on every retry of one NACK. The server treats it opaquely and passes it through.
- The single remembered key (`consumer_last_nack_attempt`, latest-key-only, UNK-03 recommended) is sufficient: a well-formed client sends the same key for a retry of attempt N and a new key for attempt N+1.
- DLQ promotion stays gated on the per-consumer failure count (`INV-13`); this row changes only the key source, not promotion.
- `auth.py`'s `X-Request-Id` middleware is per-request (its `_request_id_middleware` assigns `request.state.request_id` at auth.py:367) and therefore CANNOT serve as a retry-stable key; it is referenced only, not modified.

## Design decisions

- **Caller key, not per-request UUID.** Read `idempotency_key` (new) from the NACK query and pass it unchanged to `nack_event(last_nack_attempt=key)`. This makes a retry of the same attempt deduplicate (`REQ-002`, `REQ-001`).
- **Keyless → 400 (UNK-01 recommended).** Validate presence explicitly and raise `HTTPException(400)` when absent, giving a controlled error detail rather than relying on FastAPI's default message.

## Alternatives considered

- **Server-derived fallback key** (UNK-01 option 2): derive `f"{consumer_id}:{event_id}:{current_attempt}"` when absent. Rejected as the default — it reintroduces server-side identity coupling; the recommended model rejects keyless NACKs so the contract is explicit. The fallback remains an available branch if the owner switches later.
- **Mandatory `Query(...)` vs explicit check:** an explicit `default=""` + presence check yields a controlled 400 detail matching the route's existing style (cf. `_do_ack`); a bare `Query(...)` relies on FastAPI's generic message.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Add `idempotency_key: str = Query(default="")` to the `nack()` signature (after `consumer_id`).
2. After the existing `consumer_id` validation, add the UNK-01 presence check: raise `HTTPException(status_code=400, detail="idempotency_key is required for NACK")` when the key is empty.
3. In `_nack_and_promote()`, remove the local `import uuid` and `attempt_id = str(uuid.uuid4())`; pass `last_nack_attempt=idempotency_key` (new) to `_nack_event(...)`.
4. Run the validation sequence.

### Method

Current `nack()` (ack_route.py:124-155) reads `event_id` (`Query(default="")`) and `consumer_id` (`Query(...)`) and validates both. `_nack_and_promote()` (ack_route.py:157-206) mints `attempt_id = str(uuid.uuid4())` at ack_route.py:166 and calls `_nack_event(db, event_id, consumer_id, last_nack_attempt=attempt_id)` at ack_route.py:167-169. Replace that per-request UUID with the caller key.

```python
# ack_route.py — nack() signature + keyless gate (edit existing nack())
async def nack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(...),
    idempotency_key: str = Query(default=""),   # (new) caller-supplied NACK idempotency key
    _principal: Principal | None = None,
    _identity: Principal | None = None,
) -> dict[str, Any]:
    ...
    if not consumer_id:
        raise HTTPException(status_code=400, detail="consumer_id is required for NACK")
    # UNK-01 (recommended): reject a NACK without an idempotency key
    if not idempotency_key:   # (new)
        raise HTTPException(status_code=400, detail="idempotency_key is required for NACK")
    ...
```

```python
# ack_route.py — _nack_and_promote() key source (edit existing function body)
def _nack_and_promote() -> tuple[str, int | None, bool]:
    """Nack an event and promote to DLQ if max retries exceeded.
    ...
    """
    # REMOVED: local `import uuid` and `attempt_id = str(uuid.uuid4())`
    # REQ-002: use the caller-supplied idempotency key, not a per-request UUID
    nack_result = _nack_event(
        db, event_id, consumer_id, last_nack_attempt=idempotency_key   # (new)
    )
    ...
```

### Details

- **`REQ-002` (no per-request UUID):** the `import uuid` (ack_route.py:164) and `attempt_id = str(uuid.uuid4())` (ack_route.py:166) are removed; `last_nack_attempt` carries the caller key. `_nack_event` (`delivery_repo.py::nack_event`) compares it against the remembered key.
- **`REQ-001` (key passes route→repo unchanged):** `idempotency_key` (new) flows from the query into `last_nack_attempt` with no transformation.
- **`REQ-006` / UNK-01:** the presence gate enforces the recommended reject-400 contract. If the owner later adopts the server-derived fallback, replace the gate with the derived key and document it — do not leave keyless NACKs silently passing an empty key.
- **Preserve `INV-13`:** the DLQ-promotion tail (ack_route.py:190-203, `is_promotable`/`promote_single`) is unchanged.

## Compatibility considerations

- New mandatory query parameter `idempotency_key` (new): external subscribers must send it. Existing `/nack` callers that omit it now receive 400 — the seq 06 endpoint tests cover the new contract. This is the intended contract enforcement (`REQ-002`).
- `nack()` return shape is unchanged.

## Security considerations

- No new credentials or secrets. The 400 detail names the parameter, not any sensitive value.

## Rollback considerations

- Revert the `ack_route.py` edit (`git checkout scripts/eventbus/ack_route.py`) restores the per-request UUID behavior. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `nack()` + `_nack_and_promote()` | Integration: `/nack` with repeated vs distinct keys; keyless → 400 | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` | Same key repeat = no-op 200; distinct = counted once; keyless = 400 |
| DLQ promotion unchanged | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py` | `INV-13` promotion unchanged |
| `ack_route.py` static | Complexity/dead code/security | `uv run radon cc scripts/eventbus/ack_route.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | Complexity contained; bandit/vulture clean |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `nack()` reads `idempotency_key` (new) from the query and rejects an empty key with 400 (UNK-01 recommended).
- `_nack_and_promote()` contains no `uuid.uuid4()` call and passes the caller key as `last_nack_attempt` to `_nack_event()`.
- DLQ promotion (`is_promotable`/`promote_single`) is unchanged.
- ruff, mypy, bandit, vulture, lint-imports pass; `test_eventbus_ack_endpoint.py` asserts the new contract.

## Out of Scope

- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- Dedup-scope schema (`scripts/eventbus/schema.sql`, seq 04).
- Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).
- UNK-02 key origin / UNK-03 dedup scope values — recorded, not prescribed here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `idempotency_key` (new) query param, enforce UNK-01 keyless 400, pass caller key through as `last_nack_attempt` (drop per-request UUID) | Pending | — | — | UNK-01 reject-400 is the recommended default (recorded) |
| 2 | Add/update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `scripts/eventbus/ack_route.py`
