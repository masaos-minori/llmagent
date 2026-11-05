# Implementation Procedure — `scripts/db/recovery.py`

## Goal

Reorder corruption recovery in `scripts/db/recovery.py` so every mandatory
verification runs on the staged candidate **before** activation, roll back or
report an explicit non-serviceable state on failure, and populate the
`RecoveryResult` contract (`REQ-003`, `REQ-004`, `REQ-006`).

## Scope
**Release unit**: contract activation

## Assumptions

- `_stage_restore` (`scripts/db/recovery_restore.py`) is refactored by seq 01 to
  stage the full candidate unit (database plus correctly-named `-wal`/`-shm`
  sidecars) and to raise filesystem failures; seq 01 keeps `os.replace` (current
  L102) and the step-4a final move (current L104-L114) inside the staging
  function and its return type stays `None`. This row completes the
  staging/activation split as a coordinated edit on `scripts/db/recovery_restore.py`
  — the only place activation is removed, because Plan Phase 2 assigns the
  ordering to `scripts/db/recovery.py` — stripping `os.replace` and the step-4a
  move from `_stage_restore` and making it return the staged sidecar paths keyed
  by suffix (`dict[str, Path]`); the caller then verifies the staged candidate
  before performing the swap. (Verified 2026-11-05; see seq 01's Verification
  note on the same gap.)
- The corrupt original is archived (`shutil.copy2` to a timestamped
  `_corrupt_` path) inside staging, so a post-activation failure can restore from
  that archive.
- `_run_logical_verification` (`scripts/db/recovery_verification.py`, seq 03)
  returns `(False, "verification_unavailable")` for a `sqlite3.Error` or an
  unknown mandatory target; this Plan maps that detail to the
  `verification_unavailable` (new) action value.
- Cross-plan: `scripts/db/rotation.py` imports `DbCondition`, `run_integrity_check`,
  `verify_domain_identity` from `db.recovery`; those names and signatures are
  unchanged, so the import contract is preserved. `logical_ok` / `active_db_state` (new)
  additions to `RecoveryResult` (seq 04) are additive.
- `UNK-01` (exclusive-access mechanism) is out of scope; this Plan documents the
  requirement, does not implement a stop/lock helper.

## Design decisions

- Split staging from activation: `_stage_restore` stages the candidate unit in
  `temp_restore` and returns the staged sidecar paths; it no longer performs
  `os.replace`. Verification then runs on `temp_restore`.
- Activate only after both the physical integrity check and the logical
  verification pass on the candidate, via a single atomic `os.replace` of the
  database plus a move of each sidecar to its final `db_path.name + suffix`
  location.
- On any candidate-verification failure, do not activate; the live database is
  byte-identical (`AC-003`). Report the failure with `active_db_state` (new)
  `preserved_original` (new).
- On a post-activation failure, restore the archived original; if that restore
  fails, report an explicit non-serviceable action and preserve every artifact
  (`AC-004`).

## Alternatives considered

- Verifying after activation (current behavior) was rejected: a failed
  verification left an unverified database active with no rollback.
- Carrying the active state only in `action` + `detail` was rejected in favor of
  one additive machine-readable field (`active_db_state` (new), see `UNK-06`, seq 04).

## Compatibility considerations

- Public entry points `recover_corruption`, `run_integrity_check`,
  `verify_domain_identity`, `backup_is_usable` keep their signatures.
- `RecoveryResult` gains two additive fields with defaults (`seq 04`); existing
  consumers (`scripts/agent/commands/db_session_ops.py`,
  `scripts/agent/services/db_maintenance_service.py`, `scripts/db/__init__.py`)
  are unaffected.
- The new `verification_unavailable` (new) and rollback action values are additive;
  existing action strings keep their meaning.

## Security considerations

- No new file operations beyond the existing archive/copy/move; the atomic swap
  uses `os.replace` on the resolved paths. Confirm the post-activation rollback
  restores from the archived original and never from an unverified path.

## Rollback considerations

- Revert the commit; the pre-change order (activate-then-verify) is the defective
  behavior being removed.

## Implementation

### Target file

`scripts/db/recovery.py`

Coordinated edit owned by this row (per Verification 2026-11-05):
`scripts/db/recovery_restore.py` — removal of `os.replace` and the step-4a move
from `_stage_restore` and its return-type change to `dict[str, Path]` (see
Procedure step 1). No other `recovery_restore.py` change belongs to this row;
seq 01's naming/fail-closed changes land before it.

### Procedure

1. In `scripts/db/recovery_restore.py` (coordinated edit): remove `os.replace`
   (current L102) and the step-4a move loop with its `try/except OSError`
   (current L104-L114) from `_stage_restore`; copy the backup sidecars to
   `temp_restore.parent / f"{temp_restore.name}{suffix}"` and return the staged
   paths as `dict[str, Path]`; update the docstring to staging-only.
2. In `_restore_from_backup` (current L252-L289): after staging the candidate,
   verify the **candidate** (`temp_restore`) before activation — run
   `_run_integrity_check(temp_restore, target)` and
   `_run_logical_verification(temp_restore, target)` — and branch on the result
   before any `os.replace`.
3. Add activation: when both checks pass, perform the single atomic swap of
   `temp_restore` → `db_path` and move each staged sidecar to
   `db_path.parent / f"{db_path.name}{suffix}"`; clean up quarantine; return
   success with `logical_ok=True`, `active_db_state="restored"`.
4. On candidate physical-verification failure: return a failure result with
   `active_db_state="preserved_original"`, `logical_ok=False`; do not activate.
5. On candidate logical-verification failure: map
   `logical_detail == "verification_unavailable"` to action
   `verification_unavailable` (new); otherwise `logical_verify_failed`; set
   `logical_ok=False`, `active_db_state="preserved_original"`.
6. On a post-activation failure (`_post_restore_failure` returns non-None):
   restore the archived original from `corrupt_archive`; if the restore raises,
   report a non-serviceable action and `active_db_state="non_serviceable"`,
   preserving artifacts.
7. In the `OSError` handler (current L285-L289): restore the archived original
   when available before reporting `error`; leave the live database untouched on
   pre-activation failure.
8. Update the `recover_corruption` docstring action-value list (current L336-L349)
   to document `verification_unavailable` (new) and the rollback/non-serviceable action.

### Method

- Introduce a `_verify_candidate(candidate_path, target)` helper returning
  `(condition, logical_ok, logical_detail)` by running the integrity check and
  logical verification on the candidate; use it in `_restore_from_backup` before
  activation.
- Keep `_post_restore_failure` as the post-activation re-check; wrap it in a
  rollback that restores the archive and classifies a failed rollback as
  non-serviceable.
- Thread `logical_ok` and `active_db_state` (new) through `_failure` (or set them on
  each returned `RecoveryResult`) so every restore outcome populates them.

### Details

Before (defective ordering, current L272-L289):

```python
_stage_restore(...)          # stages AND os.replace (activates) here
failure = _post_restore_failure(db_path, target, dry_run)   # verifies AFTER activate
if failure is not None:
    return failure           # unverified file already active
return RecoveryResult(success=True, ..., dry_run=dry_run)   # logical_ok absent -> None
```

After (verify the candidate, then activate):

```python
```python
staged = _stage_restore(db_path, backup, corrupt_archive, temp_restore, quarantine_dir)  # stage unit, no os.replace (split completed by this row, step 1)
condition, logical_ok, logical_detail = _verify_candidate(temp_restore, target)
if condition != DbCondition.HEALTHY:
    return _failure("restore_verify_failed", ..., dry_run,
                   logical_ok=False, active_db_state="preserved_original")
if not logical_ok:
    action_val = ("verification_unavailable"
                  if logical_detail == "verification_unavailable"
                  else "logical_verify_failed")
    return _failure(action_val, logical_detail, dry_run,
                   logical_ok=False, active_db_state="preserved_original")
_activate_candidate(temp_restore, db_path, staged)   # single atomic swap + sidecars
post = _post_restore_failure(db_path, target, dry_run)
if post is not None:
    return _rollback_or_non_serviceable(db_path, corrupt_archive, post, dry_run)
shutil.rmtree(quarantine_dir, ignore_errors=True)
return RecoveryResult(success=True, action="restored", detail=str(backup),
                      dry_run=dry_run, logical_ok=True, active_db_state="restored")
```

Coordinate the `verification_unavailable` (new) action value with seq 03
(`_run_logical_verification`) and the `active_db_state` (new) field with seq 04
(`RecoveryResult`).

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -k "restore or rollback"` —
  unverified candidates are never activated (live DB byte-identical); rollback
  restores the original; a failed rollback yields the non-serviceable action.
- `uv run pytest tests/db/test_db_recovery.py -k "logical"` — failure actions
  returned instead of `(True, None)`.
- Success-path assertion: `result.logical_ok is True` and `active_db_state ==
  "restored"`.
- `uv run ruff check . && uv run ruff format --check .`, `uv run mypy scripts/`,
  `uv run lint-imports` — clean.

## Completion criteria

- A candidate failing physical or logical verification is never activated; the
  live database is untouched.
- Post-activation failure restores the archived original or reports a
  non-serviceable state; a failed rollback is reported as its own action.
- Every restore outcome sets `logical_ok` to `True`/`False` and names the active
  state; `lint-imports` clean.

## Out of Scope

- Sidecar naming/fail-closed staging (`scripts/db/recovery_restore.py`, seq 01);
  logical-verification fail-closed change (`scripts/db/recovery_verification.py`,
  seq 03); the `RecoveryResult` field addition (`scripts/db/models.py`, seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-194403 | 20261105-195318 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-195318 | Companion test row seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-195318 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-195319 | N/A: docs updated by seq 07 |

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
- **Requirement ID**: `REQ-003` (verify candidate before activation), `REQ-004`
  (rollback / non-serviceable), `REQ-006` (consistent `logical_ok` + active state)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `scripts/db/recovery.py`