# Implementation Procedure: app.py outbox + reconcile wiring in _dlq_loop

## Goal

Run the outbox consumer and the (now extended) reconciliation inside the existing
`app.state.dlq_task` loop each cycle, so pending generation resumes after restart and the
shutdown join semantics stay unchanged (REQ-004, REQ-006, REQ-008; plan AC-3, AC-6).

## Scope

**In scope:**
- `scripts/eventbus/app.py::_dlq_loop` (`app.py:139-158`): two new steps after the sweep.

**Out of scope:**
- Startup/shutdown sequence (`app.py:95-136`) — untouched; the task already joins before the
  lock-guarded close (ebshutdown002), and outbox work rides the same task (REQ-008).
- `_DLQ_INTERVAL` value, `sweep_orphans` call.

## Assumptions
- Verified at HEAD `124e340b4`: `app.py:80` `app.state.dlq_task = asyncio.create_task(_dlq_loop(app))`;
  `_dlq_loop` sweep via `await run_with_db_lock(_sweep)` at 146-151; cancel+join at 107-110.
- `reconcile_missing_dlq_files` is today called only from tests (`test_eventbus_dlq.py:759+`);
  docs-03 already describes scheduled reconciliation ("Reconciliation runs on a schedule").
  This wiring makes that documented claim true — the plan Background states this Plan wires
  the extension into the loop.
- Rows 03/07 provide `process_outbox(db, deadletter_dir, cfg, run_locked)` and the retry config.

## Design decisions
- Cycle order per plan Design: `sweep_orphans` → `process_outbox` (new) → `reconcile_missing_dlq_files`.
  Sweep is now pure-DB; outbox interleaves its own locked DB steps (`run_locked` (new) =
  `route_helpers.run_with_db_lock`, injected) with file writes outside any lock hold;
  reconcile keeps its existing "caller holds `run_with_db_lock`" contract (its file writes
  are rare rebuilds of already-committed state — bounded, and its design deliberately reuses
  the sweep's lock pattern).
- `process_outbox` (new) is awaited directly (it is async and acquires the lock per DB step
  internally); reconcile runs as one `await run_with_db_lock(...)` call.
- Nonzero outbox/reconcile counts are logged at warning level (operator visibility; the
  report dict from row 03 is logged as-is).
- The per-cycle `except (OSError, sqlite3.Error)` guard around the cycle body stays; an
  outbox-internal error never kills the task (REQ-006: pending rows are retried next cycle).
- Reconcile runs every 60s cycle at current EventBus DLQ volumes; cadence tuning is explicitly
  deferred to UNK-02 operational observation (no new knob in this Plan).

## Alternatives considered
- A separate asyncio task for the outbox: rejected — the plan's shutdown criterion (REQ-008,
  AC-6) is satisfied for free by riding the existing `dlq_task` join; a second task would
  extend the ebshutdown002 sequence.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Extend the `from eventbus.dlq import ...` line (currently `sweep_orphans` only, `app.py:40`)
   with `process_outbox` (new), `reconcile_missing_dlq_files`.
2. In `_dlq_loop`, after the sweep block: `await process_outbox(db, cfg.deadletter_dir, cfg,
   run_with_db_lock)`; then `result = await run_with_db_lock(lambda:
   reconcile_missing_dlq_files(db, cfg.deadletter_dir))` and log when any count is nonzero.

### Method
Two additive calls inside the existing try block; no lifecycle change.

### Details
- `run_with_db_lock` is already imported in `app.py` for the sweep.
- Type the injected runner parameter in row 03 as `Callable[[Any], Awaitable[Any]]` so mypy
  accepts the import.

## Compatibility considerations
- Deployed EventBus (port 8015, live pid holds `/opt/llm/db/eventbus.sqlite`) needs the
  service restart in Phase 5 with the migration applied first (plan Risk; deploy checklist).

## Security considerations
- Logs carry counts only, never payloads.

## Rollback considerations
- Removing the two calls reverts to today's loop; outbox rows simply stay pending (harmless).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_dlq_outbox.py tests/eventbus/test_eventbus_shutdown.py`
  — restart-with-pending-rows (AC-3) and in-flight-join (AC-6, row 11) run through the real
  `TestClient` lifespan so this wiring is exercised, not just unit-mocked.

## Completion criteria
- Every 60s cycle consumes due outbox rows and reports reconciliation classes; shutdown joins
  the in-flight cycle before the DB close; no new failure can stop the task.

## Out of Scope
- Outbox internals (row 03), config (row 07), shutdown sequence (unchanged by design).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import + two loop calls | Completed | 20261031-074813 | 20261031-074813 | After rows 03/07 _dlq_loop: sweep -> process_outbox -> reconcile with warning logs |
| 2 | Run outbox + shutdown tests | Completed | 20261031-074813 | 20261031-074813 | shutdown join unchanged and proven by row 11 test |

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
- **Requirement ID**: `REQ-004`, `REQ-006`, `REQ-008`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/app.py`