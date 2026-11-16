# Plan 008: Artifact retention sweeps and collision-safe generated names

## Goal
- Bound the disk growth of every artifact class `scripts/db` creates (rotation/drill archives, drill JSON outputs, retained quarantine directories, failed-restore temp leftovers) with configured age/count retention, make the `_restored` working copy short-lived, and make same-second generated names collision-safe so no artifact is ever silently overwritten.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: new `ArtifactRetentionConfig` + `purge_archive_artifacts()` sweep in `scripts/db/maintenance.py`; six new `agent.toml` keys (config file, `ProductionConfigValidator` registry, reference table); `_restored` copy deletion + JSON-name uniquifier in `scripts/db/recovery_drill.py`; `resolve_unique_path()` in `scripts/db/config.py` applied at the five name-generation sites (`rotation.py`, `recovery.py`, `recovery_restore.py`, `recovery_drill.py`); tests; docs (`db_06`, `db_07` section 12).
- **Out-of-Scope**: offsite/remote backup (Issue); restore verification logic (Issue); the quarantine-back/retention-on-success behavior itself (owned by `plans/20261115-041125_dbreview003_restore-sidecar-handling.md`, which this plan's quarantine sweep builds on); scheduling on the production host (the repo documents cadence only — the existing `purge_corrupt_archives` has no in-repo caller either, confirmed this cycle: `db_maintenance_service.py` calls only `vacuum_db`/`purge_old_sessions`).
- **Dependencies**:
  - **Depends on**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md | phase all | Issue's own dependency row: 003's retain-on-success is what makes quarantine directories an accumulating class, and 003 defers their cleanup to this plan (003 Scope, Out-of-Scope bullet).
  - **Depends on**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md | phase all | 006 lands first and defines the maintenance-mode contract (config-error propagation, honest failure data) that `purge_archive_artifacts` must follow.
  - **Depends on**: plans/20261115-050559_dbreview007_retention-input-validation.md | phase all | 007 lands first and fixes the retention-value semantics (0 = disabled, negative = `ValueError`) and `get_typed` bool rejection that the new `ArtifactRetentionConfig.from_config` reuses.
  - **Depends on**: plans/20261115-051359_dbreview009_drill-harness-fidelity.md | phase all | 009 lands first and restructures `_drill_one_domain`'s failure handling; 008's `_restored`-deletion and JSON-uniquifier edits apply to 009's landed shape.

## Background
Re-verified 2026-11-16 against the git repo working tree (this repository, the implementation target). The originally-recorded line numbers came from the deployed `/opt/llm` copy, which has since diverged and is no longer the target; every anchor below is re-measured against the repo source. Gap 5 and Gap 6 as first worded did not survive re-verification and are reframed (see Claims 5/6).

Artifact-class directory map (repo-verified):
- `sqlite_archive_dir` (default `/opt/llm/db/archive`, `config/agent.toml:16`, resolved by `rotation._resolve_archive_dir` — not a `DbConfig` field): normal rotation archives `{stem}_{ts}{suffix}` (`rotation.py:47-48`) plus drill recovery-point archives of the same shape. Never pruned.
- `<archive_dir>/drills` (`recovery_drill.py:278` default `{resolved_archive}/drills`): drill JSON `{domain}_{ts}.json` (`_persist_artifact`, `:262`) and drill working copy `{name}_restored{suffix}` (`:212-215`). Never pruned.
- `db_path.parent` (the live DB directory, `/opt/llm/db`): corrupt archives `{stem}_corrupt_{ts}{suffix}` (`recovery.py:424`, pruned by `purge_corrupt_archives`), quarantine directories `{stem}_sidecar_quarantine_{ts}` (`recovery.py:426`), and `temp_restore` `{stem}.tmp_{ts}{suffix}` (`recovery.py:425`).

- Claim 1 (rotation archives never purged): **Confirmed.** `purge_corrupt_archives` (`scripts/db/maintenance.py:404-449`) globs only `{stem}_corrupt_*{suffix}` under `db_path.parent` for rag and session only (`:426`, pattern `:429`). Files created by `rotation._archive_db_file` (`{stem}_{ts}{suffix}` under `sqlite_archive_dir`) — including workflow archives and drill-created recovery-point archives — match no purge anywhere in `scripts/`. `rotation.py` (118 lines) has no prune function and no `prune_old_chunks`.
- Claim 2 (drill outputs unbounded): **Confirmed.** Each drill run writes a recovery-point archive into `archive_dir`, a full copy `{name}_restored{suffix}` (`recovery_drill.py:212-215`), and a JSON artifact `{domain}_{ts}.json` (`_persist_artifact`, `:258-264`) under `<archive_dir>/drills`; nothing deletes them. (Correction: the JSON name is timestamped per run, not a fixed name — the unbounded-accumulation gap holds, the earlier "fixed filename overwrites" wording was wrong for the repo.)
- Claim 3 (quarantine leftovers): **Confirmed, via Plan 003's landed shape.** The repo restore creates a quarantine *directory* `{stem}_sidecar_quarantine_{ts}` only when a sidecar actually quarantines (`recovery_restore.py:45`), and on success `_retain_quarantine_archive` (`recovery.py:488` → `recovery_restore.py:96-104`) keeps it as a forensic archive and explicitly defers removal to "the operator-side artifact retention issue" (`recovery_restore.py:100-101`) — this plan. `.tmp_` leftovers (`recovery.py:425`) are unlinked by `_cleanup_staged` (`:334-344`, invoked at `:442/464/499`) but survive a crash between staging and cleanup.
- Claim 4 (second-granularity name collisions): **Confirmed.** `format_timestamp` = `YYYYMMDD_HHMMSS` (`config.py:56-61`). Same-second names collide with no uniquifier anywhere: `rotation.py:47-48` (backup API silently overwrites — Issue reproduction), `recovery.py:423-426` (`corrupt_archive`, `temp_restore`, `quarantine_dir` from one `ts`), `recovery_restore.py:46-48` (quarantined sidecar file, `ts = int(time.time())` at `:39`), `recovery_drill.py:212` (`isolated`) and `:262` (artifact JSON). No `resolve_unique_path` exists in the repo.
- Claim 5 (corrupt-archive retention): **Reframed — original wording false for the repo.** The corrupt keys ARE already wired: `CorruptArchiveRetentionConfig.from_config` (`maintenance.py:158-170`) feeds `purge_corrupt_archives` (`:404-449`), age-then-count. The real repo gap is *scope*: `purge_corrupt_archives` iterates only `rag_db_path` and `session_db_path` (`:426`), so corrupt archives of other restored domains and quarantined sidecar files are outside its sweep. This plan's quarantine sweep (REQ-002 sweep 3) covers the directory class; corrupt-file sweep scope stays owned by `purge_corrupt_archives` (not edited here).
- Claim 6 (collision-safe names): **Reframed.** The earlier premise that a `resolve_unique_path` counter suffix already exists and "does not propagate to retention" is false — no uniquifier exists in the repo at all. The gap is that same-second generated names silently overwrite; `resolve_unique_path` is genuinely new (REQ-003).

**Maintainer decisions (2026-11-15), resolving the Issue's Unresolved Question:** rotation/drill archives 14 files / 30 days; drill JSON 14 files / 30 days per domain with `_restored` copies deleted immediately after the drill; quarantine directories 10 / 90 days per source DB; `.tmp_` and orphan `_restored` leftovers removed after 1 day (in-code constant, not config); collisions resolved by counter-suffix uniquifier (`_2`, `_3`, ...), not by sub-second timestamps and not by failing. Maintainer decisions are unchanged; only the code anchors they map onto were corrected.

## Problem
The archive directory, drill directory, and DB directories grow without bound (each leftover is a full or partial database copy), and same-second operations overwrite each other's archives — destroying the forensic evidence the retention system is meant to preserve.

## Reason for Change
Unbounded growth eventually exhausts the disk hosting the live databases; an overwritten corrupt archive or drill artifact destroys forensic evidence (Issue).

## Implementation Intent
Add one maintenance entry point that applies age-then-count retention to every artifact class (reusing the existing two helper shapes), delete the drill's working copy at the end of the domain drill, and route every generated artifact path through one `resolve_unique_path()` counter-suffix helper.

## Requirements
- `REQ-001`: `ArtifactRetentionConfig` (dataclass, `maintenance.py`, pattern of `CorruptArchiveRetentionConfig` at `maintenance.py:144-170`): `archive_max_files=14`, `archive_max_age_days=30`, `drill_artifact_max_files=14`, `drill_artifact_max_age_days=30`, `quarantine_max_files=10`, `quarantine_max_age_days=90`; `from_config()` reads the six `agent.toml` keys via `get_typed`/`_non_negative_int` (007 semantics: missing → default, `0` = disabled for that limit, negative → `ValueError`, bool rejected). Key names follow the existing `sqlite_<class>_max_files`/`sqlite_<class>_max_age_days` pattern (matching the landed `sqlite_corrupt_archive_max_files`/`sqlite_corrupt_archive_max_age_days`): `sqlite_archive_max_files`, `sqlite_archive_max_age_days`, `sqlite_drill_artifact_max_files`, `sqlite_drill_artifact_max_age_days`, `sqlite_quarantine_max_files`, `sqlite_quarantine_max_age_days`. New keys registered in `ProductionConfigValidator` valid-keys tuple (`scripts/agent/production_config_validator.py:186-202`, alongside the existing `sqlite_corrupt_archive_*` keys) and added to `config/agent.toml` beside the existing keys at `:14-18` (AC-1).
- `REQ-002`: `purge_archive_artifacts(cfg=None, mode=STRICT)` in `maintenance.py` runs four sweeps and returns `MaintenanceResult(action="purge_archive_artifacts")` with `data` counts per class; follows the 006 mode contract (STRICT raises, BEST_EFFORT returns partial counts, config errors propagate):
  1. archives in `sqlite_archive_dir` (resolved via `rotation._resolve_archive_dir()`): pattern `{stem}_*{suffix}` per domain (rag/session/workflow) excluding `{stem}_corrupt_*` (corrupt archives live in the DB dir and are owned by `purge_corrupt_archives`; the exclusion is a safety guard), age 30d then count 14, most recent file per source database never deleted (Issue constraint);
  2. drill JSON in `<archive_dir>/drills`: pattern `{domain}_*.json` per domain, age 30d then count 14; the drill `_restored` working copies are removed by sweep 4, not here;
  3. quarantine directories `{stem}_sidecar_quarantine_*` in each domain DB dir: age 90d then count 10 per source DB, most recent directory per source DB never deleted; `shutil.rmtree` applies only to directories matching the full pattern;
  4. stale working leftovers: files matching `{stem}.tmp_*{suffix}` in DB dirs and `*_restored{suffix}` in the drills dir older than 86400 s (module constant `_STALE_WORK_FILE_MAX_AGE_SECONDS`, no config key) are removed (AC-2, AC-3, AC-4, AC-5).
- `REQ-003`: `resolve_unique_path(dest: Path) -> Path` in `config.py` next to `format_timestamp`: no existing match → `dest`; otherwise insert a counter (`name_2.ext`, `name_2` for directories) before the suffix, incrementing until free (cap 10000, then `RuntimeError`). `format_timestamp` itself is unchanged (AC-6).
- `REQ-004`: `resolve_unique_path` applied at name creation: `rotation.py:48` (`dest`, before `sqlite3.connect`); `recovery.py:423-426` (`corrupt_archive`, `temp_restore`, `quarantine_dir`, all built from the single `ts` at `:423`); `recovery_restore.py:46-48` (quarantined sidecar path, `ts` from `int(time.time())` at `:39`); `recovery_drill.py:212` (`isolated`) and `:262` (artifact JSON). No overwrite and no failure on same-second operations (AC-6).
- `REQ-005`: `_drill_one_domain` deletes `isolated` (`unlink(missing_ok=True)`) after `_persist_artifact` at the end of every completed domain drill (`recovery_drill.py`, copy created at `:212-215`, persisted at `:254`); the JSON artifact and recovery-point archive remain (AC-7).
- `REQ-006`: tests (Tests section) for: config defaults/boundary semantics; each sweep (age, count, never-delete-most-recent, pattern exclusion); same-second collision at rotation and drill (two artifacts coexist); `_restored` absent after a drill run; stale leftover sweep (AC-1..AC-7).
- `REQ-007`: docs updated (`db_06` retention section + weekly cadence line; `db_07` section 12 lifecycle), `agent.toml` reference tables regenerated (`tools/generate_reference_table.py --check`), `tools/check_docs_consistency.py --domain db` green (AC-8).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | `ArtifactRetentionConfig` + `purge_archive_artifacts()` four-sweep entry point reusing the existing age/count helper shapes; weekly cadence table line | REQ-001, REQ-002, REQ-007 / AC-1..AC-5 | `:404-449` corrupt-only purge (pattern `{stem}_corrupt_*` at `:429`, rag/session only at `:426`); reusable helpers `_delete_corrupt_archives_by_age`/`_beyond_limit` at `:352-374`/`:377-401`; cadence table `:11-17` (re-verified 2026-11-16) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/config.py | Modify | `resolve_unique_path()` helper; `format_timestamp` untouched | REQ-003 / AC-6 | `:56-61` second-resolution `format_timestamp` (re-verified 2026-11-16) | tests/db/test_db_maintenance.py (unit tests for `resolve_unique_path`) | Verified |
| scripts/db/rotation.py | Modify | `dest` routed through `resolve_unique_path` before `sqlite3.connect`/`backup` | REQ-004 / AC-6 | `:47-48` timestamped dest, silent overwrite reproduced by the Issue; 118 lines, no existing prune function (re-verified 2026-11-16) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/recovery.py | Modify | `corrupt_archive`/`temp_restore`/`quarantine_dir` names routed through `resolve_unique_path` (naming lines only) | REQ-004 / AC-6 | `:423-426` three names from one `ts` (`ts` at `:423`) (re-verified 2026-11-16) | tests/db/test_db_recovery.py (existing collision-free naming re-run) | Verified |
| scripts/db/recovery_restore.py | Modify | quarantined sidecar file name routed through `resolve_unique_path` | REQ-004 / AC-6 | `:46-48` `{name}{suffix}_corrupt_{ts}` (`ts = int(time.time())` at `:39`) (re-verified 2026-11-16) | tests/db/test_db_recovery.py | Verified |
| scripts/db/recovery_drill.py | Modify | `isolated` and artifact JSON names uniquified; `isolated` deleted after `_persist_artifact` | REQ-004, REQ-005 / AC-6, AC-7 | `:212-215` isolated working copy retained today; `:262` timestamped JSON, same-second second run overwrites (re-verified 2026-11-16, repo landed drill shape) | `tests/db/test_recovery_drill.py` | Verified |
| scripts/agent/production_config_validator.py | Modify | Add the six new keys to the valid-keys set | REQ-001 / AC-1 | `:186-202` `valid_keys.update((...))` tuple already includes the two `sqlite_corrupt_archive_*` keys (re-verified 2026-11-16) | tests/agent (existing validator tests) | Verified |
| config/agent.toml | Modify | Add six keys with defaults 14/30/14/30/10/90 and comments | REQ-001 / AC-1 | `:14-18` existing archive/retention/corrupt keys (re-verified 2026-11-16) | N/A | Verified |
| tests/db/test_db_maintenance.py | Modify | Config-boundary tests; four-sweep tests incl. never-delete-most-recent and pattern exclusion; rotation same-second collision test | REQ-006 / AC-1..AC-6 | No retention sweep tests exist for archives/drills/quarantine (grep this cycle); `_archive_db_file` already exercised here (file is 1596 lines) | tests/db/test_db_maintenance.py | Verified |
| tests/db/test_recovery_drill.py | Modify | `_restored` absent after drill; same-second artifacts coexist | REQ-006 / AC-6, AC-7 | 764 lines; drill tests exercise `run_drill`/`_persist_artifact` artifacts (re-verified 2026-11-16); no `_restored` assertion exists (grep this cycle) | tests/db/test_recovery_drill.py | Verified |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | Modify | Document the new config keys, the four sweeps, and the weekly cadence entry | REQ-007 / AC-8 | `:42` corrupt-retention paragraph is the pattern; cadence documented in `maintenance.py:11-17` (re-verified 2026-11-16) | `tools/check_docs_consistency.py --domain db` | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | Modify | Section 12: `_restored` copy lifecycle (deleted after drill), unique artifact names; quarantine-directory retention sweep cross-reference | REQ-007 / AC-8 | `:156-191` drill section; `:177` artifact-location text (`{drill_dir}/{domain}_{timestamp}.json`); `:191` retention-deferred marker to replace (re-verified 2026-11-16) | `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/maintenance.py `:144-170`, `:352-401` | `CorruptArchiveRetentionConfig` and the two age/count helpers are the pattern and reuse point — sweeps stay consistent with the existing corrupt-retention semantics | scripts/db/maintenance.py / REQ-001, REQ-002 |
| plans/20261115-041125_dbreview003_restore-sidecar-handling.md | Lands first; its landed quarantine shapes (records, retained dir, deferred mkdir) define what the sweep enumerates | scripts/db/maintenance.py / REQ-002 |
| plans/20261115-051359_dbreview009_drill-harness-fidelity.md | Lands first; its landed `_drill_one_domain` failure-handling shape is where the `isolated` unlink is inserted | scripts/db/recovery_drill.py / REQ-005 |
| scripts/db/store_impl.py `:191-205`, scripts/db/helper.py | Not edited here; 006/007 landed shapes in `maintenance.py` must be re-read before appending the new entry point | scripts/db/maintenance.py / REQ-002 |
| scripts/agent/startup_validation.py `:72-93` | Explains how unknown `agent.toml` keys are classified against the validator registry — why the new keys must be registered | scripts/agent/production_config_validator.py / REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`): `ArtifactRetentionConfig.from_config` returns maintainer defaults when keys are absent; `0` disables the matching limit; negative raises `ValueError`; bool raises; the six keys validate in `ProductionConfigValidator` (no unknown-key classification at startup).
- AC-2 (`REQ-002`): Seeded archives (15 files, one per same domain, plus a `_corrupt_` file and a newer `_restored`-free set): sweep deletes by age first, then count, keeps the most recent archive per source database, never touches `{stem}_corrupt_*` files or non-matching names.
- AC-3 (`REQ-002`): Drill JSON sweep keeps the 14 most-recent per domain and removes age-exceeding ones; orphan `_restored`/`{stem}.tmp_*` files older than 1 day are removed, younger ones are not.
- AC-4 (`REQ-002`): Quarantine sweep removes directories older than 90 days or beyond 10 per source DB, never the most recent; only directories matching `{stem}_sidecar_quarantine_*` are ever rmtree'd (a non-matching directory and any stray live file are untouched).
- AC-5 (`REQ-002`): STRICT raises on filesystem errors; BEST_EFFORT returns partial counts; config errors propagate in both modes (006 contract).
- AC-6 (`REQ-003`, `REQ-004`): Two rotations, two drills, or two restores forced into the same second each produce two coexisting artifacts (`_2` suffix); no `shutil.copy2`/backup-API overwrite occurs; `format_timestamp` output unchanged.
- AC-7 (`REQ-005`): After `run_drill` on fixtures, no `*_restored*` file exists in the drill dir and the JSON artifacts do.
- AC-8 (`REQ-007`): `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_docs_consistency.py --domain db` pass; `db_06` and `db_07` text match the landed behavior.

## Tests
- `REQ-001` (AC-1): new `TestArtifactRetentionConfig` class in `tests/db/test_db_maintenance.py`: defaults-from-empty-config, explicit values, `0` → disabled sweep (nothing deleted), negative → `ValueError`, bool → `ValueError` (007 landed semantics).
- `REQ-002` (AC-2..AC-5): tmp-dir fixtures with `os.utime` backdating (no clock patching needed for age; deterministic): archive sweep (count + age + most-recent-never-deleted + `_corrupt_` exclusion + workflow stem included); drill JSON sweep; quarantine directory sweep (dirs with backdated mtimes; assert a non-matching dir untouched); stale leftovers (1d+1s old removed, 1d-1s old kept); `OSError` injection → STRICT raises / BEST_EFFORT partial; config-error propagation both modes.
- `REQ-003`/`REQ-004` (AC-6): `resolve_unique_path` unit tests (free path, single collision → `_2`, directory variant, cap `RuntimeError`) in `tests/db/test_db_maintenance.py`; rotation collision test: patch `db.rotation.format_timestamp` to a constant, call `_archive_db_file` twice on a fixture DB → two distinct files, both intact (Issue reproduction pinned); drill collision test in `tests/db/test_recovery_drill.py`: patch `db.recovery_drill.format_timestamp` to a constant, run `run_drill("workflow", ...)` twice → two JSON artifacts coexist.
- `REQ-005` (AC-7): extend `test_all_domains_drill_passes_and_live_dbs_untouched` (`tests/db/test_recovery_drill.py:238`) style: after `run_drill("all", ...)`, `list(drill.glob("*_restored*")) == []` and `_load_artifacts(drill)` (`:201-202`) non-empty.
- Regression watch (no assertion changes expected): `tests/db/test_db_recovery.py` naming-adjacent tests (`corrupt_archive`/`temp_restore` names appear in assertions; counter suffix appears only on same-second collisions, which fixtures do not produce — verify and pin); `purge_corrupt_archives` tests stay green (that function is not edited here); Plan 003's landed retention tests stay green (this sweep does not run inside restore).

## Documentation Impact
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`: new retention-keys paragraph after the corrupt-archive paragraph (`:42` pattern) documenting the six keys, their defaults, `0`-disables semantics, the four sweep classes, the 1-day stale-work-file constant, and the weekly cadence line for `purge_archive_artifacts()`.
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12: drill-directory lifecycle (`_restored` copies are working files removed at the end of the drill; JSON artifacts retained per `db_06`); same-second artifact names are made unique with a counter suffix; quarantine-directory retention + sweep cross-reference (matching 003's landed retention text).
- `agent.toml` reference tables regenerated/checked with `tools/generate_reference_table.py --check` (Issue Constraint).

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `maintenance.py` top `_delete_sessions_beyond_limit` B(7), `purge_old_sessions` B(6); `recovery_drill.py` top `run_drill` C(11), `_verify_rag_session` B(6) | `uv run radon cc scripts/db/maintenance.py scripts/db/recovery_drill.py scripts/db/config.py scripts/db/rotation.py -s` (run this cycle; recovery_drill numbers re-confirmed) | 2026-11-15 |
| vulture targets | 1 known finding: `recovery_drill.py:248` `_last_archive` (removed by Plan 009 landing before this plan) | `uv run vulture scripts/db` (recorded under Plan 009 this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (recorded under Plan 005; re-run before implementation) | 2026-11-15 |
| coverage targets | project total 95% | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (recorded under Plan 005) | 2026-11-15 |
| operational check | dev host has no crontab (`no crontab for sugimoto`, re-run this cycle); archive dir `/opt/llm/db/archive` (`agent.toml:16`); sweeps are repo-side only, production scheduling is an operator action | `crontab -l`; `config/agent.toml` read this cycle | 2026-11-15 |

## Assumptions
- Sweeps use file/directory `mtime` for age (the existing corrupt-retention helpers do exactly this, `maintenance.py:362` / `:387-388`; quarantine copy mtimes equal restore time, which is the meaningful age).
- `drill_dir` is always `<archive_dir>/drills` (`recovery_drill.py:278` default) so the sweep can derive it from `sqlite_archive_dir` without a new key; a custom `--drill-dir` is not swept (CLI override is manual-use only). Confidence Medium — UNK-02.
- Quarantine directories live only in the domain DB directories (`recovery.py:426` builds from `db_path.parent`); eventbus is out of scope (`recovery.py`/`rotation.py` assign eventbus to the EventBus service — `rotate_all_dbs` docstring `rotation.py:103-104`).
- Most-recent-never-deleted for archives is per source database stem, matching `purge_corrupt_archives`'s "applied independently per source database" (`maintenance.py:410`).
- Adding `purge_archive_artifacts` to the cadence table is documentation only; wiring a scheduler is operator-side (the existing `purge_corrupt_archives` has no in-repo caller — confirmed this cycle).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any production cron today already deletes archive-dir contents out-of-band (the Issue's "external cron job cannot be excluded") | Production host crontab not inspectable from the dev host | Maintainer confirms before deploying; sweeps are idempotent (glob + age/count), so a redundant external cleanup would not conflict | False |
| UNK-02 | Whether anyone uses the drill `--drill-dir` override with a custom path in production | No evidence in repo/docs | Sweep the default location only (Assumptions); maintainer flags if a custom dir exists | False |
| UNK-03 | Whether `tests/db/test_db_recovery.py` asserts exact `corrupt_archive`/`temp_restore` filename shapes that a counter suffix could break | Counter suffix only appears on same-second collisions (fixtures are single-shot) | Phase 2 runs the file; adjust any fixture that collides | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | Medium (new entry point; existing functions unchanged) | 2 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/config.py | Modify | Low (pure new helper) | 3 | High | not applicable |
| scripts/db/rotation.py | Modify | Low-medium (every rotation's dest naming) | 2 | High | not applicable |
| scripts/db/recovery.py | Modify | Low (three naming lines only) | 4 | High | not applicable |
| scripts/db/recovery_restore.py | Modify | Low (one naming line) | 2 | High | not applicable |
| scripts/db/recovery_drill.py | Modify | Medium (drill artifact lifecycle changes) | 2 | High | not applicable |
| scripts/agent/production_config_validator.py | Modify | Low (key set addition) | 1 | High | not applicable |
| config/agent.toml | Modify | Low (six keys with defaults) | 1 | High | deployed copy must be updated on the production host (operator) |
| tests (two files) | Modify | Low (test-only) | — | High | not applicable |
| docs (two files) | Modify | Low (docs) | — | High | not applicable |

## Cross-Plan Target Overlap Scan

- Run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15, after this Plan freezes — the last plan of the dbreview00X batch). Findings involving this plan and judgments:
  - `scripts/db/maintenance.py` and `tests/db/test_db_maintenance.py` (006+007+008): **sequencing, disjoint regions** — fixed order 004 → 006 → 007 → 008; 008 appends a new config class + new entry point + new test class and edits no function 006/007 touched; Phase 1 re-reads landed `maintenance.py` shapes (006 transaction wrap, 007 guards) before appending.
  - `scripts/db/config.py` (007+008): **disjoint symbols** — 007 edits `build_db_config` value parsing; 008 adds `resolve_unique_path` beside `format_timestamp` and edits neither.
  - `scripts/db/recovery.py` (002+003+004+008): **disjoint regions** — 008 edits only the three name-construction lines `:423-426`; 002/003 own the restore/rollback flow around them; 004 owns the probe functions. Fixed batch order resolves ordering.
  - `scripts/db/recovery_restore.py` (003+008): **disjoint lines** — 003 edits return-shapes of `_quarantine_sidecar_files`/`_stage_restore`; 008 wraps one name in `resolve_unique_path` at `:46-48`. 008 lands last.
  - `scripts/db/recovery_drill.py` and `tests/db/test_recovery_drill.py` (009+008): **sequencing** — 009 lands first (failure handling, logging); 008 edits the landed end-of-drill (`isolated` unlink) and `_persist_artifact` naming, and extends the landed test file's fixture helpers.
  - `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` (006+008): **disjoint paragraphs** — 006 edits mode/atomicity text; 008 appends the retention-keys paragraph after `:42`; 008 re-reads landed wording.
  - `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (002+003+004+009+008): **section isolation** — 008 touches only section 12 lifecycle text on top of 009's drill edits; re-read landed text before editing.
  - No contradictions found between any pair's designs: 008 consumes landed shapes (003 quarantine dirs, 006 mode contract, 007 value semantics, 009 drill flow) rather than altering them.

## Design
- **One new entry point, not a broadened old one**: `purge_corrupt_archives` keeps its exact scope (its tests and docstring contract stay untouched; 006/007 also landed there). `purge_archive_artifacts` is the sibling sweep for the remaining classes. Rejected alternative: extending `purge_corrupt_archives` — would change an existing documented contract that three other plans already reference.
- **Reuse the existing helper shapes**: `_delete_corrupt_archives_by_age`/`_delete_corrupt_archives_beyond_limit` (`maintenance.py:352-374`/`:377-401`) are already pattern-parameterized; the new sweeps call them with archive-dir/drill-dir patterns rather than duplicating glob-age-count logic (with 007's landed 0/negative semantics in place at the config layer). Quarantine-directory sweep needs the never-delete-most-recent guard applied per source DB across both rules (archives: within `max_files ≥ 1` the newest always survives the count rule; the age rule must skip the newest file even if older than the age limit — explicit `min_keep=1` guard on the age sweep for archives/quarantine classes).
- **Quarantine sweep safety**: directories are only removed when the full name matches `{stem}_sidecar_quarantine_[0-9_]*` (regex, not substring), they are directories, and the most recent per DB is skipped; `shutil.rmtree` is used only after that match (Issue constraint: no recursive deletion outside temporary directories — quarantine dirs are exactly the temporary artifact class). `ignore_errors=False` so STRICT surfaces real failures.
- **Uniquifier instead of sub-second timestamps**: `resolve_unique_path` keeps every naming format, docs, and existing readers intact and makes collisions produce `_2` (Issue's chosen option; maintainer decision). Cap 10000 + `RuntimeError` prevents an infinite loop under pathological contention. It is applied after the timestamp is formatted, so name ordering (sorted retention sweeps by mtime, not name) is unaffected.
- **`_restored` deletion at end of drill**: the isolated copy is a verification working file, not a recovery point (the recovery point is the archive itself) — maintainer decision. Deleted after `_persist_artifact` so failure forensics (JSON + archive) always survive; maintenance sweep catches crashes between verification and deletion (1-day stale rule).
- **Naming-site routing only, no plumbing through restore logic**: `recovery.py`/`recovery_restore.py` changes are exactly the three+one name constructions wrapped in `resolve_unique_path`; quarantine records (Plan 003) carry actual paths, so moved-back paths follow the uniquified names automatically.
- **Architecture check** (Step 3): `maintenance.py` already imports `db.config` (`build_db_config`); `rotation.py`/`recovery.py`/`recovery_drill.py` already import `db.config` (`format_timestamp`), so `resolve_unique_path` adds no new cross-module import edges. New import edge: `maintenance.py` may need `re` (stdlib) for the quarantine regex — allowed (stdlib). `lint-imports` contracts unchanged; run before freeze completion and before commit.
- **Persisted schema check**: no DB schema changes; `agent.toml` gains six keys (validator registry updated, reference tables regenerated — Issue Constraint).

## Implementation steps
1. **Phase 1: Naming uniqueness** (REQ-003, REQ-004; `scripts/db/config.py`, `scripts/db/rotation.py`, `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_drill.py`)
   - [ ] Add `resolve_unique_path()` (REQ-003; scripts/db/config.py)
   - [ ] Route the five name-construction sites through it (REQ-004; scripts/db/rotation.py, scripts/db/recovery.py, scripts/db/recovery_restore.py, scripts/db/recovery_drill.py)
   - [ ] Run `uv run pytest tests/db -q` (collision-free baseline + UNK-03 check)
2. **Phase 2: Retention config and sweeps** (REQ-001, REQ-002; `scripts/db/maintenance.py`, `scripts/agent/production_config_validator.py`, `config/agent.toml`)
   - [ ] `ArtifactRetentionConfig` + `purge_archive_artifacts()` four sweeps with 006 mode contract and 007 value semantics (REQ-001, REQ-002; scripts/db/maintenance.py)
   - [ ] Register six keys in the validator set (REQ-001; scripts/agent/production_config_validator.py) and add them to `config/agent.toml` (REQ-001; config/agent.toml)
   - [ ] `isolated` end-of-drill deletion (REQ-005; scripts/db/recovery_drill.py)
3. **Phase 3: Tests** (REQ-006; `tests/db/test_db_maintenance.py`, `tests/db/test_recovery_drill.py`)
   - [ ] Add the Tests-section tests; run `uv run pytest tests/db tests/agent -v` and the regression watch list
4. **Phase 4: Docs, tables, validation** (REQ-007)
   - [ ] Update `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 12 (REQ-007)
   - [ ] `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_docs_consistency.py --domain db`
   - [ ] Run ruff, basedpyright (CI form), bandit `-ll`, `lint-imports`; diff-cover ≥ 90% on the branch diff
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; production `agent.toml` keys and any cron wiring for `purge_archive_artifacts` are operator decisions (maintainer confirms UNK-01)

### Release units
**Unit**: collision-safe-naming | **Phases**: 1 | **Reason**: `resolve_unique_path` plus its five call sites is independently testable and independently valuable (it stops evidence loss even without retention).
**Unit**: retention-sweeps-and-drill-lifecycle | **Phases**: 2, 3, 4 | **Reason**: config class, sweeps, tests, and docs form one retention contract; splitting config from sweeps leaves unbounded growth.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/config.py | `resolve_unique_path` unit tests (free/collide/dir/cap) | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-6 unit half |
| scripts/db/rotation.py + recovery naming sites | Same-second collision integration tests on fixture DBs | `uv run pytest tests/db -v` | AC-6 asserted; existing recovery tests green (UNK-03) |
| scripts/db/maintenance.py | Sweep matrix tests (age/count/never-delete/pattern-exclusion/mode matrix) | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-2..AC-5 asserted |
| scripts/db/recovery_drill.py | Drill lifecycle tests (`_restored` gone, JSON coexistence) | `uv run pytest tests/db/test_recovery_drill.py -v` | AC-7, AC-6 asserted |
| config/agent.toml + validator | Startup classification with new keys | `uv run pytest tests/agent -v` | AC-1 validator half |
| docs + reference tables | Doc consistency | `uv run python tools/generate_reference_table.py --check` → `uv run python tools/check_docs_consistency.py --domain db` | AC-8 asserted |
| scripts/ (regression) | Full suite | `uv run pytest tests/ -n auto` | No regressions |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | ≥ 90% on branch diff (baseline 95%) |

## Risks
- **Risk**: a sweep glob accidentally matches a live or user file (e.g., a file named like a quarantine dir) → **Mitigation**: full-name regex patterns + `is_file`/`is_dir` type checks + most-recent-never-deleted guard + tests asserting non-matching names are untouched (AC-2, AC-4).
- **Risk**: deleting `_restored` copies removes debugging material an operator used between drill steps → **Mitigation**: maintainer decision; JSON artifact retains every verification verdict and the archive is the recovery point; 1-day stale sweep covers crash leftovers.
- **Risk**: retention deletes an archive the operator still relies on for rollback → **Mitigation**: maintainer-set 14/30 bounds with never-delete-most-recent per DB (hard Issue constraint); age rule also skipped for the newest file (Design min_keep guard).
- **Risk**: sweeping quarantine directories conflicts with a still-running restore that created them → **Mitigation**: sweep runs as a separate maintenance entry (weekly cadence), not inside the restore flow; age rules (90d/1d) are far outside any running restore window; most-recent-never-deleted covers the active one.
- **Risk**: `resolve_unique_path` cap `RuntimeError` fires in a pathological same-second burst and aborts a rotation → **Mitigation**: cap is 10000 per name per second, unreachable under daily rotation cadence; the failure is explicit (vs today's silent overwrite).
- **Risk**: overlapping edits with 002/003/006/007/009 across `maintenance.py`, `recovery.py`, `recovery_drill.py`, test files → **Mitigation**: 008 is last in the fixed batch order; Phase 1 re-reads all landed shapes (Overlap Scan judgments).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Naming uniqueness (config.py + four call sites) | In Progress | — | — |  |
| 2 | Retention config and sweeps (maintenance.py, validator, agent.toml, drill copy deletion) | In Progress | — | — |  |
| 3 | Tests (test_db_maintenance.py, test_recovery_drill.py) | In Progress | — | — |  |
| 4 | Docs, reference tables, validation | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-008-1 | 4 | Operator decision (recorded at plan time) | Completed | maintainer | — | Decided 20261116-155505: add the six keys to the production `/opt/llm/config/agent.toml` at deploy time (keys must first land via procedures seq 02 and seq 08, since no loader reads them before seq 02 runs and `deploy.sh` re-copies `config/agent.toml` each deploy); do NOT schedule `purge_archive_artifacts()` weekly at this stage — no caller wired. UNK-01 measured on the production host 20261116: no user crontab; system cron carries only standard run-parts jobs (logrotate, man-db, mlocate, tmpfiles) and nothing touches `/opt/llm` archive files. |
| implementations/20261116-144812_01_scripts_db_maintenance.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-144812_02_scripts_db_config.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-144812_03_scripts_db_rotation.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-144812_04_scripts_db_recovery.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-144812_05_scripts_db_recovery_restore.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-144812_06_scripts_db_recovery_drill.py.md | 1, 2, 3 | Procedure | Pending | — | — |
| implementations/20261116-144812_07_scripts_agent_production_config_validator.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-144812_08_config_agent.toml.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-144812_09_tests_db_test_db_maintenance.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261116-144812_11_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261116-144812_12_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-054021
- **Related target files**: scripts/db/maintenance.py, scripts/db/config.py, scripts/db/rotation.py, scripts/db/recovery.py, scripts/db/recovery_restore.py, scripts/db/recovery_drill.py, scripts/agent/production_config_validator.py, config/agent.toml, tests/db/test_db_maintenance.py, tests/db/test_recovery_drill.py, docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1 ("reusing the existing config pattern"); Unresolved Question answered 2026-11-15 (14/30, 14/30, 10/90 + 1d tmp) | scripts/db/maintenance.py, scripts/agent/production_config_validator.py, config/agent.toml | Phase 2 | AC-1 | Config-boundary tests + validator tests | Explicit in code (pattern `maintenance.py:144-170`, validator `:186-202` re-verified 2026-11-16) |
| REQ-002 | Problem bullets 1-3; Required Changes bullet 1; Constraint "Never delete the most recent verified archive per database" | scripts/db/maintenance.py | Phase 2 | AC-2..AC-5 | Sweep matrix tests on tmp dirs | Verified by test (gap confirmed this cycle: no sweep covers `rotation.py:47-48` archives or drill outputs) |
| REQ-003 | Problem bullet 4; Required Changes bullet 3; maintainer decision (counter suffix) | scripts/db/config.py | Phase 1 | AC-6 | `resolve_unique_path` unit tests | Explicit in code (`config.py:56-61` re-verified 2026-11-16) |
| REQ-004 | Target Files bullets 2-5 | scripts/db/rotation.py, scripts/db/recovery.py, scripts/db/recovery_restore.py, scripts/db/recovery_drill.py | Phase 1 | AC-6 | Collision integration tests | Explicit in code (`rotation.py:47-48`, `recovery.py:423-426`, `recovery_restore.py:46-48`, `recovery_drill.py:212/:262` re-verified 2026-11-16) |
| REQ-005 | Problem bullet 2; maintainer decision (restored 即削除) | scripts/db/recovery_drill.py | Phase 2 | AC-7 | Drill lifecycle test | Explicit in code (`:212-215` retention today, re-verified 2026-11-16) |
| REQ-006 | Testing Expectations | tests/db/test_db_maintenance.py, tests/db/test_recovery_drill.py | Phase 3 | AC-1..AC-7 | New tests | Verified by test (gaps confirmed this cycle by grep) |
| REQ-007 | Documentation Impact; Constraint (reference tables refreshed) | docs/41_db/db_06..., docs/41_db/db_07... | Phase 4 | AC-8 | `generate_reference_table.py --check`, `check_docs_consistency.py --domain db` | Explicit in docs (`db_06:42`, `db_07:156-191` re-verified 2026-11-16) |