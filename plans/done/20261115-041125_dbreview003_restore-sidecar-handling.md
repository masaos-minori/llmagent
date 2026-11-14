## Goal
- Make every restore failure path restore the complete live unit (main file plus its quarantined `-wal`/`-shm`), remove activated backup-origin sidecars on rollback, and turn quarantine-directory retention after a successful restore from an accident of ordering into an explicit, tested, documented policy.

## Priority
High

## Scope
- **In-Scope**: moving quarantined original sidecars back to their live names on every terminal failure path; removing backup-origin sidecars activated at live names when a rollback happens; retaining the quarantine directory after success (maintainer decision, 2026-11-15); failure-branch sidecar tests; documentation of quarantine retention in `db_07` and ADR-008.
- **Out-of-Scope**: the activation-holder and rollback-vocabulary work (`plans/20261115-035004_dbreview002_partial-activation-rollback.md`, planned first); periodic cleanup/rotation of retained quarantine and temp artifacts (`issues/20261114-092857_dbreview008_artifact-retention-gaps.md`); logical verification and vec extension (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`).
- **Dependencies**: coordinate with `plans/20261115-035004_dbreview002_partial-activation-rollback.md` (same functions).
  - **Depends on**: plans/20261115-035004_dbreview002_partial-activation-rollback.md | phase all | 002 introduces the activation holder (swap-started + moved-sidecar record) and the extended `_rollback_or_non_serviceable`; this Plan's quarantine-back step is added on top of those shapes, so 003 lands after 002.

## Plan-Document Correction (re-verification after Plans 001/002 closed)

- All Background claims re-confirmed against the current tree this cycle: `recovery.py:361` `quarantine_dir` creation; `:374`/`:395` cleanup-only failure returns; `:415` success-path `shutil.rmtree` (plan cites `:414-415`; 414 is its comment); `:426` handler cleanup; `:431` main-only rollback; `recovery_restore.py:22-35` (`_quarantine_sidecar_files`, returns `None`) and `:75-112` (`_stage_restore` returns only the staged dict); test assertions `:834`, `:1063`, `:1436` (quarantine kept on OSError), `:1459`; helper tests at `:683`, `:717`, `:749`, `:769`; sole production caller `recovery.py:366`; no test caller of `_stage_restore` (grep).
- Correction 1 (docs evidence): `db_07` has no line-77 claim — `grep "terminal path" docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is empty. The text REQ-006 must edit is instead `db_07:34` (staging helper contract: "Staging is fail-closed... caller's cleanup handler") and `db_07:63` ("A candidate that fails verification is never activated: the live database is untouched" + "cleans up the half-written temp files and preserves the archive"). Target-file row evidence updated accordingly.
- Correction 2 (REQ-004 dedup): Plan 002's REQ-004 (procedures `implementations/20261115-080732_1_scripts_db_recovery.py.md` step 6 and `implementations/20261115-080732_2_tests_db_test_db_recovery.py.md` step 5) implements exactly the `_cleanup_staged` failure-safe change and its forced-unlink test. Plan 003 lands after 002 (dependency row), so 003 re-verifies AC-5 against the landed 002 test; it does not re-implement `_cleanup_staged` or add a duplicate test.
- Shapes Plan 003 builds on (from Plan 002's landed procedures): `_ActivationProgress` holder (`replaced` flag + moved-sidecar list) and `_rollback_or_non_serviceable(db_path, corrupt_archive, failure, dry_run, moved_sidecars kwarg)`. 003's quarantine-back step extends the same helper after the main-file replace and threads quarantine records through the pre-activation failure returns.

## Background
From the Source Issue (F-003), re-verified line-by-line against the post-pull tree (2026-11-15). The Issue's claim that quarantine happens "before verification" is true in the current code but is no longer the defect: the upstream fix (commit `4543c2aa4`) deliberately quarantines the live `-wal`/`-shm` at staging time — `quarantine_dir` is created at `scripts/db/recovery.py:361`, `_stage_restore` (`scripts/db/recovery_restore.py:75-112`) calls `_quarantine_sidecar_files` (`:22-35`, copy2 + unlink per suffix) at `:91-93` before any swap. That part of the Issue is resolved; the Issue's Proposed Fix 1 ("run quarantine at the activation step") is superseded. The verified remaining defects:

- Pre-activation candidate failure: `recovery.py:373-386` and `:387-402` report `restore_verify_failed` / `logical_verify_failed` / `verification_unavailable` with `active_db_state="preserved_original"` after `_cleanup_staged` (`:374`, `:395`) — but the live main file still sits in place while its sidecars remain inside the quarantine directory and are never moved back. The live unit is broken and the reported state contradicts the filesystem.
- Post-activation rollback (`_rollback_or_non_serviceable`, `recovery.py:305-325`; `os.replace(corrupt_archive, db_path)` at `:315`, and the `OSError` handler `:424-443`, main-file `os.replace` at `:431`) moves only the main file. Sidecars that `_activate_candidate` (`:284-295`) had moved to live names are not removed (`_cleanup_staged` at `:298-302` unlinks only paths that still exist; after activation the staged paths are gone), so a rolled-back directory holds the original main plus **backup-origin** `-wal`/`-shm`. The Issue's second-pass note ("rollback does not leak candidate sidecars") holds only for the pre-activation partial-swap case, not post-activation.
- On success `shutil.rmtree(quarantine_dir, ignore_errors=True)` (`recovery.py:414-415`) silently discards the only copies of the corrupt database's WAL/SHM — the Issue's open retention question, answered by the maintainer 2026-11-15: retain on success; cleanup delegated to Issue 008. Existing tests freeze today's opposite behavior: `test_restore_with_stale_wal_shm_before_swap` (`tests/db/test_db_recovery.py:788-835`, assertion `:834`), `test_wal_shm_sidecars_land_at_final_locations_after_activation` (`:1024-1063`, `:1063`), `test_successful_restore_removes_the_quarantine_directory` (`:1438-1459`, `:1459`).

## Problem
The fail-closed contract "a candidate that fails verification never touches the live database" (`db_07` line 63) is false for sidecars: the live unit is disassembled before verification and never reassembled on failure, a post-activation rollback can leave backup-origin sidecars attached to the original main file, and the corrupt WAL's only copies are deleted on success.

## Reason for Change
Data integrity: WAL-resident committed transactions can be silently lost or mismatched after a failed restore, and reported `active_db_state` contradicts filesystem reality. The retention of corrupt-sidecar copies is an unowned decision the Issue requires to be made explicit; the maintainer answered it (retain).

## Implementation Intent
Keep quarantine where the upstream fix put it (staging, before verification) and fix what it left incomplete, building on Plan 002's activation holder:

- Quarantine records (live name → quarantine path) are returned to `db.recovery` so every terminal failure path can move the quarantined originals back to their live names, reassembling the original unit.
- The rollback composition (Plan 002's extended `_rollback_or_non_serviceable`) additionally removes sidecars the activation had moved to live names (Plan 002 AC-2) and then moves quarantined originals back (this Plan).
- On success the quarantine directory is retained as a forensic archive (`recovery.py:414-415` `rmtree` removed); retention lifetime/cleanup is delegated to Issue 008.

## Requirements
- `REQ-001`: `_quarantine_sidecar_files` and `_stage_restore` return the quarantine records (live name → quarantine path per suffix); `db.recovery` threads them through every terminal path. After any pre-activation failure (candidate integrity `recovery.py:373-386`, candidate logical `:387-402`), the live directory holds the original main file plus its original sidecars byte-identically (AC-1).
- `REQ-002`: On post-activation rollback, quarantined originals are moved back to their live names after the archived original main is replaced (`:315`, `:431` paths); a partial quarantine (one suffix recorded) moves back only what was recorded (AC-1). Combined with Plan 002's candidate-sidecar removal, after rollback the live directory holds exactly the original unit and no candidate file at any name (AC-1, AC-2).
- `REQ-003`: After a **successful** restore the quarantine directory and its copies are retained (maintainer decision recorded 2026-11-15: retain for forensics; the corrupt WAL may contain transactions the backup lacks). `recovery.py:414-415` `shutil.rmtree` is removed; the retained path is logged. Retention lifetime/cleanup is delegated to Issue 008 (AC-3).
- `REQ-004`: `_cleanup_staged` (`recovery.py:298-302`) is made failure-safe (per-path try/except with logging) so a cleanup error cannot escape its call sites, including the `OSError` handler at `:426` (AC-5). Landed by Plan 002's REQ-004 before this Plan (Correction 2); this Plan verifies the outcome, it does not re-implement it.
- `REQ-005`: Tests assert the live file set and contents after each failure branch (pre-activation integrity failure, pre-activation logical failure, post-activation rollback, `OSError`-during-swap) and assert retention on success (AC-1, AC-2, AC-3).
- `REQ-006`: `db_07` and ADR-008 state the whole-unit failure-path behavior and the retention decision in behavior/intent terms (AC-4).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/recovery.py | Modify | Thread quarantine records through failure paths; add quarantine-back to `restore_verify_failed`/`logical_verify_failed`/`verification_unavailable` returns and to the rollback composition; success-path `rmtree` removal; `_cleanup_staged` made failure-safe | REQ-001..REQ-004 / AC-1, AC-2, AC-3, AC-5 | `recovery.py:361` `quarantine_dir` creation, `:374`/`:395` cleanup-only failure returns, `:404-405` activation, `:414-415` `shutil.rmtree(quarantine_dir...)`, `:424-443` OSError handler (`:426` cleanup, `:431` main-only rollback) (checked in Step 2, post-pull) | tests/db/test_db_recovery.py | Verified |
| scripts/db/recovery_restore.py | Modify | `_quarantine_sidecar_files` returns the quarantine records; `_stage_restore` surfaces them to the caller; docstrings updated | REQ-001 / AC-1 | `recovery_restore.py:22-35` helper returns `None`; `:91-93` call site; `_stage_restore` currently returns only the staged dict (`:112`) (checked in Step 2) | tests/db/test_db_recovery.py | Verified |
| tests/db/test_db_recovery.py | Modify | Add sidecar fixtures + failure-branch assertions; flip the three success-path "quarantine removed" assertions to retention; rename the retention test | REQ-003, REQ-005 / AC-1, AC-2, AC-3 | `:834`, `:1063`, `:1459` assert quarantine absent on success; `:1436` already asserts quarantine kept on OSError; no failure-branch test uses sidecar fixtures (`test_unverified_candidate_is_never_activated` `:897-931`, `test_post_activation_failure_rolls_back_the_original` `:933-963` have none) (checked in Step 3) | tests/db/test_db_recovery.py | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Contract text (line 63) must state whole-unit restore semantics on failure paths; the staging/cleanup claims at lines 34 and 63 must reflect the retention policy for quarantined copies | REQ-006 / AC-4 | `db_07:34` quarantine-at-staging description (accurate post-pull); `db_07:63` "the live database is untouched" and "cleans up the half-written temp files and preserves the archive" (checked in Step 3; the previously cited line-77 claim does not exist — see Correction 1) | `tools/check_docs_consistency.py --domain db` | Verified |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Modify | Issue Constraint: the retention behavior "must be an explicit decision recorded in ADR-008 terms"; add the retention decision and whole-unit rollback intent to the recovery policy section | REQ-006 / AC-4 | `adr_02_05_008...:403` lists the restore-file-staging API; retention decision currently absent (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| plans/20261115-035004_dbreview002_partial-activation-rollback.md | Defines the activation-holder and extended `_rollback_or_non_serviceable` shapes this Plan builds on | scripts/db/recovery.py / REQ-002 |
| scripts/db/models.py | `RecoveryResult` fields unchanged; only values of `active_db_state` are in play | scripts/db/recovery.py / REQ-001 |
| scripts/db/recovery_verification.py | Candidate verification opens only the staged temp file; confirms quarantined live sidecars are not verification inputs | scripts/db/recovery.py / REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): After any terminal failure path (pre- or post-activation), the live directory holds the original main file plus its original `-wal`/`-shm` byte-identically.
- AC-2 (`REQ-002`): After a post-activation rollback, no sidecar originating from the backup candidate remains at live names (together with Plan 002's AC-2).
- AC-3 (`REQ-003`, `REQ-005`): A successful restore leaves the quarantine directory and its copies in place; the retention decision is asserted by tests.
- AC-4 (`REQ-006`): `uv run python tools/check_docs_consistency.py --domain db` is clean and both docs state whole-unit rollback and retention.
- AC-5 (`REQ-004`): A forced `unlink` failure inside `_cleanup_staged` still produces the documented failure result (no escaped exception).

## Tests
- `REQ-001` (AC-1): new failure-branch tests in `tests/db/test_db_recovery.py` with a live `-wal`/`-shm` pair fixture and a forced candidate integrity failure / candidate logical failure (patterns of `:897-931`) assert live sidecar bytes restored and quarantine entries moved back.
- `REQ-002` (AC-1, AC-2): post-activation failure tests (reuse Plan 002's fault-injection fixtures; patterns of `:933-963`, `:1409-1436`) assert the original unit fully reassembled and no candidate-origin sidecar at live names.
- `REQ-003` (AC-3): flip `:834`, `:1063`, `:1459` from quarantine-absent to quarantine-present; rename `test_successful_restore_removes_the_quarantine_directory` (`:1438`) to assert retention with `*_corrupt_*` copies inside.
- `REQ-004` (AC-5): unit test forcing an `OSError` from one staged path's unlink asserts the remaining staged paths are still removed and the recovery result is unchanged.
- `REQ-005`: existing helper tests `test_quarantine_sidecar_files` / `test_quarantine_sidecar_files_raises_on_copy_failure` (`:683-716`, `:749-768`) extend to the returned records; behavior unchanged otherwise. `:1436` (quarantine kept on OSError) stays unchanged.

## Documentation Impact
Yes. `REQ-006` drives `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (whole-unit failure semantics, retention) and `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (explicit retention decision, per the Issue Constraint). Both are db-domain recovery docs per `docs/00_index.md`.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `recovery_restore.py` all A; `recovery.py` top `_restore_from_backup` C(13) | `uv run radon cc scripts/db/recovery_restore.py -s`; `uv run radon cc scripts/db/recovery.py -s` (run this cycle) | 2026-11-15 |
| vulture targets | No `scripts/db` findings repo-wide | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | 2026-11-15 |
| coverage targets | project total 95%; tree clean at recording | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle) | 2026-11-15 |
| operational check | no process holds `/opt/llm/db/rag.sqlite` or `/opt/llm/db/session.sqlite` (`fuser` empty, exit 1); dev-host only | `fuser /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite` (run this cycle, recorded under Plan 002 Step 3) | 2026-11-15 |

## Assumptions
- Quarantine-at-staging is kept: verification opens only the staged candidate in the temp directory (`recovery.py:370-372`, `recovery_verification.py:124-145`); live sidecars are not inputs, so deferral is unnecessary and rejected (see Design).
- The maintainer's retention answer (retain on success, asked and answered 2026-11-15) is the ADR-008 decision to record; Issue 008 owns cleanup scheduling.
- Quarantine entries are `copy2` of the original plus `unlink` (`recovery_restore.py:34-35`); moving them back yields byte-identical live sidecars (content-preserving).
- `quarantine_dir.mkdir(exist_ok=True)` (`recovery_restore.py:92`) runs on every restore even without sidecars; after retention-on-success the directory may persist empty. Phase 2 defers the mkdir to the first actual quarantine so successful restores without sidecars create nothing (recorded as a behavior decision, not a silent side effect).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a backup-origin WAL can ever be applied to a restored original (Issue second-pass reproduction said no, confidence Low) | No further reproduction performed; behavior depends on SQLite internals and journal state | Kept as precaution (candidate-sidecar removal on rollback is required by AC-2 regardless); re-test only if a real incident occurs | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/recovery.py | Modify | High (restore state machine; `recover_corruption` services) | 9 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/recovery_restore.py | Modify | Medium (staging helper return type; only caller is `recovery.py`) | 0 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_recovery.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Low (docs) | 0 | High (single author, >70%) | not applicable (rsynced) |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Modify | Low (docs) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run with Plans 001+002+003 frozen (`tools/check_plan_target_overlaps.py`, 2026-11-15): 3 findings — `scripts/db/recovery.py` (002+003), `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (002+003), `tests/db/test_db_recovery.py` (001+002+003). Judgment: **sequencing** — Plan 003 is implemented after Plan 002 lands (dependency row above); 002's holder/rollback-completion lands first and 003's quarantine-back builds on it, `db_07` line 77 and the quarantine-retention text are edited once by 003 after 002's action/state-mapping edit, and 003's Phase 4 re-reads 002's landed wording. Plan 001's added test is disjoint from 002/003 test edits.
- Update after Plan 004 froze (same tool, 2026-11-15): 4th finding — `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (003+004). Judgment: **compatible sections, sequencing** — 003 adds retention/quarantine paragraphs; 004 edits the condition enumeration (lines 123/257) and dry-run citation (line 308); different sections, 003 lands first and 004 re-reads landed wording.
- Update after Plan 009 froze (same tool, 2026-11-15): `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is now shared by 4 plans (002+003+004+009). Judgment: **compatible sections** — 009 edits only section 12 (drill artifacts and the `rto_seconds` row); 002/003/004 own the restore/probe sections. Batch order 002 → 003 → 004 → 009; no contradiction.
- Update after Plan 008 froze (same tool, 2026-11-15): `docs/41_db/db_07...` now 5 plans (002+003+004+009+008); `scripts/db/recovery.py` now 4 plans (002+003+004+008); `scripts/db/recovery_restore.py` now 2 plans (003+008). Judgment: **compatible sections, sequencing** — 008 edits only name-construction lines (`recovery.py:359-361`, `recovery_restore.py:33` — one name wrapped in `resolve_unique_path`, disjoint from 003's return-shape changes) and section-12 lifecycle text; its quarantine sweep is the cleanup 003 explicitly delegates to it. 008 is last in the fixed batch order 001→008; no contradiction.

## Design
- **Whole-unit rollback via quarantine records**: `_quarantine_sidecar_files` returns `list[tuple[Path, Path]]` (live name → quarantine path); `_stage_restore` returns the records alongside the staged dict; `db.recovery` threads them to every terminal path. On failure, the handler order is: remove activated candidate sidecars from live names (Plan 002 holder), `os.replace(corrupt_archive, db_path)` (existing `:315`/`:431`), then `shutil.move` each recorded quarantine path back to its live name. Only recorded pairs are moved back — nothing invented is restored; partial quarantine is safe. Rejected alternative: deferring quarantine until activation (the Issue's Proposed Fix 1) — superseded by the upstream staging-time quarantine that is already fail-closed (`:26-27` copy/unlink failure raises), and deferral would re-break the pairing guarantee the upstream fix was written to establish.
- **Retention**: remove `recovery.py:414-415` `shutil.rmtree`; log the retained archive path; defer `quarantine_dir.mkdir` to the first actual quarantine so sidecar-free restores create no empty directory. The directory name is already timestamped (`recovery.py:361` `<stem>_sidecar_quarantine_<ts>`). Cleanup scheduling, disk-usage policy, and rotation are explicitly Issue 008 scope, keeping this Plan's blast radius on recovery semantics.
- **Cleanup safety**: `_cleanup_staged` wraps each `unlink` in try/except with logging (`:298-302` is currently unguarded and called from inside the `OSError` handler at `:426`, where a secondary exception would escape `recover_corruption` entirely).
- **Architecture check** (Step 3): `recovery_restore.py` imports only `shutil/time/pathlib/logging`; return-type change adds no import edge; `lint-imports` reported 6 contracts kept this cycle.
- **Persisted schema check**: N/A — no DDL, no schema version, no migration; file-level sidecar handling only.

## Implementation steps
1. **Phase 1: Quarantine records** (REQ-001; `scripts/db/recovery_restore.py`, `scripts/db/recovery.py`)
   - [ ] `_quarantine_sidecar_files` returns the (live → quarantine) records; `_stage_restore` surfaces them; docstrings updated (REQ-001; scripts/db/recovery_restore.py)
   - [ ] `_restore_from_backup` threads the records into all terminal paths and defers the `quarantine_dir` creation to first quarantine (REQ-001, REQ-003; scripts/db/recovery.py)
2. **Phase 2: Whole-unit failure paths and retention** (REQ-002, REQ-003, REQ-004; `scripts/db/recovery.py`)
   - [ ] Pre-activation failure returns (`:373-402`) move recorded quarantine pairs back before reporting (REQ-001, REQ-002)
   - [ ] Extend the rollback composition (Plan 002's holder + `_rollback_or_non_serviceable`) to move quarantined originals back after the main-file replace (REQ-002)
   - [ ] Remove the success-path `shutil.rmtree(quarantine_dir, ...)`; log the retained archive path (REQ-003)
   - [ ] Verify the `_cleanup_staged` failure-safe behavior landed by Plan 002 (REQ-004; no re-implementation — Correction 2)
3. **Phase 3: Failure-branch and retention tests** (REQ-005; `tests/db/test_db_recovery.py`)
   - [ ] Add sidecar-fixture failure tests: pre-activation integrity/logical failure, post-activation rollback, OSError-during-swap; assert whole-unit reassembly and no candidate sidecars (REQ-005)
   - [ ] Flip the three success-path quarantine assertions (`:834`, `:1063`, `:1459`) to retention; rename `:1438` test (REQ-003, REQ-005)
   - [ ] Confirm the `_cleanup_staged` forced-unlink test landed by Plan 002 covers AC-5 (REQ-004; no duplicate test — Correction 2)
4. **Phase 4: Documentation, validation & deployment hand-off** (REQ-006; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
   - [ ] Update `db_07` whole-unit failure semantics and terminal-path cleanup text; record the explicit retention decision in ADR-008 (REQ-006)
   - [ ] Run `uv run pytest tests/db`, full suite `-n auto`, ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db` (AC-4)
   - [ ] diff-cover on the branch diff reaches 90% per `rules/toolchain.md`
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision

### Release units
**Unit**: whole-unit-rollback-retention | **Phases**: 1, 2, 3 | **Reason**: removing the success-path `rmtree` and adding quarantine-back break the existing quarantine assertions (`:834`, `:1063`, `:1459`) until the Phase 3 test updates land; Phases 1-2 alone leave `tests/db` red.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/recovery.py | Failure-branch file-set assertions (tmp dirs) | `uv run pytest tests/db/test_db_recovery.py -v` | AC-1, AC-2, AC-3 asserted |
| scripts/db/recovery_restore.py | Helper tests extended to returned records | `uv run pytest tests/db/test_db_recovery.py -v` | `:683-768` helper tests keep passing with record assertions added |
| scripts/db (regression) | Existing recovery suite | `uv run pytest tests/db -v` | No regressions beyond the documented assertion flips |
| scripts/db/recovery.py (radon) | Complexity guard | `uv run radon cc scripts/db/recovery.py -s` | Baseline top `_restore_from_backup` C(13); quarantine-back composition lives in the rollback helper, not in `_restore_from_backup` |
| docs targets | Docs consistency | `uv run python tools/check_docs_consistency.py --domain db` | No findings |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | Baseline recorded this cycle (total 95%); branch diff ≥ 90% |

## Risks
- **Risk**: retained quarantine directories accumulate on production DB directories → **Mitigation**: directory created only when sidecars actually quarantine (rare: corruption restores only); cleanup policy is Issue 008, which sequences after 003 and consumes this Plan's retention decision.
- **Risk**: overlapping edits with Plan 002 in `_restore_from_backup`/`_activate_candidate`/`_rollback_or_non_serviceable` → **Mitigation**: strict order 002 → 003 recorded in both Plans; 003's procedures target the post-002 code shapes (activation holder).
- **Risk**: moving quarantined sidecars back onto a live path that a service is actively reopening could race with a WAL restart → **Mitigation**: rollback happens while no verified DB is live; operational baseline this cycle showed no process holding the DB files (re-check at deployment per Plan 002 UNK-01).
- **Risk**: `_stage_restore` return-type change breaks an unlisted caller → **Mitigation**: grep in Step 3 found exactly one production caller (`recovery.py:366`) and no test caller; `lint-imports` + full suite re-run in Phase 4.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Quarantine records (scripts/db/recovery_restore.py, scripts/db/recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-082016_1 (records) and 20261115-082016_2 (caller threading) |
| 2 | Whole-unit failure paths and retention (scripts/db/recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-082016_2 |
| 3 | Failure-branch and retention tests (tests/db/test_db_recovery.py) | In Progress | — | — | Procedure generated: implementations/20261115-082016_3 |
| 4 | Documentation, validation & deployment hand-off (docs/41_db/db_07..., docs/10_adr/adr_02_05_008...) | In Progress | — | — | Procedure generated: implementations/20261115-082016_4 and 20261115-082016_5 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261115-082016_1_scripts_db_recovery_restore.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-082016_2_scripts_db_recovery.py.md | 2 | Procedure | Created | — | — |
| implementations/20261115-082016_3_tests_db_test_db_recovery.py.md | 3 | Procedure | Created | — | — |
| implementations/20261115-082016_4_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 4 | Procedure | Created | — | — |
| implementations/20261115-082016_5_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 4 | Procedure | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-041125
- **Related target files**: scripts/db/recovery.py, scripts/db/recovery_restore.py, tests/db/test_db_recovery.py, docs/41_db/db_07_api_and_operations-recovery-and-reference.md, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Background bullets 1-2 (post-pull re-verification) | scripts/db/recovery_restore.py, scripts/db/recovery.py | Phase 1 | AC-1 | Phase 3 pre-activation failure tests | Explicit in code (Step 2, post-pull) |
| REQ-002 | Background bullet 2 (post-activation sidecar leak) | scripts/db/recovery.py | Phase 2 | AC-1, AC-2 | Phase 3 post-activation rollback tests | Explicit in code (Step 2) |
| REQ-003 | Background bullet 3; maintainer answer 2026-11-15 | scripts/db/recovery.py | Phase 2 | AC-3 | Phase 3 flipped assertions `:834`, `:1063`, `:1459` | Explicit in code (Step 2) |
| REQ-004 | Cleanup-safety gap found in Step 2 re-verification | scripts/db/recovery.py | Phase 2 | AC-5 | Phase 3 forced-unlink test | Explicit in code (Step 2) |
| REQ-005 | Required Changes bullet 4; Testing Expectations | tests/db/test_db_recovery.py | Phase 3 | AC-1, AC-2, AC-3 | Phase 3 tests themselves | Verified by test (gap confirmed in Step 3) |
| REQ-006 | Documentation Impact; Issue Constraint (ADR-008 terms) | docs/41_db/db_07_api_and_operations-recovery-and-reference.md, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Phase 4 | AC-4 | `check_docs_consistency.py --domain db` | Explicit in code (Step 3) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-082016 -->