# Implementation Procedure — `scripts/db/recovery_restore.py`

## Goal

Make sidecar handling in `scripts/db/recovery_restore.py` atomic and fail-closed for
`REQ-001` (resolve WAL/SHM sidecar paths from the full database filename, e.g.
`rag.sqlite-wal`, not `rag-wal`) and `REQ-002` (quarantine, copy, rename, and
placement failures of WAL/SHM files are fatal recovery errors, not warnings).

## Scope
**Release unit**: sidecar naming and fixtures

## Assumptions

- Production layout is four databases under `/opt/llm/db` named `rag.sqlite`,
  `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite` with `-wal`/`-shm`
  sidecars (`rules/env.md` L71, live `/opt/llm/db` layout `rag.sqlite-wal` /
  `rag.sqlite-shm`). `Path.stem` of `rag.sqlite` is `rag`, so the current
  `{stem}{suffix}` computation yields `rag-wal` / `rag-shm`, which never exist.
- `_stage_restore` keeps its existing contract of raising filesystem failures to
  the caller's cleanup handler (`_restore_from_backup` in
  `scripts/db/recovery.py`); this Plan only changes the internal naming and
  removes the two `logger.warning(...; proceeding without it)` swallow points.
- Cross-plan: `tests/db/test_db_recovery.py` sidecar fixtures
  (`test.db` / `test-wal` / `test-shm`) are replaced with production-equivalent
  names by this Plan's own test row (seq 05) and by the Phase 1 fixture step; the
  production branch and the fixture fix land together so the suite does not break
  in either direction.
- Cross-plan: `drillmetrics001` (sequenced after this Plan) does not touch
  `recovery_restore.py`; no interaction.

## Design decisions

- Compute every sidecar path as `Path(str(db_path) + suffix)` /
  `Path(str(backup) + suffix)` so the computed name is `rag.sqlite-wal`, matching
  the real file. Apply the same rule to the quarantine destination name using
  `db_path.name` so it stays unique and collision-free.
- Remove the `try/except OSError` that downgrades failures to warnings in both
  `_quarantine_sidecar_files` and `_stage_restore` step 4a; let `OSError`
  propagate so the caller reports a failed recovery (`AC-002`).

## Alternatives considered

- Keeping the warning-and-proceed posture was rejected: the previous "success" was
  an unverified activation next to a missing sidecar, which is exactly the defect
  this Plan fixes.
- Adding a compatibility alias for the old `rag-wal` name was rejected: no real
  file is ever named that way, so there is nothing to preserve.

## Compatibility considerations

- `scripts/db/recovery.py` imports `_resolve_backup`, `_stage_restore` from
  `db.recovery_restore`; the public signatures are unchanged, so the import
  contract (`lint-imports`) is preserved. Only internal behavior changes.
- `tests/agent/test_wal_backup_security.py` characterizes sidecar path-traversal
  safety; it does not assert the old `rag-wal` naming, so it stays green. Verify
  it during validation.

## Security considerations

- Sidecar paths stay derived from the resolved database path with no new
  interpolation; the full-filename join `str(db_path) + suffix` cannot introduce a
  path traversal beyond what `db_path` already carries. Confirm no test asserts a
  traversal vector that depends on `.stem`.

## Rollback considerations

- Revert the commit that lands this change; the pre-change behavior logged
  warnings and proceeded, which is the defective behavior being removed.

## Implementation

### Target file

`scripts/db/recovery_restore.py`

### Procedure

1. In `_quarantine_sidecar_files` (current L22-L38): replace the `stem`-based
   sidecar name with the full-database-filename form and remove the
   warning-swallowing `except OSError`.
2. In `_stage_backup_sidecars` (current L41-L53): replace the `stem`-based
   sidecar name with the full-database-filename form.
3. In `_stage_restore` (current L75-L114): replace the step-4a staged-sidecar
   rename target (current L105-L114) with the full-database-filename form and
   remove its `except OSError` warning; keep the staging copies at L97-L102
   consistent with the full-filename rule.
4. Run the sidecar/quarantine/stage tests and the whole `tests/db/test_db_recovery.py`
   suite; confirm no code path computes `rag-wal` / `rag-shm` (grep).

### Method

- `_quarantine_sidecar_files`: compute `sidecar = Path(str(db_path) + suffix)`,
  build the quarantine name from `db_path.name` (e.g. `rag.sqlite-wal_corrupt_<ts>`),
  copy then unlink, and let any `OSError` propagate (no `try/except`).
- `_stage_backup_sidecars`: compute `sidecar = Path(str(backup) + suffix)` and
  stage to `temp_restore_dir / f"{backup.name}{suffix}"`.
- `_stage_restore` step 4a: move each staged sidecar to
  `db_path.parent / f"{db_path.name}{suffix}"` and let `OSError` propagate (no
  `try/except`).

### Details

Before (defective):

```python
stem = db_path.stem
...
sidecar = db_path.parent / f"{stem}{suffix}"          # -> rag-wal, never exists
...
except OSError:
    logger.warning("Failed to quarantine sidecar file %s; proceeding without it", sidecar)
```

After (fail-closed, full-filename):

```python
for suffix in ("-wal", "-shm"):
    sidecar = Path(str(db_path) + suffix)              # -> rag.sqlite-wal
    if sidecar.exists():
        quarantine_name = f"{db_path.name}{suffix}_corrupt_{ts}"
        quarantine_path = quarantine_dir / quarantine_name
        shutil.copy2(sidecar, quarantine_path)         # OSError propagates
        sidecar.unlink()
```

Apply the analogous change to `_stage_backup_sidecars` (use `backup.name`) and to
`_stage_restore` step 4a (use `db_path.name`). Remove both
`logger.warning(...; proceeding without it)` blocks. The caller
(`_restore_from_backup` in `scripts/db/recovery.py`) already treats a raised
`OSError` as a failed recovery, satisfying `AC-002`.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -k "sidecar or quarantine or stage"` —
  no sidecar failure yields a successful result; computed names match
  `rag.sqlite-wal` / `rag.sqlite-shm`.
- `uv run ruff check . && uv run ruff format --check .` — clean.
- `uv run lint-imports` — 0 broken contracts.
- `rg "rag-wal|rag-shm" scripts/` — no producer of the wrong naming remains.

## Completion criteria

- Every sidecar path in `recovery_restore.py` is `Path(str(<db>) + suffix)`; no
  `.stem`-derived sidecar name remains.
- Quarantine, copy, rename, and placement failures raise instead of logging a
  warning and proceeding.
- Sidecar tests use production-equivalent names and pass; `lint-imports` clean.

## Out of Scope

- The verify-before-activation ordering and rollback (`scripts/db/recovery.py`,
  seq 02); the `RecoveryResult` contract (`scripts/db/models.py`, seq 04); the
  logical-verification fail-closed change (`scripts/db/recovery_verification.py`,
  seq 03).

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
- **Requirement ID**: `REQ-001` (full-filename sidecar resolution), `REQ-002` (fatal sidecar failures)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `scripts/db/recovery_restore.py`
