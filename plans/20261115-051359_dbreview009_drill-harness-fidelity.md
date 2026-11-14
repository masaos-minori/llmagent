# Plan 009: Recovery drill artifact fidelity and harness cleanup

## Goal
- Make the drill harness keep its "always write an artifact" promise under archive-stage failures, make `rto_seconds` measure the restore copy it names, remove the dead `_last_archive` helper, and replace the library-module `print` with logging — with tests pinning each behavior.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: archive-stage exception handling in `_drill_one_domain`; RTO clock placement; `_last_archive` removal; `print` → logging in `run_drill`/`main`; tests in `tests/db/test_recovery_drill.py`; the RTO/artifact-failure statements in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12.
- **Out-of-Scope**: retention of drill outputs and archives (issue 008, `issues/20261114-092857_dbreview008_artifact-retention-gaps.md`); rotation behavior itself (`scripts/db/rotation.py` is not modified — the drill only catches what it raises).
- **Dependencies**: none per the Issue.
  - **Depends on**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | phase all | sequencing only: 004 edits `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` and `scripts/db/recovery.py` and lands first; 009 edits the drill section of the same doc (`:156-189`) and does not touch `recovery.py`. No behavioral dependency.

## Background
From the Source Issue (F-009, commit `0fe68d3`), re-verified against the post-pull tree (HEAD `edc79f698`, 2026-11-15). The harness was restructured upstream since the Issue was filed; the four Issue claims map onto the current file as follows:

- Claim 1 (archive-stage failures escape): **Confirmed.** `_drill_one_domain` (`scripts/db/recovery_drill.py:185-192`) catches only `FileNotFoundError` from `_archive_db_file`. That function also raises `RuntimeError` from `_verify_archive` (`scripts/db/rotation.py:74,80`) and can raise `sqlite3.Error` from `sqlite3.connect`/`src.backup` (`rotation.py:50-53`). An escaping error skips `_persist_artifact` (`recovery_drill.py:244`), aborts `run_drill`'s domain loop (`:290-301`), and contradicts the docstring "always return its audit artifact" (`:150-153`).
- Claim 2 (RTO excludes the restore copy): **Confirmed.** `shutil.copy2(recovery_point, isolated)` runs at `:204`; `started = time.time()` is taken at `:206`, after the copy, so `rto_seconds` (`:222`) times verification only. **Maintainer decision (2026-11-15): include the copy — `started` moves before the copy; the field name stays (the Issue's compatibility constraint forbids renaming).**
- Claim 3 (`_last_archive` dead): **Confirmed.** Defined `:248-263`; repo-wide grep finds no caller; `uv run vulture scripts/db/recovery_drill.py` reports it unused (60% confidence, this cycle).
- Claim 4 (`print` in a library module): **Confirmed as a rule violation.** `run_drill` prints at `:300`; `rules/coding.md:84-85` states "no print() in library modules" with an ast-grep check over `scripts/`. `recovery_drill.py:300` is the only `print(` in `scripts/db/` (grep this cycle). CLI logging convention exists at `scripts/db/create_schema.py:127` (`logging.basicConfig(level=logging.INFO)` in `main`).

Parts of the Issue text that were superseded by the upstream harness rewrite are treated as retired, not re-planned: there is no `DomainDrillResult` dataclass, no row-count-only `verified` flag (the current verification is integrity + per-domain consistency + schema fingerprint: `:97-125`, `:237-242`), no quarantine step, and no redundant success-path copy. Test coverage exists (`tests/db/test_recovery_drill.py`, 637 lines) — the Issue's "zero coverage" context no longer applies; only the Issue's *new* tests (archive-failure, timing boundary) are missing.

## Problem
An archive verification failure crashes the whole drill with no artifact for the failing domain and no drill of the remaining domains; `rto_seconds` under-reports the recovery time it names; the module carries dead code and a rule-breaking `print`.

## Reason for Change
The drill is the evidence that recovery works. A drill that crashes without a record, or under-reports its recovery time, weakens that evidence (Issue).

## Implementation Intent
Catch the archive stage's full exception set per domain and persist a failed artifact before continuing; start the RTO clock before the isolated copy; delete the unused helper; route the per-domain status line through `logger` with `main()` configuring logging, matching `create_schema.py`.

## Requirements
- `REQ-001`: `_drill_one_domain` catches `(FileNotFoundError, RuntimeError, sqlite3.Error)` around `_archive_db_file`; on `RuntimeError`/`sqlite3.Error` the artifact records `error=str(exc)` and a non-passing verification (`archive_failed: False` added to `verification`; existing `missing_source: False` shape for `FileNotFoundError` unchanged), persists, and returns — so `run_drill` continues to the next domain (AC-1).
- `REQ-002`: `started = time.time()` moves before `shutil.copy2(recovery_point, isolated)`; `rto_seconds` = copy + verification; `restore_start_ts` therefore names the true restore start; field names unchanged (AC-2; maintainer decision 2026-11-15).
- `REQ-003`: delete `_last_archive` (`:248-263`); no consumer exists (grep + vulture this cycle) and none is planned (issue 008 targets rotation archives and artifact retention, not this helper) (AC-3).
- `REQ-004`: `run_drill`'s status line (`:300`) uses `logger.info`; `main()` calls `logging.basicConfig(level=logging.INFO)` (pattern `create_schema.py:127`) so the CLI still shows per-domain PASS/FAIL (AC-4).
- `REQ-005`: tests in `tests/db/test_recovery_drill.py`: patched `_archive_db_file` raising `RuntimeError` and `sqlite3.Error` (artifact written, failing verdict, remaining domains drilled, `run_drill` returns False); timing-order test (recorded copy-completion timestamp ≥ `restore_start_ts`); a test that the status line is reachable via logging caplog rather than stdout (AC-1, AC-2, AC-5).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery_drill.py | Modify | Broaden the archive-stage `except` and persist a failed artifact (REQ-001); move `started` before the copy (REQ-002); delete `_last_archive` (REQ-003); `print` → `logger.info` + `basicConfig` in `main` (REQ-004) | REQ-001..REQ-004 / AC-1..AC-4 | `:185-192` FileNotFoundError-only; `:204/:206/:222` timing; `:248-263` dead helper; `:300` print (checked Step 2, post-pull) | tests/db/test_recovery_drill.py | Verified |
| tests/db/test_recovery_drill.py | Modify | Add archive-failure continuation tests (`RuntimeError`, `sqlite3.Error`), timing-order test, logging-based status test | REQ-005 / AC-1, AC-2, AC-5 | 637 lines; no test patches `_archive_db_file` to raise (grep this cycle); CLI tests assert returncode and artifacts only, no stdout assertions (`:593-637`) | tests/db/test_recovery_drill.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Section 12: state that archive-stage failures are recorded per domain and other domains still drill; state `rto_seconds` covers the isolated copy plus verification | REQ-001, REQ-002 / AC-1, AC-2 | `:156-189` drill section; `:182` "restore start to completion" wording becomes accurate only after REQ-002 (read this cycle) | N/A | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/rotation.py `:25-81` | `_archive_db_file`/`_verify_archive` define the exact exception set the drill must catch (`RuntimeError` at `:74,80`; sqlite3 connect/backup errors) — **no edit required** | scripts/db/recovery_drill.py / REQ-001 |
| scripts/db/create_schema.py `:127` | Existing CLI logging convention (`logging.basicConfig(level=logging.INFO)` in `main`) to copy | scripts/db/recovery_drill.py / REQ-004 |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md `:156-189` | Section 12 is the current drill contract the tests must keep matching | docs/41_db/db_07_api_and_operations-recovery-and-reference.md / REQ-001, REQ-002 |
| plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | Lands first in the same docs file and owns `scripts/db/recovery.py` probe-side-effect fixes; 009 re-reads the landed drill section before editing | docs/41_db/db_07_api_and_operations-recovery-and-reference.md / Documentation Impact |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-005`): With `_archive_db_file` patched to raise `RuntimeError` for one domain, that domain's artifact exists with `error` populated and a non-passing `verification`, the other domains are still drilled and persisted, `run_drill` returns False (exit 1 via `main`).
- AC-2 (`REQ-002`, `REQ-005`): A test records the completion timestamp of the isolated copy (wrapped `shutil.copy2`) and asserts `artifact["restore_start_ts"] <=` that timestamp and `rto_seconds > 0` covering it.
- AC-3 (`REQ-003`): `_last_archive` is absent; `uv run vulture scripts/db/recovery_drill.py` reports no unused code; full suite green.
- AC-4 (`REQ-004`): No `print(` remains in `scripts/db/recovery_drill.py`; the per-domain status line appears via caplog in a unit test and via logging output in the CLI subprocess tests.
- AC-5 (`REQ-005`): All new tests pass; every pre-existing artifact-key and verdict assertion in `test_recovery_drill.py` stays unchanged (artifact schema keys are not modified).

## Tests
- `REQ-001` (AC-1): `patch("db.recovery_drill._archive_db_file", side_effect=RuntimeError("archive verification failed for x: integrity check ..."))` on the rag domain while session/workflow build normally → rag artifact exists, `error` set, `verification` non-passing, session/workflow artifacts exist, `run_drill("all", ...)` returns False. Repeat with `sqlite3.Error("disk I/O error")`.
- `REQ-002` (AC-2): wrap `shutil.copy2` with a recorder capturing `time.time()` after the copy; assert `artifact["restore_start_ts"] <= recorded_copy_end` and `artifact["rto_seconds"] >= 0` (deterministic ordering assertion, no sleeps).
- `REQ-003` (AC-3): no new test; deletion verified by vulture + suite green (no caller existed).
- `REQ-004` (AC-4): pytest `caplog.at_level(logging.INFO, logger="db.recovery_drill")` around `run_drill` asserts one INFO line per drilled domain containing the domain and PASS/FAIL.
- Regression watch (no assertion changes expected): `test_all_domains_drill_passes_and_live_dbs_untouched` (`:235-248`), the rag/session/workflow verdict tests (`:291-557`), and the CLI exit tests (`:593-637`) — none assert on stdout text or on `_last_archive`; `restore_start_ts` value shifts earlier, and no existing test asserts its exact value (grep this cycle).

## Documentation Impact
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12: (a) state that archive-stage failures (`FileNotFoundError`, integrity/identity `RuntimeError`, sqlite3 errors) are recorded in that domain's artifact and the remaining domains are still drilled; (b) `rto_seconds` row: measured time **of the isolated restore copy plus verification**, from restore start to completion. The existing `error` row (`:187`) already promises an artifact on failure — REQ-001 makes it true for the archive stage.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `recovery_drill.py` top `run_drill` C(11), `_verify_rag_session` B(6), `_drill_one_domain` A(5) | `uv run radon cc scripts/db/recovery_drill.py -s` (run this cycle) | 2026-11-15 |
| vulture targets | 1 finding: `:248` unused `_last_archive` (60%) | `uv run vulture scripts/db/recovery_drill.py` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (recorded under Plan 005; tree unchanged since) | 2026-11-15 |
| coverage targets | project total 95% | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (recorded under Plan 005) | 2026-11-15 |
| operational check | drill cron entry unchanged; dev-host only | `crontab -l` entry `17 4 * * * ... recovery-drill` (recorded in notes this cycle) | 2026-11-15 |

## Assumptions
- `_archive_db_file`'s failure mode "left in place for forensics" (`rotation.py:35-36`) means a failed archive file may exist on disk; the drill records the error and does not attempt restore from it — REQ-001 stops after recording (no `isolated` copy is made). Confidence: the docstring states it (checked this cycle).
- Existing artifact readers tolerate a new `verification["archive_failed"]: False` key on failure paths only (readers today read `integrity`, per-check keys, and `error`; docs section 12 keys are additive). If a strict external reader exists, the failing verdict can instead be expressed with existing keys (`integrity: False` + `error`) — same AC-1 outcome. (Unknown UNK-01.)
- `logging.basicConfig` in `main` does not double-log for cron because the module is run as `__main__` only there (checked `:337-338`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any external reader of drill artifact JSON rejects a new `verification["archive_failed"]` key on failure paths | No external reader found in repo; docs do not promise a closed key set | Default to the additive key; if the maintainer objects before Phase 1, express the failure with `integrity: False` + `error` only (Assumptions) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery_drill.py | Modify | Low-medium (cron drill, deploy opt-in drill hook per docs `:173`) | 2 | High (single author, >70%) | not applicable (rsynced); drill hook at deploy reads exit codes only |
| tests/db/test_recovery_drill.py | Modify | Low (test-only) | 2 | High (single author, >70%) | not applicable |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Low (docs) | 3 | High (single author, >70%) | not applicable |

## Cross-Plan Target Overlap Scan

- Run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15, after this Plan freezes): expected finding — `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` shared with Frozen Plans 002, 003, 004. Judgment: **sequencing + section isolation** — fixed batch order 002 → 003 → 004 → ... → 009; 009 edits only section 12 (drill), 002/003/004 edit restore/probe sections. `scripts/db/recovery_drill.py` and `tests/db/test_recovery_drill.py` are targeted by no other plan (004 targets `scripts/db/recovery.py` and `tests/db/test_db_recovery.py` — different files; confirmed by this scan run). No contradiction: 009's drill contract does not change restore semantics owned by 002/003/004.
- Update after Plan 008 froze (same tool, 2026-11-15): `docs/41_db/db_07...` now 5 plans; `scripts/db/recovery_drill.py` and `tests/db/test_recovery_drill.py` are now shared with Plan 008. Judgment: **sequencing** — 008 lands after 009 and edits 009's landed shape only (end-of-drill `isolated` unlink, `_persist_artifact` naming, extensions of 009's landed test fixtures); 009's failure-handling restructure is untouched. No contradiction.

## Design
- **Catch at the domain boundary, not inside rotation**: the exception set is exactly what `_archive_db_file` documents (`FileNotFoundError` `rotation.py:39`, `RuntimeError` from `_verify_archive` `:74,80`, plus `sqlite3.Error` from connect/backup `:50-53`). Rejected alternatives: catching `Exception` (absorbs programming errors the docstring doesn't promise); making `_verify_archive` non-raising (rotation's contract "a failing archive raises" is documented at `rotation.py:35` and in docs `db_07:121`).
- **Failure artifact shape**: reuse the existing `FileNotFoundError` pattern (`verification = {"missing_source": False}` + `error`, `recovery_drill.py:187-192`) — archive-stage failures set `verification = {"archive_failed": False}` and `error=str(exc)`, `integrity` stays `None`→falsy and `run_drill`'s `ok` computation (`:294-298`) yields FAIL without further changes. Artifact keys on success paths untouched (Issue constraint).
- **Clock placement**: `started` moves before `shutil.copy2` (`:204→206`); `rto_seconds` formula (`:222`) unchanged, only its meaning widens to the true restore. `backup_duration_seconds` (`:198`, archive creation) is unaffected.
- **Delete `_last_archive`**: no caller exists (grep, vulture). Rejected alternative: wiring it into 008 — 008's scope is rotation archive retention and drill-artifact retention windows, not selecting "latest archive" (its plan will not reference this helper).
- **Logging instead of print**: `logger.info("[drill] %s: %s %s", ...)` in `run_drill`; `main()` gains `logging.basicConfig(level=logging.INFO)` per `create_schema.py:127`. CLI cron output preserved (logging writes to stderr; cron captures it). Rejected alternative: moving the loop report into `main` — would duplicate the domain loop and the ok-computation (logic must stay with `run_drill`, whose tests call it directly).
- **Architecture check** (Step 3): no new import edges (imports unchanged at `:20-49`; `_last_archive` deletion removes no import — `Path`/glob use persists via other call sites; ruff confirms). `lint-imports` contracts unchanged.
- **Persisted schema check**: artifact JSON gains one failure-path key only (UNK-01); success-path schema unchanged.

## Implementation steps
1. **Phase 1: Drill failure handling, clock, dead code, logging** (REQ-001..REQ-004; `scripts/db/recovery_drill.py`)
   - [ ] Broaden the `_archive_db_file` `except` to `(FileNotFoundError, RuntimeError, sqlite3.Error)` with the failure-artifact pattern above (REQ-001; scripts/db/recovery_drill.py)
   - [ ] Move `started` before `shutil.copy2` (REQ-002; scripts/db/recovery_drill.py)
   - [ ] Delete `_last_archive` (REQ-003; scripts/db/recovery_drill.py)
   - [ ] `print` → `logger.info` in `run_drill`; `basicConfig` in `main` (REQ-004; scripts/db/recovery_drill.py)
2. **Phase 2: Tests** (REQ-005; `tests/db/test_recovery_drill.py`)
   - [ ] Add the archive-failure continuation tests (`RuntimeError`, `sqlite3.Error`), the copy-order timing test, and the caplog status test (REQ-005)
   - [ ] Run `uv run pytest tests/db/test_recovery_drill.py -v`, then the regression watch list
3. **Phase 3: Docs and validation** (Documentation Impact)
   - [ ] Update section 12 artifact-failure and `rto_seconds` statements in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
   - [ ] Run ruff, basedpyright (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db`; `uv run vulture scripts/db/recovery_drill.py` reports clean; diff-cover ≥ 90% on the branch diff
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision

### Release units
**Unit**: drill-harness-fidelity | **Phases**: 1, 2, 3 | **Reason**: the four harness changes share one module, one test file, and one docs section; splitting leaves a drill whose artifact promise is half-true.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery_drill.py | Archive-failure integration tests on real fixture DBs with patched `_archive_db_file` | `uv run pytest tests/db/test_recovery_drill.py -v` | AC-1 asserted |
| scripts/db/recovery_drill.py | Timing-order test (wrapped copy2 recorder) | `uv run pytest tests/db/test_recovery_drill.py -v` | AC-2 asserted, deterministic |
| scripts/db/recovery_drill.py | caplog status test | `uv run pytest tests/db/test_recovery_drill.py -v` | AC-4 asserted |
| scripts/db/recovery_drill.py (vulture) | Dead-code check | `uv run vulture scripts/db/recovery_drill.py` | No findings (baseline: 1 `_last_archive`) |
| scripts/db/ (print rule) | Rule grep | `grep -n "print(" scripts/db/recovery_drill.py` | No matches (AC-4) |
| tests/db/test_recovery_drill.py | Full-file regression run | `uv run pytest tests/db -q` | All pre-existing tests green unchanged |
| scripts/ (regression) | Full suite | `uv run pytest tests/ -n auto` | No regressions |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | ≥ 90% on branch diff (baseline 95%) |

## Risks
- **Risk**: broadening the `except` absorbs an `sqlite3.Error` that indicates a broader outage (disk full) → **Mitigation**: the error text is persisted in the artifact and logged, and `run_drill` still returns False (exit 1) so cron alerts fire; the drill's job is per-domain reporting, not triage suppression.
- **Risk**: `rto_seconds` values grow (copy included) and a reader comparing against a historical threshold misreads the jump → **Mitigation**: docs `db_07:182` already states "Measurement semantics, not a threshold"; the docs update names the widened scope explicitly.
- **Risk**: new `verification["archive_failed"]` key on failure paths breaks an unseen strict reader → **Mitigation**: UNK-01 fallback (express failure via existing `integrity`/`error` keys) decided before Phase 1 if the maintainer objects.
- **Risk**: logging change alters cron output format → **Mitigation**: message text preserved verbatim (`[drill] <domain>: PASS/FAIL {...}`); cron captures stderr; CLI subprocess tests re-run unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drill failure handling, clock, dead code, logging (scripts/db/recovery_drill.py) | Pending | — | — | |
| 2 | Tests (tests/db/test_recovery_drill.py) | Pending | — | — | |
| 3 | Docs and validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-009-1 | — | Follow-up (recorded at plan time) | Open | maintainer | — | RTO values in historical artifacts under `/opt/llm/data/archives/drills` (if any) are verification-only; post-change artifacts are copy+verification. No action unless a dashboard consumes them. |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092858_dbreview009_drill-harness-fidelity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-051359
- **Related target files**: scripts/db/recovery_drill.py, tests/db/test_recovery_drill.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem bullet 1; Required Changes bullet 1 | scripts/db/recovery_drill.py | Phase 1 | AC-1 | Archive-failure continuation tests | Verified by test (Issue reproduction; re-verified Step 2 at `:185-192`, `rotation.py:74,80`) |
| REQ-002 | Problem bullet 2; Required Changes bullet 2; Unresolved Question answered 2026-11-15 (include copy) | scripts/db/recovery_drill.py | Phase 1 | AC-2 | Timing-order test | Verified by test (`:204/:206/:222` checked Step 2) |
| REQ-003 | Problem bullet 3; Required Changes bullet 3 | scripts/db/recovery_drill.py | Phase 1 | AC-3 | vulture clean + suite green | Explicit in code (`:248-263`; grep + vulture this cycle) |
| REQ-004 | Problem bullet 4 (Needs-confirmation resolved against `rules/coding.md:84-85` this cycle) | scripts/db/recovery_drill.py | Phase 1 | AC-4 | caplog test + print grep | Explicit in code (`:300`; only print in `scripts/db/`) |
| REQ-005 | Testing Expectations | tests/db/test_recovery_drill.py | Phase 2 | AC-1, AC-2, AC-5 | New tests | Verified by test (gap confirmed this cycle: no `_archive_db_file` failure tests exist) |
