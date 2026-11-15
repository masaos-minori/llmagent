## Goal
- Make every recovery probe (integrity check, domain-identity check, logical verification) read-only and side-effect-free, treat a missing database file as its own non-HEALTHY condition that is never created by probing, and report it for operator intervention instead of an automatic restore.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: `SQLiteHelper` read-only open mode (`mode=ro` URI, no write pragmas); existence check + `DbCondition.MISSING` in the integrity probe; read-only probe call sites for backups, archives, rotated archives, drill copies, and post-activation live re-checks; the staged-candidate probe stays read-write (Issue Constraint); new `missing_database` recovery action (no automatic restore — maintainer decision 2026-11-15); hash/directory-unchanged and read-only-backup tests; ADR-008 and `db_07` condition/action updates.
- **Out-of-Scope**: what `PRAGMA integrity_check` verifies; vec extension handling (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`, planned); production pragma policy for normal write connections (Issue AI Instruction); quarantine/sidecar semantics (`plans/20261115-041125_dbreview003_restore-sidecar-handling.md`).
- **Dependencies**: none per the Issue; batch sequencing applies.
  - **Depends on**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md | phase all | sequencing only: 003 rewrites the activation/rollback region of `scripts/db/recovery.py` that this Plan also touches; 004 lands after 003 so the two do not collide. No behavioral dependency: `missing_database` never enters the restore flow, so it does not interact with 002's archive-less rollback concern.

## Background
From the Source Issue (F-004), re-verified against the post-pull tree: `apply_connection_pragmas` (`scripts/db/helper.py:30-42`) runs `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` on **every** open (`write_mode` gates only `foreign_keys`); `SQLiteHelper._connect` uses a plain `sqlite3.connect` (`helper.py:145-149`) which **creates** a missing file. `_run_integrity_check` (`recovery.py:91-106`) and `_verify_domain_identity` (`recovery.py:157-176`) open their subject through that path, so: a missing path probes "healthy" and is created; a rollback-journal backup is converted to WAL and its bytes change; a `0444` backup fails the pragma with `attempt to write a readonly database` and is classified `PERMISSION_FAILURE` → `bad_backup`. Consumers that probe archives/backups: `rotation._verify_archive` (`rotation.py:72,78`), the drill (`recovery_drill.py:97-98,131`), `_backup_is_usable` (`recovery.py:180-188`). `docs/10_adr/adr_02_05_008...:308` even documents the mutation as a known gap ("a rollback-journal file is switched to WAL when opened and is not covered"). Adversarial finding: `run_integrity_check`'s docstring claims "Consumers are the migration gate (rows 01/06)" — no migration-gate consumer exists (grep: only `rotation.py` and `recovery_drill.py` import it); stale claim to fix in this Plan.

## Plan-Document Correction (re-verification at procedure generation, 2026-11-15)

- All Background and target-file claims re-verified this cycle against the current tree (no code changes have landed since the plan was frozen): `helper.py:38-42` unconditional `journal_mode=WAL`/`synchronous=NORMAL` (`:41-42` gate only `foreign_keys`); `helper.py:145-149` plain `sqlite3.connect` creates a missing file; `recovery.py` `DbCondition` enum `:31-36`, `_run_integrity_check` `:91-106` (open at `:99`), `_verify_domain_identity` `:157-176` (open at `:167`), `_backup_is_usable` `:180-188` (probe at `:187-188`), stale "migration gate" docstring claim `:214-216` (grep: `run_integrity_check`/`verify_domain_identity` consumers are only `rotation.py:72,78` and `recovery_drill.py:97-98,131` — the claim is confirmed stale); `_NO_RESTORE_CONDITIONS` `:447`; `_result_for_condition` `:456`; `recovery_verification.py:141` default open; drill's own ro reads at `recovery_drill.py:78`; ADR citations at `:123` (Decision Detail #14 enumeration), `:257` (INV-13), `:308` (dry-run test citation "a rollback-journal file is switched to WAL when opened and is not covered"); `db_07` enum text `:41`, diagnosis bullets `:45-52`, dry-run bullets `:75-76`, recovery-contract bullets `:65-66`. No claim disconfirmed. `test_recover_permission_failure` (`tests/db/test_db_recovery.py:112`) patches `_run_integrity_check` directly (not file permissions), so the read-only probe change does not break it; the `mock_sqlite_helper` fixture (`:32-40`) patches the helper class with MagicMock, which tolerates new kwargs.
- Correction 1 (docs anchor drift): after Plan 003's docs procedures (`implementations/20261115-082016_4`/`_5`) land, the ADR line citations 123/257/308 shift (Decision Detail #21 and the new Recovery Policy Matrix row insert lines before them) and `db_07` lines 34/63 shift (retention text). Plan 004's docs procedures must anchor by content (Decision Detail #14 text, INV-13 text, the dry-run citation parenthetical, the `db_07` enum sentence at "The enum distinguishes:" and the recovery-contract bullets) and re-read the landed 003 wording before editing.
- Correction 2 (overlap invisible to the scan): Plan 001's procedure `implementations/20261115-075008_1_scripts_db_recovery_verification.py.md` edits the same `recovery_verification.py:141` open call that REQ-005 makes `read_only` (it threads the `sqlite_vec_so` kwarg); `tools/check_plan_target_overlaps.py` no longer reports it because Plan 001 is archived. Judgment: **sequencing** 001 → 004, compatible — the landed call composes both kwargs (`load_vec` on a read-only connection is legal per Design). Overlap scan re-run this cycle: 10 findings; 004 rows match the recorded judgments (`helper.py`/`test_sqlite_helper.py` with Plan 005; `recovery.py` with Plan 008 name-construction lines only; `db_07` with Plans 008/009; `test_db_maintenance.py` with Plans 006/007/008).
- Correction 3 (test-fake signature): `tests/db/test_sqlite_helper.py` defines a local fake helper (`_InMemoryHelper`, `:16`) whose `open` (`:23-25`) mirrors the current `SQLiteHelper.open` kwargs; the REQ-001 unit tests must extend this fake with the `read_only` kwarg, otherwise fake-based calls raise `TypeError`.

## Problem
Verification mutates its subject (backup bytes, journal mode, sibling sidecars, created files) and reports a missing database as HEALTHY, sending `recover_corruption` down the vacuum/dry-run branch — under `dry_run=True` too.

## Reason for Change
Forensic value of archives, checksum-based backup validation, and dry-run's no-side-effect promise all depend on probes being pure reads. The missing-file misclassification turns a vanished database into a silently "healthy" empty one.

## Implementation Intent
Add an explicit read-only open to the Helper (`file:...?mode=ro` URI, write pragmas skipped), default every probe call site to it, keep the staged candidate's integrity probe read-write per the Issue Constraint, and classify a missing path as a new `DbCondition.MISSING` that `recover_corruption` reports as `missing_database` without attempting a restore (maintainer decision).

## Requirements
- `REQ-001`: `SQLiteHelper.open(read_only=True)` connects via `file:<path>?mode=ro` URI and applies only `PRAGMA busy_timeout` (no `journal_mode`/`synchronous`/`foreign_keys` writes); a missing path raises instead of being created. Default behavior of `open()` is unchanged for all existing write/normal paths.
- `REQ-002`: `_run_integrity_check` checks existence first and returns a new `DbCondition.MISSING` (`"missing"`) with a path-carrying detail without opening or creating anything; the public `run_integrity_check` wrapper probes read-only (consumers `rotation`, `recovery_drill` require no call-site change).
- `REQ-003`: `_backup_is_usable` and `_verify_domain_identity` probe read-only; a read-only backup (e.g. `0444`) verifies successfully as HEALTHY. The staged-candidate integrity probe in `_verify_candidate` stays read-write (Issue Constraint: candidate may need WAL recovery).
- `REQ-004`: `recover_corruption` maps `MISSING` to a distinct result: `action="missing_database"`, `active_db_state="missing"`, detail names the path; no restore attempt, no vacuum, no file creation — identical under `dry_run=True` (maintainer decision 2026-11-15: no automatic restore for a missing live DB).
- `REQ-005`: `_run_logical_verification` opens its target read-only (its queries are pure reads); the read-write candidate flow established by Plan 003 is not weakened because the integrity stage still runs read-write first.
- `REQ-006`: Tests: sha256 of a backup before/after `run_integrity_check`/`_verify_archive`; directory listing before/after (no created `-wal`/`-shm`); missing path yields MISSING + no file (also `dry_run=True`); `0444` backup verifies healthy; read-only open unit test on the Helper.
- `REQ-007`: Fix the stale `run_integrity_check` docstring consumer claim (migration gate does not consume it); ADR-008 condition enumeration (line 123, INV-13 at 257) and the dry-run test citation (line 308) plus `db_07` action/condition tables gain `missing`/`missing_database`.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/helper.py | Modify | Add `read_only` open mode: `mode=ro` URI connect path and pragma skipping | REQ-001 / AC-1, AC-3 | `helper.py:38-39` unconditional WAL/synchronous pragmas (`:41-42` gates only `foreign_keys` via `write_mode`); `:145-149` plain `sqlite3.connect` creates files (checked in Step 2, post-pull) | tests/db/test_sqlite_helper.py | Verified |
| scripts/db/recovery.py | Modify | `DbCondition.MISSING`, existence check, `read_only` probe selection (`_run_integrity_check`, `_verify_domain_identity`, `_backup_is_usable`, `run_integrity_check` wrapper), `missing_database` result, docstring fix | REQ-002..REQ-004, REQ-007 / AC-2, AC-3 | `recovery.py:99` integrity open, `:167` identity open, `:187-188` backup probe, `:214-216` stale "migration gate" claim, enum at `:31-36` (checked in Step 2) | tests/db/test_db_recovery.py | Verified |
| scripts/db/recovery_verification.py | Modify | `_run_logical_verification` opens read-only | REQ-005 / AC-1 | `recovery_verification.py:141` `SQLiteHelper(...).open()` default (checked in Step 2) | tests/db/test_db_recovery.py | Verified |
| tests/db/test_sqlite_helper.py | Modify | Unit coverage for `read_only` open: pragma skipping, missing path raises, default unchanged | REQ-001 / AC-1 | `test_sqlite_helper.py:24` open signature exercised today; no read-only case exists (grep, Step 3) | tests/db/test_sqlite_helper.py | Verified |
| tests/db/test_db_recovery.py | Modify | Hash/dir-unchanged probe tests, MISSING tests (incl. dry_run), `0444` backup healthy test | REQ-002..REQ-006 / AC-1..AC-3 | Existing suite has no byte/dir-unchanged probe test (grep Step 3); Issue Testing Expectations | tests/db/test_db_recovery.py | Verified |
| tests/db/test_db_maintenance.py | Modify | Rotation archive probe invariance test (`_verify_archive` leaves archive bytes/mode unchanged) | REQ-006 / AC-1 | Rotation tests live here (grep found no separate rotation test file, Step 3) | tests/db/test_db_maintenance.py | Verified |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Modify | Condition enumeration (line 123, INV-13 line 257) and dry-run citation (line 308) gain `missing`; remove the "switched to WAL ... not covered" caveat after the fix | REQ-007 / AC-4 | ADR lines 123/257/308 quoted from this cycle's grep | `tools/check_docs_consistency.py --domain db` | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Action table gains `missing_database`; probe semantics stated as side-effect-free reads | REQ-007 / AC-4 | `db_07` carries the recovery action/state contract (Plan 002 consumer scan, this cycle) | `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/rotation.py | `run_integrity_check`/`verify_domain_identity` consumer at `:72,78`; **no edit required** — the public wrapper's read-only default covers it; verified this cycle | scripts/db/recovery.py / REQ-002 |
| scripts/db/recovery_drill.py | Consumer at `:97-98,131`; already uses `mode=ro` URIs for its own reads (`:78`); no edit required | scripts/db/recovery.py / REQ-002 |
| scripts/db/models.py | `RecoveryResult.active_db_state` gains the `"missing"` value in docs only; fields unchanged | scripts/db/recovery.py / REQ-004 |
| scripts/agent/services/db_maintenance_service.py, scripts/agent/services/rag_maintenance_service.py | `recover_corruption` consumers: confirm they tolerate a new action value (they log/report, do not enumerate exhaustively) | scripts/db/recovery.py / REQ-004 |

## Acceptance Criteria
- AC-1 (`REQ-001..REQ-003`, `REQ-005`, `REQ-006`): Verifying a backup/archive leaves its bytes, journal mode, and sibling files unchanged (sha256 + directory assertions in tests).
- AC-2 (`REQ-002`, `REQ-004`, `REQ-006`): A missing live database yields `DbCondition.MISSING` / `action="missing_database"` and no file is created, including `dry_run=True`.
- AC-3 (`REQ-003`, `REQ-006`): A read-only backup (0444) verifies successfully (HEALTHY, usable), and the staged-candidate integrity probe remains read-write (candidate WAL-recovery behavior unchanged — Plan 003 candidate tests stay green).
- AC-4 (`REQ-007`): `uv run python tools/check_docs_consistency.py --domain db` is clean; ADR-008 lists the new condition; `db_07` lists the new action.

## Tests
- `REQ-001` (AC-1): `tests/db/test_sqlite_helper.py` — `open(read_only=True)` on a rollback-journal DB: `PRAGMA journal_mode` still `delete` afterwards, directory shows no `-wal`/`-shm`; on a missing path: `sqlite3.OperationalError` and file still absent.
- `REQ-006` (AC-1, AC-2, AC-3): `tests/db/test_db_recovery.py` — sha256 + `listdir` before/after `run_integrity_check` and `_backup_is_usable`; `recover_corruption` with a missing live path returns `missing_database`, file count unchanged (also `dry_run=True`); `chmod 0o444` backup passes `_backup_is_usable`.
- `REQ-006` (AC-1): `tests/db/test_db_maintenance.py` — after `rotate`, the archive's sha256 equals the copy's bytes pre-verification.
- Regression: existing `tests/db` recovery suite plus Plan 003's candidate/sidecar tests stay green.

## Documentation Impact
Yes. `REQ-007` drives `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (condition enumeration, INV-13, dry-run citation) and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (action table, probe semantics) — both db-domain recovery docs per `docs/00_index.md`.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `helper.py` top `open` B(8); `recovery.py` top `_restore_from_backup` C(13); `recovery_verification.py` top A(5); `rotation.py` top A(3) | `uv run radon cc scripts/db/helper.py -s`; `scripts/db/recovery.py -s`; `scripts/db/recovery_verification.py -s`; `scripts/db/rotation.py -s` (run this cycle) | 2026-11-15 |
| vulture targets | No `scripts/db` findings repo-wide | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | 2026-11-15 |
| coverage targets | project total 95%; tree clean at recording | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle) | 2026-11-15 |
| churn30 targets | recovery.py 9, rotation.py 3, helper.py 3, recovery_verification.py 7 | `git log --name-only --pretty=format: --since=30.days -- scripts/ | sort | uniq -c | sort -rn` (captured this cycle, `/tmp/opencode/churn30.txt`) | 2026-11-15 |

## Assumptions
- `sqlite3.connect("file:...?mode=ro", uri=True)` raises `OperationalError` (does not create) for absent files — standard SQLite behavior; verified behaviorally in the Phase 1 tests (checked in Step 3 as mechanism, test in Phase 2).
- `PRAGMA integrity_check` and plain SELECTs succeed on read-only connections against WAL-mode databases (reads integrate the WAL); checkpointing is left to normal write opens (services already open read-write).
- Consumers of `recover_corruption` treat unknown action values as report/log strings (db_maintenance_service / rag_maintenance_service read `result.action`/`detail`; checked in Step 3 for both services).
- Maintainer decision recorded 2026-11-15: a missing live DB is never auto-restored.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether removing the probe-time WAL conversion changes any operational behavior that implicitly relied on the side effect (e.g. an integrity probe as opportunistic WAL recovery for a live DB after a crash) | No code path was found that depends on probe-side checkpointing (Step 3 grep: services open read-write for normal work); host cron unknowns mirror Plan 002 UNK-01 | Operator confirms during rollout observation; normal service opens still recover/checkpoint | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/helper.py | Modify | High (every DB component opens through this Helper; default behavior preserved) | 3 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/recovery.py | Modify | High (restore state machine + `DbCondition` consumers `rotation`, `recovery_drill`) | 9 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/recovery_verification.py | Modify | Medium (verification stage only) | 7 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_sqlite_helper.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_recovery.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_maintenance.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Modify | Low (docs) | 0 | High (single author, >70%) | not applicable (rsynced) |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Low (docs) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15): 4 findings — `scripts/db/recovery.py` (002+003+004), `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (002+003+004), `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (003+004), `tests/db/test_db_recovery.py` (001+002+003+004). `tests/db/test_db_maintenance.py` is additionally shared with Plan 006 (frozen 2026-11-15: purge/vacuum/prune mode-and-transaction tests, disjoint from 004's rotation-invariance tests) and Plan 007 (frozen 2026-11-15: retention boundary tests; it also aligns the shared `_make_session_db` harness to the `T/Z` format — 004's rotation tests do not use that harness; 007 runs the whole file). Judgment: **sequencing** — fixed batch order 001→002→003→004; 004 edits the probe region of `recovery.py` (functions 91-235) while 002/003 edit the restore region (284-443): disjoint function ranges within the file, executed in order. In ADR-008, 003 adds retention/quarantine paragraphs and 004 edits the condition enumeration (lines 123/257) and the dry-run citation (line 308) — different sections, no contradiction. Plan 004's new `missing_database` must be added to the docs sections 002/003 already rewrote — its Phase 4 re-reads their landed wording. Test edits are per-plan disjoint (001 vec test, 002 action-flips, 003 quarantine flips, 004 invariance/MISSING additions).
- Update after Plan 005 froze (same tool, 2026-11-15): 2 more findings — `scripts/db/helper.py` (004+005) and `tests/db/test_sqlite_helper.py` (004+005). Judgment: **sequencing** — 005 lands after 004 and wraps 004's landed `open`/`_connect`/pragma shapes in its teardown handler; its tests are disjoint from 004's read-only unit tests.
- Update after Plan 009 froze (same tool, 2026-11-15): `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is now shared by 4 plans (002+003+004+009). Judgment: **compatible sections** — 009 edits only section 12 (drill artifacts and the `rto_seconds` row); 004 owns the probe/dry-run sections. Batch order 002 → 003 → 004 → 009; no contradiction.
- Update after Plan 008 froze (same tool, 2026-11-15): `docs/41_db/db_07...` now 5 plans; `scripts/db/recovery.py` now 4 plans (008 edits only the name-construction lines `:359-361`, disjoint from 004's probe functions `91-235`); `tests/db/test_db_maintenance.py` now 4 plans (008 appends a new retention test class). Judgment: **compatible sections, sequencing** — 008 is last in the fixed batch order 001→008; no contradiction.

## Design
- **Helper read-only mode**: `open(read_only=True)` routes `_connect` to `sqlite3.connect(f"file:{escaped}?mode=ro", uri=True, ...)` (escape via `urllib.request.pathname2url` to keep exotic paths valid) and calls a pragma path that applies `busy_timeout` only. `apply_connection_pragmas` gains the gating parameter (or a sibling `apply_read_only_pragmas`) so the write-pragma default is untouched (Issue AI Instruction: production pragma policy unchanged). `load_vec` behavior is unchanged (extension loading is connection-local and legal on ro connections). Rejected alternative: a separate ProbeHelper class — duplicates lifecycle, config boundaries, and vec loading for one flag.
- **Probe classification**: `_run_integrity_check(db_path, target, *, read_only: bool)` — existence first (`MISSING`, no open), then open per call site: backup/identity/public wrapper/live probes `read_only=True`; `_verify_candidate`'s integrity stage `read_only=False` (Issue Constraint). Public `run_integrity_check` fixes its docstring consumer list (rotation, drill) and probes read-only.
- **Missing policy**: `_result_for_condition` gains a `MISSING` branch → `_failure("missing_database", ...)`, `active_db_state="missing"`; NOT added to `_NO_RESTORE_CONDITIONS` (it deserves its own action, not a generic `error`). Dry-run path unchanged otherwise.
- **Enum addition**: `DbCondition.MISSING = "missing"` — StrEnum consumers (`rotation`, `drill`, services) compare by value; docs enumeration updated (Issue Constraint: "document any new enum member").
- **Architecture check** (Step 3): no new import edges (`urllib.request` is stdlib; arch-linter contracts 6 kept this cycle). `lint-imports` re-run in Phase 4.
- **Persisted schema check**: N/A — no DDL/schema change; only connection mode.

## Implementation steps
1. **Phase 1: Helper read-only open** (REQ-001; `scripts/db/helper.py`)
   - [ ] `open(read_only=True)`: ro-URI connect + busy-timeout-only pragma path (REQ-001; scripts/db/helper.py)
   - [ ] Unit tests: pragma skipping, missing-path raise, default unchanged (REQ-001; tests/db/test_sqlite_helper.py)
2. **Phase 2: Probe call sites and MISSING classification** (REQ-002..REQ-005, REQ-007; `scripts/db/recovery.py`, `scripts/db/recovery_verification.py`)
   - [ ] `DbCondition.MISSING` + existence-first check in `_run_integrity_check`; docstring consumer fix (REQ-002, REQ-007; scripts/db/recovery.py)
   - [ ] Read-only probes in `_backup_is_usable`, `_verify_domain_identity`, public wrapper; read-write kept for candidate integrity (REQ-003; scripts/db/recovery.py)
   - [ ] `MISSING` → `missing_database` result in `_result_for_condition` (REQ-004; scripts/db/recovery.py)
   - [ ] `_run_logical_verification` read-only open (REQ-005; scripts/db/recovery_verification.py)
3. **Phase 3: Invariance and policy tests** (REQ-006; `tests/db/test_db_recovery.py`, `tests/db/test_db_maintenance.py`)
   - [ ] sha256/dir-unchanged probe tests; MISSING incl. dry_run; 0444 backup healthy; rotation archive invariance (REQ-006)
   - [ ] Run `uv run pytest tests/db` and full suite `-n auto` (AC-1..AC-3)
4. **Phase 4: Documentation, validation & deployment hand-off** (REQ-007; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`)
   - [ ] ADR-008 condition enumeration/INV-13/dry-run citation; `db_07` action table + probe semantics (REQ-007)
   - [ ] Run ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db` (AC-4)
   - [ ] diff-cover on the branch diff reaches 90% per `rules/toolchain.md`
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision

### Release units
**Unit**: ro-probes-missing-policy | **Phases**: 2, 3 | **Reason**: the `MISSING` classification and `missing_database` action change results asserted by existing tests until the Phase 3 test updates land; Phase 2 alone leaves `tests/db` red. Phase 1 is independently validatable (additive Helper parameter).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/helper.py | Unit: ro open semantics, default unchanged | `uv run pytest tests/db/test_sqlite_helper.py -v` | AC-1 unit assertions pass |
| scripts/db/recovery.py | Unit/integration: probes non-mutating (sha256/dir), MISSING policy, 0444 backup | `uv run pytest tests/db/test_db_recovery.py -v` | AC-1..AC-3 asserted |
| scripts/db/rotation.py (consumer, no edit) | Regression through rotation tests | `uv run pytest tests/db/test_db_maintenance.py -v` | Rotation archive invariance test passes |
| scripts/ (regression) | Full DB + service suites | `uv run pytest tests/ -n auto` | No regressions (drill, services, consistency) |
| scripts/db/helper.py (radon) | Complexity guard | `uv run radon cc scripts/db/helper.py -s` | Baseline top `open` B(8); keep B — extract the ro connect branch into `_connect_read_only` rather than deepening `open` |
| docs targets | Docs consistency | `uv run python tools/check_docs_consistency.py --domain db` | No findings |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | Baseline recorded this cycle (95%); branch diff ≥ 90% |

## Risks
- **Risk**: the ro probe no longer checkpoints/converts live DBs opportunistically → **Mitigation**: UNK-01; normal service opens are read-write and perform recovery; rollout observation confirms no reliance.
- **Risk**: `mode=ro` cannot open databases whose sidecars or directory permissions require write access even for reads (e.g. WAL DB whose `-wal` is on a read-only mount) → **Mitigation**: probe falls back — if the ro open raises `PERMISSION_FAILURE`, the result is honest (`permission_failure`), matching the Issue's intent that read-only media must verify **successfully** only when actually readable; the 0444-file test covers the plain-file case, and a WAL-mode ro test is included in Phase 3.
- **Risk**: Helper is the shared open path for every DB component; a defect in the new flag could leak into production opens → **Mitigation**: default parameters unchanged; new branch only reachable via explicit `read_only=True`; full-suite run in Phase 3/4.
- **Risk**: new enum/action values consumed by external monitoring parsers (grep of repo showed none) → **Mitigation**: docs-first in Phase 4; UNK mirrors Plan 002 UNK-01 host-cron check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Helper read-only open (scripts/db/helper.py, tests/db/test_sqlite_helper.py) | In Progress | — | — | Procedure generated: implementations/20261115-084603_1_scripts_db_helper.py.md, implementations/20261115-084603_4_tests_db_test_sqlite_helper.py.md |
| 2 | Probe call sites and MISSING classification (scripts/db/recovery.py, scripts/db/recovery_verification.py) | In Progress | — | — | Procedure generated: implementations/20261115-084603_2_scripts_db_recovery.py.md, implementations/20261115-084603_3_scripts_db_recovery_verification.py.md |
| 3 | Invariance and policy tests (tests/db/test_db_recovery.py, tests/db/test_db_maintenance.py) | In Progress | — | — | Procedure generated: implementations/20261115-084603_5_tests_db_test_db_recovery.py.md, implementations/20261115-084603_6_tests_db_test_db_maintenance.py.md |
| 4 | Documentation, validation & deployment hand-off (docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md) | In Progress | — | — | Procedure generated: implementations/20261115-084603_7_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md, implementations/20261115-084603_8_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261115-084603_1_scripts_db_helper.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-084603_2_scripts_db_recovery.py.md | 2 | Procedure | Created | — | — |
| implementations/20261115-084603_3_scripts_db_recovery_verification.py.md | 2 | Procedure | Created | — | — |
| implementations/20261115-084603_4_tests_db_test_sqlite_helper.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-084603_5_tests_db_test_db_recovery.py.md | 3 | Procedure | Created | — | — |
| implementations/20261115-084603_6_tests_db_test_db_maintenance.py.md | 3 | Procedure | Created | — | — |
| implementations/20261115-084603_7_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 4 | Procedure | Created | — | — |
| implementations/20261115-084603_8_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 4 | Procedure | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-041859
- **Related target files**: scripts/db/helper.py, scripts/db/recovery.py, scripts/db/recovery_verification.py, tests/db/test_sqlite_helper.py, tests/db/test_db_recovery.py, tests/db/test_db_maintenance.py, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Constraint (per-call read-only) | scripts/db/helper.py | Phase 1 | AC-1 | test_sqlite_helper ro-open unit tests | Explicit in code (Step 2: helper.py:39-41, 145) |
| REQ-002 | Required Changes bullet 2; Problem bullet 1 | scripts/db/recovery.py | Phase 2 | AC-2 | MISSING tests incl. dry_run | Explicit in code (Step 2: recovery.py:91-106) + live repro in Issue |
| REQ-003 | Problem bullets 2-3; Required Changes bullet 1 | scripts/db/recovery.py | Phase 2 | AC-1, AC-3 | sha256/dir tests, 0444 test | Confirmed by mechanism + Issue repro |
| REQ-004 | Unresolved Question (maintainer answer 2026-11-15: no auto restore) | scripts/db/recovery.py | Phase 2 | AC-2 | `missing_database` assertion | Maintainer decision |
| REQ-005 | Target Files list; probe semantics | scripts/db/recovery_verification.py | Phase 2 | AC-1 | dir-unchanged test for logical stage | Explicit in code (Step 2: recovery_verification.py:141) |
| REQ-006 | Required Changes bullet 4; Testing Expectations | tests/db/test_db_recovery.py, tests/db/test_db_maintenance.py, tests/db/test_sqlite_helper.py | Phase 1, 3 | AC-1..AC-3 | New tests | Pending |
| REQ-007 | Documentation Impact; adversarial finding F5 (stale docstring consumer claim) | scripts/db/recovery.py, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Phase 2, 4 | AC-4 | `check_docs_consistency.py --domain db` | Explicit in code (Step 2: recovery.py:214-216; ADR 123/257/308) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-084603 -->