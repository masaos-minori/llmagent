## Goal

Record the result and wall-clock time of every `_dlq_loop` cycle on `app.state`, so `/health` can report the last DLQ sweep outcome instead of a permanently `running` task that may be failing silently (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Each cycle is one sweep + `process_outbox` + reconciliation pass; its "result" is `ok` when the try body completes and `failed` when the per-cycle `except (OSError, sqlite3.Error)` fires (the existing swallow point).
- The recorded time is an ISO-8601 UTC string via the shared `now_iso()` helper (`eventbus.json_utils`), matching the format `/health` and other EventBus code already emit.
- `app.state` is process-local and in-memory, so the value resets to `not_run` (new) on restart (resolves UNK-05 without a schema change); `/health` must treat a missing/`not_run` (new) value as "no sweep yet", not as an error.
- The assignment is a single immutable per-cycle write (one str, one optional str), so the race with the concurrent `/health` read noted in the Plan's Risks is benign — FastAPI route handlers run on the same event loop and the attribute bind is atomic.

## Design decisions
- Store two attributes keyed for readability: `app.state.last_dlq_cycle_result` (new) (`"ok"` / `"failed"` / `"not_run"`) and `app.state.last_dlq_cycle_time` (new) (ISO-8601 str or `None`). `/health` reads both by name.
- Initialize both in `lifespan` before `app.state.dlq_task` is created, so the very first `/health` (before any cycle) reports `not_run` (new)/`None` instead of raising `AttributeError`.

## Alternatives considered
- Deriving the sweep result from `dlq_task.status == "running"` alone: rejected — that is exactly what hides a perpetually-failing task; the explicit result string carries the fail-closed signal `/health` needs.
- Persisting `last_dlq_cycle_time` (new) in `dlq_outbox` or a status table: rejected — a schema change and `user_version` bump; the Plan keeps this in-memory only.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Add the `now_iso` import next to the other `eventbus.*` imports.
2. In `lifespan`, initialize the two `app.state` keys just before `app.state.dlq_task = asyncio.create_task(_dlq_loop(app))`.
3. In `_dlq_loop`, record the cycle result at the end of the successful try body (before `await asyncio.sleep(_DLQ_INTERVAL)`) and in the `except` block.
4. Do not rename or remove any existing `app.state` key.

### Method
1. Add the import (after the `eventbus.route_helpers` import block, before `subscribe_route`):
```python
from eventbus.json_utils import now_iso
```
2. In `lifespan`, insert before the `dlq_task` creation (line ~93):
```python
    # Last DLQ loop-cycle outcome and time, reported by /health (REQ-005).
    # Initialized so the first /health before any sweep reads 'not_run', not a KeyError.
    app.state.last_dlq_cycle_result = "not_run"
    app.state.last_dlq_cycle_time = None
```
3. In `_dlq_loop`, at the end of the try body, immediately before `await asyncio.sleep(_DLQ_INTERVAL)`:
```python
            app.state.last_dlq_cycle_result = "ok"
            app.state.last_dlq_cycle_time = now_iso()
```
   And in the existing except block:
```python
        except (OSError, sqlite3.Error):
            logger.exception("dlq_loop error")
            app.state.last_dlq_cycle_result = "failed"
            app.state.last_dlq_cycle_time = now_iso()
```

### Details
- The success-path assignment sits inside the try, after reconciliation, so a cycle that completes all three phases reports `ok`; any exception short-circuits to the except path and reports `failed`.
- `now_iso()` returns an ISO-8601 UTC timestamp; store it verbatim so `/health` can surface it unchanged.
- Keep the two writes adjacent to their outcomes so the result and its time never desynchronize.
- The new import does not cross the `eventbus-is-isolated` boundary (`json_utils` is an internal EventBus helper already imported by `dlq_repo`).

## Compatibility considerations
- Additive: two new `app.state` keys; no existing key renamed or removed. Existing consumers of `app.state` (broker, db, config, tasks) are untouched.
- `/health` gains fields that read these keys; until `/health` is wired (sibling procedure), the keys are inert writes.
- No change to shutdown: `dlq_task` is still cancelled the same way; the new keys carry no lifecycle responsibility.

## Security considerations
- The recorded values are operational telemetry (a status string and a timestamp); no secrets, credentials, or PII. They appear in the `/health` response like every other degraded reason.

## Rollback considerations
- N/A: revert the commit; the two state keys and the import are isolated to this file.

## Validation plan
- `uv run ruff format scripts/eventbus/app.py`, `uv run ruff check scripts/eventbus/app.py` — clean (the added import sorts into the `eventbus.*` group).
- `uv run mypy scripts/eventbus/app.py` — passes.
- `uv run lint-imports` — no new boundary crossing.
- `uv run python tools/check_module_size.py` — module stays under the size gate.
- `uv run pytest tests/eventbus -v` — existing shutdown and DLQ outbox tests still pass; the `test_eventbus_health.py` companion asserts the recorded result surfaces in `/health` (sibling procedure).

## Completion criteria
- `lifespan` initializes `last_dlq_cycle_result = "not_run"` and `last_dlq_cycle_time = None` before the DLQ task starts.
- `_dlq_loop` sets `last_dlq_cycle_result` (new) to `"ok"` at the end of a successful cycle and `"failed"` in the except block, each with `now_iso()` for `last_dlq_cycle_time` (new).
- `ruff format`, `ruff check`, `mypy`, `lint-imports`, and `check_module_size.py` pass; `tests/eventbus` passes.

## Out of Scope
- Reading these keys in `/health` — that is the sibling procedure for `scripts/eventbus/health_route.py`.
- Counting terminal-failed outbox rows — that is the sibling procedure for `scripts/eventbus/dlq_repo.py`.
- Any persistence of `last_dlq_cycle_time` (new) across restarts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record each `_dlq_loop` cycle result and time on `app.state` (REQ-005) | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` — record the result and time of each DLQ loop cycle for `/health`
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `scripts/eventbus/app.py`
