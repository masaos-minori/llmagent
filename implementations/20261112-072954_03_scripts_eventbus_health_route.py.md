## Goal

Report, from `/health`, the number of terminal-failed `dlq_outbox` rows and the result and time of the last `_dlq_loop` cycle, adding two degraded reasons (`dlq_outbox_failed` (new), `dlq_sweep_failing` (new)) that return HTTP 503 like every existing reason while leaving `liveness`, `readiness`, and role checks unchanged (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/eventbus/dlq_repo.py` gains `count_failed_outbox(db)` (sibling procedure, seq 01); import it here.
- `scripts/eventbus/app.py` records `app.state.last_dlq_cycle_result` (`"ok"` / `"failed"` / `"not_run"`) and `app.state.last_dlq_cycle_time` (ISO-8601 str or `None`) (sibling procedure, seq 02).
- `request.app.state` may lack those keys before the first cycle in a resumed process; read them with `getattr(..., default)` so a missing key never raises `AttributeError`.
- The count query runs on the already-open `get_db(request)` connection under `run_with_db_lock`; a `sqlite3.Error` there must not mask the existing `db_unavailable` handling — on failure set the count to `None` and omit the reason.
- `terminal_failed_outbox` (new) is `int | None` in the response; `last_dlq_sweep` (new) is `{"result": str, "time": str | None}`.

## Design decisions
- Compute `terminal_failed` once, near the other degraded-reason inputs, and append `dlq_outbox_failed` (new) only when it is greater than zero; append `dlq_sweep_failing` (new) only when `last_result == "failed"`. Both land in `degraded_reasons`, so `status_code` becomes 503 automatically and `liveness`/`readiness` (computed separately) are untouched.
- Expose the values as two new top-level response fields so `eventbus_10` can document them and the test can assert them without reading private state.

## Alternatives considered
- Reading `app.state` keys directly with attribute syntax: rejected — a resumed process whose DLQ task has not yet recorded a cycle could raise `AttributeError`; `getattr` with defaults is safe.
- Wrapping the count in the same `run_with_db_lock(_check)` block: rejected — that block only runs `check_db`; the count is a separate indexed read and belongs in its own guarded call so its failure is handled independently.

## Implementation
### Target file
`scripts/eventbus/health_route.py`

### Procedure
1. Import `count_failed_outbox` from `eventbus.dlq_repo` (add to the `from eventbus.*` imports).
2. In `health_check`, after `degraded_reasons.extend(capacity_degraded_reasons)` (line 105) and before the tiered health checks (line 107), insert the terminal-failed count + last-sweep read and the two new reason appends.
3. Add the two new fields to the returned `JSONResponse` content dict, after `"dlq_task": dlq_task_status,` (line 117).
4. Do not rename or remove any existing field, key, or reason.

### Method
1. Add the import (after the `route_helpers` import block, before `logger`):
```python
from eventbus.dlq_repo import count_failed_outbox
```
2. Insert after line 105 (`degraded_reasons.extend(capacity_degraded_reasons)`):
```python
    # Terminal-failed outbox rows and a failing sweep cycle (REQ-005): real
    # failures, HTTP 503 like every other degraded reason, outside liveness and
    # readiness. A count-query failure reports db_unavailable (above) and omits
    # the count rather than raising.
    terminal_failed = None
    try:
        terminal_failed = await run_with_db_lock(
            lambda: count_failed_outbox(db)
        )
    except sqlite3.Error:
        terminal_failed = None
    last_result = getattr(request.app.state, "last_dlq_cycle_result", "not_run")
    last_time = getattr(request.app.state, "last_dlq_cycle_time", None)
    if terminal_failed and terminal_failed > 0:
        degraded_reasons.append("dlq_outbox_failed")
    if last_result == "failed":
        degraded_reasons.append("dlq_sweep_failing")
```
3. Add to the response content (after `"dlq_task": dlq_task_status,`):
```python
            "terminal_failed_outbox": terminal_failed,
            "last_dlq_sweep": {"result": last_result, "time": last_time},
```

### Details
- `run_with_db_lock` runs the sync `count_failed_outbox` inside the DB lock via `asyncio.to_thread` and re-raises; the `except sqlite3.Error` catches that and sets `None`, so the route never propagates a count failure.
- `lambda: count_failed_outbox(db)` closes over the route's `db` (`get_db(request)`); no new argument is needed.
- `getattr` defaults (`"not_run"`, `None`) mean the very first `/health` before any sweep reports `last_dlq_sweep.result == "not_run"` and no `dlq_sweep_failing` (new) reason.
- The two new reasons are ordinary entries in `degraded_reasons`; they flow into `overall` (line 111) and `status_code` (line 112) unchanged, preserving the documented 503-for-any-degraded rule.
- No import crosses the `eventbus-is-isolated` boundary: `dlq_repo` is an internal EventBus module.

## Compatibility considerations
- Additive: two new response fields and two new possible entries in `degraded_reasons`. No existing field renamed or removed; existing consumers that ignore unknown fields are unaffected.
- The existing tests (`test_health_*`) do not assert an exact `degraded_reasons` equality for the healthy path except the capacity-only test (line 95: `== ["subscribers_at_capacity"]`); with a fresh DB `terminal_failed` is `0` and `last_result` is `"not_run"`, so neither new reason fires and that assertion still holds.
- `eventbus_10` documents the new fields and reasons (sibling procedure, seq 09).

## Security considerations
- Read-only count and operational telemetry (a status string, a timestamp); no secrets, credentials, or PII. The endpoint still requires `Role.MONITORING` (`require_role`), unchanged.

## Rollback considerations
- N/A: revert the commit; the import, the two state reads, the two reason appends, and the two response fields are isolated to this route.

## Validation plan
- `uv run ruff format scripts/eventbus/health_route.py`, `uv run ruff check scripts/eventbus/health_route.py` — clean (import sorts into the `eventbus.*` group).
- `uv run mypy scripts/eventbus/health_route.py` — passes.
- `uv run lint-imports` — no new boundary crossing.
- `uv run python tools/check_module_size.py` — module stays under the size gate.
- `uv run pytest tests/eventbus -v` — the companion `test_eventbus_health.py` asserts the count and both reasons surface and the status code stays 503 while `liveness`/`readiness` are unchanged; existing health/shutdown/outbox tests still pass.

## Completion criteria
- `health_route.py` imports `count_failed_outbox`, reads `last_dlq_cycle_result`/`last_dlq_cycle_time` via `getattr`, appends `dlq_outbox_failed` (new) when the count is `> 0` and `dlq_sweep_failing` (new) when the last result is `"failed"`, and returns `terminal_failed_outbox` (new) and `last_dlq_sweep` (new) in the body.
- Every degraded reason (including the two new ones) yields HTTP 503; `liveness` and `readiness` are computed as before and unaffected.
- `ruff format`, `ruff check`, `mypy`, `lint-imports`, `check_module_size.py` pass; `tests/eventbus` passes.

## Out of Scope
- Adding `count_failed_outbox` to `dlq_repo.py` — sibling procedure (seq 01).
- Recording each `_dlq_loop` cycle result on `app.state` — sibling procedure (seq 02).
- Documenting the new fields/reasons in `eventbus_10`/`eventbus_03` and regenerating `eventbus_08` — sibling procedures (seq 09, 10, 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` — report terminal-failed outbox count and last-sweep result/time from `/health` with two new 503 degraded reasons
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `scripts/eventbus/health_route.py`
