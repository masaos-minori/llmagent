## Goal
- Make a test-suite run fail, naming the file, when any file under `/opt/llm/db/` changed during the run, including changes made by a subprocess that the per-test in-process guard cannot see.

## Priority
High

## Scope
- **In-Scope**:
  - A session-level fingerprint of the production database files (existence, size, modification time, content hash from a byte-level read, including `-wal` and `-shm` sidecars) recorded at session start and compared at session finish.
  - Skipping the check silently when `/opt/llm/db` does not exist (CI, other hosts), and an explicit opt-out through the existing `production_paths_allowed` marker.
  - Making `tools/check_conftest_integrity.py` require the new detection so it cannot be removed silently.
  - A small shared fixture that builds an isolated subprocess environment, and its use in `tests/deploy/test_init_db_eventbus_schema.py`.
  - A regression test that a write to a temporary stand-in "production" directory is detected.
  - One sentence in the test guidance stating the guarantee.
- **Out-of-Scope**:
  - Cleaning rows that earlier runs left in a production database (a separate owner decision).
  - Isolating non-database production paths beyond what the existing guard covers.
  - Changing the migration or deploy procedure, and any change to a production file.
- **Dependencies**: N/A: none. Re-verified in Step 2 (2026-11-02): no open Issue or Plan lists `tests/conftest.py`, `tools/check_conftest_integrity.py`, or `tests/deploy/test_init_db_eventbus_schema.py` as a target. `tools/check_plan_target_overlaps.py` found no overlap for this Plan.

## Background
- `Operationally observed` (2026-10-30, from the Issue): the full suite modified the production `workflow.sqlite` through `tests/deploy/test_init_db_eventbus_schema.py`, which runs the real `deploy/init_db.sh`; the `create_schema.py` subprocess reached the production default path. No test failed and no guard fired.
- `Explicit in code` (checked in Step 3): `tests/conftest.py` `_forbid_production_paths` (autouse, function scope) patches `sqlite3.connect` and `logging.FileHandler.__init__` inside the test process only. The helper `_run` in the deploy test builds its environment from `PATH` and `HOME` only, so the isolation variables set by `conftest.py` are not inherited.
- `Explicit in code` (checked in Step 3): `tests/conftest.py` already defines `pytest_sessionfinish`, which only removes the isolation root. `tools/check_conftest_integrity.py` verifies required autouse fixtures only (`REQUIRED_AUTOUSE_FIXTURES`); it does not inspect hooks.
- Verified in Step 2 (2026-11-02, read-only `immutable=1` query): the current production `workflow.sqlite` has no `schema_migrations` table and its modification time is 2026-09-20, so the earlier contamination is no longer present; only the missing detection remains.
- `Explicit in code` (checked in Step 3): at least four other test modules (`tests/deploy/test_start_agent_preflight.py`, `tests/deploy/test_init_db_ledger_gate.py`, `tests/deploy/test_load_env_gate.py`, `tests/eventbus/test_eventbus_startup.py`) also build a subprocess `env` by hand. `pytest-xdist` is a declared dependency, so session-scoped fixtures can run once per worker.

## Problem
Isolation depends on every test setting up its own environment correctly. A test that spawns a subprocess with a custom environment bypasses all in-process guards; the only symptom is a changed production file, found by a person comparing timestamps.

## Reason for Change
The affected data is the live workflow database (and, in principle, the other databases). A silent write by a test run is a data-integrity risk, and schema work now being deployed makes the production file state meaningful to the migration procedure.

## Implementation Intent
Add a detection that does not depend on test authors: record a read-only fingerprint of the production database files at session start and compare at session finish, failing the run and naming each changed file. Skip silently when `/opt/llm/db` is absent. Keep the per-test guard unchanged. Add a fixture that builds an isolated subprocess environment so tests that spawn processes stop rebuilding it by hand.

## Requirements
- `REQ-001`: A session-level check MUST fingerprint every file under the production database directory (including `-wal` and `-shm`) at session start using only file metadata and byte-level reads, and MUST fail the session at finish with a message naming each changed, added, or removed file. A change to a sidecar alone MUST count.
- `REQ-002`: The check MUST be skipped silently when the production database directory does not exist, and a test carrying `production_paths_allowed` MUST NOT cause its own legitimate changes to be attributed to the session.
- `REQ-003`: `tools/check_conftest_integrity.py` MUST fail when the new detection is removed from `tests/conftest.py`.
- `REQ-004`: An isolated-subprocess-environment fixture MUST be added to `tests/conftest.py` and used by `tests/deploy/test_init_db_eventbus_schema.py`, so the subprocess inherits the isolation variables.
- `REQ-005`: A regression test MUST show that a write to a temporary stand-in directory is detected and that an unchanged directory and an absent directory pass.
- `REQ-006`: The test guidance MUST state in one sentence that a session which changes production database files fails.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/conftest.py` | Session fingerprint fixture and the isolated-subprocess-environment fixture | The existing guard is in-process only; `_PRODUCTION_ROOT`, `_CREATED_ROOT`, and `pytest_sessionfinish` exist but nothing detects a subprocess write | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-4 | `_forbid_production_paths`, `_is_production_path`, `pytest_sessionfinish`, `_PRODUCTION_ROOT` (checked in Step 3) | `tests/test_production_isolation.py` | Verified |
| `tools/check_conftest_integrity.py` | Require the new fixture | `REQUIRED_AUTOUSE_FIXTURES` lists three fixtures; a removed detection would pass silently | REQ-003 / AC-3 | `REQUIRED_AUTOUSE_FIXTURES`, `extract_autouse_fixture_names` (checked in Step 3) | `tests/tools/test_check_conftest_integrity.py` | Verified |
| `tests/tools/test_check_conftest_integrity.py` | Test the new requirement | The tests cover missing and non-autouse fixtures for the current names only | REQ-003 / AC-3 | `test_missing_fixture_name_is_reported`, `test_fixture_present_but_not_autouse_is_still_missing` (checked in Step 3) | itself | Verified |
| `tests/test_production_isolation.py` | Regression tests for the detection | It already tests the guard and the opt-out marker; add stand-in directory detection tests | REQ-002, REQ-005 / AC-1, AC-2 | `test_guard_rejects_production_sqlite_connect`, `test_opt_out_marker_skips_guard` (checked in Step 3) | itself | Verified |
| `tests/deploy/test_init_db_eventbus_schema.py` | Use the isolated-environment fixture | `_run` builds `env` from `PATH` and `HOME` only | REQ-004 / AC-4 | `_run` in the test module (checked in Step 3) | itself | Verified |
| `skills/python-test-and-fix/workflow.md` | One sentence on the guarantee | The production-isolation paragraph says the guard fails a test that opens a database; it does not say a changed production file fails the session | REQ-006 / AC-5 | "Verify Production Isolation" paragraph (checked in Step 3) | `check_skills_references.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `skills/python-test-and-fix/SKILL.md` | Core rule "Verify Production Isolation Before Running Tests" that the workflow sentence must stay consistent with | REQ-006 |
| `rules/toolchain.md` | Alternative location considered for the guarantee sentence; stays unchanged | REQ-006 |
| `tests/deploy/test_init_db_ledger_gate.py` | Another caller that builds a subprocess `env` by hand; informs the fixture signature, not modified | REQ-004 |
| `deploy/init_db.sh` | The script the deploy test runs; confirms which environment overrides it honors | REQ-004 |
| `pyproject.toml` | Marker registration and `pytest-xdist` dependency | REQ-001, REQ-002 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-005`): A test that writes to a configured stand-in production directory makes the session fail with a message naming the file; a sidecar-only change is also detected.
- AC-2 (`REQ-002`, `REQ-005`): A run that changes nothing passes; the check is skipped when the directory is absent; a change made inside a test marked `production_paths_allowed` does not fail the session.
- AC-3 (`REQ-003`): `check_conftest_integrity.py` reports a finding when the new fixture is removed from `tests/conftest.py`.
- AC-4 (`REQ-004`): The deploy test uses the fixture and passes; the subprocess environment contains the isolation variables.
- AC-5 (`REQ-006`): `skills/python-test-and-fix/workflow.md` states the guarantee; `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-6 (`REQ-001`): One full-suite run on this host passes with the check enabled, and the production file metadata compared by hand before and after is unchanged.

## Tests
- `REQ-001`, `REQ-002`, `REQ-005`: unit tests of the fingerprint and compare helpers against a temporary directory used as the stand-in (changed, added, removed, sidecar-only, unchanged, absent), plus the opt-out case.
- `REQ-003`: tests of the checker with the fixture present and absent.
- `REQ-004`: the existing deploy test run with the fixture.
- `REQ-001`: one full-suite run with a read-only before/after comparison of the production files.

## Documentation Impact
- Yes, small: one sentence in `skills/python-test-and-fix/workflow.md` (REQ-006). No `docs/*.md` change: this Plan changes test infrastructure, not system design documentation.

## Assumptions
- A1: A changed `-wal` or `-shm` sidecar alone, without a main-file change, counts as a production touch (from the Issue). Falsifiable by a read-only open creating a sidecar; the fingerprint uses plain file reads, never a SQLite connection.
- A2: The production databases are small (tens of kilobytes each; `/opt/llm/db` listing in Step 2), so a content hash on every session start and finish is affordable. Falsifiable by measuring the check's overhead.
- A3: The check is skipped in CI because `/opt/llm/db` is absent there (from the Issue).
- A4: Under `pytest-xdist` each worker records its own baseline; a change by any worker is reported by every worker that observes it. Falsifiable by an xdist run.
- A5: Design choice (recorded in Design): the detection is a session-scoped autouse fixture, not a hook, because `check_conftest_integrity.py` inspects autouse fixtures only.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a failing session-fixture teardown gives an acceptable report (the error attaches to the last test) | Not exercised; `pytest_sessionfinish` exit-status handling is the alternative | Try the fixture teardown first; if the report is unclear, fall back to reporting from `pytest_sessionfinish` and extend the checker | False |
| UNK-02 | Whether the check should also run in CI | CI has no `/opt/llm/db`; behavior there is assumed to be a skip | Confirm with a run on a host without the directory | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/conftest.py` | Modify | High (loaded by every test) | 6 | N/A | not applicable (rsynced) |
| `tools/check_conftest_integrity.py` | Modify | Low (pre-commit hook only) | 1 | N/A | not applicable (rsynced) |
| `tests/tools/test_check_conftest_integrity.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `tests/test_production_isolation.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_eventbus_schema.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `skills/python-test-and-fix/workflow.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |

## Design
- Detection: a session-scoped autouse fixture records a fingerprint map for every file under the production database directory: size, `st_mtime_ns`, and a content hash from a plain byte read, never a SQLite connection. At teardown it recomputes the map and fails, naming every file that changed, appeared, or disappeared. If the directory is absent at start, the fixture yields without doing anything.
- Opt-out semantics: after a test carrying `production_paths_allowed` finishes, the baseline is refreshed, so that test's legitimate changes are not attributed to the session while later tests are still covered. Alternative rejected: skipping the whole session check when any selected test has the marker (it would disable the check whenever `tests/test_production_isolation.py` runs).
- Why a fixture: `tools/check_conftest_integrity.py` checks autouse fixtures only, so a fixture is protected by adding its name to `REQUIRED_AUTOUSE_FIXTURES`; the alternative (a `pytest_sessionfinish` change plus a checker extension) is kept as the fallback in UNK-01.
- Stand-in testing: the fixture reads the production directory from a module-level constant so a test can point it at a temporary directory without touching `/opt/llm`.
- Subprocess environment: a non-autouse fixture in `tests/conftest.py` returns the isolation variables (the same ones the module sets for the test process) merged with the caller's extras and the `PATH`/`HOME` the real scripts need. The deploy test adopts it; the other four hand-built callers stay unchanged (out of scope; adopting them is a later cleanup).
- Compatibility: the per-test guard is unchanged; no production file is written or opened with a writing connection.

## Implementation steps
1. **Phase 1: Detection and its tests**
   - [ ] Add the fingerprint helpers and the session-scoped autouse fixture to `tests/conftest.py` (`REQ-001`, `REQ-002`; `tests/conftest.py`)
   - [ ] Add stand-in directory tests for changed, added, removed, sidecar-only, unchanged, absent, and opt-out cases (`REQ-002`, `REQ-005`; `tests/test_production_isolation.py`)
2. **Phase 2: Integrity checker**
   - [ ] Add the fixture name to `REQUIRED_AUTOUSE_FIXTURES` and extend the checker tests (`REQ-003`; `tools/check_conftest_integrity.py`, `tests/tools/test_check_conftest_integrity.py`)
3. **Phase 3: Subprocess environment fixture**
   - [ ] Add the isolated-subprocess-environment fixture to `tests/conftest.py` and use it in the deploy test (`REQ-004`; `tests/conftest.py`, `tests/deploy/test_init_db_eventbus_schema.py`)
4. **Phase 4: Guidance and verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Add the guarantee sentence (`REQ-006`; `skills/python-test-and-fix/workflow.md`)
   - [ ] Run one full-suite run and compare the production file metadata by hand before and after; run the checkers named in the Validation plan (`REQ-001`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/conftest.py`, `tests/test_production_isolation.py` | Unit over a temporary stand-in directory | `uv run pytest tests/test_production_isolation.py -v` | all pass |
| `tools/check_conftest_integrity.py` | Unit | `uv run pytest tests/tools/test_check_conftest_integrity.py -v`; `uv run python tools/check_conftest_integrity.py` | passes; reports a finding when the name is removed in the fixture test |
| `tools/check_conftest_integrity.py` | Lint, type, security on the changed tool | `uv run ruff format tools/check_conftest_integrity.py`; `uv run ruff check tools/check_conftest_integrity.py`; `uv run mypy tools/check_conftest_integrity.py`; `uv run bandit tools/check_conftest_integrity.py` | clean |
| `tests/deploy/test_init_db_eventbus_schema.py` | Integration | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` | passes |
| Full suite | Integration (AC-6) | `uv run pytest -v` with `stat` of `/opt/llm/db` files before and after | passes; metadata unchanged |
| `skills/python-test-and-fix/workflow.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |

## Risks
- **Risk**: A session fixture teardown error is attached to the last test and confuses the report. → **Mitigation**: UNK-01 names the `pytest_sessionfinish` fallback; the failure message names the changed file.
- **Risk**: Under `pytest-xdist` several workers report the same change. → **Mitigation**: Assumption A4; the duplication is harmless and is checked in one xdist run.
- **Risk**: Reading the databases while a real service writes them produces a false positive on a host where services run. → **Mitigation**: the production services are separate processes on this host; a change in the window is exactly what the check should surface, and the message names the file so a person can judge; the opt-out marker exists for legitimate cases.
- **Risk**: The shared environment fixture changes what the deploy test's subprocess sees (for example an inherited `LLMAGENT_CONFIG_DIR` overriding the test's own sandbox config). → **Mitigation**: the deploy test is the only adopter, and its existing assertions run in AC-4; the full-suite run in AC-6 is the independent check.
- **Risk**: Blast radius of `tests/conftest.py` is every test file. → **Mitigation**: the new fixture does nothing when the directory is absent and only reads files otherwise; one full-suite run is part of verification.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Detection and its tests: `tests/conftest.py`, `tests/test_production_isolation.py` | In Progress | — | — |  |
| 2 | Integrity checker: `tools/check_conftest_integrity.py`, `tests/tools/test_check_conftest_integrity.py` | In Progress | — | — |  |
| 3 | Subprocess environment fixture: `tests/conftest.py`, `tests/deploy/test_init_db_eventbus_schema.py` | In Progress | — | — |  |
| 4 | Guidance and verification: `skills/python-test-and-fix/workflow.md` and a full-suite run | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261102-084616_01_tests_conftest.py.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261102-084616_02_tools_check_conftest_integrity.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261102-084616_03_tests_tools_test_check_conftest_integrity.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261102-084616_04_tests_test_production_isolation.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261102-084616_05_tests_deploy_test_init_db_eventbus_schema.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-084616_06_skills_python-test-and-fix_workflow.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-075648
- **Related target files**: `tests/conftest.py`, `tools/check_conftest_integrity.py`, `tests/tools/test_check_conftest_integrity.py`, `tests/test_production_isolation.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `skills/python-test-and-fix/workflow.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (session fingerprint); Implementation Intent | `tests/conftest.py` | Phase 1 | AC-1, AC-6 | stand-in directory tests; full-suite run | Explicit in issue |
| REQ-002 | Required Changes (opt-out marker); Constraints (no effect without `/opt/llm/db`) | `tests/conftest.py` | Phase 1 | AC-2 | opt-out and absent-directory tests | Explicit in issue |
| REQ-002 | Testing Expectations (detection tests) | `tests/test_production_isolation.py` | Phase 1 | AC-2 | stand-in directory tests | Explicit in issue |
| REQ-003 | Required Changes (integrity checker); Background (checker inspects autouse fixtures only) | `tools/check_conftest_integrity.py` | Phase 2 | AC-3 | checker tests | Confirmed by repository evidence |
| REQ-003 | Testing Expectations (checker tests) | `tests/tools/test_check_conftest_integrity.py` | Phase 2 | AC-3 | fixture-removed test | Explicit in issue |
| REQ-004 | Required Changes (isolated helper); Background (`_run` env) | `tests/conftest.py` | Phase 3 | AC-4 | deploy test run | Confirmed by repository evidence |
| REQ-004 | Target Files (deploy test uses the helper) | `tests/deploy/test_init_db_eventbus_schema.py` | Phase 3 | AC-4 | deploy test run | Explicit in issue |
| REQ-005 | Required Changes (regression test) | `tests/test_production_isolation.py` | Phase 1 | AC-1, AC-2 | stand-in directory tests | Explicit in issue |
| REQ-006 | Documentation Impact (one note in test guidance) | `skills/python-test-and-fix/workflow.md` | Phase 4 | AC-5 | `check_skills_references.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-084616 -->