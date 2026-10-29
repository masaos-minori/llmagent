# Plan: Run EventBus test fixtures through the production lifespan and shutdown path

## Goal
- Make the EventBus health fixture and the shared `make_eventbus_client()` helper start the application only through the production `lifespan()` and stop it only through its context exit (`_shutdown_lifespan()`), with no hand-built `app.state` and no hand-written teardown, and pin two sequential lifecycles with a test.

## Priority
Medium

## Scope
- **In-Scope**: the `client` fixture and the helper functions `_init_state` / `_do_cleanup` in `tests/eventbus/test_eventbus_health.py`; `make_eventbus_client()` and the helper functions `_init_state` / `_do_cleanup` in `tests/eventbus/eventbus_helpers.py`; one new test of two sequential lifecycles in `tests/eventbus/test_eventbus_shutdown.py`; recording the real helper names so the related Plan is re-verified.
- **Out-of-Scope**: any change under `scripts/`; the private schema copy and the `make_test_client` helper (`plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`); the two-lifecycle `/subscribe` restart scenarios and their fixture (`plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`); requirement-identifier cleanup (`issues/20261029-090453_eventbus004_test-requirement-id-cleanup.md`); other test files that build `app.state` by hand (see UNK-02); renaming identifiers or editing comments beyond what a fixture change requires.
- **Dependencies**: sequencing only, neither blocks this Plan. `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md` adds a two-lifecycle fixture to `tests/eventbus/eventbus_helpers.py`; this Plan adds no competing fixture and should land after it or rebase on it. `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` also edits `tests/eventbus/eventbus_helpers.py` and cites helper names that do not exist (see Design); its procedure generation must re-verify those names. Related, archived: `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (settled shutdown sequence).

## Background
`lifespan()` in `scripts/eventbus/app.py:70` clears the shutdown flag, loads the config, opens the database, populates the token maps, creates the broker, and starts the DLQ sweep task; after `yield` it awaits `_shutdown_lifespan()` (line 95), which sets the shutdown flag, stops the sweep, shuts the broker down, and closes the connection under the database lock (its docstring says the tests exercise the same sequence; only `tests/eventbus/test_eventbus_shutdown.py` calls it, directly or through `lifespan()`).

In `tests/eventbus/test_eventbus_health.py` the `client` fixture (line 49) calls `_init_state()` (line 15) on a throwaway event loop, which opens a connection and a broker, and then enters `with TestClient(eb_app.app)` (line 75), so the production lifespan opens and assigns a second pair. The first connection and broker are never closed. After the `with` block `app.state.db` is `None`, so the fixture's `_do_cleanup()` (line 28) has no connection left to close.

`make_eventbus_client()` (`tests/eventbus/eventbus_helpers.py:101`) also runs `_init_state()` (line 164) before it builds `TestClient(eb_app.app)` (line 145) and attaches a hand-written `_cleanup` (lines 151-159).

## Problem
Tests built on these fixtures run against a lifecycle the production service never creates: state initialized twice, an orphaned first connection and broker, a different teardown order, and cleanup code that is dead. A lifecycle regression in `lifespan()` or `_shutdown_lifespan()` is not seen through that scaffolding.

Corrections to the Issue (Step 2 findings, each checked once against the repository):
- The Issue says `make_eventbus_client()` does not enter the client, so the lifespan does not run. The helper itself does not enter it, but all 7 call sites enter it with `with make_eventbus_client(...) as c` (`test_eventbus_publish.py:21`, `test_eventbus_crash_ack.py:52`, `test_eventbus_slow_consumer.py:21`, `test_eventbus_subscribe_transition.py:24`, `test_eventbus_concurrent.py:19`, `test_eventbus_auth.py:1502`, `tests/deploy/test_setup_services_eventbus.py:343`). For them the production lifespan already runs and the helper's hand-built state is a second, orphaned initialization, the same defect as the health fixture. No caller needs pre-startup `app.state` mutation, so no caller has to stay on a hand-built path.
- The Issue lists `test_admin_topics_authorization.py` as a caller. It does not call `make_eventbus_client()` (the name appears in a docstring only); it builds its own state in `_make_admin_test_client` and returns an unentered `TestClient` (line 61), a separate hand-built fixture outside this Issue's target files.
- The helper's `_init_state` / `_do_cleanup` are not imported by any other test module (`rg` for imports of them from `eventbus_helpers`, checked in Step 3), and no caller uses the helper's `_cleanup` attribute (the `._cleanup()` callers in `test_eventbus_auth.py` and `test_admin_topics_authorization.py` belong to their own builders).
- The Issue's observation that the related Plan cites helpers that do not exist is confirmed: `make_event_bus_ctx`, `open_consumer_db`, and `subscribe_client` appear nowhere outside `plans/`, `issues/`, and `implementations/` (`rg`, checked in Step 2). The helpers that exist in `tests/eventbus/eventbus_helpers.py` are `eventbus_test_tokens`, `eventbus_auth_headers`, `make_eventbus_client`, `_init_state`, `_do_cleanup`, and `principal_map`. `make_test_client` is a helper that Plan intends to add, not an existing one.
- Two-lifecycle coverage partly exists: `test_shutdown_clears_app_state_db` (`test_eventbus_shutdown.py:233`) and `test_second_lifecycle_does_not_inherit_shutdown_flag` (line 255) cover the cleared connection reference and the cleared flag. What is not pinned is that the second lifecycle opens a new, usable connection rather than reusing the closed one.

## Reason for Change
The lifecycle fixes in `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` made the shutdown sequence the single supported teardown, and the fixtures should exercise it. The related Plan will fail its own verification because of the missing helper names, so the correct names are recorded here before a procedure is generated from it. No incident is cited; not time-sensitive.

## Implementation Intent
Use the production lifecycle as the contract and keep fixture code thin. The health fixture and the shared helper stop initializing state by hand and rely on the lifespan entered by `TestClient` as a context manager; the helper's hand-written teardown and its unused `_init_state` / `_do_cleanup` are removed. The helper's docstring states that the returned client must be entered as a context manager, which is how every caller already uses it. One test is added next to the existing lifecycle tests to pin the two-lifecycle behavior.

## Requirements
- `REQ-001`: the health fixture starts and stops the application only through `with TestClient(eb_app.app)`; `test_eventbus_health.py` has no `_init_state` or `_do_cleanup`, and each test opens exactly one connection and one broker.
- `REQ-002`: `make_eventbus_client()` builds the config, patches `load_config` and the schema path, and returns the `TestClient` with its default `Authorization` header, with no hand-built `app.state` and no hand-written cleanup; its signature and the callers' use as a context manager are unchanged; `_init_state` and `_do_cleanup` are removed from `tests/eventbus/eventbus_helpers.py`.
- `REQ-003`: a test shows that two sequential `lifespan()` runs in one process succeed, that the second run opens a new usable connection (the closed first connection is not reused), and that the shutdown flag does not leak into the second run.
- `REQ-004`: no production code changes, existing assertions keep their meaning, and the real helper names are recorded so the related Plan is re-verified before its implementation procedure is generated.

## Implementation Target Files
**Freeze status**: Frozen (every row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_health.py | Modify | Remove `_init_state`, `_do_cleanup`, and the hand-written setup and teardown from the `client` fixture; rely on the lifespan | REQ-001, REQ-004; AC-1 | `_init_state` at line 15, `_do_cleanup` at line 28, fixture at lines 49-92 calling `_init_state` before `with TestClient(eb_app.app) as c` at line 75 (checked in Step 2) | The existing tests in this file | Verified |
| tests/eventbus/eventbus_helpers.py | Modify | Drop the hand-built state, the `_cleanup` attribute, and the unused `_init_state` / `_do_cleanup`; document that the client must be entered | REQ-002, REQ-004; AC-2 | `make_eventbus_client` at line 101 calls `_init_state` (line 164) before `TestClient(eb_app.app)` (line 145) and defines `_cleanup` (lines 151-159); `_do_cleanup` at line 179; no importer of the two helpers and no caller of the helper's `_cleanup` (checked in Step 3) | `tests/eventbus/test_eventbus_publish.py`, `test_eventbus_crash_ack.py`, `test_eventbus_slow_consumer.py`, `test_eventbus_subscribe_transition.py`, `test_eventbus_concurrent.py`, `test_eventbus_auth.py`, `tests/deploy/test_setup_services_eventbus.py` | Verified |
| tests/eventbus/test_eventbus_shutdown.py | Modify | Add the two-sequential-lifecycles test next to the existing lifecycle tests | REQ-003; AC-3 | `test_shutdown_clears_app_state_db` at line 233 and `test_second_lifecycle_does_not_inherit_shutdown_flag` at line 255 drive `eb_app.lifespan(eb_app.app)` directly; no assertion that the second lifecycle holds a new connection (checked in Step 3) | The new test itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/app.py | `lifespan()` and `_shutdown_lifespan()` are the reference behavior; no production change | REQ-001, REQ-002, REQ-003 |
| tests/eventbus/conftest.py | The autouse resets of the shutdown flag and the principal map must stay valid; nothing becomes redundant | REQ-002, REQ-003 |
| tests/deploy/test_setup_services_eventbus.py | Caller outside `tests/eventbus/` that enters the helper's client at line 343 | REQ-002 |
| docs/24_eventbus/eventbus_08_reference_api.md | Confirm it lists no test fixture names (checked: it lists production symbols only) | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001): `test_eventbus_health.py` contains no `_init_state` and no `_do_cleanup`, its fixture is `with TestClient(eb_app.app) as c`, and each test opens exactly one connection and one broker.
- `AC-2` (REQ-002): `make_eventbus_client()` keeps its signature and default `Authorization` header, builds no `app.state` itself, and has no hand-written teardown; `eventbus_helpers.py` has no `_init_state` / `_do_cleanup`; all 7 call sites pass without assertion changes.
- `AC-3` (REQ-003): a test shows two sequential lifecycles succeed, the second one's `app.state.db` is a different, usable connection, and the shutdown flag does not leak.
- `AC-4` (REQ-004): `uv run pytest tests/eventbus` and the deploy test file pass with no assertion changes in touched tests, no file under `scripts/` is modified, and the Design section lists the real helper names for the related Plan's re-verification.

## Tests
- `T1` (REQ-001): `uv run pytest tests/eventbus/test_eventbus_health.py -v` passes unchanged.
- `T2` (REQ-002): `uv run pytest` for each of the 7 caller files passes unchanged, including `tests/deploy/test_setup_services_eventbus.py`.
- `T3` (REQ-003): the new two-lifecycle test passes and fails if the second lifecycle reuses the closed connection.
- `T4` (REQ-004): full `uv run pytest tests/eventbus` and `git diff --stat` showing only the three target files.

## Documentation Impact
N/A: no `docs/*.md` update required. `docs/24_eventbus/eventbus_08_reference_api.md` lists production symbols, not test fixture names (checked in Step 3), so it needs no change for the helper removal.

## Assumptions
- The first connection and broker that the helper and the health fixture build by hand are orphaned for every caller that enters the client, so removing them cannot change what a test observes: the lifespan assigns the config, database, schema, broker, token maps, and sweep task after `load_config` is patched to return the same config (falsifiable by the full test run).
- `test_health_degraded_when_db_unavailable` replaces `app.state.db` with a mock; at exit the lifespan closes that mock and the real connection is left to garbage collection, exactly as today. Fixing that leak is not in scope.
- Per-caller migration is unnecessary: the Issue's "migrate callers" step collapses to changing the helper once, because every caller already enters the client.
- Sequencing with the two related Plans (both edit `tests/eventbus/eventbus_helpers.py`): compatible regions (the other Plans add helpers; this Plan removes two and edits `make_eventbus_client`); rebase carefully when they land first.
- Blast radius of `make_eventbus_client` measured with `rg -l` / `rg -c`: 9 files and 16 references including the definition, under the `rules/toolchain.md` large-radius rule of thumb (more than about 10 files or 20 references); the callers' use is unchanged, so a single commit is acceptable.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner of `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` wants this work merged into that Plan after its premises are corrected | Owner decision | Decide at plan approval; until then this Plan stays separate and the related Plan's procedure generation re-verifies its helper names (Design) | False |
| UNK-02 | Whether other hand-built fixtures should follow: `_make_admin_test_client` in `tests/eventbus/test_admin_topics_authorization.py:17` and the class-level fixtures in `tests/eventbus/test_eventbus_auth.py` (not entered, own `_cleanup`), and other modules defining `_init_state` / `_do_cleanup` (`test_eventbus_restart_resume.py`, `test_eventbus_app_isolation.py`, `test_eventbus_route_helpers_metrics.py`, `test_eventbus_offsets.py`) | Per-file inspection of which double-initialize and which never enter the client | Separate Issue after this Plan lands; not opened here to avoid speculative scope | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_health.py | Modify | Low — fixture used only by this file's tests (checked in Step 3) | N/A | N/A | not applicable (rsynced) |
| tests/eventbus/eventbus_helpers.py | Modify | Medium — `make_eventbus_client` has 7 call sites in 7 files, one outside `tests/eventbus/`; `eventbus_test_tokens`, `eventbus_auth_headers`, and `principal_map` are untouched (checked in Step 3) | N/A | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_shutdown.py | Modify | Low — one added test | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification: 3 target files, all under `tests/eventbus/`, no public or runtime-facing interface change, no schema change. Validation quality baseline (Step 5): `N/A: no Python target under scripts/ or tools/`.

Design decisions:
1. The health fixture becomes the minimal lifespan fixture: patch `load_config`, `_ENVELOPE_SCHEMA_PATH`, and `get_schema_path`, then `with TestClient(eb_app.app) as c:` with the `Authorization` header; nothing after the `with` block.
2. `make_eventbus_client()` keeps building the config from `eventbus_test_tokens()` and applying the `sse_idle_timeout` override, patching the same three names, and returning the `TestClient` with the role header; it no longer runs `_init_state` and no longer attaches `_cleanup`. Alternative rejected: a second lifecycle-based helper next to it, because every caller already enters the client and two helpers would be a competing fixture.
3. The new test lives in `test_eventbus_shutdown.py` and drives `eb_app.lifespan(eb_app.app)` twice, as the neighboring tests do, asserting that the second run's `app.state.db` is a different object from the first and answers a query, and that `run_with_db_lock` works in the second run.

Real helper names for the related Plan's re-verification (`plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`): existing in `tests/eventbus/eventbus_helpers.py` — `eventbus_test_tokens`, `eventbus_auth_headers`, `make_eventbus_client`, `principal_map` (and `_init_state` / `_do_cleanup` until this Plan removes them); not existing anywhere outside `plans/`, `issues/`, `implementations/` — `make_event_bus_ctx`, `open_consumer_db`, `subscribe_client`; to be added by that Plan — `make_test_client`, `apply_production_schema`. That Plan's claim that `test_eventbus_health.py` does not bypass the lifespan is wrong: its fixture initializes state by hand (Background).

## Implementation steps
1. **Phase 1: Health fixture**
   - [ ] Remove `_init_state`, `_do_cleanup`, and the setup and teardown around `with TestClient(eb_app.app) as c`; keep the config, the three patches, and the header (REQ-001; File Path: tests/eventbus/test_eventbus_health.py)
2. **Phase 2: Shared helper**
   - [ ] Remove the `_init_state` call, the `_cleanup` attribute, and the `_init_state` / `_do_cleanup` functions from `make_eventbus_client()`'s module; update the docstring to say the client must be entered as a context manager, with the lifespan starting and stopping the app (REQ-002; File Path: tests/eventbus/eventbus_helpers.py)
3. **Phase 3: Two-lifecycle test**
   - [ ] Add the test that runs two sequential lifespans and asserts a new usable connection and no leaked shutdown flag (REQ-003; File Path: tests/eventbus/test_eventbus_shutdown.py)
4. **Phase 4: Verification**
   - [ ] Run the validation plan; deployment: N/A, no `scripts/` or `config/` change, so no `skills/deploy/SKILL.md` hand-off (REQ-004; File Path: tests/eventbus/test_eventbus_health.py, tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_shutdown.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_health.py | Integration (fixture lifecycle) | `uv run pytest tests/eventbus/test_eventbus_health.py -v` | All pass, no assertion changes |
| tests/eventbus/eventbus_helpers.py | Integration (every caller) | `uv run pytest tests/eventbus/test_eventbus_publish.py tests/eventbus/test_eventbus_crash_ack.py tests/eventbus/test_eventbus_slow_consumer.py tests/eventbus/test_eventbus_subscribe_transition.py tests/eventbus/test_eventbus_concurrent.py tests/eventbus/test_eventbus_auth.py tests/deploy/test_setup_services_eventbus.py` | All pass |
| tests/eventbus/test_eventbus_shutdown.py | Unit (two lifecycles) | `uv run pytest tests/eventbus/test_eventbus_shutdown.py -v` | New test passes |
| tests/eventbus | Package regression | `uv run pytest tests/eventbus` | All pass |
| tests/eventbus | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus` | Clean |
| whole change | Scope | `git diff --stat` | Only the three target files |

## Risks
- **Risk**: a test relied on the helper's hand-built state surviving the lifespan, so removing it changes behavior → **Mitigation**: the lifespan already overwrites that state for every entering caller; the per-caller test run in the Validation plan confirms it before the change is committed.
- **Risk**: a future caller uses `make_eventbus_client()` without entering the client and finds no state → **Mitigation**: the docstring states the requirement and the lifespan gives the same failure mode as an unstarted app, visible immediately in the test.
- **Risk**: merge conflict in `tests/eventbus/eventbus_helpers.py` with the two related Plans → **Mitigation**: land after `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md` or rebase; regions differ.
- **Risk**: the new test is flaky because two lifecycles share module-level state (shutdown flag, metrics) → **Mitigation**: `tests/eventbus/conftest.py` autouse resets the flag and the principal map, and the neighboring `test_second_lifecycle_does_not_inherit_shutdown_flag` already runs two lifespans in one process.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the health fixture to rely on the lifespan (tests/eventbus/test_eventbus_health.py) | Pending | — | — | REQ-001 |
| 2 | Make `make_eventbus_client()` lifespan-only and remove `_init_state` / `_do_cleanup` (tests/eventbus/eventbus_helpers.py) | Pending | — | — | REQ-002 |
| 3 | Add the two-sequential-lifecycles test (tests/eventbus/test_eventbus_shutdown.py) | Pending | — | — | REQ-003 |
| 4 | Run the validation plan; no deploy (tests only) | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-090402_eventbus003_test-lifecycle-production-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-092424
- **Related target files**: tests/eventbus/test_eventbus_health.py, tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_shutdown.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (health fixture); `test_eventbus_health.py:15,28,49-92` (Step 2) | tests/eventbus/test_eventbus_health.py | Phase 1 | AC-1 | T1 | Confirmed by repository evidence |
| REQ-002 | Required Changes (shared helper); `eventbus_helpers.py:101,145,151-159,164,179`; all 7 callers enter the client (Step 2) | tests/eventbus/eventbus_helpers.py | Phase 2 | AC-2 | T2 | Derived from confirmed evidence |
| REQ-003 | Required Changes (two-lifecycle test); `test_eventbus_shutdown.py:233,255` (Step 3) | tests/eventbus/test_eventbus_shutdown.py | Phase 3 | AC-3 | T3 | Confirmed by repository evidence |
| REQ-004 | Constraints (no production change, assertions keep meaning); Acceptance Criteria (related Plan re-verified); phantom helper names (Step 2) | tests/eventbus/test_eventbus_health.py | Phase 4 | AC-4 | T1, T4 | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria (related Plan re-verified) | tests/eventbus/eventbus_helpers.py | Phase 4 | AC-4 | T2, T4 | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria | tests/eventbus/test_eventbus_shutdown.py | Phase 4 | AC-4 | T4 | Explicit in issue |
