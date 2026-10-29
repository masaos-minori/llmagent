# Plan: remove the residual EventBus test drift not covered by eventbus003/004 (ebtestdrift007)

## Goal
- Land only the source issue's items that no other plan or pending procedure covers: delete the
  dead inline fallback schema in `tests/eventbus/test_eventbus_restart_resume.py`, rename the two
  misspelled `dmq` tests in `tests/eventbus/test_eventbus_requeue_edge_cases.py` to `dlq`, and move
  the hand-built fixture in `tests/eventbus/test_admin_topics_authorization.py` onto the production
  lifespan -- without touching production code.

## Priority
Low (source issue priority; maintenance and readability only, no behavior is wrong today).

## Scope
- **In-Scope** (the three residuals verified as uncovered on 2026-10-29):
  - Removal of the dead fallback branch in `_create_tables`
    (`tests/eventbus/test_eventbus_restart_resume.py:282-311`) so a missing
    `scripts/eventbus/schema.sql` fails with a clear error instead of a private inline DDL.
  - Rename `test_requeue_non_dmq_event` (`test_eventbus_requeue_edge_cases.py:76`) and
    `test_requeue_valid_dmq_event` (`:88`) to `dlq` spellings.
  - Replace the hand-built app state in `_make_admin_test_client`
    (`test_admin_topics_authorization.py:17`, state assignment `:81-93`, `_cleanup` `:63-72`) with
    the production-lifespan pattern established by eventbus003's `test_eventbus_health.py`
    procedure (`implementations/20261029-101908_01_tests_eventbus_test_eventbus_health.py.md`).
- **Out-of-Scope** (source-issue items already covered elsewhere -- removed from this Plan on
  2026-10-29 rescope, see Rescope Record):
  - `test_eventbus_health.py` lifespan fixture, `eventbus_helpers.py` fixture cleanup, and the
    two-sequential-lifecycles shutdown test: covered by
    `plans/done/20261029-092424_eventbus003_test-lifecycle-production-path.md` (procedures
    `20261029-101908_01/02/03`).
  - `REQ-*`/`UNK-*`/`AC-*` identifier cleanup across 18 `tests/eventbus` files: covered by
    `plans/done/20261029-092617_eventbus004_test-requirement-id-cleanup.md` (procedures
    `20261029-102038_01..18`).
  - New restart/resume scenario coverage: owned by
    `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md` (procedures
    `20261029-111247_01/02/03`).
  - Production code and schema changes; the agent API test layer (`tests/agent/`).
- **Dependencies** (sequencing, all complementary edits to the same files):
  - `test_eventbus_requeue_edge_cases.py`: implement this Plan's rename **after** procedure
    `20261029-102038_05_tests_eventbus_test_eventbus_requeue_edge_cases.py.md` (eventbus004,
    comments and docstrings only; its document explicitly forbids test renames, so this Plan owns
    the rename).
  - `test_eventbus_restart_resume.py`: implement after procedures
    `20261029-111247_02_tests_eventbus_test_eventbus_restart_resume.py.md` and
    `..._03_...replay_subscribe.py.md` (ebresumetest004) land; those keep `_create_tables`
    in place, this Plan then removes only the dead fallback branch.
  - `test_admin_topics_authorization.py`: implement after eventbus003 procedures
    `20261029-101908_01` (health pattern) and `20261029-101908_02` (helpers) land; this row is the
    follow-up that eventbus003 UNK-02 deferred as "separate Issue after this Plan lands" for this
    file. Pending procedures `20261029-115727_07` (audit-test assertions), `20261029-101422_03`
    (appended class), and `20261029-102038_12` (comment labels) touch disjoint regions of the
    same file and need no ordering against this Plan's row.

## Background
Re-verified 2026-10-29 against HEAD `c8689f78b`, directly from the source issue
(`issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`):
- `test_eventbus_restart_resume.py::_create_tables` (:277) loads the production
  `scripts/eventbus/schema.sql` (:311) when present; the inline `CREATE TABLE` fallback
  (:282-311 `else` branch) is dead in normal runs and carries columns (`acked`,
  `consumer_delivery_failure_count`) the canonical schema no longer defines -- the issue's
  "fallback schema can mask a missing `schema.sql`" failure mode.
- `dmq` exists nowhere in `tests/`, `scripts/`, or `docs/` except the two test method names at
  `test_eventbus_requeue_edge_cases.py:76` and `:88`; neither name is referenced elsewhere.
- `test_admin_topics_authorization.py` builds `app.state` by hand (`:81-93`), attaches a private
  `_cleanup` (`:63-72`), and does not enter the client through the lifespan -- the same pattern
  eventbus003 removes in `test_eventbus_health.py`.
- `test_eventbus_schema_version.py:64` also contains an inline `CREATE TABLE events`, but it is an
  intentional old-shape fixture that proves `open_db` refuses an unstamped database; reviewed
  2026-10-29 and excluded (it is not a fallback schema).
- Issue identifiers `H-03`: no occurrences remain under `tests/eventbus/` (grep 2026-10-29); the
  issue's placeholder concern is already resolved.

## Problem
Tests can pass against a state the production lifespan would never create, the fallback schema can
mask a missing `scripts/eventbus/schema.sql`, and the misspelled `dmq` acronym makes tests harder
to search.

## Reason for Change
Maintenance and readability; the fallback schema is the one item with a correctness angle (it hides
a missing canonical file). Nothing is time-sensitive.

## Implementation Intent
Delete the dead fallback branch instead of replacing the loader (the production-schema load at
`:311` already exists); rename the two tests name-only; and reuse eventbus003's lifespan pattern
for the admin fixture. No assertions, no production code, no new helpers.

## Requirements
- `REQ-001`: `tests/eventbus/test_eventbus_restart_resume.py::_create_tables` contains no inline
  `CREATE TABLE` fallback; when `scripts/eventbus/schema.sql` is missing it raises a clear error
  (e.g. `FileNotFoundError` with the path) instead of executing a private DDL.
- `REQ-002`: `test_requeue_non_dmq_event` is renamed `test_requeue_non_dlq_event` and
  `test_requeue_valid_dmq_event` is renamed `test_requeue_valid_dlq_event`; no `dmq` substring
  remains in `tests/eventbus/`.
- `REQ-003`: `tests/eventbus/test_admin_topics_authorization.py` builds its client through the
  production lifespan (no hand-assigned `app.state.*`, no attached `_cleanup`), following the
  `test_eventbus_health.py` pattern established by procedure `20261029-101908_01`.
- `REQ-004`: cross-cutting constraint: no production file changes; no assertion, fixture-behavior,
  or test-count change (renames and teardown-path consolidation only).

## Implementation Target Files
**Freeze status**: Frozen (re-derived 2026-10-29 from the source issue's Required Changes bullets
3 and 2 plus eventbus003 UNK-02's deferred admin-fixture item; all rows verified against HEAD
`c8689f78b` by direct read this cycle; `tools/check_plan_target_overlaps.py`: no findings). The
previous freeze (2026-10-29, 11 rows) is void -- see Rescope Record and Blocker Log.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_restart_resume.py | Delete the dead inline DDL fallback branch in `_create_tables`; raise a clear error when `scripts/eventbus/schema.sql` is missing | A private fallback schema with stale columns can mask a missing canonical file | REQ-001; AC-1 | `_create_tables` at :277; fallback branch :282-311 (fallback DDL :284-309); production load at :311 (checked 2026-10-29) | The file's existing tests, run twice in one session | Verified |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Rename `test_requeue_non_dmq_event` -> `test_requeue_non_dlq_event`, `test_requeue_valid_dmq_event` -> `test_requeue_valid_dlq_event` | The acronym is DLQ; the issue names these two tests explicitly | REQ-002; AC-2 | Method definitions at :76 and :88; no other `dmq` occurrence in `tests/`, `scripts/`, `docs/` (grep 2026-10-29) | The file's existing tests (name-only change) | Verified |
| tests/eventbus/test_admin_topics_authorization.py | Replace the hand-built `_make_admin_test_client` state and `_cleanup` with the production-lifespan pattern | Test passes against state the production lifespan would never create; eventbus003 UNK-02 deferred this file | REQ-003; AC-3 | `_make_admin_test_client` at :17; `app.state` assignments :81-93; `_cleanup` :63-72; `TestClient(eb_app.app)` not entered as context at :61 (checked 2026-10-29) | The file's existing tests; two sequential lifecycles in one process | Verified |

## Rescope Record (2026-10-29)
Cause (verified, see Blocker Log): the previous frozen table was fabricated at Plan generation --
its helper names (`make_event_bus_ctx`, `open_consumer_db`, `subscribe_client`), `x_<role>_`
identifiers, `dmq` variable sites, `db/schema.sql`, the 18-file census, and its audit-script /
mapping-doc / `assets/` requirements match no committed tree and no section of the source issue.
Correspondence: the Plan was reduced to the source issue's four Required Changes, of which two are
already owned by origin-side plans whose procedures exist as pending documents:

| Source issue Required Change | Disposition | Owner |
|---|---|---|
| Production-lifespan fixtures (health, helpers, shutdown two-lifecycle) | Removed from this Plan (covered) | eventbus003, procedures `20261029-101908_01/02/03` |
| Delete inline fallback schema, fail clearly when `schema.sql` is missing | Kept: REQ-001 | this Plan |
| Rename the two `dmq` tests to `dlq` | Kept: REQ-002 | this Plan |
| `REQ-*`/`UNK-*`/`AC-*`/`H-03` identifier cleanup | Removed from this Plan (covered; `H-03` already absent) | eventbus004, procedures `20261029-102038_01..18` |
| Admin-topics lifespan fixture (issue Target Files; eventbus003 UNK-02 deferral) | Kept: REQ-003 | this Plan, after `101908_01/02` land |

Fabricated items deleted outright (never in the source issue): the canonical mapping-doc section,
the `tools/audit_test_terminology.py` audit script and its tests, the `assets/terminology_audit/`
report, the five "inline `TestClient(`/`EventBus(`" site fixes, the `x_*` bulk rename (old
UNK-01), and the old UNK-02 report-location question.

## Verification findings (2026-10-29, preserved from the voided freeze)
The 2026-10-28 census never matched any committed tree at any time:
`git log -S`/`-G` over `--all` shows `make_event_bus_ctx`, `open_consumer_db`,
`subscribe_client`, every `x_<role>_` identifier, and a standalone `dmq` appear only inside
`plans/`/`issues/`/`implementations/` prose (first in `1f08092d9`); `tests/eventbus` held 24+
`.py` files since its creation (never 18); `db/` does not exist (canonical DDL is
`scripts/eventbus/schema.sql`); zero direct `EventBus(`/`EventConsumer(` constructions exist;
`test_eventbus_consumer_authorization.py:27/:30`, `test_eventbus_publish.py:36`,
`test_eventbus_crash_ack.py:34`, `test_eventbus_dlq_promotion.py:41` do not contain the cited
inline sites; `docs/24_eventbus/eventbus_08_reference_api.md` is 149 lines (no fixture names at
:155-157); the governance doc lives at `docs/00_governance/` (no `docs/07_governance/`);
`tools/TOOL_DESCRIPTIONS.md` is 227 lines (census said 598). The same fabricated helpers propagated
into the eventbus001-004 plan documents (`b5890746f`/`d34cf7486`);
`plans/done/20261029-092424_eventbus003_test-lifecycle-production-path.md` line 115 independently
confirmed them fictitious. The census was fabricated at Plan generation, not invalidated by later
commits.

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/schema.sql | Canonical DDL that `_create_tables` already loads; the fallback must be deleted, not re-pointed | REQ-001 |
| implementations/20261029-111247_02_tests_eventbus_test_eventbus_restart_resume.py.md | Lands first on the same file; keeps `_create_tables` -- this Plan removes only the fallback branch | REQ-001 sequencing |
| implementations/20261029-102038_05_tests_eventbus_test_eventbus_requeue_edge_cases.py.md | Lands first on the same file; comments/docstrings only, forbids renames -- this Plan owns the rename | REQ-002 sequencing |
| implementations/20261029-101908_01_tests_eventbus_test_eventbus_health.py.md | The lifespan-fixture pattern REQ-003 must copy (remove `_init_state`/`_do_cleanup`, enter `TestClient` as a context manager) | REQ-003 |
| plans/done/20261029-092424_eventbus003_test-lifecycle-production-path.md | UNK-02 defers the admin fixture to a separate pass; conftest compatibility notes | REQ-003; Scope Dependencies |
| tests/eventbus/conftest.py | Autouse shutdown-flag/principal-map resets must stay untouched | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `grep -n "CREATE TABLE" tests/eventbus/test_eventbus_restart_resume.py` returns
  nothing; a temporarily hidden `scripts/eventbus/schema.sql` makes the file's tests fail with a
  clear path-carrying error (verified then restored).
- AC-2 (REQ-002): `grep -rn "dmq" tests/eventbus/` returns nothing; pytest collection count for
  the file is unchanged.
- AC-3 (REQ-003): `test_admin_topics_authorization.py` contains no `app.state.` assignment and no
  `_cleanup` attribute; its tests pass under two sequential lifecycles in one process.
- AC-4 (REQ-004): full suite green with unchanged assertion semantics; no production file in the
  diff.

## Tests
- REQ-001: `uv run pytest tests/eventbus/test_eventbus_restart_resume.py` (same pass count), plus
  the AC-1 grep gate and the missing-schema error probe.
- REQ-002: `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py` (same pass count,
  renamed collection ids).
- REQ-003: `uv run pytest tests/eventbus/test_admin_topics_authorization.py`, then the same file a
  second time in the same session (no state leak).
- Gates: run each touched file twice in one session, then `uv run pytest tests/eventbus` (baseline
  411 passed / 1 skipped; count changes only from ebresumetest004 procedures landing first), then
  full `uv run pytest`; ruff on the three changed files; mypy on the three changed files.

## Documentation Impact
Not required (source issue wording). No `docs/` change; the rename may only matter to readers of
`docs/24_eventbus/` test examples -- grep before landing shows no doc references either test name.

## Assumptions
- The ebresumetest004 and eventbus003/004 procedures land before this Plan's rows (Scope
  Dependencies); line numbers cited above shift accordingly and must be re-grepped at
  implementation time.
- Renaming test methods cannot change behavior; the full suite green is the characterization gate.
- The admin-fixture rewrite can reuse `make_eventbus_client`'s post-eventbus003 form or a local
  lifespan-context client; the health procedure's pattern decides this -- no new helper is planned.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether other hand-built fixtures (`test_eventbus_auth.py` class-level fixtures, `test_eventbus_app_isolation.py`, `test_eventbus_offsets.py`, `test_eventbus_route_helpers_metrics.py`) also move to the lifespan pattern -- eventbus003 UNK-02 listed them and only the admin file was pulled into this Plan | Owner decision recorded in eventbus003 UNK-02 | Follow-up Issue after eventbus003 procedures land; not folded here to avoid speculative scope | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/eventbus/test_eventbus_restart_resume.py | Delete dead fallback branch + explicit error | Restart-resume tests | 11 | 2 | Yes: tests/ is rsynced by deploy.sh (no runtime service) |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Two test renames (name-only) | Requeue tests | 12 | 2 | Yes: tests/ rsync (no runtime service) |
| tests/eventbus/test_admin_topics_authorization.py | Fixture rewrite onto production lifespan | Admin-topic auth tests | 7 | 2 | Yes: tests/ rsync (no runtime service) |

## Design
- Fallback removal: keep `schema_path` resolution and the `executescript(schema_path.read_text())`
  line; replace the `if not exists()` fallback branch with an explicit `raise FileNotFoundError`
  naming the path. No shared-loader helper: the file is the only private-DDL holder left after
  eventbus003 lands, so a helper would be a new abstraction with one user (Deletion-First).
- Rename: two `def` lines only; docstrings that restate the names are updated in the same edit.
- Admin fixture: mirror `101908_01`'s health pattern -- build the distinct admin/consumer token
  config and patches as today, then `with TestClient(eb_app.app) as c:` (lifespan creates
  `app.state`), dropping `_init_state`-style assignments, `_do_cleanup`, and the attached
  `_cleanup`. The distinct-token requirement (docstring at :19-23) is preserved by keeping the
  config construction, not the state construction.
- Sequencing with pending procedures: three files shared with pending procedures
  (`101908_01/02`, `102038_05`, `111247_02/03`); each shared edit is complementary and ordered as
  listed in Scope Dependencies. `tools/check_plan_target_overlaps.py` reports no findings against
  the currently active plans.

## Implementation steps
1. **Phase 1: Fallback schema removal** (after ebresumetest004 `111247_02`/`03` land)
   - [ ] Delete the fallback branch in `test_eventbus_restart_resume.py::_create_tables`; raise a clear error when `schema.sql` is missing (REQ-001; tests/eventbus/test_eventbus_restart_resume.py)
2. **Phase 2: dmq rename** (after eventbus004 `102038_05` lands)
   - [ ] Rename the two `dmq` test methods to `dlq` spellings (REQ-002; tests/eventbus/test_eventbus_requeue_edge_cases.py)
3. **Phase 3: Admin fixture lifespan rewrite** (after eventbus003 `101908_01`/`02` land)
   - [ ] Rewrite `_make_admin_test_client` onto the production-lifespan pattern (REQ-003; tests/eventbus/test_admin_topics_authorization.py)
4. **Phase 4: Verification**
   - [ ] AC-1..AC-4 greps and probes; each touched file run twice in one session; `uv run pytest tests/eventbus`, then full `uv run pytest`; ruff/mypy on changed files (REQ-001..REQ-004)
   - [ ] Deployment/scripts check: no `scripts/` file changes; tests/ rsynced by the normal deploy flow, no service restart needed (REQ-004)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_restart_resume.py | Integration (existing tests) + failure probe | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py`; AC-1 grep + missing-schema probe | Same pass count; zero `CREATE TABLE` in the file; clear error when `schema.sql` hidden |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | Existing tests, name-only change | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py` | Green; collection shows the two `dlq` names; `grep -rn dmq tests/eventbus/` empty |
| tests/eventbus/test_admin_topics_authorization.py | Existing tests through the lifespan, run twice in one session | `uv run pytest tests/eventbus/test_admin_topics_authorization.py` (x2) | Green both times; no `app.state.` assignment in the file |
| Whole suite + static gates | Regression | `uv run pytest`; ruff; mypy; bandit re-scan (3 B101 baseline, no production files touched) | No new failure; no new bandit finding |

## Risks
- **Risk**: this Plan and pending procedures share three files (overlap checker exemption relies on
  the documented order) → **Mitigation**: Scope Dependencies name the exact predecessor
  procedures; implementers re-grep line anchors before editing.
- **Risk**: the admin-fixture rewrite changes teardown ordering and leaks state into later tests →
  **Mitigation**: run the file twice in one session (issue's Testing Expectations) plus the full
  suite; conftest autouse resets stay untouched.
- **Risk**: removing the fallback breaks an environment where `scripts/eventbus/schema.sql` is
  genuinely absent (tests run from a checkout without `scripts/`) → **Mitigation**: the failure is
  the point -- the issue mandates a clear error over a silent stale schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fallback schema removal (REQ-001) | In Progress | 2026-10-29 | — | After `111247_02`/`03` land |
| 2 | dmq rename (REQ-002) | In Progress | 2026-10-29 | — | After `102038_05` lands |
| 3 | Admin fixture lifespan rewrite (REQ-003) | In Progress | 2026-10-29 | — | After `101908_01`/`02` land |
| 4 | Verification gates (REQ-001..REQ-004) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | No hard blocker; UNK-01 (other hand-built fixtures) is deferred by design | No | — |
| All | 2026-10-29 root-cause investigation: the previous frozen inventory was never true of any committed tree — `make_event_bus_ctx`/`open_consumer_db`/`subscribe_client` and every `x_<role>_` identifier appear ONLY inside `plans/`/`issues/`/`implementations/` documents across the full git history (`git log -S`/`-G` over `--all`), `tests/eventbus` has had 24+ `.py` files since its creation (never 18), a standalone `dmq` identifier never existed, and the `dmq` issue was the misspelling in the two method names `test_requeue_non_dmq_event`/`test_requeue_valid_dmq_event` (:76, :88) which the plan misread as a variable at `:76,88`. The plan also cited issue sections that do not exist in `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`, while the issue's actual REQ-identifier-comment cleanup was absent from the plan. The same fabricated helpers propagate into `b5890746f`/`d34cf7486` (eventbus001-004); the archived `plans/done/20261029-092424_eventbus003_test-lifecycle-production-path.md` independently confirmed the fiction at its Step 2. Procedure generation was refused per the Blocked-on-new-target-discovery rule | Yes | 2026-10-29 |
| Rescope | 2026-10-29: the Plan was re-derived directly from the real issue. Covered items were removed (lifespan fixtures → eventbus003 `101908_01/02/03`; identifier cleanup → eventbus004 `102038_01..18`); fabricated items (mapping-doc section, audit script, `assets/` report, inline-construction fixes, `x_*` bulk rename) were deleted; the three genuine residuals became the new frozen table. `tools/check_plan_target_overlaps.py`: no findings | Yes | 2026-10-29 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-130401_01_tests_eventbus_test_eventbus_restart_resume.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-130401_02_tests_eventbus_test_eventbus_requeue_edge_cases.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-130401_03_tests_eventbus_test_admin_topics_authorization.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan (re-scope pass 2026-10-29)
- **Source issue**: `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-234655 (rescoped 2026-10-29)
- **Related target files**: `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_admin_topics_authorization.py`
- **Related pending procedures (sequencing predecessors)**: `implementations/20261029-101908_01_tests_eventbus_test_eventbus_health.py.md`, `implementations/20261029-101908_02_tests_eventbus_eventbus_helpers.py.md`, `implementations/20261029-102038_05_tests_eventbus_test_eventbus_requeue_edge_cases.py.md`, `implementations/20261029-111247_02_tests_eventbus_test_eventbus_restart_resume.py.md`, `implementations/20261029-111247_03_tests_eventbus_test_eventbus_replay_subscribe.py.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 2 ("Delete the inline fallback schema and fail with a clear message") + Acceptance bullet 2 | tests/eventbus/test_eventbus_restart_resume.py | Phase 1 | AC-1 | Restart tests + grep gate + missing-schema probe | Explicit in issue |
| REQ-002 | Issue Required Changes bullet 3 ("Rename the two dmq tests to dlq") + Acceptance bullet 3 | tests/eventbus/test_eventbus_requeue_edge_cases.py | Phase 2 | AC-2 | Existing tests after rename | Explicit in issue |
| REQ-003 | Issue Target Files (`test_admin_topics_authorization.py`) + Acceptance bullet 1 ("Health and admin tests use the production lifespan fixture") -- admin half not covered by eventbus003 (UNK-02 deferral) | tests/eventbus/test_admin_topics_authorization.py | Phase 3 | AC-3 | Existing tests, run twice in one session | Explicit in issue |
| REQ-004 | Issue Constraints (renames/comment edits behavior-preserving, production untouched) | all target files | Phases 1-4 | AC-4 | Full suite + diff scope check | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-130401 -->