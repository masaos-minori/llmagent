# Plan: restart and resume integration coverage through /subscribe (ebresumetest004)

## Goal
- Prove end-to-end that a consumer resumes through the public `/subscribe` endpoint after a full
  application restart (shutdown, then a second production lifespan on the same SQLite file), and
  retire misleading test names and a stale skip so that direct-SQL tests are named as unit tests.

## Priority
Medium

## Scope
- **In-Scope**:
  - A shared two-lifecycle lifespan fixture/helper in `tests/eventbus/eventbus_helpers.py`.
  - Restart-resume integration tests in `tests/eventbus/test_eventbus_restart_resume.py`: same
    consumer resumes after restart; different consumer starts from the beginning; out-of-order ACK
    does not skip the lowest unacked event; ordered ACK fast-forwards; topic filtering and consumer
    authorization hold through the endpoint; duplicate active consumer id rejected; client
    disconnect removes the subscriber.
  - Leak assertions across lifecycles (connection, broker, shutdown flag, subscriber queue).
  - Renaming direct-SQL tests (incl. `test_subscribe_yields_matching_event`) to unit-test names.
  - Resolving the skipped `test_resume_from_sqlite_offset` (unskip or document a current reason).
- **Out-of-Scope**: changes to resume or replay behavior; a general SSE client library for tests;
  authorization model changes.
- **Dependencies**: The shutdown Plan `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md`
  is archived and its procedure `implementations/20261028-115236_04_tests_eventbus_test_eventbus_shutdown.py.md`
  is implemented (`implementations/` top level is empty), so the second-lifecycle prerequisite
  (shutdown clears admission state and nulls `app.state.db`) is settled. The sibling Plan
  `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` reuses this Plan's fixture:
  implement this Plan first. Related archived issue:
  `issues/done/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md`.

## Background
All tests in `tests/eventbus/test_eventbus_restart_resume.py` run inside one `TestClient`
lifecycle; none closes it and reopens a second one on the same database. `TestOutOfOrderAckNoSkipOnReconnect`
(lines 274-307) and `test_get_resume_position_no_offset` call `ack_event_for_consumer`,
`get_consumer_offset` and `get_resume_position` directly without crossing `/subscribe`. Two tests
(`test_reconnect_after_ordered_acks_replays_next_event_first`,
`test_reconnect_after_out_of_order_ack_replays_lowest_unacked_first`) do use `/subscribe` through
`_reconnect_ids()` (finite `sse_idle_timeout` 0.5 s) but stay within one lifecycle.
`test_resume_from_sqlite_offset` is skipped at line 196 citing the issue `ebsse01` by its old
`issues/` path; that issue is archived (2026-09-11) and the skip has never been re-evaluated.
Production facts verified 2026-10-28: `lifespan()` calls `clear_shutdown_flag()` at startup and
`_shutdown_lifespan` nulls `app.state.db`, so a second lifecycle in one process is designed to be
safe — but no test exercises it.

## Problem
At-least-once resume after a process restart is not verified end to end: no test proves that a
second lifecycle (new connection, new broker, cleared shutdown state) resumes the same consumer
from the persisted position through the public endpoint; direct-SQL tests claim endpoint coverage
by their names.

## Reason for Change
Resume correctness depends on the offset, delivery and replay path across a restart, which is what
production restarts exercise; single-lifecycle tests can pass while a stale connection, broker or
shutdown flag breaks the second start. No incident cited; Medium; not time-sensitive.

## Implementation Intent
Add one reusable fixture that starts the lifespan, yields a client, shuts it down and starts a
second lifespan on the same database path; drive `/subscribe` with the existing finite harness
(`sse_idle_timeout`) so assertions come from real SSE output; keep the direct-query tests as
clearly named unit tests; resolve the skip empirically. Per the issue's AI instruction: tests only;
if a second lifecycle exposes a production defect, stop and report it with the failing test.

## Requirements
- `REQ-001`: `tests/eventbus/eventbus_helpers.py` provides a fixture/helper that runs two complete
  production lifecycles (`TestClient(app)` context enter/exit twice) on the same tmp database path
  and exposes both clients; a probe test asserts lifecycle 2 has a new DB connection, a new
  `EventBroker`, `_shutting_down` cleared and no leftover subscriber queue.
- `REQ-002`: `tests/eventbus/test_eventbus_restart_resume.py` gains integration tests crossing the
  two lifecycles and asserting resume behavior from real `/subscribe` output for: same-consumer
  resume at the acked position; a different consumer starting from the beginning; out-of-order ACK
  preserving the lowest unacked event; ordered-ACK fast-forward; topic filtering and consumer
  authorization through the endpoint; duplicate active consumer id rejected; client disconnect
  removing the subscriber.
- `REQ-003`: The new tests assert no broker, connection, shutdown flag or subscriber-queue state
  leaks across lifecycles (the lifecycle-2 half is the REQ-001 probe).
- `REQ-004`: Direct-SQL tests are renamed so the name states query/row-conversion coverage:
  `test_subscribe_yields_matching_event` in `tests/eventbus/test_eventbus_replay_subscribe.py` and
  any direct-SQL test in the restart file; names change, assertions do not.
- `REQ-005`: The skipped `test_resume_from_sqlite_offset` is removed or replaced by the new tests;
  if it still fails deterministically, the skip stays with a comment citing the archived issue path
  and the current observed reason.
- `REQ-006`: All new tests terminate deterministically via finite idle timeouts or explicit
  synchronization; no sleeps.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 2026-10-29: all target rows Verified; `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` findings reviewed as documented sequencing dependencies).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/eventbus_helpers.py | Add the shared two-lifecycle lifespan fixture and leak-probe helper | No reusable second-lifecycle harness exists today | REQ-001, REQ-003; AC-1, AC-2 | File holds the existing client builders (e.g. `_init_eventbus_state`, lines 131-174 hand state setup); `scripts/eventbus/app.py` lifespan startup clears the shutdown flag and `_shutdown_lifespan` nulls `app.state.db` | Probe test added in the restart file consumes it | Verified |
| tests/eventbus/test_eventbus_restart_resume.py | Add restart integration tests; rename direct-SQL tests; resolve the skip | No test crosses two lifecycles; two tests claim endpoint coverage via SQL; one test skipped with a stale citation | REQ-002, REQ-004, REQ-005, REQ-006; AC-1, AC-3, AC-4 | Skip at line 196 cites old `issues/` path; `TestOutOfOrderAckNoSkipOnReconnect` (lines 274-307) and `test_get_resume_position_no_offset` run SQL directly; `_reconnect_ids()` finite-timeout pattern already in the file | The new tests themselves | Verified |
| tests/eventbus/test_eventbus_replay_subscribe.py | Rename `test_subscribe_yields_matching_event` to a query/row-conversion name | Name claims subscribe behavior while the test runs a SQL query and `_row_to_dict()` directly | REQ-004; AC-3 | Test at line 82; its own comment at line 87 states `/replay` already validates SSE framing and the same `_row_to_dict` is reused | Existing test, renamed; `pytest --collect-only` diff | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/app.py | Lifespan startup/shutdown contract the fixture relies on (`clear_shutdown_flag` at startup, `_shutdown_lifespan` clearing `app.state.db`) | REQ-001 |
| scripts/eventbus/subscribe_route.py | Public `/subscribe` contract: SSE framing, `sse_idle_timeout`, duplicate-consumer rejection | REQ-002 |
| tests/eventbus/conftest.py | Existing autouse state resets (`_reset_db_conn_state`, `_reset_auth_state`, `_ensure_route_helpers_metrics_registered`) that bound cross-test leakage | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-002): at least one test crosses two complete production lifecycles on the same database
  file and asserts resume position from real `/subscribe` output.
- AC-2 (REQ-001): the second lifecycle demonstrably uses a new connection and broker.
- AC-3 (REQ-004): direct-query tests are named as unit tests; no skipped test remains without a
  documented current reason.
- AC-4 (REQ-006): the new tests terminate deterministically (bounded by idle timeouts; suite run
  shows no hangs).

## Tests
- REQ-001: probe test — lifecycle 2 asserts fresh `sqlite3` connection object, new `EventBroker`,
  `db_conn._shutting_down` cleared, empty subscriber registry.
- REQ-002: seven scenario tests listed in Scope, each driving `/subscribe` across the two
  lifecycles with `_reconnect_ids()`-style finite termination.
- REQ-003: leak assertions embedded in lifecycle-2 fixtures; plus a double run of the touched
  files in one session (`uv run pytest tests/eventbus/test_eventbus_restart_resume.py` twice) to
  confirm no state leaks (flag, principal map, metrics registry).
- REQ-004: `pytest --collect-only` diff shows name changes only; assertions untouched.
- Suite and gates: new tests run alone and with `uv run pytest tests/eventbus`; ruff on changed
  files; mypy on `tests/eventbus` (files scope).

## Documentation Impact
N/A: tests-only change; the issue states no documentation is required and no documented behavior
changes.

## Assumptions
- `TestClient(app)` context-manager entry/exit runs the production lifespan (Starlette behavior);
  the REQ-001 probe verifies rather than assumes this.
- The existing `client` fixture and `_reconnect_ids()` remain valid for the single-lifecycle tests
  in the same file.
- Fixture location decision (issue allows `conftest.py` or `eventbus_helpers.py`): chosen
  `eventbus_helpers.py` because `conftest.py` today holds only autouse resets; revisit only if a
  leak needs an autouse guard (then as a separate follow-up issue, not here).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is the skip on `test_resume_from_sqlite_offset` still required now that `ebsse01` is archived and `_reconnect_ids()` ends streams by idle timeout? | No re-run of the test since the 2026-09-11 archival | Run it unskipped with the REQ-001 fixture at the Phase 2 checkpoint; keep or remove per the deterministic result | False |
| UNK-02 | Does a second `with TestClient(eb_app.app)` on the same database leak `db_conn._shutting_down` or the Prometheus metrics registry today? | No second-lifecycle test exists to observe it | REQ-001 probe test decides; if the leak is production-side, stop and report per the issue instruction before writing the scenario tests | True |

## Affected areas
N/A: Path A tests-only; none of the three target files is deployed by `deploy.sh`, so
`deploy.sh Impact` is nil for every row.

## Design
- Fixture shape: a generator that yields `(client_1, client_2)` built from two sequential
  `with TestClient(app)` blocks over one tmp `db_path`; between lifecycles it snapshots
  `app.state.db` identity, broker identity and `db_conn._shutting_down` for the probe assertions.
  It reuses the config-builder already in `eventbus_helpers.py` rather than re-handling
  `app.state` (that hand-built pattern is what ebtestdrift007 removes).
- Termination: only the finite `sse_idle_timeout` pattern (`_reconnect_ids()`) and response-body
  reads; no raw socket reads, no sleeps.
- Scenario coverage maps one-to-one to REQ-002's seven scenarios; scenarios that duplicate an
  existing single-lifecycle test keep the existing unit test as well (rename, not replace).
- If the probe (REQ-001) fails, the deliverable is a defect report plus the failing probe test;
  no production edits under this Plan (issue instruction).

## Implementation steps
1. **Phase 1: Two-lifecycle fixture and probe**
   - [ ] Add the two-lifecycle lifespan fixture to `tests/eventbus/eventbus_helpers.py` (REQ-001; tests/eventbus/eventbus_helpers.py)
   - [ ] Add the leak-probe test to `tests/eventbus/test_eventbus_restart_resume.py` and run it; on failure STOP and report (REQ-001, REQ-003; tests/eventbus/test_eventbus_restart_resume.py)
2. **Phase 2: Scenario tests and naming**
   - [ ] Add the seven restart/resume scenario tests to `tests/eventbus/test_eventbus_restart_resume.py` (REQ-002, REQ-006; tests/eventbus/test_eventbus_restart_resume.py)
   - [ ] Rename direct-SQL tests in `tests/eventbus/test_eventbus_restart_resume.py` and rename `test_subscribe_yields_matching_event` in `tests/eventbus/test_eventbus_replay_subscribe.py` (REQ-004; tests/eventbus/test_eventbus_restart_resume.py, tests/eventbus/test_eventbus_replay_subscribe.py)
   - [ ] Resolve the skip on `test_resume_from_sqlite_offset` (unskip/remove or re-document with the archived path) (REQ-005; tests/eventbus/test_eventbus_restart_resume.py)
3. **Phase 3: Verification**
   - [ ] `uv run pytest tests/eventbus/test_eventbus_restart_resume.py tests/eventbus/test_eventbus_replay_subscribe.py` alone, then twice in one session, then `uv run pytest tests/eventbus`; ruff on changed files; mypy on `tests/eventbus`. Deployment/scripts check: N/A — no target file is deployed by `deploy.sh`; no config or schema file changes (REQ-001..REQ-006; tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_restart_resume.py, tests/eventbus/test_eventbus_replay_subscribe.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/eventbus_helpers.py | Integration probe (two lifecycles) | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -k lifecycle` | Probe passes or a defect report is filed |
| tests/eventbus/test_eventbus_restart_resume.py | Integration + double-run | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py` run twice in one session | Deterministic pass; no cross-test state leak |
| tests/eventbus/test_eventbus_replay_subscribe.py | Rename-only regression | `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py`; `pytest --collect-only` diff | Same assertions, names changed only |
| tests/eventbus (whole) | Suite + static gates | `uv run pytest tests/eventbus`; ruff; mypy | Suite green (411 passed baseline plus new tests); 0 unexplained skips |

## Risks
- **Risk**: two lifecycles in one process leak global state (metrics registry, shutdown flag) and
  produce order-dependent failures → **Mitigation**: REQ-001 probe gate before any scenario test is
  written; double-run checkpoint (UNK-02).
- **Risk**: unskipping `test_resume_from_sqlite_offset` fails deterministically because the
  client-disconnect defect persists → **Mitigation**: REQ-005 allows the skip to stay with a
  refreshed, current-reason comment citing the archived path.
- **Risk**: SSE tests hang if finite-timeout wiring is wrong → **Mitigation**: only the proven
  `_reconnect_ids()` termination pattern; no unbounded stream reads.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Two-lifecycle fixture + probe (REQ-001, REQ-003) | Pending | — | — | |
| 2 | Scenario tests, renames, skip resolution (REQ-002, REQ-004..REQ-006) | Pending | — | — | |
| 3 | Verification gates (no deploy step; tests only) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-02 probe outcome unknown until Phase 1 runs | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261028-122337_ebresumetest004_subscribe-restart-integration-tests.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-234121
- **Related target files**: `tests/eventbus/eventbus_helpers.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_replay_subscribe.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1 | tests/eventbus/eventbus_helpers.py | Phase 1 | AC-2 | Probe test | Explicit in issue |
| REQ-002 | Issue Required Changes bullet 2 | tests/eventbus/test_eventbus_restart_resume.py | Phase 2 | AC-1, AC-4 | Seven scenario tests | Explicit in issue |
| REQ-003 | Issue Required Changes bullet 3 | tests/eventbus/eventbus_helpers.py | Phase 1 | AC-2 | Leak assertions in probe | Explicit in issue |
| REQ-004 | Issue Required Changes bullet 4 | tests/eventbus/test_eventbus_replay_subscribe.py | Phase 2 | AC-3 | collect-only diff | Explicit in issue |
| REQ-004 | Issue Required Changes bullet 4 | tests/eventbus/test_eventbus_restart_resume.py | Phase 2 | AC-3 | collect-only diff | Explicit in issue |
| REQ-005 | Issue Required Changes bullet 5 | tests/eventbus/test_eventbus_restart_resume.py | Phase 2 | AC-3 | Unskip run (UNK-01) | Needs confirmation |
| REQ-006 | Issue Constraints bullet 1 | tests/eventbus/test_eventbus_restart_resume.py | Phase 2 | AC-4 | Double-run determinism | Explicit in issue |
