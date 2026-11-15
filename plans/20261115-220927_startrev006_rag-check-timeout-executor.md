## Goal
- Make the startup RAG consistency check stoppable, so that when its startup bound expires the check actually stops, releases its database connection, and no longer delays process exit.

## Priority
Medium

## Scope
- **In-Scope**: a public stop hook on `SQLiteHelper` built on SQLite's progress handler; an optional stop event on `RagMaintenanceService.consistency`; the RAG step of `StartupValidationPipeline.check_services` creating the event, passing it, and setting it when the bound expires; the bound as a named module constant so tests can shorten it; tests; one documentation sentence.
- **Out-of-Scope**: what the consistency check verifies and its severity classification (`scripts/db/rag_consistency.py` is not modified); the check's performance on large databases; making other executor-backed calls cancellable; the shutdown-signal handling of startup stages (`issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md`, which will reuse the stop event added here).
- **Dependencies**: related, not blocking: `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md` (abandoning this wait on a shutdown request needs the same stop; implement this Plan first so that issue reuses the event). `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` edits the head of `StartupValidationPipeline.check_services`; this Plan edits its RAG step (a different part of the method); implement Plan 005 first. `plans/20261115-043850_dbreview005_helper-open-leak.md` reworks `SQLiteHelper.open` in the same file as the new method (sequencing only, see Assumptions).

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214906_startrev006_rag-check-timeout-executor.md`).
- `StartupValidationPipeline.check_services` runs `RagMaintenanceService().consistency()` in the default thread executor under `asyncio.wait_for`; on a timeout it records a warning and continues. The worker thread keeps running, because a running executor job cannot be cancelled, and it keeps its `rag` database connection open.
- Reproduced in the review: a 3 s blocking call in the default executor under a 0.2 s `wait_for` raised the timeout at 0.2 s and `asyncio.run` returned at 3.0 s, when the worker finished (the mechanism; the real duration of `consistency()` on a production-sized database is not measured).
- `RagMaintenanceService.consistency` opens `SQLiteHelper("rag")` and calls `check_rag_consistency`, a series of read-only queries, each stage wrapped in `except sqlite3.Error` that records a diagnostic and moves on (Explicit in code, read in Step 3).
- Found in Step 2 of this cycle: a connection-level stop is available without touching the check. SQLite's progress handler can abort a long query when a `threading.Event` is set; reproduced with a throwaway script: a long query aborted with `OperationalError: interrupted` 0.2 s after the event was set. `SQLiteHelper` exposes no such hook today, so one public method is added there.
- The Issue left the placement of the stop open; it is decided here (connection level, in `SQLiteHelper`, used by `RagMaintenanceService`).
- `consistency()` has one other caller, `cmd_session._rag_consistency`; the new argument is optional, so that caller is unchanged.
- Related, not overlapping: `plans/20261115-050112_dbreview006_maintenance-error-semantics.md` changes the maintenance error contract in `db.maintenance`, not this timeout.

## Problem
After a timeout the agent starts and runs, and on exit `asyncio.run` blocks until the consistency check completes (bounded only by the runtime's own executor join limit), so a slow check shows up as a hang at shutdown long after the "timed out" message, and the thread holds a database connection for that whole time. The message and the behavior disagree.

## Reason for Change
The check exists to catch corruption early; when it is slow it is exactly the case in which the user waits most. The fix is small and local. Medium because the effect is delay and a lingering connection, not data corruption.

## Implementation Intent
Give the check its own stop. `SQLiteHelper` gains a public method that installs a progress handler on its connection which aborts the running statement when a given `threading.Event` is set. `RagMaintenanceService.consistency` takes an optional `stop` event and installs the hook when given one. The pipeline creates an event per run, passes it, and sets it when `wait_for` times out; the aborted queries surface as `sqlite3.Error`, which `check_rag_consistency` already records as diagnostics, and the context manager closes the connection. Result semantics are unchanged: fatal findings stay fatal, a timeout stays a warning with startup continuing. The check's code and the `scripts/db/rag_consistency.py` module are not modified.

## Requirements
- `REQ-001`: `SQLiteHelper` provides a public method that makes the running SQL statement abort promptly once a given `threading.Event` is set, and leaves behavior unchanged when it is never called.
- `REQ-002`: `RagMaintenanceService.consistency` accepts an optional stop event, installs the hook when given one, and behaves exactly as today without one.
- `REQ-003`: When the startup bound expires, the pipeline sets the stop event, reports the existing warning, and the consistency run stops within a short, tested interval and releases its connection.
- `REQ-004`: Closing the event loop after a timed-out check does not wait for the check's natural duration.
- `REQ-005`: A check that finishes in time behaves as before, including fatal findings, and the RAG step's timeout bound is a named constant.
- `REQ-006`: The startup validation design text for the RAG step states that the timeout stops the check and startup continues with RAG consistency unverified.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/helper.py | Provide the stop hook | Add a public method (for example `interrupt_when(stop, check_every=...)`) that installs `sqlite3.Connection.set_progress_handler` returning non-zero while `stop` is set; document that the aborted statement raises `sqlite3.OperationalError` | REQ-001; AC-1 | `SQLiteHelper` at line 64 holds the connection (`_require_conn` at line 141) and exposes `execute`, `executemany`, `commit` but no progress-handler or interrupt hook; no `set_progress_handler` or `.interrupt(` anywhere in `scripts/`; 18197 bytes, limit 24576 (checked in Step 3) | tests/db/test_sqlite_helper.py | Verified |
| scripts/agent/services/rag_maintenance_service.py | Accept the stop event | Give `RagMaintenanceService.consistency` an optional keyword `stop: threading.Event \| None = None`; when given, call the new helper hook right after `open()` | REQ-002; AC-2 | `consistency` at line 46 opens `SQLiteHelper("rag").open()` and calls `check_rag_consistency(db)` with no deadline; callers: `startup_validation.py` and `cmd_session._rag_consistency` (checked in Step 3) | tests/agent/test_startup_validation.py | Verified |
| scripts/agent/startup_validation.py | Create, pass and set the event; name the bound | In the RAG step of `check_services`, create a `threading.Event` per run, pass it to `consistency`, set it in the `TimeoutError` handler, and replace the literal `30.0` by a module constant | REQ-003, REQ-004, REQ-005; AC-3, AC-4, AC-5 | The RAG step at lines 219-258: `run_in_executor(None, lambda: RagMaintenanceService().consistency())` under `asyncio.wait_for(..., timeout=30.0)`; radon C (17) for `check_services` (checked in Step 3 and Step 5) | tests/agent/test_startup_validation.py | Verified |
| tests/db/test_sqlite_helper.py | Hook tests | Add tests: with the event set, a long statement aborts with `sqlite3.OperationalError` within a short bound; with the event never set, statements are unaffected; the hook can be installed on a reused connection without error | REQ-001; AC-1, AC-6 | The file holds helper test classes such as `TestReuseConnection` (line 261) using temporary databases (checked in Step 3) | tests/db/test_sqlite_helper.py | Verified |
| tests/agent/test_startup_validation.py | Pipeline tests | Add tests: a fake `RagMaintenanceService` whose `consistency(stop=...)` blocks until the event is set; after a shortened bound the warning is reported, the event is set, the fake returns, and `asyncio.run` of the check returns without waiting for the fake's natural duration; an in-time check still reports fatal findings | REQ-003, REQ-004, REQ-005; AC-3, AC-4, AC-5, AC-6 | The file patches `RagMaintenanceService` as `MagicMock(return_value=rag_service)` (lines 66, 222, 352) and asserts `rag_consistency` outcomes (lines 94, 263-312) (checked in Step 3) | tests/agent/test_startup_validation.py | Verified |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Document the stop | In the startup validation description (line 60 area), state that the RAG consistency check is bounded, that the timeout stops the check, and that startup then continues with RAG consistency unverified | REQ-006; AC-7 | Line 60 describes the two validation stages and lists their checks without the stop behavior (checked in Step 3) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/rag_consistency.py | `check_rag_consistency` records `sqlite3.Error` per stage and continues; the aborted statements must surface as that error class | REQ-002, REQ-003 |
| scripts/agent/commands/cmd_session.py | The other caller of `consistency()`; it must stay unchanged | REQ-002 |
| tests/agent/test_startup.py | Patches `RagMaintenanceService` for the `rag_consistency` outcomes; must keep passing | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): With the stop event set, a long statement on a `SQLiteHelper` connection aborts with `sqlite3.OperationalError` within a short bound; with the event never set, statements run unchanged.
- AC-2 (REQ-002): `RagMaintenanceService.consistency()` without arguments behaves exactly as before; with `stop` it installs the hook before running the check.
- AC-3 (REQ-003): After the startup bound expires, the event is set, the pipeline reports the existing timeout warning, and the consistency run returns within a short, tested interval with its connection closed.
- AC-4 (REQ-004): `asyncio.run` of a pipeline run whose check timed out returns without waiting for the fake check's natural duration.
- AC-5 (REQ-005): A check that finishes in time yields the same outcomes as before, including a fatal finding as a pipeline fatal; the RAG step's bound is a named module constant.
- AC-6 (REQ-001, REQ-003): `uv run pytest tests/db/test_sqlite_helper.py tests/agent/test_startup_validation.py tests/agent/test_startup.py` passes with the new cases, and the stop tests fail against the pre-change code.
- AC-7 (REQ-006): The startup validation description states the bounded check and its stop; `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` pass.
- AC-8 (REQ-001, REQ-002, REQ-003): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: helper tests with a temporary database and a long self-join statement; the event is set from a timer thread; assert `sqlite3.OperationalError` and a short elapsed time; a control run with the event never set.
- REQ-002, REQ-003, REQ-004: pipeline tests with a fake service whose `consistency` loops on `stop.is_set()`; the module constant is monkeypatched to a small value; assert the warning, the set event, and the loop-close time.
- REQ-005: an in-time fake returning a fatal finding still produces a pipeline fatal; the existing `rag_consistency` outcome tests keep passing.
- REQ-006: documentation checks listed under AC-7.
- Write the stop tests first and confirm they fail on the current code.

## Documentation Impact
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` must be updated (REQ-006): one sentence on the bounded RAG consistency check, that the timeout stops the check, and that startup continues with RAG consistency unverified. Policy only: no timeout values, counts or file lists (`skills/DESIGN.md` Docs content policy).

## Assumptions
- The progress-handler approach stops `check_rag_consistency` without modifying it because each stage catches `sqlite3.Error` and continues; after the event is set, a stage whose queries are short may still complete, and the discarded report is not used on a timeout; falsifiable by the pipeline test (the fake) plus a helper test against a real long statement.
- A `check_every` operation count of the order of a thousand VM steps keeps the handler overhead negligible while bounding the abort latency to milliseconds; the exact value is chosen at implementation time and measured in the helper test.
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports four findings naming this Plan. (1) `scripts/agent/startup_validation.py` and (2) `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, shared with `plans/20261115-220913_startrev005_posture-probed-twice-startup.md`: compatible with a sequencing preference; Plan 005 edits the head of `check_services` and the readiness description, this Plan edits the RAG step and the startup-validation description, so no line or sentence is shared; implement Plan 005 first. (3) `scripts/db/helper.py` and (4) `tests/db/test_sqlite_helper.py`, shared with `plans/20261115-043850_dbreview005_helper-open-leak.md`: compatible; that Plan reworks the failure paths of `open`, `_connect` and `_load_vec_extension`, this Plan only adds one public method and its tests; at implementation time confirm that `_require_conn` still returns the connection that `open` stored after that Plan's change, and place the new method outside `open`. No Plan is a hard prerequisite of the other.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How long `consistency()` takes on the production-sized `rag` database, which sets how visible the exit delay is | A timed run on production data (not run here; production paths are not touched by tests) | Operational observation after deployment; the fix does not depend on it | False |
| UNK-02 | Order against `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md`, which will reuse the stop event (open sibling issue, related, not blocking) | The shape of the shutdown race in that issue | Implement this Plan first: `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md` | False |
| UNK-03 | Order against `plans/20261115-220913_startrev005_posture-probed-twice-startup.md`, which edits the head of `check_services` (open sibling Plan, related, not blocking) | Merge order of two edits to one method | Implement Plan 005 first; the edits touch different parts: `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` | False |
| UNK-04 | Interaction with `plans/20261115-043850_dbreview005_helper-open-leak.md`, which reworks `SQLiteHelper.open` (open Frozen Plan, related, not blocking) | Whether `_require_conn` still returns the opened connection after that Plan | Re-read the final shape of `open` at implementation time; `plans/20261115-043850_dbreview005_helper-open-leak.md` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/helper.py | Modify | Medium: `SQLiteHelper` is used by every database consumer; the change only adds a method and leaves existing behavior untouched | 4 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/services/rag_maintenance_service.py | Modify | Low: two callers; the new keyword is optional | 3 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_validation.py | Modify | Medium: every agent startup passes through `check_services`; the change touches only the RAG step | 10 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/db/test_sqlite_helper.py | Modify | Low: tests only | 5 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_startup_validation.py | Modify | Low: tests only | 8 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Modify | Low: one sentence of one design document | 17 | High: one author | not applicable (rsynced): `docs/` is not deployed |

## Design
- **Design decision (where the stop lives)**: options weighed. (1) A cooperative flag inside `check_rag_consistency`: rejected, it is shared with the recovery verification and would thread a parameter through eight query helpers. (2) A dedicated thread instead of the default executor: rejected, the thread still cannot be stopped. (3) Run the check in a subprocess and kill it: rejected as disproportionate. (4) A connection-level stop through SQLite's progress handler, exposed as one public `SQLiteHelper` method: chosen; it stops the work in the one place where the time is spent and leaves the check untouched. Compatibility impact: none for existing callers; one new public method and one optional keyword.
- **Failure semantics**: after the event is set, aborted statements raise `sqlite3.OperationalError`, a `sqlite3.Error`, which each stage of `check_rag_consistency` already records as a diagnostic; the pipeline discards that report on a timeout and reports the existing warning.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `rag_maintenance_service.py` already imports `SQLiteHelper`; `helper.py` adds only a standard-library `threading` import; no cross-layer import is added (checked in Step 5).
- **Dependency graph**: `consistency()` is called by `startup_validation.py` and `cmd_session.py`; `SQLiteHelper.open()` is used widely and unchanged (checked in Step 3).
- **Historical analysis**: `helper.py` 4 commits, `rag_maintenance_service.py` 3, `startup_validation.py` 10, `test_sqlite_helper.py` 5 and `test_startup_validation.py` 8 in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: no port or service is touched; the check opens the production `rag` database in production, and tests use temporary databases (the test suite's isolation applies); the stop makes the connection close earlier, not later (checked in Step 5).
- **Persisted schema check**: no DDL, schema version or migration is touched, so `rules/persisted-schema-change.md` does not apply.
- **Validation quality baseline**: radon: `check_services` C (17) today and the change adds no branch beyond the handler line; vulture and bandit: no finding in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Stop hook on the helper**
   - [ ] Write the helper hook tests first and confirm they fail before the change (REQ-001; tests/db/test_sqlite_helper.py)
   - [ ] Add the public stop method on `SQLiteHelper` (REQ-001; scripts/db/helper.py)
2. **Phase 2: Service and pipeline**
   - [ ] Write the pipeline stop tests first and confirm they fail on the current code (REQ-003, REQ-004, REQ-005; tests/agent/test_startup_validation.py)
   - [ ] Add the optional `stop` keyword to `consistency` (REQ-002; scripts/agent/services/rag_maintenance_service.py)
   - [ ] In the RAG step, create the event, pass it, set it on timeout, and name the bound (REQ-003, REQ-004, REQ-005; scripts/agent/startup_validation.py)
3. **Phase 3: Documentation**
   - [ ] State the bounded check and its stop in the startup validation description (REQ-006; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
4. **Phase 4: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002, REQ-003; scripts/db/helper.py, scripts/agent/services/rag_maintenance_service.py, scripts/agent/startup_validation.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/helper.py | Unit | `uv run pytest tests/db/test_sqlite_helper.py tests/db/test_helper_thread_safety.py -q` | New hook tests pass; existing helper tests pass |
| scripts/agent/services/rag_maintenance_service.py and scripts/agent/startup_validation.py | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py -q` | Stop tests pass; existing `rag_consistency` outcome tests pass |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | `helper.py` stays under its limit; no drift |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Documentation | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_content_policy.py` | No findings |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: The progress handler adds overhead to every statement on the connection it is installed on (likelihood low) → **Mitigation**: installed only on the consistency connection and only when a stop event is passed; the check interval is chosen so the overhead is negligible and measured in the helper test.
- **Risk**: A stage whose statements are short is not interrupted and the thread lingers briefly after the event is set (likelihood low) → **Mitigation**: the stages are bounded by the same statements the progress handler sees; the pipeline test and the helper test assert the stop interval.
- **Risk**: `SQLiteHelper` is a widely used class and a public method is added (likelihood low) → **Mitigation**: the method is additive and unused unless called; helper tests and thread-safety tests run in the validation plan.
- **Risk**: Plans 005 and this Plan, and a later Plan for the sibling issue, edit `check_services` (likelihood medium) → **Mitigation**: implement Plan 005 first, this Plan second, and the shutdown-signal work third; each edit touches a different part of the method.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Stop hook on the helper (scripts/db/helper.py, tests/db/test_sqlite_helper.py) | Pending | — | — | |
| 2 | Service and pipeline (scripts/agent/services/rag_maintenance_service.py, scripts/agent/startup_validation.py, tests/agent/test_startup_validation.py) | Pending | — | — | |
| 3 | Documentation (docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md) | Pending | — | — | |
| 4 | Deployment and verification (scripts/db/helper.py, scripts/agent/services/rag_maintenance_service.py, scripts/agent/startup_validation.py) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214906_startrev006_rag-check-timeout-executor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-220927
- **Related target files**: scripts/db/helper.py, scripts/agent/services/rag_maintenance_service.py, scripts/agent/startup_validation.py, tests/db/test_sqlite_helper.py, tests/agent/test_startup_validation.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1); progress-handler reproduction in Step 2 | scripts/db/helper.py | Phase 1 | AC-1 | helper hook tests | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes (2); Testing Expectations | tests/db/test_sqlite_helper.py | Phase 1 | AC-1, AC-6 | `uv run pytest tests/db/test_sqlite_helper.py -q` | Derived from confirmed evidence |
| REQ-002 | Issue Implementation Intent (the check's own bound); Unresolved Questions (placement decided in Step 2) | scripts/agent/services/rag_maintenance_service.py | Phase 2 | AC-2 | service and pipeline tests | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes (1), (2); Acceptance Criteria (1) | scripts/agent/startup_validation.py | Phase 2 | AC-3 | pipeline stop test | Confirmed by repository evidence |
| REQ-004 | Issue Acceptance Criteria (2); executor reproduction | scripts/agent/startup_validation.py | Phase 2 | AC-4 | loop-close time test | Confirmed by repository evidence |
| REQ-005 | Issue Constraints (fatal findings stay fatal; timeout stays a warning) | scripts/agent/startup_validation.py | Phase 2 | AC-5 | in-time fatal-finding test | Explicit in issue |
| REQ-003 | Issue Required Changes (4); Testing Expectations | tests/agent/test_startup_validation.py | Phase 2 | AC-3, AC-6 | `uv run pytest tests/agent/test_startup_validation.py -q` | Explicit in issue |
| REQ-004 | Issue Acceptance Criteria (2) | tests/agent/test_startup_validation.py | Phase 2 | AC-4, AC-6 | loop-close time test | Explicit in issue |
| REQ-005 | Issue Acceptance Criteria (3) | tests/agent/test_startup_validation.py | Phase 2 | AC-5, AC-6 | in-time fatal-finding test | Explicit in issue |
| REQ-006 | Issue Documentation Impact; line 60 of the startup health document | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Phase 3 | AC-7 | `check_docs_quality`, `check_docs_content_policy` | Explicit in issue |
