## Goal
- Give `lifespan()` explicit ownership of the shared SQLite connection during shutdown so the connection is never closed while any worker — the DLQ sweep thread, a route-handler worker thread, or an SSE task — may still execute SQL against it, and make the regression test assert that invariant directly instead of asserting the unsafe close-on-timeout fallback.

## Priority
High

## Scope
- **In-Scope**:
  - Track the DLQ sweep worker (`_dlq_loop`) as an explicit future/task and stop scheduling new sweep cycles once shutdown begins.
  - Wait for the in-flight sweep worker to finish before closing the shared connection; never call `db.close()` while the lock was not acquired / exclusive ownership is not proven.
  - Close the queued-thread race (a worker blocked on `get_db_lock()` inside `run_with_db_lock` running SQL after close) via a shutdown flag that makes `run_with_db_lock` fail fast or drain (owner decision, see UNK-03).
  - Extract one shutdown/cleanup helper shared by production `lifespan()` and the `tests/eventbus/` suite so both execute the same lifecycle sequence.
  - Update `tests/eventbus/test_eventbus_shutdown.py` to assert the connection-ownership invariant and remove the close-on-timeout requirement; remove the `_noop_dlq_loop` workaround from `tests/eventbus/test_eventbus_app_isolation.py`.
  - Document the shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy in the EventBus ops doc and ADR-006.
- **Out-of-Scope**:
  - The DLQ sweep logic itself (interval, what it sweeps) — unchanged.
  - The agent shutdown WAL checkpoint step.
  - Deployment-script readiness verification (`deploy/init_db.sh`, `deploy/setup_services.sh`) and mandatory-table checks — those belong to EVENTBUS-022, tracked in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, not this issue.
  - Connection pooling / per-worker connection isolation (would broadly change durability and locking boundaries).
- **Dependencies**:
  - Related memo tasks H-01 and H-05 share the same connection-and-lock model. No open issue under `issues/` overlaps.
  - Owner decision required on the bounded-shutdown policy (UNK-01) before implementation; non-blocking with a sign-off gate.

## Background
Confirmed against HEAD (adversarial re-verification):
- `lifespan()` (`scripts/eventbus/app.py:89-118`) cancels the DLQ asyncio task (`app.state.dlq_task.cancel()` + `await`), shuts down the broker, then acquires the global DB lock via `asyncio.to_thread(lock.acquire, timeout=_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS)` (5.0 s) and calls `app.state.db.close()` in a `finally` even when the lock was not acquired; the fallback logs `shutdown: db lock not acquired within 5.0s; closing db anyway (a sweep thread may still be using it)`.
- Waiting for an in-flight sweep is therefore already implemented: cancelling the task does not stop a sweep already running on its `asyncio.to_thread()` worker thread, so the lock-acquire serializes the close behind the running sweep. Covered by `test_shutdown_waits_for_inflight_sweep_before_closing_db` in `tests/eventbus/test_eventbus_shutdown.py`.
- The unsafe part is only the timeout fallback: when the lock cannot be acquired within 5.0 s, the DB is closed anyway. That fallback is asserted by `test_shutdown_logs_warning_when_lock_timeout_exceeded`, which explicitly requires "still close the DB".
- A second, unnamed race: cancelling `_dlq_loop`'s task does not cancel a worker thread that is still queued on `get_db_lock()` inside `run_with_db_lock`. After shutdown releases the lock, that queued thread acquires it and runs SQL on the already-closed connection (`sqlite3.ProgrammingError`, swallowed/logged as `dlq_loop error`). Route handlers and SSE tasks that use `run_with_db_lock` share the same exposure if the server shuts down with requests in flight.
- `tests/eventbus/test_eventbus_app_isolation.py` works around the segfault by monkeypatching `_dlq_loop` with a no-op coroutine (`_noop_dlq_loop`, lines 71-74) and doing inline cleanup in `_do_cleanup` (lines 31-43). The memo's path `tests/test_eventbus_app_isolation.py` does not exist; the real file is `tests/eventbus/test_eventbus_app_isolation.py`.

## Problem
A lock-acquisition timeout is positive evidence that another worker may still own the shared connection, yet the current fallback closes it anyway, which can crash inside the SQLite C library or interrupt an active transaction. A worker thread queued on the lock when shutdown starts can run SQL on the closed connection after shutdown releases the lock. The regression test enforces the unsafe behavior ("still close the DB") rather than the safety invariant.

## Reason for Change
Controlled restart and WAL checkpoint procedures depend on orderly, exclusive connection shutdown, and a regression test must enforce the safety invariant ("connection never closed while a worker may use it") rather than the timeout fallback. Production and tests must exercise the same lifecycle sequence.

## Implementation Intent
Track the sweep worker as an explicit future and stop scheduling new sweeps when shutdown begins. Prove exclusive ownership of the connection before closing it: wait for the in-flight sweep to finish and ensure no worker is queued on the lock, then close. Replace the close-on-timeout fallback with a documented bounded-shutdown policy that never closes a connection another worker owns. Extract the shutdown sequence into one helper used by both `lifespan()` and the test suite. Whether shutdown fails fast (a shutdown flag makes `run_with_db_lock` refuse new work) or drains in-flight work is an owner decision recorded as UNK-03.

## Requirements
- `REQ-001`: Shutdown MUST prove exclusive ownership of the shared connection before calling `db.close()` — it MUST NOT close while any worker (sweep thread, route-handler thread, SSE task) may execute SQL against it. (Acceptance 1, 4)
- `REQ-002`: Once shutdown begins, `lifespan()` MUST schedule no new sweep cycles and MUST wait for the in-flight sweep worker to finish before proceeding to close. (Required changes 1, 2)
- `REQ-003`: Shutdown MUST remain bounded in wall-clock time. The bound value and its enforcement policy (wait indefinitely / terminate the process / isolate the connection and leave it to process exit) is an owner decision recorded as UNK-01; the bound MUST stay compatible with the process manager's stop timeout. (Constraints, Required change 3)
- `REQ-004`: A worker thread queued on the DB lock when shutdown starts MUST NOT run SQL against the closed connection. Handled by a shutdown flag that makes `run_with_db_lock` fail fast after shutdown begins, or by a bounded drain (owner decision, UNK-03). (Acceptance 4)
- `REQ-005`: Production `lifespan()` and the `tests/eventbus/` suite MUST share one cleanup helper so they execute the same lifecycle sequence. (Required change 5, Acceptance 3)
- `REQ-006`: The regression test MUST assert the "connection not closed while a worker may use it" invariant directly. The timeout test MUST NO LONGER require close-on-timeout. (Acceptance 2, Problem)

## Implementation Target Files
**Freeze status**: Frozen (set once `issue-to-plan` Step 8's Implementation Target
Files Validation passed — `check_workitem_structure.py` and
`check_plan_target_overlaps.py` both report No findings; every row is `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/app.py` | `lifespan()` delegates to one shared cleanup helper; `_dlq_loop` tracked as an explicit future; stop scheduling sweeps on shutdown; never close while lock unacquired | Main shutdown-contract change; removes close-on-timeout fallback; unifies prod/test lifecycle | REQ-001, REQ-002, REQ-005, REQ-006; Acceptance 1, 2, 3 | `lifespan()` app.py:68-118; `_dlq_loop()` app.py:121-134 | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/db_conn.py` | Add module-level shutdown flag (+ optional active-user counter) co-located with `get_db_lock()`; host the shared cleanup helper's DB-close coordination | Connection layer owns the lock; flag lives next to it; proves exclusive ownership before close | REQ-001, REQ-004; Acceptance 1, 4 | `get_db_lock()`/`open_db()` app.py:38, db_conn.py:1-58 | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` checks the shutdown flag (fail fast) or participates in the bounded drain; increments/decrements the active-user counter if used | Closes the queued-thread race and in-flight-request exposure | REQ-004; Acceptance 4 | `run_with_db_lock()` route_helpers.py:131-... | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `tests/eventbus/test_eventbus_shutdown.py` | Assert the connection-ownership invariant directly; replace close-on-timeout test with a safe-bounded-policy assertion; keep real `_dlq_loop` (no no-op) | Regression test must enforce the invariant, not the removed fallback | REQ-006; Acceptance 2, 3 | `test_shutdown_waits_for_inflight_sweep_before_closing_db`, `test_shutdown_logs_warning_when_lock_timeout_exceeded` | this file | Verified |
| `tests/eventbus/test_eventbus_app_isolation.py` | Remove `_noop_dlq_loop` monkeypatch and inline `_do_cleanup`; drive shutdown through the shared helper with the real `_dlq_loop` | Workaround exists only to dodge the segfault the fix removes; unifies prod/test lifecycle | REQ-005; Acceptance 3 | `_noop_dlq_loop` isolation test:71-74; `_do_cleanup` isolation test:31-43 | this file | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Record the connection-ownership invariant (INV-01) and the bounded-shutdown policy; update EVENTBUS-021 known-issue note | Canonical record of the shutdown/connection ownership rule | REQ-001, REQ-003; Acceptance 1 | INV-01 known-issue adr_02_04_006:276-277 | N/A | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Document the shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy (new "Shutdown" subsection under Configuration/DLQ Operations) | Ops doc for controlled restart and process-manager stop compatibility | REQ-002, REQ-003; Acceptance 3 | "DLQ Operations" eventbus_07:177; health/degraded eventbus_07:118-124 | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/db.py` | Facade re-exports; needed to know what the shared helper re-exports and how `run_with_db_lock` imports the lock | `scripts/eventbus/route_helpers.py`, `scripts/eventbus/db_conn.py`; REQ-004 |
| `scripts/eventbus/dlq_repo.py` | Sweep/DLQ redelivery API used by `_dlq_loop`'s `_sweep()`; out of scope but must be read to preserve sweep behavior | `scripts/eventbus/app.py`; REQ-002 |
| `implementations/done/20260913-102829_01_scripts_eventbus_app_py.md` | Prior shutdown-fix context (how `db.close()` was routed through `get_db_lock()`) | `scripts/eventbus/app.py`; REQ-001 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | EVENTBUS-021/022 known-issue tracking; confirms deploy-readiness gaps belong to EVENTBUS-022, not this issue | `docs/24_eventbus/eventbus_07_configuration-and-operations.md`; Scope |

## Acceptance Criteria
- The shared connection is never closed while another worker may use it (REQ-001; Acceptance 1).
- Real DLQ-loop shutdown tests pass without replacing the loop with a no-op and the timeout test no longer requires close-on-timeout (REQ-006; Acceptance 2).
- Repeated full-suite runs complete without a SQLite crash, and production and tests use the same lifecycle sequence via the shared helper (REQ-005; Acceptance 3).
- A sweep or request thread that is still queued on the database lock when shutdown starts cannot run SQL on the closed connection (REQ-004; Acceptance 4).
- The bounded-shutdown policy is documented and stays compatible with the process manager's stop timeout (REQ-003; Acceptance 3).

## Tests
- Shutdown with no in-flight sweep: shared helper closes the connection cleanly and the timeout fallback is gone (REQ-001, REQ-006).
- Sweep completes within the shutdown window: `lifespan()` waits for the sweep, then closes exclusively (REQ-002).
- Sweep exceeds the window: the documented bounded-shutdown policy applies WITHOUT closing a connection another worker owns (REQ-003; replaces the old close-on-timeout assertion).
- Sweep raises an exception mid-run: shutdown still proves ownership and closes safely (Acceptance 2).
- Worker queued on the lock at shutdown start: with the shutdown flag set, `run_with_db_lock` fails fast / drains so the queued thread never runs SQL on the closed connection (REQ-004).
- `tests/eventbus/test_eventbus_app_isolation.py` runs the real `_dlq_loop` through the shared helper (no no-op) and isolates app state (REQ-005).
- Repeated full `tests/eventbus/` runs complete without a SQLite crash (Acceptance 3).
- Then ruff and mypy.

## Documentation Impact
Yes. The shutdown sequence, the connection-ownership rule, and the bounded-shutdown policy must be documented. Target docs named via `docs/00_index.md` / `routing.md` Docs mapping:
- `docs/24_eventbus/eventbus_07_configuration-and-operations.md` — shutdown sequence + bounded-shutdown policy (Configuration / DLQ Operations sections). Drives REQ-002, REQ-003.
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` — connection-ownership invariant (INV-01) + bounded-shutdown policy; update the EVENTBUS-021 known-issue note. Drives REQ-001, REQ-003.
No deployment-script documentation is in scope (EVENTBUS-022).

## Assumptions
- `get_db_lock()` returns the same module-level `threading.Lock()` that `run_with_db_lock()` acquires for every DB operation, including `_dlq_loop`'s sweep — confirmed by reading `db_conn.py`.
- `threading.Lock.acquire(timeout=...)` returns `False` on timeout without raising — standard-library behavior.
- The shared cleanup helper can live in the `eventbus` layer (re-exported from `app.py`) so `tests/eventbus/` can import it without crossing the import-linter boundary (`eventbus must not import from agent, mcp_servers, rag, db`). No new module under `shared/`.
- No systemd unit or process-manager stop policy exists in this repo; the stop timeout is an external/ops constraint (UNK-02).
- `deploy.sh` rsyncs `scripts/` and `docs/` wholesale to `/opt/llm/`, so every target row's `deploy.sh Impact` is "not applicable (rsynced)".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Safe bounded-shutdown policy: wait indefinitely, terminate the process, or isolate the connection and leave it to process exit? | Owner availability; no existing policy in repo | Owner decision; non-blocking with a sign-off gate before implementation (per `rules/coding.md` Explicit sign-off gates) | False |
| UNK-02 | Process-manager stop timeout and whether it leaves room for a longer wait than the current 5.0 s; service-unit location not confirmed in repo | No systemd unit / stop policy in repo; ops environment not reviewed | Confirm with ops; document the constraint in `eventbus_07` (UNK-02) | False |
| UNK-03 | Should a shutdown flag make `run_with_db_lock` callers fail fast after shutdown starts (closing the queued-thread race + in-flight-request exposure), or is draining enough? | Trade-off between fast shutdown and in-flight request completion | Owner/engineering decision; recorded in design, applied at implementation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/app.py` | `lifespan()` shutdown sequence + `_dlq_loop` tracking + shared helper | FastAPI entrypoint; low direct callers (FastAPI runtime) | 6 (last change 2026-10-22) | N/A (git-fame unavailable) | not applicable (rsynced) |
| `scripts/eventbus/db_conn.py` | Shutdown flag + counter + helper coordination | All DB access routes through this layer | 0 | N/A | not applicable (rsynced) |
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` shutdown-flag / drain + counter | Called by 6 route modules (`ack_route`, `dlq_route`, `health_route`, `publish_route`, `replay_route`, `subscribe_route`) + `_dlq_loop`; high blast radius | 0 (last change 2026-09-15) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_shutdown.py` | Regression test rewrite | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_app_isolation.py` | Remove no-op workaround; use shared helper | Test-only | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | INV-01 + bounded-shutdown policy | Doc-only | 0 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Shutdown-sequence + policy doc | Doc-only | 0 | N/A | not applicable (rsynced) |

Baseline complexity (radon): `lifespan()` = B (7); `run_with_db_lock()` = A (2).
bandit and vulture are clean on all target files. Refactor of `lifespan()` may raise its
complexity grade; keep the shared helper small to avoid it.

## Design
**North star (REQ-001):** `db.close()` runs only after exclusive ownership of the shared
connection is proven. Every candidate mechanism below serves that invariant; the owner
decision (UNK-01) picks which one.

**Candidate mechanisms:**
1. **Active-user counter + bounded wait.** Maintain a reference count of live DB users,
   incremented inside `run_with_db_lock()` around the critical section and decremented
   after. On shutdown, set a shutdown flag, wait until the counter reaches zero with a
   bounded grace period, then close. Directly proves in-flight ownership. Does not by
   itself stop a thread *queued* on the lock (it has not yet incremented), so it must be
   paired with mechanism 2.
2. **Shutdown flag, fail-fast.** A module-level flag in `db_conn.py` (co-located with
   `get_db_lock()`). `run_with_db_lock()` checks it before acquiring: if shutdown has
   begun, it raises/refuses instead of enqueuing. This closes the queued-thread race
   (REQ-004) and the in-flight-request exposure at once. In-flight holders finish their
   current SQL; queued callers get an error. Owner decision: fail fast (UNK-03) vs. allow
   a bounded drain.
3. **Connection isolation.** Give each worker its own connection/pool so closing "the"
   connection is not a global event. Correct but broadly changes durability/locking
   boundaries; out of scope for this issue.

**Recommended direction (subject to UNK-01/UNK-03 sign-off):** combine 1 + 2 with a
documented bounded shutdown. `db_conn.py` owns the flag (+ counter); `route_helpers.py`'s
`run_with_db_lock()` checks the flag and updates the counter; `app.py`'s `lifespan()`
delegates to one shared helper that stops scheduling sweeps, waits for the in-flight
sweep, waits for the counter to drain (bounded per UNK-01), asserts no worker remains,
and closes. The helper lives in the `eventbus` layer (re-exported from `app.py`) so
`tests/eventbus/` imports it without crossing the import-linter boundary.

**Shared helper location.** Keep the helper in `app.py` (e.g. `async def
_shutdown_lifespan(app)`) rather than a new module, to minimize surface area; move it to
`scripts/eventbus/lifecycle.py` only if the refactor warrants separation of concerns.
Either way it stays inside the `eventbus` layer.

**Bounded-shutdown policy (UNK-01).** The plan does NOT prescribe the policy. Options, in
order of increasing shutdown aggressiveness: (a) wait for the counter to reach zero with
a generous grace period, then close; (b) after the grace period, terminate the process
via the process manager (requires a stop timeout, UNK-02); (c) isolate the connection and
let it close at process exit. Whatever is chosen must never close a connection another
worker owns as a "fallback" — that is the defect being removed.

**Import-linter.** `eventbus-is-isolated` is KEPT (verified above). The helper, flag, and
counter stay within `eventbus`; nothing moves to `shared/`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Preparation / shared helper + connection-layer primitives**
   - [ ] Add the shutdown flag (+ optional active-user counter) to `scripts/eventbus/db_conn.py`, co-located with `get_db_lock()`; add accessors used by both `run_with_db_lock()` and the helper. (REQ-004; `scripts/eventbus/db_conn.py`)
   - [ ] Extract one shutdown/cleanup helper that stops scheduling sweeps, waits for the in-flight sweep, drains/asserts exclusive ownership, and closes — re-exported from `scripts/eventbus/app.py` for test reuse. (REQ-005; `scripts/eventbus/app.py`)
   - [ ] Wire `lifespan()` in `scripts/eventbus/app.py` to delegate to the shared helper; track `_dlq_loop` as an explicit future and stop scheduling new cycles on shutdown. (REQ-002; `scripts/eventbus/app.py`)
2. **Phase 2: Route-layer exposure**
   - [ ] Update `run_with_db_lock()` in `scripts/eventbus/route_helpers.py` to check the shutdown flag (fail fast per UNK-03) and update the active-user counter. (REQ-004; `scripts/eventbus/route_helpers.py`)
3. **Phase 3: Tests**
   - [ ] Rewrite `tests/eventbus/test_eventbus_shutdown.py` to assert the connection-ownership invariant directly and replace the close-on-timeout assertion with the documented bounded-shutdown behavior; keep the real `_dlq_loop`. (REQ-006; `tests/eventbus/test_eventbus_shutdown.py`)
   - [ ] Remove the `_noop_dlq_loop` monkeypatch and inline `_do_cleanup` from `tests/eventbus/test_eventbus_app_isolation.py`; drive shutdown through the shared helper with the real loop. (REQ-005; `tests/eventbus/test_eventbus_app_isolation.py`)
4. **Phase 4: Documentation**
   - [ ] Document the shutdown sequence, connection-ownership rule, and bounded-shutdown policy in `docs/24_eventbus/eventbus_07_configuration-and-operations.md`. (REQ-002, REQ-003; `docs/24_eventbus/eventbus_07_configuration-and-operations.md`)
   - [ ] Record INV-01 and the bounded-shutdown policy in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; update the EVENTBUS-021 known-issue note. (REQ-001, REQ-003; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
5. **Phase 5: Validation**
   - [ ] Run ruff, mypy, bandit, vulture, lint-imports, and repeated full `tests/eventbus/` runs; confirm no SQLite crash and the invariant holds. (Acceptance 2, 3)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/app.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/route_helpers.py` | Unit: shutdown helper drives real `_dlq_loop`; assert close happens only after exclusive ownership; queued-thread fails fast | `uv run pytest tests/eventbus/test_eventbus_shutdown.py tests/eventbus/test_eventbus_app_isolation.py` | Invariant holds; no close-on-timeout; no no-op loop |
| `tests/eventbus/` (whole suite) | Integration: repeated runs to catch non-deterministic segfault | `uv run pytest tests/eventbus/` (repeat) | No `Fatal Python error: Segmentation fault`; stable across runs |
| `scripts/eventbus/*` | Static: complexity, dead code, security | `uv run radon cc scripts/eventbus/app.py scripts/eventbus/route_helpers.py scripts/eventbus/db_conn.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `lifespan()` complexity contained; bandit/vulture clean |
| Import boundaries | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Types / format | Quality gates | `uv run mypy`, `uv run ruff` | Pass |

## Risks
- **Risk**: `run_with_db_lock()` has high blast radius (6 route modules + `_dlq_loop`); a wrong shutdown-flag check could break in-flight requests outside shutdown. → **Mitigation**: measure callers with `rg` before changing (done: 6 route modules + loop); flag only affects behavior after shutdown begins; covered by full-suite runs.
- **Risk**: Refactoring `lifespan()` (radon B 7) raises complexity past maintainability limits. → **Mitigation**: keep the shared helper small; push lock/flag logic into `db_conn.py`.
- **Risk**: Owner has not decided the bounded-shutdown policy (UNK-01); implementing the wrong one reintroduces an unsafe fallback. → **Mitigation**: non-blocking sign-off gate; the plan records options, not a prescription; close-on-timeout fallback is removed regardless of policy.
- **Risk**: Removing `_noop_dlq_loop` from the isolation test reintroduces the segfault if the fix is incomplete. → **Mitigation**: the shared helper must prove exclusive ownership before close; repeated full-suite runs validate before merge.
- **Risk**: Queued-thread handling (UNK-03) may need fail-fast that returns errors to in-flight requests during shutdown. → **Mitigation**: documented as an owner decision; behavior confined to the shutdown window.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: shared helper + connection-layer primitives (flag/counter, `_shutdown_lifespan`, `_dlq_loop` tracking) | In Progress | — | — | Sign-off gate on UNK-01 before implementation |
| 2 | Phase 2: `run_with_db_lock()` shutdown-flag / drain (UNK-03) | In Progress | — | — |  |
| 3 | Phase 3: rewrite shutdown regression test; remove `_noop_dlq_loop` workaround | In Progress | — | — |  |
| 4 | Phase 4: document shutdown sequence, ownership rule, bounded-shutdown policy | In Progress | — | — |  |
| 5 | Phase 5: ruff/mypy/bandit/vulture/lint-imports + repeated full-suite runs | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: bounded-shutdown policy is an owner decision (sign-off gate) | Classified non-blocking (prose + user approval 2026-10-25); sign-off remains a pre-implementation gate, not a generation blocker | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261025-192817_01_scripts_eventbus_app.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261025-192817_02_scripts_eventbus_db_conn.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261025-192817_03_scripts_eventbus_route_helpers.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261025-192817_04_tests_eventbus_test_eventbus_shutdown.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-192817_05_tests_eventbus_test_eventbus_app_isolation.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-192817_06_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261025-192817_07_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-113939
- **Related target files**: `scripts/eventbus/app.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/route_helpers.py`, `tests/eventbus/test_eventbus_shutdown.py`, `tests/eventbus/test_eventbus_app_isolation.py`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Acceptance 1 | `scripts/eventbus/app.py`, `scripts/eventbus/db_conn.py` | 1 | Connection never closed while a worker may use it | `test_eventbus_shutdown.py` invariant assertion | Draft |
| REQ-002 | Required changes 1,2; Acceptance 2 | `scripts/eventbus/app.py` | 1 | No new sweep scheduled on shutdown; in-flight sweep awaited | `test_eventbus_shutdown.py` sweep-completes case | Draft |
| REQ-003 | Constraints; Unresolved Q1 | `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 4 | Bounded-shutdown policy documented and stop-timeout compatible | Doc review; UNK-01 sign-off | Draft |
| REQ-004 | Background race; Acceptance 4 | `scripts/eventbus/route_helpers.py`, `scripts/eventbus/db_conn.py` | 2 | Queued lock thread cannot run SQL on closed connection | `test_eventbus_shutdown.py` queued-thread case | Draft |
| REQ-005 | Required change 5; Acceptance 3 | `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_app_isolation.py` | 1, 3 | Production and tests share one lifecycle sequence | Isolation test uses shared helper | Draft |
| REQ-006 | Problem; Acceptance 2 | `tests/eventbus/test_eventbus_shutdown.py` | 3 | Timeout test no longer requires close-on-timeout | Rewritten timeout test | Draft |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261025-192817 -->