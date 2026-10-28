# Procedure: re-check the shutdown flag after acquiring the DB lock

## Goal

Make a worker that was admitted before shutdown but acquires the lock after the flag is set refuse to run SQL (Plan REQ-001).

## Scope

- Modify only `scripts/eventbus/route_helpers.py`.
- In scope: the body of `_locked()` inside `run_with_db_lock`.
- Out of scope: the lock-wait and query-duration statements (another Plan), `app.py`, `db_conn.py`, tests and docs.

## Assumptions

- The flag is a plain module-level bool read under the GIL; a worker that reads `False` after acquiring the lock finishes before shutdown can acquire it.
- The pre-check before `asyncio.to_thread` stays as the fast path.
- Overlap (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` (timing statements around the lock acquisition) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Metrics section); `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived) targeted `scripts/eventbus/app.py` (ACK/NACK wiring only). This procedure edits the shutdown re-check, the shutdown state and the Shutdown section.

## Design decisions

- Raise the same `RuntimeError("eventbus shutting down: refusing new DB work")` as the pre-check so callers handle one error.
- Place the guard before `bump_active_db_user()` so a refused worker never touches the counter.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/route_helpers.py`

### Procedure

- Inside `_locked()`, right after `with get_db_lock():` and before `lock_hold_start = time.monotonic()` / `bump_active_db_user()`, add `if is_shutting_down(): raise RuntimeError("eventbus shutting down: refusing new DB work")`.
- Leave the pre-check, the `try`/`finally` structure and the metric statements exactly as they are (the metric statements belong to the metrics Plan).

### Method

Insert a three-line guard; no signature or import change (`is_shutting_down` is already imported in the function).

### Details

- Raising inside the `with` block releases the lock through the context manager, so shutdown can acquire it next.
- `func` is never called on this path, so no SQL touches the closed connection.

## Compatibility considerations

- A request in flight at shutdown now fails with the documented shutdown error instead of a `sqlite3.ProgrammingError`; no other behavior changes.

## Security considerations

- Fail-closed: no SQL runs after shutdown began.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_shutdown.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/route_helpers.py`; `uv run ruff check scripts/eventbus/route_helpers.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/route_helpers.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- A worker queued on the lock before shutdown raises the shutdown `RuntimeError` after the lock frees and `func` is not called.

## Out of Scope

- Counter role (row 2), shutdown state (row 3), tests and docs.

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
- **Requirement ID**: REQ-001 (post-lock shutdown re-check in `run_with_db_lock`)
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115236
- **Related target files**: scripts/eventbus/route_helpers.py
