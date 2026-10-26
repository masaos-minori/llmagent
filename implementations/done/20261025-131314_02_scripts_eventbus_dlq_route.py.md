## Goal

Remove all direct SQLite access from `scripts/eventbus/dlq_route.py` (`REQ-003`) and fetch the DLQ list under a single global-lock acquisition so `total` and `items` describe one consistent snapshot (`REQ-004`).

## Scope

- Modify `scripts/eventbus/dlq_route.py`: map the typed result from `redeliver_event()` to HTTP 200/404/409 with no follow-up SQL, and combine `dlq_list` count and fetch into one `run_with_db_lock` call.
- Do not modify `scripts/eventbus/dlq_repo.py` — the typed result is defined there by the seq-01 procedure.

## Assumptions

- The typed result (`RequeueResult (new)`) is defined by the seq-01 procedure (`scripts/eventbus/dlq_repo.py`) and imported here; it will exist when this row implements. Its `status` carries one of four string values (success, not_found, not_in_dlq, already_redelivered); `new_event_id` and `new_seq` come from the same atomic result.
- The route keeps importing `count_dlq`, `fetch_dlq`, and `redeliver_event` from `eventbus.db` unchanged; only the new RequeueResult import is added.
- `run_with_db_lock` (`scripts/eventbus/route_helpers.py`) serializes its closure under the global DB lock, so running `count_dlq()` and `fetch_dlq()` inside one closure yields one consistent snapshot.

## Design decisions

- **HTTP mapping from the typed result.** Map `result.status`: success → 200 with `new_event_id`/`new_seq`; not_found → 404; not_in_dlq / already_redelivered → 409. This removes the route's existence re-query that currently distinguishes 404 from 409 (`REQ-003`).
- **Single-lock DLQ snapshot.** `dlq_list` runs one `run_with_db_lock` closure that calls both `count_dlq()` and `fetch_dlq()`, returning `total` and `items` from one snapshot (`REQ-004`).

## Alternatives considered

- Keeping the 404/409 reclassification in the route via a second unlocked `db.execute(...)`: rejected — that is the unlocked follow-up SQL this Plan removes (`REQ-003`).
- Returning `new_seq` from a separate query after `redeliver_event()`: rejected — `new_seq` must come from the same atomic result as `new_event_id` (`REQ-003`).

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Add the `RequeueResult (new)` import from `eventbus.dlq_repo`.
2. In `dlq_requeue`, consume the typed result from `redeliver_event()` and map `status` → HTTP 200/404/409; remove the `db.execute(...)` new-sequence lookup and the 404/409 reclassification.
3. In `dlq_list`, combine the count and fetch into one `run_with_db_lock` closure.

### Method

```python
from eventbus.db import count_dlq, fetch_dlq, redeliver_event
from eventbus.dlq_repo import RequeueResult (new)  # defined by the seq-01 procedure
from eventbus.route_helpers import (
    ERR_EVENT_NOT_FOUND,
    ERR_EVENT_NOT_IN_DLQ,
    get_db,
    run_with_db_lock,
)


async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support (one snapshot)."""
    db = get_db(request)

    def _snapshot() -> dict[str, Any]:
        """Count and fetch under one lock acquisition so total/items match."""
        total: int = count_dlq(db)
        rows: list = fetch_dlq(db, limit=limit, offset=offset)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [dict(r) for r in rows],
        }

    return await run_with_db_lock(_snapshot)


async def dlq_requeue(
    request: Request,
    event_id: str,
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue."""
    db = get_db(request)

    def _redeliver() -> RequeueResult:
        """Redeliver a single event from the DLQ using the lineage model."""
        return redeliver_event(db, event_id)

    result = await run_with_db_lock(_redeliver)
    if result.status == "success":
        logger.info("dlq redelivered event_id=%s -> %s", event_id, result.new_event_id)

        # Emit privileged-action audit record
        log_privileged_action(
            consumer_id="",
            request_id=request.state.request_id,
            route="/dlq/requeue",
            target=event_id,
            detail="",
        )

        return {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": result.new_event_id,
            "new_seq": result.new_seq,
        }
    if result.status == "not_found":
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
```

### Details

- The response keeps the HTTP contract fields `requeued`, `new_event_id`, and `new_seq`; `new_seq` now comes from the typed result instead of a follow-up `SELECT seq`.
- `log_privileged_action` stays on the success path only (unchanged).
- No `db.execute(...)` remains anywhere in the file (`REQ-003`).

## Compatibility considerations

- The HTTP contract is unchanged: status codes 200/404/409 and response fields `requeued`, `new_event_id`, `new_seq`. The route now depends on `redeliver_event()` returning the `RequeueResult (new)` from the seq-01 procedure; implement the two procedures in order.
- `scripts/eventbus/db.py` still re-exports `redeliver_event`, `count_dlq`, and `fetch_dlq`; the route's `eventbus.db` import is unchanged.

## Security considerations

- Removing the two unlocked `db.execute(...)` calls closes the window where the route read state outside the global DB lock and reclassified 404/409 from an unlocked read (`REQ-003`).

## Rollback considerations

- Revert to the previous route: `(bool, str | None)` mapping with the two `db.execute(...)` follow-up calls (new-seek lookup and 404/409 reclassification) and the double `run_with_db_lock` in `dlq_list`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_route.py` | Integration: requeue HTTP mapping (200/404/409), DLQ snapshot consistency | `uv run pytest tests/eventbus/` | 200/404/409 correct; `total`/`items` one snapshot |
| `scripts/eventbus/dlq_route.py` | Static: no `db.execute` remaining | `rg "db.execute" scripts/eventbus/dlq_route.py` | Zero matches |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- `scripts/eventbus/dlq_route.py` contains no `db.execute(...)` (`REQ-003`).
- `dlq_requeue` maps the typed result to 200/404/409 from the locked result alone, with `new_seq` from the same atomic result.
- `dlq_list` returns `total` and `items` from one lock acquisition (`REQ-004`).

## Out of Scope

- Typed-result definition, transaction ownership, and parameterized timestamp — handled by the sibling procedure for `scripts/eventbus/dlq_repo.py` (`REQ-001`, `REQ-002`, `REQ-005`).
- Requeue delivery semantics and DLQ file reconciliation (issue M-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove direct-SQL route behavior and combine the DLQ lock (`scripts/eventbus/dlq_route.py`) | Pending | — | — | Path B |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (no-direct-SQL route, 404/409 from typed result), `REQ-004` (single-lock DLQ snapshot)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `scripts/eventbus/dlq_route.py`
