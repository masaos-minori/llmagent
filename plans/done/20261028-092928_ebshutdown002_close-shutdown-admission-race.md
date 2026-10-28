## Goal
- Make a worker that was admitted before shutdown but acquires the DB lock after shutdown began refuse to run SQL, so no SQL executes on the shared connection after shutdown closed it.

## Priority
Medium

## Scope
- **In-Scope**:
  - Re-check the shutdown flag inside `run_with_db_lock()`'s locked section, before `func()` runs.
  - State the role of the active-user counter (observability only; not a shutdown gate) in its docstrings.
  - Clear `app.state.db` after `_shutdown_lifespan()` closes it, so later access fails explicitly.
  - Deterministic regression tests for the queued-worker, in-flight-sweep and in-flight-request cases.
  - Align the shutdown text in the EventBus operations doc with the implemented behavior.
- **Out-of-Scope**: connection pooling or per-worker connections; deployment readiness checks (EVENTBUS-022 as the eventbus004 plan defines it); sweep scheduling; the DLQ sweep logic; the bounded lock-acquire timeout; removing the active-user counter.
- **Dependencies**: `issues/20261027-155849_ebmetrics006_correct-db-timing-health.md` also edits `_locked()` in `run_with_db_lock()`; implement the two in sequence and rebase the later one. The `ebcompat002` Plan (`plans/done/20261027-120858_ebcompat002_decide-eventbus-db-facade.md`) is already consumed, but its implementation procedures are still `Pending` and may change the imports inside `run_with_db_lock()`; the guard added here does not depend on those imports.

## Background
`set_shutdown_flag()` in `scripts/eventbus/db_conn.py` documents that it makes `run_with_db_lock()` refuse new work for any thread still queued on the lock (REQ-004 of the eventbus004 Plan). `run_with_db_lock()` in `scripts/eventbus/route_helpers.py` reads the flag once, before `asyncio.to_thread(_locked)`. `_shutdown_lifespan()` in `scripts/eventbus/app.py` sets the flag, cancels the sweep task, acquires the same lock and closes `app.state.db`.

## Problem
A request passes the pre-check, its worker thread waits on the lock, shutdown acquires the lock and closes the connection, then the worker acquires the lock and runs SQL on the closed connection. The pre-check does not cover this interleaving, which contradicts the `set_shutdown_flag()` docstring.

## Reason for Change
The effect is bounded to requests in flight at shutdown (a failed request or `sqlite3.ProgrammingError`), so the priority is Medium. It is a contract violation that the eventbus004 work meant to close, and the guard is a few lines.

## Implementation Intent
Evaluate the shutdown state after the lock is acquired, in the same critical section that runs SQL, so a worker admitted earlier exits with the documented shutdown error and no SQL. Keep the existing pre-check as the fast path. Leave the lock-timeout and refuse-to-close behavior unchanged.

## Requirements
- `REQ-001`: `run_with_db_lock()` re-checks `is_shutting_down()` after acquiring the DB lock and raises the same `RuntimeError("eventbus shutting down: refusing new DB work")` without calling `func()`.
- `REQ-002`: The role of the active-user counter is stated in the `bump_active_db_user()` / `release_active_db_user()` docstrings: it is observability only and shutdown serializes through the lock instead. The counter is not removed.
- `REQ-003`: After `_shutdown_lifespan()` closes the connection it sets `app.state.db` to `None`, so `get_db()` raises its explicit `RuntimeError`; applied only if `uv run pytest tests/eventbus` stays green.
- `REQ-004`: A deterministic regression test forces the queued-worker interleaving with events or barriers (no sleeps) and fails on the current code; tests for the in-flight sweep and in-flight request cases exist and a second app lifecycle does not inherit a stale flag.
- `REQ-005`: The `set_shutdown_flag()` docstring and the Shutdown section of the EventBus operations doc describe the implemented behavior, including that a queued worker exits after the lock is acquired.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` | Add the post-lock shutdown re-check inside `_locked()` before `func()` | REQ-001 / AC-1 | `_locked()` takes `get_db_lock()`, calls `bump_active_db_user()` then `func()` with no flag check; the only `is_shutting_down()` call precedes `asyncio.to_thread` (checked in Step 3) | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/db_conn.py` | Shutdown flag and counter docs | Correct the `set_shutdown_flag()` docstring and state the counter role | REQ-002, REQ-005 / AC-3, AC-5 | `_active_db_users` is written by `bump_active_db_user` / `release_active_db_user` and read nowhere in `scripts/`; `set_shutdown_flag` docstring claims queued threads are refused (checked in Step 3) | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/app.py` | `_shutdown_lifespan` | Set `app.state.db = None` after `close()` | REQ-003 / AC-4 | `_shutdown_lifespan` calls `app.state.db.close()` and leaves the reference; `app_get_db` raises when state is missing (checked in Step 3) | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `tests/eventbus/test_eventbus_shutdown.py` | Shutdown tests | Add the queued-worker regression test and the in-flight request and second-lifecycle tests | REQ-004 / AC-2, AC-4 | Existing tests cover the in-flight sweep, lock timeout and the pre-check only (`test_shutdown_waits_for_inflight_sweep_before_closing_db`, `test_shutdown_raises_when_lock_timeout_exceeded`, `test_run_with_db_lock_refuses_after_shutdown_flag`) (checked in Step 3) | itself | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Shutdown section | Correct step 3 ("with no worker queued on it") and add the queued-worker rule | REQ-005 / AC-5 | The Shutdown section lists four steps and claims exclusive ownership with no worker queued; the code only acquires the lock (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/eventbus/conftest.py` | The autouse fixture preserves `_shutting_down` and `_active_db_users` across tests; the new tests rely on it | REQ-004 |
| `scripts/eventbus/db.py` | Re-exports `get_db_lock` used by `run_with_db_lock` | REQ-001 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Records the connection-ownership invariant the docs cite; read-only, no edit needed | REQ-005 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated rows quote only the first docstring line of the counter functions, so a body-only change needs no refresh | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): A worker admitted before shutdown that acquires the lock after the flag is set raises the shutdown `RuntimeError` and `func()` is not called.
- AC-2 (REQ-004): The queued-worker test is deterministic and fails on the pre-change code; the in-flight sweep and in-flight request cases pass.
- AC-3 (REQ-002): The counter docstrings state its role; the counter and its conftest handling remain.
- AC-4 (REQ-003, REQ-004): After shutdown `app.state.db` is `None` and `get_db` raises explicitly; a second app lifecycle starts with the flag cleared.
- AC-5 (REQ-005): The `set_shutdown_flag()` docstring and the Shutdown section match the implemented behavior.

## Tests
- Queued-worker interleaving: thread A holds the lock inside a worker, a second worker is admitted and queues, shutdown sets the flag, A releases, the queued worker must raise without running SQL (REQ-001, REQ-004).
- In-flight request: a request holding the lock at shutdown completes before close (REQ-004).
- In-flight sweep: existing test stays green (REQ-004).
- State cleared after shutdown and second lifecycle starts clean (REQ-003, REQ-004).
- Confirm the new queued-worker test fails when the guard is removed (REQ-004).
- Run `uv run pytest tests/eventbus -q`; `tools/check_mock_patch_targets.py` only if mocks are added.

## Documentation Impact
Yes (REQ-005): the Shutdown section of the EventBus operations doc (found through `docs/00_index.md` "Document References by Task"). ADR-006 states the ownership invariant and stays unchanged. State current behavior only.

## Assumptions
- The shutdown flag is a plain module-level bool read under the GIL, so a worker that reads `False` after acquiring the lock completes before shutdown can acquire it.
- Keeping the existing pre-check is harmless and still prevents spawning worker threads once shutdown began.
- Overlap judgment (compatible): `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` also targets `scripts/eventbus/app.py`, but it edits the ACK/NACK route wiring while this Plan edits `_shutdown_lifespan`; the two touch different functions and can land in either order.
- Overlap judgment (compatible): `plans/20261028-094217_ebmetrics006_correct-db-timing-health.md` also targets `scripts/eventbus/route_helpers.py` and `docs/24_eventbus/eventbus_07_configuration-and-operations.md`; it changes the timing statements around the lock acquisition and the Metrics section, while this Plan adds the post-lock shutdown re-check and edits the Shutdown section.
- The counter is not removed because removal is not needed to close the race and the Issue says to stop if its role is unclear; UNK-01 tracks a follow-up.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the active-user counter should be removed | It has no readers in `scripts/`; only `tests/eventbus/conftest.py` saves and restores it and `eventbus_08_reference_api.md` lists it | Owner decides in a follow-up Issue; removal would touch `scripts/eventbus/db_conn.py`, `scripts/eventbus/route_helpers.py`, `tests/eventbus/conftest.py` and the generated reference | False |
| UNK-02 | Whether any test reads `app.state.db` after the lifespan exits | Not exhaustively checked; the grep found only in-lifespan and fixture-teardown uses | Run `uv run pytest tests/eventbus`; if a test breaks, drop REQ-003 and record why | False |
| UNK-03 | Ordering against the `ebmetrics006` plan, which edits the same `_locked()` function | That Plan does not exist yet | Step 8b overlap check and the later procedure's rebase note | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | Modify | High | 2 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/db_conn.py` | Modify | Low | 2 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Medium | 6 | High (single author) | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_shutdown.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (5 files; changes a runtime lifecycle contract). `lint-imports` kept all 6 contracts (run in the previous cycle on unchanged import graph); every change stays inside `scripts/eventbus/`. `run_with_db_lock` is called by every route and by `_dlq_loop`, so the guard covers all DB access; no code outside it takes `get_db_lock()` except `_shutdown_lifespan`.
- Decision 1, guard location: inside `_locked()` right after `with get_db_lock():`, before `bump_active_db_user()`. Alternative (checking in the route layer) was rejected because the lock is the only point where admission and execution are atomic.
- Decision 2, counter: keep and document it. `vulture` reports unreachable code in `run_with_db_lock` after the `try` block (`route_helpers.py:151`, the query-duration observation); that belongs to the `ebmetrics006` Issue and is not touched here.
- Decision 3, `app.state.db = None`: done inside the `finally` after `close()` and before releasing the lock; `_shutdown_lifespan` becomes idempotent because its `if app.state.db` guard is then false.
- The exception type is unchanged (`RuntimeError`), so callers that already handle the pre-check error need no change.

## Implementation steps
1. **Phase 1: Regression test first**
   - [ ] Write the deterministic queued-worker test and confirm it fails on current code (REQ-004; `tests/eventbus/test_eventbus_shutdown.py`)
2. **Phase 2: Guard and state**
   - [ ] Add the post-lock shutdown re-check in `_locked()` (REQ-001; `scripts/eventbus/route_helpers.py`)
   - [ ] Clear `app.state.db` after close and add the state and second-lifecycle tests (REQ-003, REQ-004; `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`)
   - [ ] Fix the `set_shutdown_flag()` docstring and document the counter role (REQ-002, REQ-005; `scripts/eventbus/db_conn.py`)
3. **Phase 3: Documentation**
   - [ ] Correct the Shutdown section (REQ-005; `docs/24_eventbus/eventbus_07_configuration-and-operations.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) and restart the EventBus service to confirm a clean stop (REQ-001; `scripts/eventbus/route_helpers.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | Deterministic interleaving test | `uv run pytest tests/eventbus/test_eventbus_shutdown.py -q` | New test fails before the change, passes after |
| `scripts/eventbus/app.py`, `scripts/eventbus/db_conn.py` | Lifecycle tests | `uv run pytest tests/eventbus -q` | All pass |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `uv run bandit -r scripts/eventbus -c pyproject.toml` | Clean |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in Step 5: `radon cc` reports no touched function in these three modules at C or above; `vulture scripts/eventbus --min-confidence 80` reports only the unreachable code at `route_helpers.py:151`; `bandit` was clean for `scripts/` in the previous cycle on unchanged sources.

## Risks
- **Risk**: A test reads `app.state.db` after the lifespan exits and breaks on `None` → **Mitigation**: run the full eventbus suite; drop REQ-003 if one does (UNK-02).
- **Risk**: The new guard raises during normal operation if the flag is stale from a previous lifecycle → **Mitigation**: `lifespan()` already calls `clear_shutdown_flag()` at startup; the second-lifecycle test covers it.
- **Risk**: Two plans edit `_locked()` (this one and `ebmetrics006`) → **Mitigation**: implement in sequence and rebase; the changes are in different statements.
- **Risk**: A flaky interleaving test → **Mitigation**: synchronize with `threading.Event` and barriers only, no sleeps, and bound every wait with a timeout.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing queued-worker regression test | In Progress | — | — |  |
| 2 | Add the post-lock guard, clear `app.state.db`, fix docstrings, add remaining tests | In Progress | — | — |  |
| 3 | Correct the Shutdown section of the operations doc | In Progress | — | — |  |
| 4 | Deployment and verification hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-115236_01_scripts_eventbus_route_helpers.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115236_02_scripts_eventbus_db_conn.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115236_03_scripts_eventbus_app.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-115236_04_tests_eventbus_test_eventbus_shutdown.py.md | 1,2 | Procedure | Pending | — | — |
| implementations/20261028-115236_05_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155845_ebshutdown002_close-shutdown-admission-race.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-092928
- **Related target files**: `scripts/eventbus/route_helpers.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `_locked()` has no flag check | `scripts/eventbus/route_helpers.py` | Step 2 | AC-1 | `tests/eventbus/test_eventbus_shutdown.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; counter has no readers in `scripts/` | `scripts/eventbus/db_conn.py` | Step 2 | AC-3 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 4 | `scripts/eventbus/app.py` | Step 2 | AC-4 | `tests/eventbus/test_eventbus_shutdown.py` | Needs confirmation |
| REQ-004 | Required Changes 3 and 5; no test covers the interleaving | `tests/eventbus/test_eventbus_shutdown.py` | Steps 1 and 2 | AC-2, AC-4 | `uv run pytest tests/eventbus/test_eventbus_shutdown.py -q` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria 4; Documentation Impact | `scripts/eventbus/db_conn.py` | Step 2 | AC-5 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-005 | Documentation Impact; Shutdown section claims no worker queued | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Step 3 | AC-5 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |