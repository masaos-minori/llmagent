## Goal
- Make any failure inside `_activate_candidate` after `os.replace` completed trigger the shared rollback composition, so the live path never silently holds an unverified candidate, and make `_cleanup_staged` non-raising.

## Scope
**Release unit**: activation-rollback-reporting (Phases 1-2 of the plan; this document covers `scripts/db/recovery.py`; the unit is red until the companion test document lands)

- In scope: activation holder passed into `_activate_candidate` (REQ-001); unified rollback via `_rollback_or_non_serviceable` with moved-sidecar removal (REQ-002, REQ-003); non-raising `_cleanup_staged` (REQ-004).
- Cross-plan overlap `scripts/db/recovery.py` (shared with Plans 003/004/008): **compatible (sequencing)** — this document lands first; Plan 003 adds quarantine-back on top of the holder shapes created here, Plan 004 later opens the live DB `read_only=True` in the probe region (disjoint lines 141-160), Plan 008 edits only name-construction lines 359-361.

## Assumptions
- `os.replace` is atomic: if it raises, no swap happened; the holder stays unset and no rollback runs (existing test `tests/db/test_db_recovery.py:1424-1436` stays unchanged).
- `corrupt_archive` exists once `_stage_restore` completed with a live DB at staging time (`recovery_restore.py:96-98`); the handler's `corrupt_archive.exists()` guard stays the rollback precondition, not the activation indicator (Plan Assumptions). A partial activation with no archived original reports `rollback_failed`/`non_serviceable` through the helper.
- `_rollback_or_non_serviceable`'s current post-activation verification-failure behavior (the new keyword with an empty default) must stay byte-identical for `tests/db/test_db_recovery.py:933-963` and `:965-991`.

## Design decisions
- Single mutable holder `_ActivationProgress` (new) passed by the caller; `_activate_candidate` flips `replaced` **after** `os.replace` returns and appends each successfully moved live-name path. This is the Issue's Required Changes bullet 1 ("before or inside") realized as "inside, between replace and moves".
- The handler delegates to `_rollback_or_non_serviceable` instead of its duplicated inline rollback (`recovery.py:427-442`), so both failure families report the same vocabulary (`error` + `preserved_original` on rollback success; `rollback_failed` + `non_serviceable` on rollback failure). `rollback_failed` already exists in the contract — no new action token (Issue Constraint).
- Moved-sidecar removal is unlink-log-and-continue on the recorded live-name paths only; nothing unlinked is invented.

## Alternatives considered
- Caller-side flag set before calling `_activate_candidate`: rejected (Plan Design) — would trigger spurious rollback when `os.replace` itself fails, consuming `corrupt_archive` and contradicting test `:1424-1436`.
- Splitting `_activate_candidate` into replace + moves at the call site: rejected — enlarges `_restore_from_backup` (radon C(13) budget) and duplicates the swap contract.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Add `_ActivationProgress` (new) dataclass near `_cleanup_staged`: fields `replaced` (new) `bool = False` and `moved_sidecars` (new) `list[Path] = []` (REQ-001).
2. Change `_activate_candidate(db_path, temp_restore, staged)` to `_activate_candidate(db_path, temp_restore, staged, progress)`: after `os.replace(temp_restore, db_path)` set `progress.replaced = True`; inside the `for` loop, after each `shutil.move(staged_path, final)` append `final` to `progress.moved_sidecars`. Docstring: record progress so a mid-activation failure is rolled back (REQ-001). Only call site is `_restore_from_backup` (`recovery.py:404`) (REQ-001).
3. `_restore_from_backup`: replace `activated = False` (`recovery.py:364`) and the post-call `activated = True` (`404-405`) with `progress = _ActivationProgress()` before the try and pass it to `_activate_candidate` (REQ-001).
4. Rewrite the `except OSError` handler (`recovery.py:424-443`): keep `_cleanup_staged(temp_restore, staged)`; replace the `if activated and corrupt_archive.exists():` inline rollback block (`427-442`) with a call to `_rollback_or_non_serviceable(db_path, corrupt_archive, _failure("error", str(e), dry_run, logical_ok=False), dry_run)`, passing the new keyword `moved_sidecars` (new) set to `progress.moved_sidecars`. Keep the trailing `return _failure("error", str(e), dry_run)` for non-activation OSErrors (REQ-003).
5. Extend `_rollback_or_non_serviceable(db_path, corrupt_archive, failure, dry_run)` with the new keyword `moved_sidecars` (new) defaulting to an empty sequence: before `os.replace(corrupt_archive, db_path)`, unlink each recorded live-name path inside `try/except OSError` with `logger.error` (REQ-002); failure/return branches unchanged (REQ-003).
6. `_cleanup_staged` (`recovery.py:298-302`): wrap each `path.unlink()` in `try/except OSError` with `logger.error("Failed to remove staged file %s: %s", path, exc)` (REQ-004); call sites 374, 395, 426 unchanged.

### Method
- Direct edit; no new imports (dataclass already imported in the module).

### Details
- radon guard: removing the inline rollback from `_restore_from_backup` must keep its CC at or below the recorded baseline C(13); the new helper parameter does not add branches to `_restore_from_backup`.
- The `_failure("error", str(e), dry_run, logical_ok=False)` instance built in step 4 gives the helper `action="error"` on rollback success (existing vocabulary; REQ-003 only changes the state reporting and the rollback-failure action).

## Compatibility considerations
- `_activate_candidate` and `_rollback_or_non_serviceable` are module-private; only callers are in `recovery.py` (verified this cycle). No signature changes to `recover_corruption` or `RecoveryResult` (`scripts/db/models.py` untouched).
- Consumer scan (Plan Design record): `scripts/agent/services/db_maintenance_service.py:80-86` and `scripts/agent/services/rag_maintenance_service.py:61` branch only on `action == "restored"`, `detail`, `logical_ok`; the state-less `error` shape has no consumer (Plan Assumptions).
- Behavior changes only on failure paths that currently violate the documented contract; success paths and post-activation verification-failure reporting are unchanged.

## Security considerations
- No new input handling; unlinks restricted to recorded staged/live-name paths (no path interpolation from external input). Bandit baseline 45 low / 0 medium / 0 high must stay unchanged under `-ll`.

## Rollback considerations
- Revert `scripts/db/recovery.py` by checkout. Companion test document (`20261115-080732_2`) fails loudly if this code is reverted while its tests remain (intended regression alarm).

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` (baseline this cycle: 74 passed). New/updated tests live in the companion document; until they land, existing `:996-1021` assertion `action == "error"` is expected to fail after step 4 lands — same release unit, land documents `_1` and `_2` together.
- Regression: `uv run pytest tests/db -v`; `tests/db/test_db_maintenance.py` action assertions unchanged.
- Static: `uv run radon cc scripts/db/recovery.py -s` (baseline top `_restore_from_backup` C(13)), `uv run vulture scripts/ --min-confidence 80`, `uv run bandit -r scripts/ -c pyproject.toml` (`-ll` gate clean), `uv run lint-imports` (6 contracts kept), ruff, mypy (CI form) per `rules/toolchain.md`.

## Completion criteria
- Steps 1-6 implemented; companion test document green; static checks match or improve on baselines; no new action vocabulary.

## Out of Scope
- Quarantine records and moving quarantined originals back (Plan 003 procedures, land after this document).
- Quarantine retention on success and the success-path `rmtree` removal (Plan 003 REQ-003).
- Probe read-only open (Plan 004) and quarantine name sweep (Plan 008).
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` text (companion document `_3`).

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/done/20261114-092849_dbreview002_partial-activation-rollback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-035004_dbreview002_partial-activation-rollback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-080732
- **Related target files**: scripts/db/recovery.py
