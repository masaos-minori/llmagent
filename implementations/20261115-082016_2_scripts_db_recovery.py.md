## Goal
- Thread quarantine records through every terminal path of `_restore_from_backup`, reassemble the original whole unit on failure, and retain the quarantine directory on success.

## Scope
**Release unit**: whole-unit-rollback-retention (Phases 1-2 of the plan; lands after Plan 002's procedures `20261115-080732_1/_2` and after companion `20261115-082016_1`)

- In scope: `scripts/db/recovery.py` — record threading (REQ-001), quarantine-back on pre- and post-activation failures (REQ-001, REQ-002), success-path `shutil.rmtree` removal with retention logging (REQ-003), verification-only row for the cleanup-safety behavior landed by Plan 002 (REQ-004; Correction 2 of the plan).
- Cross-plan overlap `scripts/db/recovery.py` (shared with Plans 004/008): **compatible (sequencing)** — Plan 004 later opens the live DB `read_only=True` in the probe region (`recovery.py` verification calls, disjoint from the restore failure paths); Plan 008 edits name construction at `:359-361`. This document edits `:366`, the two pre-activation failure returns (`374-402`), `_rollback_or_non_serviceable`, the `OSError` handler call to the helper, and the success path (`413-415`).

## Assumptions
- Post-002 landed shapes (from `20261115-080732_1`): activation-progress holder; `_rollback_or_non_serviceable(db_path, corrupt_archive, failure, dry_run, moved_sidecars kwarg)` that unlinks moved candidate sidecars before the archived-original replace; handler delegating to that helper. This document extends the same helper, it does not rebuild the rollback (Plan Design).
- Post-`_1` landed shape: `_stage_restore` returns `(staged, records)` with `records: list[tuple[Path, Path]]` (live name → quarantine path) and creates the directory only when quarantining (this document unpacks `:366` accordingly).
- Quarantine entries are `copy2`+`unlink` pairs; moving them back yields byte-identical live sidecars (Plan Assumption).
- `corrupt_archive` retention: the quarantine-back for post-activation rollback runs only after the main-file replace succeeded; on rollback failure no reassembly is attempted (`non_serviceable` makes no reassembly claim) (AC-1/AC-2 reading).

## Design decisions
- One module-level helper `_restore_quarantine_sidecars(records)` (new): for each recorded pair, `shutil.move(quarantine_path, live_path)`; failures propagate (`OSError`) — fail-closed like staging, so a partial reassembly never reports `preserved_original` (AC-1). Partial quarantine moves back only what was recorded (AC-1, Plan Design).
- Pre-activation failure returns call `_restore_quarantine_sidecars` (new) after `_cleanup_staged` and before reporting; the live main file was never swapped, so main stays in place (AC-1).
- Post-activation rollback: extend `_rollback_or_non_serviceable` with the new keyword `quarantine_records` (new) (default empty keeps behavior for Plan 002 call sites); order inside the helper is exactly the Plan Design order — remove moved candidate sidecars (002 step), `os.replace(corrupt_archive, db_path)`, then move records back.
- Retention: remove `shutil.rmtree(quarantine_dir, ignore_errors=True)` (`recovery.py:415`); log the retained archive path only when the directory exists (after the `_1` deferral, sidecar-free restores create nothing) (REQ-003, Plan Assumption).

## Alternatives considered
- Moving quarantined originals back inside `_cleanup_staged`: rejected — cleanup is also called from the handler where reassembly rules differ; keeping reassembly in dedicated call sites/helper makes the whole-unit contract explicit.
- Deferring quarantine until activation (Source Issue Proposed Fix 1): rejected by the plan (superseded by staging-time quarantine; Plan Design).

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. `_restore_from_backup`: unpack `staged, quarantine_records = _stage_restore(...)` (`recovery.py:366`) (REQ-001).
2. Add `_restore_quarantine_sidecars(records)` (new) near `_cleanup_staged` (REQ-001, AC-1).
3. Candidate integrity-failure return (`374-386`) and candidate logical-failure return (`387-402`): after the existing `_cleanup_staged(temp_restore, staged)` and before building the `_failure(...)` result, call `_restore_quarantine_sidecars(quarantine_records)` (REQ-001, AC-1).
4. Extend `_rollback_or_non_serviceable` with the new keyword `quarantine_records` (new) defaulting to empty; after a successful `os.replace(corrupt_archive, db_path)`, call `_restore_quarantine_sidecars(quarantine_records)` before returning `preserved_original`; update its docstring (whole-unit reassembly) (REQ-002, AC-1, AC-2).
5. Handler and verification-failure call sites: pass `quarantine_records=quarantine_records` when calling `_rollback_or_non_serviceable` (both the `_post_restore_failure` path and the `OSError` handler path) (REQ-002).
6. Success path: delete `shutil.rmtree(quarantine_dir, ignore_errors=True)` (`recovery.py:415`); when `quarantine_dir.exists()`, `logger.info("Quarantine archive retained: %s", quarantine_dir)` (REQ-003, AC-3).
7. Verify (no edit): `_cleanup_staged` is already failure-safe from Plan 002 step 6; confirm the three call sites (`374`, `395`, `426`) are unchanged by steps 3-5 (REQ-004, Correction 2).

### Method
- Direct edit; no new imports (`shutil` already imported).

### Details
- radon: composition stays in helpers; `_restore_from_backup` must stay at or below the plan's baseline C(13) — after Plan 002 slimmed the handler, the two added calls and the existence-check branch keep it at or under baseline.
- `quarantine_dir` path construction (`:361`) stays on its current lines (Plan 008's disjoint edit region).

## Compatibility considerations
- `_rollback_or_non_serviceable` private; all call sites are in this module and are updated by step 5. Post-activation verification-failure vocabulary (`restore_verify_failed` / `logical_verify_failed` / `verification_unavailable` + `preserved_original`) is unchanged; only the filesystem reassembly is added.
- Existing success-path tests that assert quarantine absence (`tests/db/test_db_recovery.py:834`, `:1063`, `:1459`) break by design until companion `_3` flips them (plan Release units).

## Security considerations
- No new external input; moves restricted to recorded pairs. Bandit baseline unchanged (45 low / 0 medium / 0 high).

## Rollback considerations
- Revert together with `_1` (return-shape dependency) and `_3` (assertion flips). If Plan 002's changes are reverted, the extended helper kwargs fail loudly at import/call time.

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` after companion `_3` lands (baseline this cycle: 74 passed pre-change).
- Regression: `uv run pytest tests/db -v`; Plan 002's failure tests must stay green (shared regions).
- Static: `uv run radon cc scripts/db/recovery.py -s` (baseline C(13), must not exceed), `uv run vulture scripts/ --min-confidence 80` (no `scripts/db` findings), `uv run bandit -r scripts/ -c pyproject.toml -ll` clean, `uv run lint-imports` (6 contracts kept), ruff, mypy (CI form) per `rules/toolchain.md`.

## Completion criteria
- AC-1 and AC-2 asserted by companion `_3` tests; AC-3 retention asserted; REQ-004 verification row confirmed against Plan 002's landed test; static checks within baselines.

## Out of Scope
- Quarantine record production (`_1`).
- Retention lifetime/cleanup scheduling (Plan 008 artifact-retention sweep — the cleanup 003 explicitly delegates).
- Probe read-only open (Plan 004).
- Docs text (companions `_4`, `_5`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004 (verification only)
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: scripts/db/recovery.py
