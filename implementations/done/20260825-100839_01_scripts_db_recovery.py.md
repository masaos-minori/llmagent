## Goal
- REQ-001: `_restore_from_backup()` should re-verify the restored database's integrity
  (reusing `_run_integrity_check()`) after the atomic `os.replace()`, before returning
  `success=True`.
- REQ-002: `recover_corruption()` should reject a `target` value that is not actually
  supported, instead of the current ternary silently treating anything other than
  `"rag"` as `"session"`.

## Adversarial verification note (added during Step 2 of `prompts/03_implementation.md`)
Re-reading the current code before implementing surfaced a more severe, related bug
that the original REQ-002 scoping (and this document's now-corrected "Out of scope"
entry below) missed: `recover_corruption()`'s `db_path = Path(db_cfg.rag_db_path if target == "rag" else db_cfg.session_db_path)` line resolves `target="workflow"` and
`target="eventbus"` to `session_db_path` too — not only genuinely unsupported values.
Concretely, for `recover_corruption(target="workflow")`: `_run_integrity_check()` is
called against the **session** database file (mislabeled internally as the
`"workflow"` target), and if that file happens to be healthy, control reaches
`return _vacuum_db(target)` — which resolves its own path independently via
`SQLiteHelper("workflow")` (no explicit `db_path`) and therefore VACUUMs the **real**
`workflow.sqlite`, without ever having integrity-checked it, and without ever
reaching the ADR-011 "no_recovery_allowed" domain-policy gate a few lines below.
This means the ADR-011 Requirement #6 protection ("workflow/eventbus recovery is
prohibited, explicit decision required") is silently bypassed whenever the session
database happens to be healthy at call time. This is not a hypothetical: `"workflow"`
and `"eventbus"` are documented, supported `target` values (see this function's own
docstring), so this path is reachable through the public API, not only through a
malformed/unsupported input.
Fix: REQ-002's implementation must correct the `db_path` resolution for **all four**
supported targets (not add a guard clause next to an unchanged ternary), so that
`target="workflow"`/`"eventbus"` integrity-check and (if healthy) VACUUM the correct
file — closing the ADR-011 bypass — while still rejecting genuinely unsupported
values. See the revised Design decisions / Implementation / Validation plan below.

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
- REQ-002 (revised per Adversarial verification note above): replace the ternary
  `db_path = Path(db_cfg.rag_db_path if target == "rag" else db_cfg.session_db_path)`
  with `target_db_path = getattr(db_cfg, f"{target}_db_path", None)` followed by a
  guard clause rejecting `None` (i.e. any `target` outside the four `DbConfig`
  fields `rag_db_path`/`session_db_path`/`workflow_db_path`/`eventbus_db_path`) with
  `success=False, action="unsupported_target"`. This single change both rejects
  genuinely unsupported values (closing REQ-002 as originally scoped) and fixes the
  workflow/eventbus wrong-file bug (closing the ADR-011 bypass found above), because
  `target_db_path` is now correct for all four supported targets, not only `"rag"`.

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
1. Replace the `db_path` ternary in `recover_corruption()` with the
   `getattr(db_cfg, f"{target}_db_path", None)` resolution plus its unsupported-
   target guard clause.
2. Add a `target` parameter to `_restore_from_backup()`, replacing the hardcoded
   `target="rag"` used by the existing pre-restore backup check.
3. Add the post-`os.replace()` integrity re-check, gating the `success=True` return.
4. Pass `target=target` from `recover_corruption()`'s call to `_restore_from_backup()`.
5. Update `recover_corruption()`'s docstring `action values:` list with the two new
   action strings.

### Method
- Target resolution + guard clause (replaces the old ternary):
  ```python
  db_cfg = build_db_config()
  target_db_path = getattr(db_cfg, f"{target}_db_path", None)
  if target_db_path is None:
      return RecoveryResult(
          success=False,
          action="unsupported_target",
          detail=f"unsupported target: {target!r}",
          dry_run=dry_run,
      )
  db_path = Path(target_db_path)
  ```
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
- REQ-002 (revised) additionally closes an ADR-011 policy-bypass gap discovered
  during adversarial verification: `target="workflow"`/`"eventbus"` no longer
  integrity-checks/vacuums the wrong file, so the domain policy gate
  (`no_recovery_allowed`) is reachable as intended whenever those databases are
  actually corrupt.
- REQ-001 closes a false-success gap: `success=True` after `os.replace()` no longer
  reports a still-corrupt database as recovered.
- All changes only narrow/correct behavior (reject more, operate on the correct
  file, succeed less on failure); none introduce a new input path or privilege
  change.

## Rollback considerations
- Additive changes confined to one file, two functions, and one new constant; revert
  via a single commit revert.
- No persistent data, schema, or config format change; no migration needed.

## Validation plan
- `tests/db/test_db_recovery.py`: patch `_run_integrity_check` with a 3-call
  `side_effect` (current DB = CORRUPTION, backup = HEALTHY, post-restore = CORRUPTION)
  and assert `result.success is False` / `result.action == "restore_verify_failed"`
  (REQ-001); call `recover_corruption(target="bogus")` and assert
  `result.success is False` / `result.action == "unsupported_target"` (REQ-002).
- New regression case (Adversarial verification note): build a `DbConfig` with four
  distinct, distinguishable path values for `rag_db_path`/`session_db_path`/
  `workflow_db_path`/`eventbus_db_path`; patch `_run_integrity_check` to record the
  `db_path` it was called with; call `recover_corruption(target="workflow")` and
  assert `_run_integrity_check` was called with `Path(workflow_db_path)`, not
  `Path(session_db_path)` — proving the ADR-011 bypass is closed. Repeat for
  `target="eventbus"`.
- `tests/db/test_db_maintenance.py::TestRecoverCorruption` (the parallel test module
  that imports via `db.recovery`): add equivalent cases.
- `uv run pytest tests/db/test_db_recovery.py tests/db/test_db_maintenance.py -v`
- Full regression: `uv run pytest` and `uv run pre-commit run --all-files`.

## Out of scope
- REQ-010 (corrupt-archive retention/cleanup policy) — separate document for
  `scripts/db/maintenance.py`.
- Whether routine VACUUM-when-healthy should itself be prohibited for
  `workflow`/`eventbus` (as opposed to only corruption *recovery*) — ADR-011
  Requirement #6 is about recovery from corruption, not routine maintenance; this
  document only fixes the wrong-file bug, it does not change which operations are
  permitted once integrity is correctly checked against the right file.
- REQ-003 through REQ-009 — different files/subsystems, not covered here.
- `_classify_error()`/`DbCondition` changes — already confirmed correct (Plan
  Out-of-Scope, H-1).
- `docs/adr/ADR-011-database-corruption-recovery-safety-boundary.md` status/Known
  Deviations updates — out of scope for this document (REQ-009 covers ADR-001 only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-101500 | 20260825-102400 | Also fixed the ADR-011 bypass found during adversarial verification (see note above and doc's Design decisions) |
| 2 | Add or update tests per Validation plan | Completed | 20260825-102400 | 20260825-103200 | Added 4 new cases to `tests/db/test_db_recovery.py`, 2 new cases to `tests/db/test_db_maintenance.py`; fixed 2 existing tests whose mocks needed a 3rd `_run_integrity_check`/`fetchone` result for the new post-restore check |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-103200 | 20260825-104500 | ruff/mypy/lint-imports/bandit clean; diff-cover 100% on `scripts/db/recovery.py`; targeted tests pass; full-suite run confirmed no new regressions (116 pre-existing failures + 12 pre-existing collection errors, all verified via `git stash` to predate this change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260825-104500 | 20260825-104800 | Updated SHARED-001/002/003 in `docs/90_shared_90_inconsistencies_and_known_issues.md` (routing.md-mapped); `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` also describes these gaps but has no routing.md mapping — recorded below, not edited |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` (§9.4/§9.5/§9.7) describes the same now-fixed gaps but has no entry in `routing.md`'s Docs → task mapping table, so it was not edited per Step 5's rule against guessing | N/A: no routing.md mapping exists | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/db/recovery.py` change | 1 | Code Change | Completed | — | — |
| `tests/db/test_db_recovery.py` cases | 2 | Test | Completed | — | — |
| `tests/db/test_db_maintenance.py` cases | 2 | Test | Completed | — | — |
| `docs/90_shared_90_inconsistencies_and_known_issues.md` update | 4 | Doc Change | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/db/recovery.py
