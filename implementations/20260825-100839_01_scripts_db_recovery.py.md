## Goal
- REQ-001: `_restore_from_backup()` should re-verify the restored database's integrity
  (reusing `_run_integrity_check()`) after the atomic `os.replace()`, before returning
  `success=True`.
- REQ-002: `recover_corruption()` should reject a `target` value that is not actually
  supported, instead of the current ternary silently treating anything other than
  `"rag"` as `"session"`.

## Scope
- In scope: `scripts/db/recovery.py`'s `_restore_from_backup()` and
  `recover_corruption()` only (plus one new module-level constant).
- Out of scope: REQ-010 (corrupt-archive retention policy) — handled in the separate
  `scripts/db/maintenance.py` document.

## Assumptions
- `_classify_error()`'s `sqlite3.DatabaseError` classification is already confirmed
  correct (Plan's Out-of-Scope, H-1) and is not changed here.
- The workflow/eventbus "no automatic recovery, explicit decision required" policy
  (already documented in `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
  §9.7) is unchanged by REQ-002; REQ-002 only rejects values outside the four
  supported targets (`"rag"`, `"session"`, `"workflow"`, `"eventbus"`).
- `RecoveryResult`'s existing fields (`success`/`action`/`detail`/`dry_run`) are
  sufficient; no new field is needed, only new `action` string values.

## Design decisions
- REQ-001: call `_run_integrity_check(db_path, target)` again immediately after
  `os.replace()` succeeds; return `success=True, action="restored"` only when the
  result is healthy, otherwise return `success=False, action="restore_verify_failed"`.
- REQ-001 (supporting change): add a `target` parameter to `_restore_from_backup()`
  and use it for both the existing pre-restore backup check and the new post-restore
  check, since verifying with the wrong target's schema assumptions would be
  semantically wrong for a session restore.
- REQ-002: add a module-level `_SUPPORTED_TARGETS = ("rag", "session", "workflow",
  "eventbus")` guard clause at the top of `recover_corruption()`, before any
  target-dependent branching; return `success=False, action="unsupported_target"`
  for anything outside that set.

## Alternatives considered
- Re-running all of `recover_corruption()` to verify a restore — rejected; it would
  re-enter classification/dry-run/domain-policy branches unnecessarily, against the
  Plan's Design section (reuse `_run_integrity_check()` directly).
- Leaving the pre-restore check's `target="rag"` hardcoding in place while only
  adding a new post-restore check — rejected; it would leave the same target-mismatch
  bug in the newly-touched code path.
- Implementing REQ-002 as a dispatch dict with `try`/`except KeyError` — rejected;
  the current control flow is simple `if`/ternary branching, and an allow-list guard
  clause is the smaller diff.
- Normalizing an unknown `target` to `"session"` with a warning log — rejected; this
  is exactly the silent behavior the Plan requires closing.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Add `_SUPPORTED_TARGETS` near `DbCondition`.
2. Add the unsupported-target guard clause at the top of `recover_corruption()`.
3. Add a `target` parameter to `_restore_from_backup()`, replacing the hardcoded
   `target="rag"` used by the existing pre-restore backup check.
4. Add the post-`os.replace()` integrity re-check, gating the `success=True` return.
5. Pass `target=target` from `recover_corruption()`'s call to `_restore_from_backup()`.
6. Update `recover_corruption()`'s docstring `action values:` list with the two new
   action strings.

### Method
- Guard clause: `if target not in _SUPPORTED_TARGETS: return RecoveryResult(success=False, action="unsupported_target", detail=f"unsupported target: {target!r}", dry_run=dry_run)`.
- Post-restore check: `condition, detail = _run_integrity_check(db_path, target)`
  called after `os.replace()` succeeds, before constructing the return value; when
  `condition != DbCondition.HEALTHY`, return `RecoveryResult(success=False, action="restore_verify_failed", detail=detail or f"post-restore integrity check failed: {condition.value}", dry_run=dry_run)`.
- The existing `OSError` handler around `shutil.copy2`/`os.replace` is unchanged; the
  new check is added to the success path of that `try` block, not inside `except`.

## Compatibility considerations
- The new `target` parameter on `_restore_from_backup()` defaults to `"rag"`, so its
  only existing caller (`recover_corruption()`) is unaffected unless updated (which
  this change does).
- `recover_corruption()`'s public signature (`backup_path`, `target`, `dry_run`) is
  unchanged.
- Callers that branch on `RecoveryResult.action` (e.g.
  `scripts/agent/services/db_maintenance_service.py::DbMaintenanceService.recover_session()`,
  which only checks `raw.action == "restored"`) are unaffected — the new action
  strings fit the existing "anything other than `restored` is a failure" pattern.

## Security considerations
- REQ-002 closes a fail-open-shaped gap: an unexpected `target` value is now rejected
  explicitly instead of silently operating on the session database.
- REQ-001 closes a false-success gap: `success=True` after `os.replace()` no longer
  reports a still-corrupt database as recovered.
- Both changes only narrow behavior (reject more, succeed less); neither introduces a
  new input path or privilege change.

## Rollback considerations
- Additive changes confined to one file, two functions, and one new constant; revert
  via a single commit revert.
- No persistent data, schema, or config format change; no migration needed.

## Validation plan
- `tests/db/test_db_recovery.py`: patch `_run_integrity_check` with a 3-call
  `side_effect` (current DB = CORRUPTION, backup = HEALTHY, post-restore = CORRUPTION)
  and assert `result.success is False` / `result.action == "restore_verify_failed"`
  (REQ-001); call `recover_corruption(target="bogus")` and assert
  `result.success is False` / `result.action == "unsupported_target"`, and that
  `build_db_config`/`_run_integrity_check` were never called (REQ-002).
- `tests/db/test_db_maintenance.py::TestRecoverCorruption` (the parallel test module
  that imports via `db.recovery`): add equivalent cases.
- `uv run pytest tests/db/test_db_recovery.py tests/db/test_db_maintenance.py -v`
- Full regression: `uv run pytest` and `uv run pre-commit run --all-files`.

## Out of scope
- REQ-010 (corrupt-archive retention/cleanup policy) — separate document for
  `scripts/db/maintenance.py`.
- Correcting the `db_path` ternary's workflow/eventbus mapping — not required by
  REQ-002's Acceptance criterion (only rejecting unsupported values is required).
- REQ-003 through REQ-009 — different files/subsystems, not covered here.
- `_classify_error()`/`DbCondition` changes — already confirmed correct (Plan
  Out-of-Scope, H-1).
- `docs/adr/ADR-011-database-corruption-recovery-safety-boundary.md` status/Known
  Deviations updates — out of scope for this document (REQ-009 covers ADR-001 only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc update required by this item |

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
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/db/recovery.py
