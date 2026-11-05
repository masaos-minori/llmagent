# Implementation Procedure — `tests/db/test_db_recovery.py`

## Goal

Update the recovery unit/integration tests in `tests/db/test_db_recovery.py` so
they exercise the atomic, fail-closed protocol produced by seq 01–04 instead of
the defective behavior they currently encode: production-equivalent sidecar
naming, verify-before-activation, rollback / non-serviceable actions, populated
`logical_ok` + `active_db_state`, and the fail-closed mandatory logical
verification.

## Scope
**Release unit**: contract activation

## Assumptions

- This is the shared test file touched by seq 01 (`recovery_restore.py` sidecar
  naming), seq 02 (`recovery.py` ordering/rollback), seq 03
  (`recovery_verification.py` fail-closed), and seq 04 (`models.py`
  `active_db_state`). All four changes land together; this row's edits assume the
  post-predecessor file state.
- The current sidecar fixtures (`test.db` / `test-wal` / `test-shm`,
  `test_quarantine_sidecar_files` L655-L686, `test_stage_backup_sidecars`
  L689-L718) encode the wrong `.stem` naming and must be rewritten to
  `test.sqlite` / `test.sqlite-wal` / `test.sqlite-shm`.
- The five `assert result.logical_ok is not True` assertions (L370, L403, L436,
  L469, L503) assert the failure path but are loose; they become strict
  `is False` plus an `active_db_state == "preserved_original"` assertion.
- Cross-plan: `sessmoke001` (sequenced before this Plan) removes the
  `write_smoke_fail` trigger from `_session_inconsistency_detail` and the
  `write_smoke_test_ok` field from `SessionConsistencyReport`. Any test in this
  file that constructs a `SessionConsistencyReport` with `write_smoke_test_ok`
  (e.g. the session-detail tests around L1033-L1082) must drop that argument;
  those tests are owned by `sessmoke001` and are expected to be gone by the time
  this row runs. If any remain, remove the `write_smoke_test_ok=` keyword.
- Cross-plan: `drillmetrics001` (sequenced after this Plan) edits
  `tests/db/test_recovery_drill.py`, not this file.

## Design decisions

- Fixtures use production-equivalent names so the computed sidecar path
  `Path(str(db_path) + suffix)` resolves to a real file.
- Add one test per fail-closed branch: unverified candidate never activated
  (live DB byte-identical), post-activation failure restores the original, and a
  failed rollback yields the non-serviceable action.
- Add a WAL-mode integration test that stages `-wal`/`-shm` sidecars alongside
  the candidate and confirms they are moved to their final full-filename
  locations on success.
- Add a fault-injection test that raises during the post-activation re-check to
  exercise the rollback path.

## Alternatives considered

- Keeping the loose `is not True` assertions was rejected: the plan requires
  `logical_ok` to be populated to a definite `False` on every failure path
  (REQ-006); `is not True` also passes for `None`, which is exactly the defect.

## Compatibility considerations

- The fixture helper names and signatures stay the same; only the filenames they
  create change. No new top-level imports beyond `time`/`tempfile` already used.
- The `test_unknown_target_skips_verification` test (L1084-L1088) asserts
  `(True, None)` for the non-mandatory `workflow` target; it stays valid because
  seq 03 fails closed only for the mandatory `rag`/`session` domains. Do not
  change it.

## Security considerations

- N/A: test-only change; fixtures live under `tmp_path`, no production paths.

## Rollback considerations

- Revert the commit; the pre-change tests characterize the defective behavior.

## Implementation

### Target file

`tests/db/test_db_recovery.py`

### Procedure

1. Rewrite `test_quarantine_sidecar_files` (L655-L686) and
   `test_stage_backup_sidecars` (L689-L718) to use `test.sqlite` with
   `test.sqlite-wal` / `test.sqlite-shm` sidecars, and assert that a quarantine
   or placement failure raises instead of being swallowed.
2. Harden the five failure-path assertions (L370, L403, L436, L469, L503):
   `assert result.logical_ok is False` and
   `assert result.active_db_state == "preserved_original"`.
3. Add a success-path assertion where a fully verified candidate is activated:
   `assert result.logical_ok is True` and
   `assert result.active_db_state == "restored"`.
4. Add a "candidate never activated" test: inject a failing integrity check on
   the staged candidate and assert the live database bytes are unchanged and the
   result is a failure with `active_db_state == "preserved_original"`.
5. Add a rollback test: make the post-activation re-check fail and assert the
   archived original is restored (`active_db_state == "restored"` again, or the
   non-serviceable action when the restore itself fails).
6. Add a WAL-mode integration test: stage `test.sqlite-wal` / `test.sqlite-shm`
   alongside the candidate, run a successful restore, and assert the sidecars
   end at `test.sqlite-wal` / `test.sqlite-shm` (full-filename locations).
7. Drop any `write_smoke_test_ok=` keyword from remaining session-report
   construction calls (owned by `sessmoke001`).

### Method

- Build fixtures with `db_path = tmp_path / "test.sqlite"` and create the
  sidecars as `db_path.parent / f"{db_path.name}{suffix}"`.
- For the fail-closed branches, patch `_run_logical_verification` (or the
  integrity check) to return a failure and assert no `os.replace` occurred
  (patch `os.replace` and assert it was not called on the pre-activation path).
- For rollback, patch `_post_restore_failure` to return a non-None failure and
  assert the archive path is copied back.

### Details

Before (encodes the defect):

```python
def test_quarantine_sidecar_files():
    db_path = Path(tmpdir) / "test.db"
    wal_path = Path(tmpdir) / "test-wal"          # wrong: .stem-derived name
    ...
```

After (production-equivalent, fail-closed):

```python
def test_quarantine_sidecar_files():
    db_path = Path(tmpdir) / "test.sqlite"
    wal_path = db_path.parent / f"{db_path.name}-wal"   # -> test.sqlite-wal
    shm_path = db_path.parent / f"{db_path.name}-shm"
    ...
```

Keep `test_unknown_target_skips_verification` (L1084-L1088) asserting
`(True, None)` for `workflow`; seq 03 preserves the non-mandatory skip.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -k "sidecar or quarantine or stage"`
  — fixtures use production names; failures raise.
- `uv run pytest tests/db/test_db_recovery.py -k "restore or rollback or logical"`
  — unverified candidates are never activated; rollback restores the original;
  non-serviceable action on failed rollback.
- `uv run pytest tests/db/test_db_recovery.py -k "skips_verification"` — still
  `(True, None)` for `workflow`.
- `uv run ruff check . && uv run ruff format --check .`, `uv run lint-imports`
  — clean.

## Completion criteria

- Sidecar fixtures use production full-filename names and pass.
- Every fail-closed branch has a dedicated test; `logical_ok` is asserted to be
  a definite bool and `active_db_state` names the active state.
- WAL-mode integration and rollback-fault-injection tests exist and pass.

## Out of Scope

- The source changes themselves (`scripts/db/recovery_restore.py` seq 01,
  `scripts/db/recovery.py` seq 02, `scripts/db/recovery_verification.py` seq 03,
  `scripts/db/models.py` seq 04); this row only mirrors them in tests.
- `tests/db/test_recovery_drill.py` (seq 06); `sessmoke001`'s removal of the
  `write_smoke_fail` trigger.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion test row seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs updated by seq 07 |

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
- **Requirement ID**: `REQ-007` (fail-closed branches, WAL integration, fault injection)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `tests/db/test_db_recovery.py`
