## Goal

Make the DLQ requeue transition atomic, lock-bound, and free of a SQL-injection surface by having `redeliver_event()` own the whole state change — update, insert, sequence lookup, commit/rollback, and 404/409 classification — and return a typed result instead of the `(bool, str | None)` tuple (`REQ-001`, `REQ-002`, `REQ-005`).

## Scope

- Modify `scripts/eventbus/dlq_repo.py`: add a `RequeueResult` (new) dataclass and refactor `redeliver_event()` to run update+insert+seq-lookup+commit/rollback in one explicit transaction, classify 404/409 inside the locked operation, and bind the requeue timestamp as a parameter.
- Do not modify `scripts/eventbus/db.py` — keep `redeliver_event` re-exported unchanged; do not add a new function to the facade.

## Assumptions

- The optional `now` argument of `redeliver_event()` is retained and bound as data (no production caller passes it; keeping it avoids a breaking API change to the re-exported symbol) — resolves `UNK-01`.
- The shared connection's default `isolation_level` is preserved; explicit `conn.rollback()` on failure paths is what prevents transaction carry-over on the shared connection.
- `get_seq()` in `scripts/eventbus/event_repo.py` returns the new row's sequence inside the same transaction.
- The `run_with_db_lock` closure supplied by `scripts/eventbus/dlq_route.py` already holds the global DB lock, so the refactor performs no additional locking.

## Design decisions

- **Typed result shape.** Define a `RequeueResult` (new) dataclass in `scripts/eventbus/dlq_repo.py` with a `status` field carrying one of four new string values (success, not_found, not_in_dlq, already_redelivered) plus `original_event_exists: bool`, `already_redelivered: bool`, `new_event_id: str | None`, `new_seq: int | None`. The route maps success → 200, not_found → 404, and the two not-in-active-queue outcomes → 409, preserving the HTTP contract while removing the route's need to re-query.
- **Transaction ownership.** Within the existing `run_with_db_lock` closure, execute: concurrency guard (`redelivered_from` existence check) → conditional `UPDATE` → if `rowcount == 0`, classify via a single existence read and `rollback()` the no-match `UPDATE` → else `INSERT ... SELECT` + `get_seq()` → `commit()`. Wrap in `try/except sqlite3.Error` → `rollback()` → re-raise, guaranteeing no dangling implicit transaction on the shared connection.

## Alternatives considered

- Returning a wrapped tuple `(RequeueResult (new), extra)` instead of the dataclass alone: rejected — the dataclass carries every field the route needs and keeps the return a single value.
- Leaving the 404/409 reclassification in the route: rejected — that is the unlocked follow-up SQL this Plan removes (`REQ-003`); the classification must move into the locked repository operation.

## Implementation

### Target file

`scripts/eventbus/dlq_repo.py`

### Procedure

1. Add the `RequeueResult` (new) dataclass near the top of the module (after the imports / column constants).
2. Replace the body of `redeliver_event()` so it owns update+insert+seq-lookup+commit/rollback in one transaction, classifies 404/409, and binds the timestamp as a parameter.
3. Keep the function signature `redeliver_event(conn, event_id, now=None)` and the `redeliver_event` re-export in `scripts/eventbus/db.py` unchanged.

### Method

```python
from dataclasses import dataclass


@dataclass
class RequeueResult:  # (new) — replaces the (bool, str | None) return
    status: str
    original_event_exists: bool
    already_redelivered: bool
    new_event_id: str | None
    new_seq: int | None


def redeliver_event(
    conn: sqlite3.Connection, event_id: str, now: str | None = None
) -> RequeueResult:
    # Concurrency guard: already-redelivered check (unchanged).
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return RequeueResult("already_redelivered", True, True, None, None)

    # Timestamp computed in Python and bound as data (no f-string interpolation).
    ts = now if now is not None else now_iso()
    new_event_id = uuid.uuid4().hex
    try:
        cur = conn.execute(
            f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 "
            f"WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column constants
            (event_id,),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return RequeueResult("not_found", False, False, None, None)
        conn.execute(
            f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, redelivered_from) "
            f"SELECT ?, topic, payload, producer, ?, ? "
            f"FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column constants
            (new_event_id, ts, event_id, event_id),
        )
        new_seq = get_seq(conn, new_event_id)
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return RequeueResult("success", True, False, new_event_id, new_seq)
```

- Import `now_iso` from `eventbus.json_utils` and `get_seq` from `eventbus.event_repo` (deferred imports inside the function or module-level; match the existing deferred-import style used for `eventbus._constants`).
- The `INSERT` now binds `ts` as a `?` parameter instead of interpolating the `strftime(...)` fragment through an f-string (`REQ-005`).
- `new_seq` is read inside the same transaction via `get_seq()` so `new_event_id` and `new_seq` describe one atomic result.

### Details

- The four `status` values are new string literals owned by this Plan: success → 200 with `new_event_id`/`new_seq`; not_found → 404; not_in_dlq / already_redelivered → 409.
- The not_in_dlq outcome is available to the route if it ever needs to distinguish "row exists but dlq_at IS NULL" from "already redelivered"; both currently map to 409.
- No new function is added to `scripts/eventbus/db.py`; `redeliver_event` stays re-exported unchanged (`UNK-02` resolved).

## Compatibility considerations

- Changing `redeliver_event()`'s return type from `(bool, str | None)` to `RequeueResult` (new) is a runtime-facing interface change (Path B). The only production caller is `scripts/eventbus/dlq_route.py`; `rg` confirms no other caller in `scripts/` or `tests/`. The route must be updated to consume the typed result (`REQ-003`) — see the sibling procedure for `dlq_route.py`.
- `scripts/eventbus/db.py` keeps re-exporting `redeliver_event` with the same name; callers importing through the facade are unaffected by the name, only by the return shape (handled by the route).

## Security considerations

- Removing the `strftime(...)` f-string interpolation and binding the timestamp as a `?` parameter eliminates the latent SQL-injection boundary (`REQ-005`). Column names remain module-level constants (unchanged `# nosec B608` justification).
- `conn.rollback()` on every failure path prevents an uncommitted `dlq_requeue_count` update from being committed by a later request on the shared connection.

## Rollback considerations

- Revert the `redeliver_event()` refactor and the `RequeueResult` (new) dataclass to the previous `(bool, str | None)` implementation.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Unit: failure injection (insert/commit/constraint), rollback leaves no active transaction, connection reusable | `uv run pytest tests/eventbus/` | All pass; no uncommitted state carried across requests |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean |

## Completion criteria

- `redeliver_event()` returns a `RequeueResult` (new) whose `new_event_id` and `new_seq` come from the same atomic result (`REQ-001`).
- A failed requeue rolls back the original-row update and leaves no active transaction; a later request on the same connection succeeds (`REQ-002`).
- The requeue timestamp is bound as a SQL parameter; the default path uses `now_iso()`; an explicit `now` is stored as data (`REQ-005`).

## Out of Scope

- Route HTTP mapping and removal of direct SQLite access — handled by the sibling procedure for `scripts/eventbus/dlq_route.py` (`REQ-003`, `REQ-004`).
- Requeue delivery semantics and DLQ file reconciliation (issue M-02).
- Schema changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the typed-result refactor in `scripts/eventbus/dlq_repo.py` | Pending | — | — | Path B |
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
- **Requirement ID**: `REQ-001` (typed result), `REQ-002` (atomic transaction/rollback), `REQ-005` (parameterized timestamp)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `scripts/eventbus/dlq_repo.py`
